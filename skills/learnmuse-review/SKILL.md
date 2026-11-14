# LearnMuse review

You are the background review. You replay a finished session
and turn what happened into proposed lessons. You propose
actively, and you never apply anything: every proposal you
make is staged for the orchestrator, checked by the verifier,
and applied only after the user approves that exact change.

Muse has no daemon that reviews after every turn, so you run
on one of three triggers. Pick the one that fits the run, and
record which one you used in the review log.

## When to use

- End of a session, when the work is done and the user asks
  for a review, or says "Muse should learn this".
- A review subagent run: an isolated agent given a transcript
  excerpt, with no access to the live conversation.
- A daily cron review: the cron body reads the daily log and
  stages proposals from files. It never sees a live chat.

Do not review a session that is still running. A review
replays finished work. If the session is still in flight,
wait, or say so and stop.

## Triggers

1. Manual end-of-session. The user names the session. You
   read the conversation and the day's notes, then propose.
2. Review subagent. You are spawned with a transcript excerpt
   and the list of skills that were loaded. You have no live
   conversation to touch, which is the point: the review
   cannot change the work it is reviewing.
3. Daily cron. You read `~/memory/<date>.md` and the review
   log. You stage proposals as files. If there is nothing
   new to learn, you write "Nothing to save" in the log and
   stop. You never invent a proposal to fill a quota.
4. Session-end extraction. When a session ends, extract
   lessons from its transcript, not from a summary of it.
   Muse has no session-end event, so this runs as a
   scheduled pass inside the daily review cron: the cron
   reads all new messages since the last review watermark
   in `learnmuse-runs/review-state.md` (via `muse.db`,
   `runtime.messages` and `agent.context_items`),
   regardless of chat, and runs the review extraction on
   them. The extraction is
   staged, verified, and approved like any other review;
   nothing is installed without the user's approval for
   that exact change. Extraction may lag the actual end by
   up to a day; that lag is the honest cost of having no
   session-end event, and the daily cron remains the
   backstop.

Nudge counter (computed, not hand-kept). Muse has no
daemon counter and no live per-turn tick, so the counts
are computed, not ticked: a scheduled run counts user
turns and tool iterations from the transcript DB since
the last review watermark in `learnmuse-runs/review-state.md`,
and writes the computed counts back to that file with the
timestamp. The queries, run with `muse.db` (read-only):

- User turns: `SELECT count(*) FROM runtime.messages WHERE role = 'user' AND created_at > :watermark`
- Tool iterations: `SELECT count(*) FROM agent.context_items WHERE item_kind = 'tool_call' AND created_at > :watermark`
- Do not count from `runtime.tool_calls` or `runtime.tool_outputs`: both are empty in this deployment. `agent.context_items` is the source for tool iterations.

Fire a memory review at 10 user turns and a skill review
at 10 tool iterations, the same numbers as Hermes code.
Counts are global across chats since the watermark, the
same scope the hand-kept counts had. Label the counts as
computed at the cron cadence, not live: a threshold
crossed between runs fires at the next run, not at the
turn. Doing the work resets the count: a memory review
resets the turn count to 0, a skill review resets the
iteration count to 0, the same reset Hermes does when the
memory or skill_manage tool is used. If the state file is
missing, start both counts at 0 and say so. The daily
cron is the backstop: it runs the review even if the
counts were never kept.

If the evidence is missing, say which evidence is missing
and stop. A review without evidence is a guess.

## Coexistence check (mandatory, before staging)

Do this before you propose anything. Muse may already
learn on its own, and the user may already have a skill
library, a native learning loop, or another pack writing
to the same library. LearnMuse layers on top of what is
already there. It never installs a competing loop.

1. List the skills already installed in the library in
   scope: the skills folder for this run, usually
   `~/workspace/custom-skills`, `~/.muse/skills`, or the
   repo `skills/` folder, plus any skill loaded in the
   session under review. Search memory for the same lesson.
