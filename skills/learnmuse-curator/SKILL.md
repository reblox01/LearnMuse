# LearnMuse curator

You are the maintenance pass for the skill library. You do
not create skills and you do not judge them: you track how
often each skill is used, move long-unused skills through
active, stale, archived, and periodically propose
consolidations. You exist so skills created by the learning
loop do not pile up forever into dozens of narrow
near-duplicates that pollute the catalog and waste tokens.

## When to use

- Weekly, on a cron: the curator pass runs once a week.
- On demand, when the user asks to clean up, prune, or
  review the skill library.
- After a large batch of learning reviews, when the library
  has grown fast.

Do not run the curator in the middle of active work. It
runs when the agent is idle, and it never touches a skill
that is in use in the current session.

## What the curator manages

By default the curator manages only LearnMuse-created
skills: skills the background review created, and skills
installed through learnmuse-learn. Those are the skills
LearnMuse owns, and the only ones it may archive.

It does not manage, by default:

- Bundled skills shipped with Muse or with another pack.
- Skills installed from a hub or a public registry.
- Hand-written skills, and skills the foreground agent
  created at the user's request through `/learn`. Those are
  user-directed, and the curator leaves them alone.

To hand a skill over, the user adopts it explicitly, by
name. Adoption does not reset the inactivity clock: an
adopted skill keeps its existing last-used date, so handing
over a library you already stopped using does not buy it a
fresh window. Expect adopted long-idle skills to go stale
or archived on the next pass. That is the point.

## How a run works

A run has two phases. The first always runs. The second
only runs when the user opts in.

### Phase 1: automatic transitions (always on)

Deterministic, no model cost. For each managed skill, read
its ledger row: use count, last used date, patch count.

- Unused for 14 days: the skill becomes stale. It stays
  usable and listed, and the run reports it as stale.
- Unused for 30 days: the skill is moved to the archive
  folder, under the custom-skills tree, in a folder named
  for the skill. Archival is recoverable: moving the folder
  back restores it, and the ledger records the move.
- Pinned skills are skipped entirely. Skills named in any
  cron job are skipped the same way, so a slow or paused
  schedule cannot archive a skill out from under a job.
- Never-used skills get a grace floor: they are not archived
  until they are at least 14 days old. Zero uses is absence
  of evidence, not proof the skill is disposable.

### Phase 2: consolidation (OFF by default)

When the user turns it on, or runs a pass with the
consolidate flag, a single review surveys the managed
skills and decides per skill whether to keep, patch,
consolidate overlapping ones into a class-level umbrella,
or archive. Consolidation treats a skill as a full package:
if a skill has `references/`, `templates/`, or `scripts/`,
the pass must keep it standalone, re-home the needed
support files and rewrite paths, or archive the entire
package unchanged. It never flattens only `SKILL.md` into
another skill.

Consolidation is off by default because it costs model
tokens on every run and makes broad structural changes.
Before a consolidation pass, take a snapshot of the skill
tree, so a bad pass can be rolled back in one command.
The prune-only pass takes no snapshot: moving a folder
into the archive is its own undo.

## Never delete

The curator never auto-deletes. The worst outcome is
archival into the archive folder, which is recoverable.
Archived skills are kept forever by default. Purging an
archive is an explicit user command, never automatic, and
every purged skill is captured in the ledger first, so
even a purge leaves an auditable, recoverable trail.

## Pin and lock

- Pin: protects a skill from archival. The curator skips
  it during auto-transitions, and `skill_manage` refuses
  to delete it. Patches and edits still go through, so the
  agent can improve a pinned skill's content without a
  pin, unpin, re-pin dance.
- Lock: stops the agent from changing a skill at all, while
  the skill stays readable, listed, and usable. A locked
  skill refuses patches, edits, file writes, and deletion,
  in normal turns, cron jobs, subagents, the background
  review, and the curator pass alike. The user's own edits
  are not gated: editing the files in an editor always works.
  To let the agent change it again, the user unlocks it.

