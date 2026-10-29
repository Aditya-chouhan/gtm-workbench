# Workflow contracts

A plan is a JSON object with a nonempty `name`, `goal`, and `tasks` list. See the
complete executable example in `examples/outbound-plan.json`.

Each task has:

| Field | Meaning |
|---|---|
| `id` | Unique lowercase slug, starts with a letter, at most 64 characters |
| `role` | One of the keys printed by `python3 -m gtm_workbench roles` |
| `outcome` | Concrete output the task should deliver |
| `acceptance` | Nonempty list of things the reviewer must check |
| `limits` | Nonempty list of constraints for this task |
| `depends_on` | Optional list of prerequisite task IDs; cycles are rejected |
| `evidence` | Optional list of file paths relative to the workspace |

Every submission needs at least one citation. A citation must name one of the
task's declared evidence files, or `task:<id>` for a declared dependency. A root
task should therefore declare evidence. Validation checks graph shape; source
availability is checked when inspecting readiness and starting or handing off work.

## Review loop

1. Initialize a ledger; inspect `status`.
2. Start a ready task; export its `handoff` and give it to your assistant.
3. Submit the output with citations. Inspect `artifact` and all acceptance criteria.
4. Approve its full `artifact_sha256`, or request a revision with a reason.
5. Start the next ready task. Recheck readiness whenever upstream evidence changes.

`fail <task> --reason ...` records execution failure. `start` retries a failed task
after checking dependencies. A working/review/approved task cannot be silently
restarted: request revision first, unless it has become stale. Revision removes
approval immediately, so downstream work waits for a current result.

An approval means a local artifact passed the recorded review. It is not approval
to send, publish, buy, enroll, delete, or deploy anything. Those operations are not
available in this version. No default routines or schedules are created.

## Useful task patterns

- Outbound: qualify accounts → draft message → review readiness.
- Inbound: research supplied thread → classify intent → draft response → review.
- Content: extract supported thesis → brief formats → draft assets → review.
- Learning: define experiment → collect real outcomes → assess limitations → decide.

Do not route every task through every role. Use the smallest graph that has clear
ownership and a reviewable result. A role does not gain extra tool permissions by
being named in a task.