2. For each candidate lesson, record one result, with the
   skill name and the exact existing text quoted:
   - Already covered: a skill or memory entry already
     states the same rule.
   - Partially covered: a skill states part of the rule
     but misses a step, a pitfall, or a correction.
   - Not covered: no skill or memory entry states it.
3. If already covered: do not create a new skill, and do
   not stage a duplicate proposal. Patch the covering
   skill only if the lesson adds a step, a pitfall, or a
   correction. If it adds nothing, log "already covered,
   no change" and stop for that lesson.
4. If partially covered: patch the covering skill. Never
   create a parallel skill with the same rule.
5. If not covered: proceed to the preference order below.
6. If the user already has a native learning loop or
   another pack writing to the same library, say so in
   the review log, with the loop or pack named. Patch
   existing skills, never install a second curator or a
   second review that would fight the first, and do not
   install a competing loop without the user's explicit go.

A proposal that creates a new skill for a lesson already
covered is a duplicate. The verifier rejects it.

## The review prompt

Be active. Most sessions produce at least one lesson worth
saving, even a small one. A pass that finds nothing is a
missed learning opportunity, not a neutral outcome. But
"Nothing to save" is a real option: if the session ran
smoothly, with no corrections and no new technique, say
"Nothing to save" and stop. Do not invent a lesson.

Look for these signals. Any one of them warrants action:

- The user corrected your style, tone, format, length, or
  verbosity. Frustration is a first-class signal, not just a
  memory signal. "Stop doing X", "this is too verbose",
  "just give me the answer", or an explicit "remember this"
  means the skill that governs that task needs the lesson,
  so the next session starts already knowing.
- The user corrected your workflow, approach, or order of
  steps. Encode the correction as a pitfall or an explicit
  step in the skill that governs that class of task.
- A non-trivial technique, fix, workaround, or debugging path
  emerged that a future session would benefit from. Capture it.
- A skill that was loaded or consulted turned out to be
  wrong, missing a step, or out of date. Patch it now.
- The same mistake happened twice. A repeated mistake is the
  strongest signal in the review: the existing skill either
  does not cover it, or the lesson never landed.

## External second opinion (only when the user gave access and asked)

When a design or plan is about to close a version and the user has
given second-opinion access (Claude or GPT) and asked for the review,
run it before closing. When two reviewers are in flight, wait for both
verdicts before starting fixes, so one fix round covers both. Share
only the design or plan files, never secrets, credentials, or private
data, and only for the exact share the user asked for. When files are
attached or pasted as text, ask the reviewer to confirm it received
and read all of them before it reviews: an attachment the reviewer
never read, or a paste that interleaved, produces findings on a
partial picture. Apply the findings as fixes to the design, then
run a second round to confirm the fixes and catch what the first
round missed. Check each finding against the real code before fixing
it: a finding about a file the reviewer never saw may rest on a wrong
assumption, so confirm the file and line first and record the
correction when the code says otherwise. A reply the reviewer gives
before the brief is a preliminary reply, not a verdict: only the
brief-anchored reply counts, and a preliminary reply that contradicts
it is discarded. When a reviewer chat hits its context limit, start a
fresh chat and send a focused diff instead of re-pasting the full pack.
When the reviewer channel is blocked, a wiped browser session or a
human check that never clears, park the review, report it once, and
restart only after the user signs in: do not burn retries in a loop
while the channel is down. The external review advises; it never
approves an install, commit, push, or tag.

## Preference order

Pick the earliest action that fits. Do not jump to creating
a new skill when a patch would do.

1. Patch a skill that was loaded in this session. Look back
   through the conversation for skills the user invoked or
   you read. If one of them covers the learning, patch that
   one first. Re-read it before you patch it: a patch based
   on a stale copy is refused.
2. Patch an existing umbrella skill. If no loaded skill fits
   but a class-level skill does, patch it. Add a subsection,
   a pitfall, or broaden a trigger.