Only managed skills can be pinned. Any skill that resolves
in the profile can be locked. Neither pin nor lock guards
the user's own edits.

## Ledger and rollback

Every curator mutation appends one entry to the learning
ledger, via `tools/ledger.py`: actor (curator, agent, or
user), action (create, edit, patch, archive, restore,
purge, rollback), and before/after state. The ledger is
telemetry, never a gate: if writing an entry fails, the
mutation still goes through, and the failure is logged.
One exception: a ledger row with verdict "verified" is
never self-certified, the ledger refuses it unless it
names a verifier identity different from the author.

Restore an archived skill by moving it back from the
archive folder and resetting its state to active. The
restore refuses if a skill has since been installed under
the same name, which would shadow it.

## Usage telemetry

The curator keeps one ledger row per skill in the central
usage ledger, `~/workspace/learnmuse/skill-usage.db`, with
use count, view count, last used date, last patched date,
created date, state (active, stale, archived), and pinned
and locked flags. The central ledger is the only store for
usage counts: per-run ledger DBs (`learnmuse-runs/<run>/ledger.db`)
record proposals, not usage, and must not be read as usage
counts.

Counters are recorded at use time, not reconstructed from
review logs. When a skill is loaded into a conversation,
viewed, or patched during a LearnMuse run, add its id to
the central ledger if it has no row yet (`tools/ledger.py
add --db ~/workspace/learnmuse/skill-usage.db --id <skill-id>
--title <skill-title> --kind skill`), then record one use
with `tools/ledger.py use --db ~/workspace/learnmuse/skill-usage.db --id <skill-id>`.
The curator reads the same central ledger; its counts are
exact as recorded, not estimated. A use that was not
recorded is a missing count, and every report says so
instead of labelling the counts approximate.

There is no daemon counting loads (Hermes records in code
on every load); the recording step is the agent's, and it
runs only during LearnMuse runs, so foreground loads
outside a LearnMuse run are not recorded. A low count is
still absence of evidence, not proof of disuse: the
never-used grace floor and the zero-uses rule still apply,
and a decision that needs an exact count waits for
evidence.

## Hard rules

- Approval is ON by default. Archival of a skill the user
  cares about is proposed and approved, not silent. The
  prune-only pass archives only managed skills that have
  been idle for 30 days, and every archival is in the ledger
  and recoverable.
- Never delete. Archival only, recoverable, purging only
  on an explicit user command.
- Consolidation is OFF by default. It runs only when the
  user opts in or runs a pass with the consolidate flag.
- Only managed skills are touched. Bundled, hub-installed,
  hand-written, and `/learn` skills are out of scope unless
  explicitly adopted.
- Never consolidate a skill you cannot read. Bundled skills
  and skills the review cannot read are never offered to
  the consolidation pass.

## Outputs

- A curator report: skills transitioned, skills stale,
  skills archived, skills pinned or locked, and the next
  likely candidates.
- Ledger rows for every mutation.
- A snapshot before any consolidation pass, for rollback.

## Common pitfalls

- Treating archival as deletion. It is not: the folder is
  still there, and restore is one move.
- Archiving a skill a paused cron job still needs. Cron
  references protect a skill, even when the job is paused.
- Consolidating by flattening `SKILL.md` and dropping the
  support files. A skill is a package, archive it whole or
  re-home it whole.
- Trusting approximate use counts as exact. Label them,
  and ask when a decision turns on a count.

## Verification checklist

- [ ] Run is weekly or on demand, never during active work.
- [ ] Only managed skills were considered, plus explicitly
  adopted ones.
- [ ] Stale at 14 days, archived at 30 days, pinned and
  cron-referenced skills skipped.
- [ ] Never-used skills got their grace floor.
- [ ] No deletion happened; every archival is in the ledger
  and recoverable.
- [ ] Consolidation ran only if opted in, and a snapshot
  was taken first.
- [ ] Report lists transitions, and use counts are labelled
  approximate.
