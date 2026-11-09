# LearnMuse architecture

## Hermes to Muse mapping

Hermes is a long-running Python agent with a daemon, a prompt
cache, and a forked review agent. Muse is a personal agent with
memory files, skills, subagents, crons, and hooks, and no daemon
fork. LearnMuse keeps Hermes' ideas and re-implements them in
Muse-native shapes. Nothing is copied from Hermes' code.

| Hermes mechanism | Hermes code | Muse-native shape |
|---|---|---|
| Background review fork | `agent/background_review.py`, fork after every turn, replay conversation, write memory/skills, live chat untouched | Three triggers: manual end-of-session review, an isolated review subagent with a transcript excerpt, and a daily cron reading the daily log and staging proposals. Cron is the only truly automatic trigger, and it works from files, not live chat. |
| Nudge every 10 | Memory 10 turns, skills 10 tool iterations, code defaults in `agent/agent_init.py` | Approximate counter in a review-log state file, cron as backstop. Label counts as approximate. |
| `skill_manage` | Create, patch, edit, write_file, remove_file, delete. Skills in `~/.hermes/skills/`, agentskills.io format | Muse writes `SKILL.md` plus `skill.yaml` directly, staged in a proposals folder, installed after approval. |
| Memory | `MEMORY.md` 2,200 chars, `USER.md` 1,375 chars, frozen snapshot at session start, FTS5 session search | `~/MEMORY.md` plus daily logs, skill-imposed budgets, recall via `muse.memory_search` and `muse.db`. |
| Curator | `agent/curator.py`, 7d interval, 2h idle, stale 14d, archive 30d, never delete, consolidate off by default, only `created_by: agent` skills | Weekly cron, no idle detection, body exits quietly if no activity, same thresholds. Only LearnMuse-created skills managed by default. Adoption explicit for others. |
| `/learn`, `/refine`, `/journey` | Manual triggers in Hermes | Manual triggers in LearnMuse: learn a workflow, run a review on demand, show a timeline of learned skills. |
| GEPA | Not in hermes-agent main; lives in a companion repo, offline, PR-only | Later tier only. Offline evolve with DSPy/GEPA, held-out test set, PR-style diff, needs an LLM key and a metric. Never live mutation. |
| Write approval | `memory.write_approval` and `skills.write_approval`, both `false` by default in Hermes | Inverted in LearnMuse: approval ON by default. Stage everything, apply only on approval for that exact change. |
| Verifier | None in Hermes. The fork is judged only by counting what it wrote. | `learnmuse-verify`, a separate role. Verdicts verified / candidate / rejected / blocked, proof capsule, confidence 0-5. |

## The review prompt, adapted

Hermes' prompt says: Be ACTIVE, most sessions produce at least
one skill update, even if small. Patch a loaded skill first, then
an existing umbrella, then a support file, then create a new
class-level skill. Never delete a skill in a review. Do not capture
one-off narratives, transient errors that resolved, or unresolved
failures dressed up as a reliable workflow.

LearnMuse keeps that shape, in original wording, and adds two
rules Hermes lacks: propose actively, apply only after approval;
and every proposal goes through the independent verifier before
it lands.

## Data the pack keeps

- Skills: `~/workspace/custom-skills/learnmuse-*/`, each with
  `SKILL.md` and `skill.yaml`, `include_in_prompt: false`.
- Proposals: staged in `learnmuse-runs/<review>/proposals/`,
  one file per proposed change, with evidence and a before/after.
- Ledger: SQLite via `tools/ledger.py`, one row per learned skill
  or memory entry, with status, confidence, evidence, verdict,
  use count, and last-used date. Modelled on RedMuse's findings DB.
- Curator archive: `~/.hermes/skills/.archive/` in Hermes becomes
  an archive folder under the user's custom-skills tree in Muse,
  recoverable by moving the folder back.
- Review log: `learnmuse-runs/<review>/review-log.md`, with the
  session reviewed, proposals made, verdicts, and what was
  installed or rejected.

## What the pack never does

- Never installs, writes, or deletes a skill without the user's
  approval for that exact change.
- Never deletes in the curator. Archival only, recoverable.
- Never grades its own work. The authoring model is never the
  verifier for the same proposal.
- Never copies Hermes code, another skill's text, or a public
  skill verbatim. Ideas are credited, wording is original.
- Never sends, posts, or contacts anyone. The pack only changes
  the user's own skills and memory.
