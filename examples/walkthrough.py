"""Record real CLI outputs for a fixture workflow; no model calls or external actions."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.demo import DELIVERABLES


def record(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Output already exists; choose a new directory")
    output.mkdir(parents=True)
    workspace = output / "campaign"
    workspace.mkdir()
    here = Path(__file__).parent
    shutil.copyfile(here / "company.md", workspace / "company.md")
    repo = here.parent
    scenes = []

    def cli(*args, expected=0):
        command = [sys.executable, "-m", "gtm_workbench", "-w", str(workspace)] + list(args)
        result = subprocess.run(command, cwd=str(repo), capture_output=True, text=True)
        if result.returncode != expected:
            raise RuntimeError(result.stderr or result.stdout)
        return (result.stdout + result.stderr).strip()

    def state():
        return json.loads(cli("status"))

    def scene(title, command, detail):
        scenes.append({"title": title, "command": command, "detail": detail, "tasks": state()})

    cli("init", str(here / "outbound-plan.json"))
    scene("01 / Evidence comes first", "gtm-workbench status",
          "The root task is ready. Dependent drafts wait for reviewed research.")
    sha = None
    for index, (key, artifact) in enumerate(DELIVERABLES.items()):
        cli("start", key)
        path = output / (key + ".md")
        path.write_text(artifact)
        citations = ["company.md"]
        if index >= 1:
            citations += ["task:qualify-accounts"]
        if index == 2:
            citations += ["task:draft-email"]
        arguments = ["submit", key, str(path)]
        for cite in citations:
            arguments += ["--cite", cite]
        cli(*arguments)
        sha = next(t["artifact_sha256"] for t in state() if t["id"] == key)
        if index == 0:
            scene("02 / Review an exact artifact", "gtm-workbench submit qualify-accounts ...",
                  "The submitted file is snapshotted. Approval requires its SHA-256.")
        cli("review", key, "approve", "--reviewer", "DEMO / simulated reviewer",
            "--note", "Fixture approval for this recorded walkthrough", "--sha", sha)
        if index == 0:
            scene("03 / Approval unlocks downstream work", "gtm-workbench review qualify-accounts approve --sha ...",
                  "Approved research unlocks drafting. The final review still waits.")
    scene("04 / A complete, inspectable chain", "gtm-workbench status",
          "All three fixture outputs are reviewed. No message was sent.")
    source = workspace / "company.md"
    source.write_text(source.read_text() + "\nFixture update: product scope changed; reassess capability claims.\n")
    scene("05 / Changed evidence invalidates old work", "edit company.md → gtm-workbench status",
          "Research, draft and final review all become stale automatically.")
    rejection = cli("review", "review-campaign", "approve", "--reviewer", "DEMO",
                    "--note", "Attempt to reuse old approval", "--sha", sha, expected=2)
    scene("06 / Stale approval is rejected", "gtm-workbench review review-campaign approve --sha OLD_HASH",
          rejection)
    (output / "scenes.json").write_text(json.dumps(scenes, indent=2))
    events = json.loads(cli("events"))
    (output / "events.json").write_text(json.dumps(events, indent=2))
    cast = [{"version": 2, "width": 105, "height": 27,
             "title": "GTM Workbench / actual CLI outputs / synthetic fixture"}]
    for i, s in enumerate(scenes):
        lines = ["GTM WORKBENCH | Aditya Chouhan", "Synthetic data; simulated reviewer; actual CLI state", "",
                 s["title"], "", "$ " + s["command"], ""]
        lines += [f"{t['id']:<23} {t['status']:<10}" for t in s["tasks"]]
        lines += ["", s["detail"], "", "Recorded locally. No model calls, messages or paid actions."]
        cast.append([i * 12, "o", "\u001b[2J\u001b[H" + "\r\n".join(lines) + "\r\n"])
    cast.append([72, "o", "\r\nEnd of walkthrough.\r\n"])
    (output / "walkthrough.cast").write_text("\n".join(json.dumps(item) for item in cast) + "\n")
    print(f"Recorded {len(scenes)} scenes: {output / 'walkthrough.cast'}")
    return scenes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="walkthrough-output")
    args = parser.parse_args()
    try:
        record(args.output)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(2, f"error: {error}\n")
