import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gtm_workbench.core import WorkbenchError, Workspace, validate_plan


def plan():
    return {
        "name": "Test campaign", "goal": "Prepare reviewable work",
        "tasks": [
            {"id": "research", "role": "researcher", "outcome": "Inspect evidence",
             "evidence": ["source.md"], "acceptance": ["Cite source"], "limits": ["Draft only"]},
            {"id": "copy", "role": "outreach-writer", "outcome": "Write a draft",
             "depends_on": ["research"], "acceptance": ["Use approved research"], "limits": ["No sending"]},
            {"id": "review", "role": "campaign-reviewer", "outcome": "Review copy",
             "depends_on": ["copy"], "acceptance": ["Inspect claims"], "limits": ["Review only"]},
        ],
    }


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "source.md").write_text("Evidence version one")
        self.artifact = self.root / "draft.md"
        self.artifact.write_text("Supported draft")
        self.ws = Workspace.create(self.root, plan())

    def status(self, key):
        return next(t["status"] for t in self.ws.tasks() if t["id"] == key)

    def approve(self, key, cite=None):
        self.ws.start(key)
        self.ws.submit(key, self.artifact, cite or ["source.md"])
        sha = next(t["artifact_sha256"] for t in self.ws.tasks() if t["id"] == key)
        self.ws.review(key, "reviewer", "approve", "Checked source and output", sha)
        return sha

    def test_dependencies_block_early_work(self):
        self.assertEqual(self.status("research"), "ready")
        self.assertEqual(self.status("copy"), "blocked")
        with self.assertRaisesRegex(WorkbenchError, "Dependency"):
            self.ws.handoff("copy")
        with self.assertRaises(WorkbenchError):
            self.ws.start("copy")

    def test_full_workflow_persists_across_instances(self):
        self.approve("research")
        self.approve("copy", ["task:research"])
        self.approve("review", ["task:copy"])
        reopened = Workspace(self.root)
        self.assertEqual([t["status"] for t in reopened.tasks()], ["approved"] * 3)
        self.assertEqual(len(reopened.events()), 10)

    def test_review_is_bound_to_exact_artifact(self):
        self.ws.start("research")
        self.ws.submit("research", self.artifact, ["source.md"])
        with self.assertRaisesRegex(WorkbenchError, "hash"):
            self.ws.review("research", "human", "approve", "Checked", "wrong")
        self.assertEqual(self.status("research"), "review")

    def test_snapshot_cannot_change_by_editing_original_artifact(self):
        self.approve("research")
        self.artifact.write_text("Replaced source file")
        self.assertEqual(self.ws.artifact("research"), "Supported draft")
        self.assertEqual(self.status("research"), "approved")

    def test_source_edit_invalidates_entire_downstream_chain(self):
        self.approve("research")
        self.approve("copy", ["task:research"])
        self.approve("review", ["task:copy"])
        (self.root / "source.md").write_text("Different underlying evidence")
        self.assertEqual([t["status"] for t in self.ws.tasks()], ["stale"] * 3)

    def test_changed_source_blocks_submission_of_old_work(self):
        self.ws.start("research")
        (self.root / "source.md").write_text("New facts")
        with self.assertRaisesRegex(WorkbenchError, "restart"):
            self.ws.submit("research", self.artifact, ["source.md"])

    def test_changed_source_blocks_old_approval(self):
        self.ws.start("research")
        self.ws.submit("research", self.artifact, ["source.md"])
        sha = self.ws.tasks()[0]["artifact_sha256"]
        (self.root / "source.md").write_text("New facts")
        with self.assertRaisesRegex(WorkbenchError, "stale"):
            self.ws.review("research", "human", "approve", "Checked", sha)

    def test_revising_parent_invalidates_approved_child(self):
        self.approve("research")
        self.approve("copy", ["task:research"])
        self.ws.review("research", "human", "revise", "Missing nuance")
        self.assertEqual(self.status("copy"), "stale")
        self.artifact.write_text("New research")
        self.approve("research")
        self.assertEqual(self.status("copy"), "stale")
        self.approve("copy", ["task:research"])
        self.assertEqual(self.status("copy"), "approved")

    def test_missing_evidence_prevents_start(self):
        (self.root / "source.md").unlink()
        with self.assertRaisesRegex(WorkbenchError, "Evidence"):
            self.ws.start("research")

    def test_outside_and_symlink_evidence_are_rejected(self):
        for relative in ("../outside.md", "/etc/hosts"):
            with self.assertRaises(WorkbenchError):
                self.ws._source(relative)
        (self.root / "escape.md").symlink_to("/etc/hosts")
        with self.assertRaises(WorkbenchError):
            self.ws._source("escape.md")

    def test_cannot_cite_undeclared_sources(self):
        self.ws.start("research")
        with self.assertRaisesRegex(WorkbenchError, "declared"):
            self.ws.submit("research", self.artifact, ["unread.md"])

    def test_empty_evidence_is_rejected(self):
        self.ws.start("research")
        with self.assertRaises(WorkbenchError):
            self.ws.submit("research", self.artifact, [])

    def test_binary_and_empty_artifacts_are_rejected(self):
        self.ws.start("research")
        for data in (b"", b"\xff\xfe"):
            self.artifact.write_bytes(data)
            with self.assertRaises(WorkbenchError):
                self.ws.submit("research", self.artifact, ["source.md"])

    def test_failure_retry_is_audited(self):
        self.ws.start("research")
        self.ws.fail("research", "Model unavailable")
        self.assertEqual(self.status("research"), "failed")
        self.ws.start("research")
        self.assertEqual(self.status("research"), "working")
        self.assertEqual([e["kind"] for e in self.ws.events()],
                         ["initialized", "started", "failed", "started"])

    def test_active_work_cannot_be_silently_restarted(self):
        self.ws.start("research")
        with self.assertRaises(WorkbenchError):
            self.ws.start("research")

    def test_initialization_never_overwrites_existing_ledger(self):
        before = self.ws.events()
        with self.assertRaises(WorkbenchError):
            Workspace.create(self.root, plan())
        self.assertEqual(before, self.ws.events())

    def test_html_escapes_untrusted_content(self):
        self.artifact.write_text('<script>alert("x")</script>')
        self.approve("research")
        report = self.ws.report()
        self.assertNotIn('<script>alert("x")</script>', report)
        self.assertIn("&lt;script&gt;", report)

    def test_handoff_contains_approved_parent_snapshot(self):
        self.approve("research")
        prompt = self.ws.handoff("copy")
        self.assertIn("Supported draft", prompt)
        self.assertIn("No sending", prompt)

    def test_cli_errors_are_nonzero_without_tracebacks(self):
        result = subprocess.run([sys.executable, "-m", "gtm_workbench", "-w", str(self.root),
                                 "start", "missing"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown task", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class PlanTests(unittest.TestCase):
    def test_all_shipped_plans_validate(self):
        examples = Path(__file__).resolve().parents[1] / "examples"
        for source in examples.glob("*-plan.json"):
            with self.subTest(source=source.name):
                validate_plan(json.loads(source.read_text()))

    def test_demo_is_runnable_and_clearly_simulated(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            result = subprocess.run([sys.executable, str(root / "examples/demo.py"),
                                     "--output", str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SIMULATED DEMO", (out / "report.html").read_text())
            self.assertEqual([t["status"] for t in Workspace(out).tasks()], ["approved"] * 3)

    def test_rejects_cycle(self):
        data = plan()
        data["tasks"][0]["depends_on"] = ["review"]
        with self.assertRaisesRegex(WorkbenchError, "cycle"):
            validate_plan(data)

    def test_rejects_unknown_dependency_role_and_duplicate(self):
        for field, value in (("depends_on", ["missing"]), ("role", "made-up"), ("id", "copy")):
            data = copy.deepcopy(plan())
            data["tasks"][0][field] = value
            with self.assertRaises(WorkbenchError):
                validate_plan(data)

    def test_rejects_invalid_contract_fields(self):
        for field, value in (("acceptance", []), ("limits", "none"), ("evidence", [3]),
                             ("outcome", ""), ("depends_on", ["copy", "copy"]),
                             ("evidence", []), ("role", [])):
            data = copy.deepcopy(plan())
            data["tasks"][0][field] = value
            with self.assertRaises(WorkbenchError):
                validate_plan(data)


if __name__ == "__main__":
    unittest.main()
