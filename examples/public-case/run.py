"""Replay local review of manually authored artifacts based on real public sources."""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gtm_workbench.core import Workspace


def run(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Choose a fresh output directory")
    output.mkdir(parents=True)
    source = Path(__file__).parent
    for filename in ("public-sources.md", "product.md"):
        shutil.copyfile(source / filename, output / filename)
    tasks = []
    for key, role, outcome, depends in (
        ("assess-account", "account-analyst", "Assess public fit evidence and unknowns", []),
        ("draft-discovery", "outreach-writer", "Draft a grounded discovery question", ["assess-account"]),
        ("review-case", "campaign-reviewer", "Check claims and external-action blockers", ["assess-account", "draft-discovery"]),
    ):
        tasks.append({"id": key, "role": role, "outcome": outcome, "depends_on": depends,
                      "evidence": ["public-sources.md", "product.md"],
                      "acceptance": ["Cite source facts", "Keep unknowns explicit", "No unobserved results"],
                      "limits": ["Public evidence only", "Local review only; do not contact anyone"]})
    ws = Workspace.create(output, {"name": "PostHog / public-source discovery assessment",
                                  "goal": "Assess a real company's public context without inferring buying intent. Manually authored work and Codex technical self-review; nothing sent.",
                                  "tasks": tasks})
    for task, filename in zip(tasks, ("account-review.md", "draft.md", "review.md")):
        key = task["id"]
        ws.start(key)
        (output / (key + "-handoff.md")).write_text(ws.handoff(key))
        ws.submit(key, source / filename, task["evidence"] + ["task:" + p for p in task["depends_on"]])
        sha = next(t["artifact_sha256"] for t in ws.tasks() if t["id"] == key)
        ws.review(key, "Codex / technical self-review", "approve",
                  "Checked claim scope and source references; no user approval or external action implied", sha)
    (output / "report.html").write_text(ws.report())
    (output / "events.json").write_text(json.dumps(ws.events(), indent=2))
    print(output / "report.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="public-case-output")
    args = parser.parse_args()
    try:
        run(args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")
