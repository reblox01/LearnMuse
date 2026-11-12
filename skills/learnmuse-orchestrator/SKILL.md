# LearnMuse orchestrator

You run a LearnMuse learning review end to end. You own the
approval gate, the review log, and the budgets. You never install
a skill, write to memory, or change anything the user owns
without the user's approval for that exact change, and you never
report a lesson as learned until the verifier has passed it and
the user has approved it.

## When to use

Invoke first for any LearnMuse run:

- A learning review of a session, a day, or a week of work.
- Teaching Muse a workflow you just walked it through.
- A weekly curator pass over the skill library.
- Any request that says "Muse should learn this" or "stop
  making this mistake".

Do not invoke for ordinary work. A review is a separate run
with its own log, not a side effect of the work itself.

## Inputs

Before anything starts, collect and record all of these in
the review log:

- Session: what is being reviewed, the chat, the day's log,
  or a named date range. Exact, not "recent work".
- Scope: which skills and memory stores are in play, and
  which are out of scope.
- Budgets: max 5 proposals per review, max 3 review rounds,
  max 30 minutes of wall time for a manual review.
- Approval: the user will approve each proposal by name,
  one at a time, before anything is applied. A general
  "go ahead and learn" is not approval for a specific change.
  Optional modes below can change how approval is given,
  never whether it is given, and only if the user chose
  the mode in writing for that run. Record the mode, or
  "default", in the review log.

If any input is missing, stop and ask. A vague session is not
a reviewable session.

## Hard rules

These hold for every LearnMuse run, and no approval can
override them:

- Approval is ON by default. Every proposal is staged first,
  in `learnmuse-runs/<review>/proposals/`, one file per
  proposed change, with evidence and a before/after.
- Approval of a proposal's content is not approval to apply
  it. The user approves the exact change, then the change is
  applied, then the log records it.
- The verifier is a separate role. The agent that wrote a
  proposal never verifies it. A proposal the verifier rejects
  does not land, and a proposal with no verdict does not land.
- The curator never deletes. The worst outcome is archival,
  and archival is recoverable.
- One lesson lives in exactly one place. A lesson is either a
  memory entry or a skill rule, never both.
- Nothing in a review sends a message, posts, or contacts
  anyone. The pack only changes the user's own skills and
  memory.
- Never copy Hermes code, another skill's text, or a public
  skill verbatim. Ideas are credited, wording is original.

## Phase 0: update check

Before the gate, run learnmuse-update. The check runs once,
before any review work, and its result goes in the review log:
LearnMuse HEAD before and after any fast-forward pull, plus
one status line per source in `sources.yaml`. LearnMuse itself
auto-pulls on a fast-forward only. Reference sources never
rewrite skill content; a methodology delta becomes a follow-up
task. Nothing updates mid-run, and nothing pushes automatically.
A run that skipped the check, or proceeded under a staleness
warning, says so in its review log.

## Phase 1: gate

Record the session, scope, and budgets in
`learnmuse-runs/<review>/review-log.md`. Confirm the user
wants a review of this session and scope. If the session is
still running, wait: a review replays finished work, it never
reviews work that is still in flight.

## Phase 2: review

Run learnmuse-review. It replays the session and proposes
lessons. It prefers patching a skill that was in play, then
an existing umbrella skill, then a support file, and only
then a new class-level skill. It never deletes a skill in a
review. It stops at 5 proposals. If it finds nothing worth
saving, it says "Nothing to save" and stops; it never invents
a proposal to fill the budget.

The review runs as a separate pass from the work: as a manual
end-of-session review, as an isolated review subagent given a
transcript excerpt, or as a daily cron reading the daily log.
A cron review works from files, not from a live conversation.

When you load, view, or patch a skill during this run, add its id to the central ledger if it has no row yet, then record one use with `tools/ledger.py use --db ~/workspace/learnmuse/skill-usage.db --id <skill-id>`.

## Phase 3: verify

Run learnmuse-verify on every proposal, one at a time. The
verifier re-runs each proposal's evidence unchanged and
returns one verdict: verified, candidate, rejected, or blocked,
with a proof capsule and a confidence score from 0 to 5.
Verified needs 4 to 5. A rejected proposal is dropped and the
reason is logged. A blocked proposal waits for the missing
evidence and is logged as blocked, never as clean.

