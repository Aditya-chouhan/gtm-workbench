import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import ROLES, WorkbenchError, Workspace, validate_plan


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local handoffs and review for GTM agent teams")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--workspace", "-w", default=".", help="Workspace directory (default: current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("roles", help="List the team")
    check = commands.add_parser("validate", help="Validate a workflow without initializing it")
    check.add_argument("plan")
    init = commands.add_parser("init", help="Initialize a workflow ledger")
    init.add_argument("plan")
    commands.add_parser("status", help="Show tasks, dependencies and stale reviews")
    for name in ("handoff", "start", "artifact"):
        command = commands.add_parser(name)
        command.add_argument("task")
    submit = commands.add_parser("submit", help="Snapshot a deliverable for review")
    submit.add_argument("task")
    submit.add_argument("file")
    submit.add_argument("--cite", action="append", required=True)
    review = commands.add_parser("review", help="Approve an inspected hash or request revision")
    review.add_argument("task")
    review.add_argument("decision", choices=("approve", "revise"))
    review.add_argument("--reviewer", required=True)
    review.add_argument("--note", required=True)
    review.add_argument("--sha", help="Artifact SHA-256 required for approval")
    fail = commands.add_parser("fail")
    fail.add_argument("task")
    fail.add_argument("--reason", required=True)
    commands.add_parser("events", help="Print chronological audit events")
    report = commands.add_parser("report", help="Write a standalone HTML review report")
    report.add_argument("output")
    args = parser.parse_args(argv)
    try:
        if args.command == "roles":
            print(json.dumps(ROLES, indent=2))
            return 0
        if args.command in ("validate", "init"):
            plan = validate_plan(read_json(args.plan))
            if args.command == "init":
                Workspace.create(args.workspace, plan)
            print(f"{args.command}: {plan['name']} ({len(plan['tasks'])} tasks)")
            return 0
        ws = Workspace(args.workspace)
        if args.command == "status":
            print(json.dumps(ws.tasks(), indent=2))
        elif args.command == "handoff":
            print(ws.handoff(args.task), end="")
        elif args.command == "start":
            ws.start(args.task)
            print(f"Started {args.task}; use handoff to prepare the model prompt")
        elif args.command == "submit":
            ws.submit(args.task, args.file, args.cite)
            print(f"Submitted {args.task}; inspect artifact and status before review")
        elif args.command == "review":
            ws.review(args.task, args.reviewer, args.decision, args.note, args.sha)
            print(f"Recorded {args.decision}: {args.task}")
        elif args.command == "fail":
            ws.fail(args.task, args.reason)
            print(f"Recorded failure: {args.task}")
        elif args.command == "artifact":
            print(ws.artifact(args.task), end="")
        elif args.command == "events":
            print(json.dumps(ws.events(), indent=2))
        elif args.command == "report":
            target = Path(args.output)
            if target.exists():
                raise WorkbenchError("Report target exists; choose a new output filename")
            target.write_text(ws.report(), encoding="utf-8")
            print(str(target.resolve()))
        return 0
    except (WorkbenchError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
