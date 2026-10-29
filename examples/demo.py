"""Deterministic walkthrough. Artifacts and approvals are simulated fixtures."""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gtm_workbench.core import Workspace


DELIVERABLES = {
    "qualify-accounts": """# Account review — synthetic fixture

| Account | Fit | Evidence | Unknown |
|---|---|---|---|
| Cedar Stack | Priority discovery candidate | 42 employees; implementation manager hiring note, Oct 27 | Pain, buyer and tool stack |
| Marble Apps | Plausible fit | 28 employees; implementation team noted Oct 20 | Pain, timing and current tools |
| Birch Local | Exclude | 6 employees; consumer delivery | Outside stated company type and size |

Source: company.md. Hiring indicates a relevant function, not buying intent.
Recommendation: learn how Cedar Stack currently manages implementation handoffs.
No contacts were sourced and no lookup was performed.
""",
    "draft-email": """# Discovery email — synthetic fixture, unsent

Account: Cedar Stack. Recipient: not identified.
Subject: implementation handoffs

Hi [verified first name],

I saw your team is hiring an implementation manager. How do you track who owns
each customer handoff today?

RelayDesk imports implementation tasks from a CSV into a shared board with
owners and due dates. Would a 20-minute review of one handoff workflow be useful?

Adi

Evidence: company.md; task:qualify-accounts. Personalization requires verifying
the supplied hiring note and selecting the right contact before any use.
No customer outcomes or unsupported integrations are claimed.
""",
    "review-campaign": """# Campaign review — synthetic fixture

Decision: NOT READY TO LAUNCH.

The draft matches documented capabilities and asks about unknown pain.
Account prioritization is supported by supplied ICP facts, not proven intent.
Sources: company.md; task:qualify-accounts; task:draft-email.

Blockers: verify source freshness, identify the buyer, obtain a valid business
contact through an authorized source, check suppression/opt-out handling,
inspect sender readiness and approve final audience, copy, schedule and limits.
This local toolkit does not implement or verify those provider operations.

Suggested experiment (hypothesis only): human review of five verified accounts
before deciding whether a discovery pilot is worth running. Choose success and
stopping criteria with the owner before any send. No campaign results exist.
""",
}


def run(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Output already exists; choose a new directory")
    output.mkdir(parents=True)
    here = Path(__file__).parent
    shutil.copyfile(here / "company.md", output / "company.md")
    plan = json.loads((here / "outbound-plan.json").read_text())
    plan["simulation"] = True
    ws = Workspace.create(output, plan)
    for task in plan["tasks"]:
        key = task["id"]
        (output / f"{key}-handoff.md").write_text(ws.handoff(key))
        ws.start(key)
        artifact = output / f"{key}.md"
        artifact.write_text(DELIVERABLES[key])
        citations = task["evidence"] + ["task:" + p for p in task.get("depends_on", [])]
        ws.submit(key, artifact, citations)
        sha = next(t["artifact_sha256"] for t in ws.tasks() if t["id"] == key)
        ws.review(key, "DEMO / simulated reviewer", "approve",
                  "Fixture review only; this does not authorize sending.", sha)
    (output / "report.html").write_text(ws.report())
    (output / "events.json").write_text(json.dumps(ws.events(), indent=2))
    print(f"Demo complete: {output / 'report.html'}")
    print("3 fixture deliverables, 3 simulated reviews, no network or model calls.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="demo-output")
    args = parser.parse_args()
    try:
        run(args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")