3. Add a support file under an existing umbrella, in
   `references/` for topical depth, `templates/` for starter
   files meant to be copied, or `scripts/` for re-runnable
   actions. Add a one-line pointer in the skill's `SKILL.md`
   so future sessions know the file exists.
4. Create a new class-level skill, only when no existing
   skill covers the class. The name must be at the class
   level: not a specific error string, not a date, not a
   one-off task name. If the name only makes sense for
   today's task, it is wrong: fall back to 1, 2, or 3.

Never delete a skill in a review. Deletion is the curator's
job, and the curator never deletes either: it archives.

## Do not capture

- One-off task narratives. "Summarize today's market" or
  "analyze this PR" is not a class of work that warrants a
  skill.
- Transient errors that resolved. If retrying worked, the
  lesson is the retry pattern, not the original failure.
- Unresolved failures dressed up as a reliable workflow. If
  the session ended without finding a working method, do not
  write those attempts up as a recommended approach. Say
  "Nothing to save", or capture only a working alternative
  you are independently confident about, never the dead ends,
  and never as best practice.
- Facts that belong in memory. A lesson about who the user
  is, or a fact about the environment, goes to memory, not
  to a skill. One lesson lives in exactly one place.
- Anything the evidence does not support. A claim with no
  transcript excerpt, no file, and no test behind it is not
  a lesson, it is a guess.

## How to write a proposal

Each proposal is one file in
`learnmuse-runs/<review>/proposals/<name>.md`, with:

- Name: the skill or memory entry it touches, and the action
  (patch, add file, create, memory add).
- Evidence: the transcript excerpt, file path, or test that
  proves the lesson. Quote the exact words or the exact
  command, with the date.
- Before/after: the current text, and the proposed text, so
  the user can see the change without guessing.
- Why: one line, the mechanism. A pitfall is a generalizable
  rule plus one clause of why, attached to the step it
  affects, stated once.
- Kind: skill patch, new skill, support file, or memory entry.
- Coexistence: the result of the coexistence check above,
  already covered, partially covered, or not covered, with
  the covering skill named and its existing text quoted.
  A proposal with no coexistence field is not staged.

A proposal with no evidence is not staged. A proposal that
restates what is already loaded every turn (the repo's
`AGENTS.md`, tool schemas) is not staged.

## Budgets

- Max 5 proposals per review. A sixth lesson waits for the
  next review.
- One attempt per review pass. A failed review is logged
  and dropped, not retried in a loop.
- Prefer small patches. A patch is cheaper to verify than
  a rewrite, and a rewrite needs a stronger reason.

## Hard rules

- Propose actively, apply never. You stage proposals. The
  orchestrator, the verifier, and the user decide what lands.
- Approval is ON by default. Nothing you propose is applied
  without the user's approval for that exact change.
- The verifier is separate. You never verify your own
  proposals.
- Never copy Hermes code, another skill's text, or a public
  skill verbatim. Ideas are credited, wording is original.

## Outputs

- One proposal file per lesson, in
  `learnmuse-runs/<review>/proposals/`.
- A review summary in the review log: trigger used, skills
  loaded, signals found, proposals made, and "Nothing to
  save" when that is the honest answer.

## Verification checklist

- [ ] Session reviewed was finished, not still running.
- [ ] Trigger recorded in the review log.
- [ ] At most 5 proposals, each with evidence and a
  before/after.
- [ ] Every proposal follows the preference order, patch
  first, create last.
- [ ] No proposal captures a one-off narrative, a transient
  error, or an unresolved failure.
- [ ] No proposal duplicates a lesson already in memory or
  in another skill.
- [ ] Coexistence check ran before staging, and every
  proposal records its result with the covering skill
  named and its existing text quoted.
- [ ] "Nothing to save" was used honestly when nothing was
  worth saving.
