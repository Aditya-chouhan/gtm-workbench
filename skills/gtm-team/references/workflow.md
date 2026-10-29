# Optional GTM Workbench interface

Run from an available GTM Workbench checkout with Python 3.9+. No model API or
network connection is required. This skill alone does not install the runtime.

```bash
python3 -m gtm_workbench roles
python3 -m gtm_workbench validate plan.json
python3 -m gtm_workbench -w campaign init plan.json
python3 -m gtm_workbench -w campaign status
python3 -m gtm_workbench -w campaign start task-id
python3 -m gtm_workbench -w campaign handoff task-id
python3 -m gtm_workbench -w campaign submit task-id draft.md --cite source.md
python3 -m gtm_workbench -w campaign artifact task-id
python3 -m gtm_workbench -w campaign events
```

Plan fields: `name`, `goal`, `tasks`. Each task requires `id`, `role`, `outcome`,
nonempty `acceptance` and `limits` lists. Optional `depends_on` lists task IDs;
optional `evidence` lists relative workspace files. The graph must be acyclic.
Task roles: coordinator, researcher, account-analyst, outreach-writer,
campaign-reviewer, conversation-analyst, content-editor, content-producer,
experiment-analyst. Submission citations must name declared evidence files or
`task:<dependency-id>`. At least one citation is required per submission.

A ready task can start. Start captures input hashes. Submit snapshots a UTF-8 text
artifact for review. The user inspects it and its `artifact_sha256` in status.
With actual user authorization for that exact artifact, record:

```bash
python3 -m gtm_workbench -w campaign review task-id approve \
  --reviewer 'Reviewer name' --note 'Actual review findings' --sha FULL_SHA256
```

Revision uses `review task-id revise --reviewer ... --note ...`. Failure uses
`fail task-id --reason ...`; restart with `start`. Changed source/dependency hashes
make prior work stale; restart affected tasks against current inputs. A task may
be blocked by missing evidence or an unapproved prerequisite.

Approvals are self-reported local review records. They authorize no provider action.
The CLI does not send, spend, launch models, schedule, publish or update CRM records.
