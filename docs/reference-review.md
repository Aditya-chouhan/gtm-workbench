# Reference review

Reviewed October 29, 2026. Reference:
[timscheuerai/grokbot-gtm-team](https://github.com/timscheuerai/grokbot-gtm-team),
revision `53c611add383eadd8d967609fdff016b125637e7`.
The review covered every Markdown file and the license in that checkout.
The reference's platform capabilities are described by its author; no Grok Bot,
OXYGEN, Claude Code or Codex integration was exercised as part of this review.

## What the reference gets right

It gives each specialist a narrow responsibility, keeps planning separate from
execution, makes drafts the default, and asks for explicit approval on outbound
actions. The setup instructions collect the company's context rather than assuming
one team's tools are universal. Its documentation also acknowledges that connector
restrictions are instructions rather than per-agent technical access controls.

## Coverage and design observations

| Inspected files | Observed design | Workbench response |
|---|---|---|
| `README.md`, `setup-prompt.md` | A prompt creates a hosted bot team; setup depends on the host's capabilities | A runnable local example with no accounts; explicit manual assistant interface |
| `agents/01-chief-of-staff.md` | Central routing and terminal handoff; outcome/inputs/skill/limits | Structured task contracts plus persistent state and review checkpoints |
| `agents/02-outbound-lead.md` | Campaign contracts and one scheduled status rollup | Task-specific acceptance criteria; on-demand JSON and HTML status |
| `agents/03-lead-sourcer.md` | Cold/warm sourcing, evidence and spend boundaries | Supplied-account qualification with explicit unknowns; live sourcing is out of v0.1 |
| `agents/04-outbound-copywriter.md` | Grounded sequence drafting and voice context | Original outreach role; preserve evidence/dependency references in the task ledger |
| `agents/05-sequences-deliverability.md` | Approved list/copy loading and campaign health | Readiness review with declared missing checks; no unsupported claim of live delivery controls |
| `agents/06-social-engagement.md` | Watchlists, engagement queues and comment drafts | Can be modeled as research and content tasks; no social scraper is provided |
| `agents/07-reply-manager.md` | Supplied-thread triage and reply drafting | Conversation analyst contract; no implied inbox integration |
| `agents/08-deal-reactivation.md` | Ranking prior conversations using documented context | Conversation analysis with evidence and unknowns; no numerical close-probability claim |
| `agents/09-head-of-content.md` | Channel planning and role coordination | Editorial brief tasks followed by reviewed production tasks |
| `agents/10-linkedin-writer.md`, `11-x-writer.md`, `12-youtube-writer.md` | Platform-specific writers calling external skills | One original content producer role with explicit requested channel and output |
| `agents/13-graphic-designer.md` | Editable assets and rendering requirements | Asset briefs supported; image generation/rendering is not claimed by this runtime |
| `agents/14-content-room.md` | Group chat for short handoff pointers | Local task dependencies and artifact snapshots; no group chat required |
| `guides/rules.md` | Approval, spend and connector rules in prose | Enforced local task/review transitions, with honest limits on external enforcement |
| `guides/claude-code-and-codex.md` | Persistent terminal sessions and manual/host-driven work dispatch | Portable handoff text; no terminal sessions or authenticated subscriptions started automatically |
| `LICENSE` | MIT permission and notice requirement | Preserve Tim Scheuer's upstream notice alongside this project's MIT license |

## Where improvement can be demonstrated

The inspected source consists of prompts, guides and assets. It does not ship a
local task runtime, structured dependency validator, artifact approval fingerprints,
persistent task ledger or executable workflow tests. Workbench implements these
specific additions. Its tests demonstrate local invariants, not superior GTM
strategy or business performance. Hosted features available outside the reference
repository are outside this comparison.

We deliberately reduce the number of roles and let a task contract supply channel
detail. More agents would increase routing overhead without demonstrating better
results. The implementation, role prose, demo fixtures and documentation are
original. Inspiration is attributed; no personal performance claims or screenshots
from the reference author are represented as Aditya's work.