## Phase 4: approval

Show the user each verified proposal with its before/after,
its evidence, and its verdict. Apply only the proposals the
user approves, by name, for that exact change. If the user
approves a patch, apply the patch exactly as shown; a
different patch needs a new proposal and a new verdict.

## Phase 5: install

For each approved proposal, apply it to the right place:

- A skill patch or new skill goes into
  `~/workspace/custom-skills/` as `SKILL.md` plus `skill.yaml`.
  A new skill is written to a temp folder first, checked, and
  only then moved into place.
- A memory entry goes into `~/MEMORY.md` or `~/memory/`,
  following learnmuse-memory budgets.
- Record every applied change in the ledger with
  `tools/ledger.py`, with status, confidence, evidence, and
  verdict.

## Phase 6: log and close

Finish the review log with: session reviewed, proposals made,
verdicts, what was installed, what was rejected or blocked,
and what to check next time. The next session is the test:
run the same kind of task again and check the mistake does
not repeat. If it repeats, the lesson did not land, and the
next review must say so.

## Budgets

- Max 5 proposals per review. A sixth lesson waits for the
  next review.
- Max 3 review rounds per review. A proposal rejected twice
  is dropped for this review.
- Max 30 minutes wall time for a manual review. A cron review
  that cannot finish in its slot stops and logs where it got to.
- One attempt per review pass. A failed review is logged and
  dropped, not retried in a loop.

## Optional modes: tap-free and token-saver

Approval stays ON by default. These modes are opt-in only,
chosen by the user in writing for a named run or a named
period, and recorded in the review log. A mode is never
assumed, and no mode overrides the hard rules above: the
verifier is still separate, a rejected or blocked proposal
never lands, and the curator never deletes.

1. Batch approve. The user reviews the verified list once
   and approves by name in one message, for example
   "apply 1, 3, and 4". This is still per-change approval
   by name, just in one message instead of one tap per
   proposal. A proposal not named in the batch does not land.
2. Auto-install verified confidence 5 only. The user opts
   in in writing, for a named review or a named period.
   Only a proposal with verdict verified and confidence 5
   installs without a per-change tap. Confidence 4,
   candidate, rejected, and blocked never auto-install.
   The user can revoke the opt-in at any time, and
   revocation takes effect immediately. Every auto-install
   is logged in the review log and the ledger, with the
   opt-in recorded. Default: OFF.
3. Weekly digest. Instead of telling the user about each
   verified proposal as it lands, collect verified
   proposals and send one digest per week. The user
   approves by name from the digest. Nothing installs
   before digest approval.
4. Low-token mode. Weekly review cadence instead of daily,
   max 3 proposals per review instead of 5, and curator
   monthly instead of weekly. Use this when background
   usage needs trimming. The daily cron in the README
   prompt is the default, this mode replaces it only
   when the user chooses it.

## Outputs

- `learnmuse-runs/<review>/review-log.md`: the full record.
- `learnmuse-runs/<review>/proposals/`: one file per proposal.
- Ledger rows for every proposal, via `tools/ledger.py`.
- A short closing message: proposals, verdicts, installed,
  rejected, blocked, and the next check.

## Common pitfalls

- Treating "the user said go" as approval for a specific
  change. It is not. Approval names the change.
- Letting the review author also verify. The verifier is
  separate, always.
- Saving a one-off story as a skill. A skill is a rule for a
  class of task, not a diary entry.
- Saving the same lesson in memory and in a skill. Pick one.
- Reviewing a session that is still running. Wait for it to
  finish, or the review will learn from half a story.

## Verification checklist

- [ ] Review log exists with session, scope, and budgets.
- [ ] Update check ran, or its absence is logged.
- [ ] At most 5 proposals, each staged with evidence and
  a before/after.
- [ ] Every proposal has a verifier verdict, none missing.
- [ ] Only approved, verified proposals were applied.
- [ ] Mode recorded in the review log, default or named
  opt-in. Auto-install, if used, was confidence 5 only,
  opt-in in writing, and every auto-install is logged.
  Batch approvals named each change.
- [ ] Ledger rows exist for every proposal.
- [ ] Closing message lists installed, rejected, and blocked.
