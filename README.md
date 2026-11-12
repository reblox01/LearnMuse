# LearnMuse

![LearnMuse banner](assets/banner.jpg)

**LearnMuse - Muse that learns, built for Muse.ai.**

Muse that grows with you. A Muse-native skill pack that gives Muse
Hermes-style auto-improvement: a background review that turns
finished work into reusable skills, bounded memory, a curator that
prunes stale skills without ever deleting, and an independent
verifier so a bad auto-created skill cannot propagate.

No Docker, no LLM key, no separate engine. Muse is the engine.

Inspired by the architecture of Hermes Agent
([NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent),
the post-turn background review, the skill system, and the Curator),
rebuilt from scratch as skills and playbooks that anyone with
Muse.ai can install and run. Skill content here is original writing.
Hermes itself is MIT-licensed, and its mechanisms are credited in
[`docs/RESEARCH.md`](docs/RESEARCH.md) and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quick start

In Muse.ai: no terminal needed. Ask Muse to install the pack, and
it fetches the skills from the repo and sets up the daily review.
Paste this, one prompt does the whole setup:

```text
Install the LearnMuse skill pack from https://github.com/reblox01/LearnMuse
and run a learning review on my last session.
Stage every proposal, verify each one, and install nothing
without my approval for that exact change.
Then set up a daily LearnMuse review: once a day, review
yesterday's work from my files, stage at most 5 proposals,
verify each one separately, and only tell me when one is
verified and worth my approval. Never install, commit, or
push from the daily review.
```

Same install, other jobs:

```text
Install the LearnMuse skill pack from https://github.com/reblox01/LearnMuse
and teach it how I just deployed the staging server, as a new skill.
```

```text
Install the LearnMuse skill pack from https://github.com/reblox01/LearnMuse
and run the weekly curator pass on my skills.
Archive stale ones, never delete, and show me the ledger.
```

Verifier-only install, for people who already have a
learning loop and want just the verifier. One prompt:

```text
Install only the LearnMuse verifier from https://github.com/reblox01/LearnMuse:
learnmuse-verify plus tools/ledger.py, nothing else.
Use it to check any auto-created skill before trusting it:
a reviewer that did not write the skill checks it first.
Install nothing else from the pack.
```

Or from a terminal, in a clone:

```bash
./scripts/install.sh --verify-only
```

## The loop, in one paragraph

After a session, a review replays what happened and proposes
lessons: patch a skill that was in play first, then an existing
umbrella, then a support file, and only then a new class-level
skill. Every proposal is staged, scanned, and checked by a
separate verifier before it lands. Memory holds who you are and
facts about your environment, skills hold how to do a class of
task, and one lesson lives in exactly one place. Once a week the
curator archives skills unused for 30 days, never deletes, and
every mutation is in a ledger you can roll back.

## What Muse already does vs what LearnMuse adds

| Muse already does | LearnMuse adds |
|---|---|
| Skills, memory, and scheduled jobs | The connected loop: review a finished session, stage the lesson, verify it, then install it after your approval |
| Create a skill when you ask for one | A background review that finds lessons on its own, plus a coexistence check so it patches what you already have instead of creating a duplicate |
| Learn in the background, in its own way | An independent verifier that re-runs the proof, a ledger with use counts, and a curator that archives, never deletes |
| Remember facts across sessions | A baseline audit of the existing library, to catch a bad rule already in place, not just a bad new proposal |

## What it does for you, in concrete terms

1. Teach once, it sticks. You correct Muse once, for
   example "always check the live site before saying
   something is missing". The review turns that into a
   skill rule, the verifier checks it, you approve it,
   and the next session just does it. No re-explaining.
2. Stops repeating a mistake. The worked example in
   `examples/sample-review.md` is a deploy that restarted
   before migrating, twice. The fix is a skill patch:
   migrate first, then restart. The next deploy is the
   test: if it runs migrate first without being told,
   the lesson landed.
3. Overnight review. Once a day, or once a week in
   low-token mode, the review reads yesterday's work,
   stages at most 5 proposals (3 in low-token mode),
   the verifier checks each one, and you approve by name
   in the morning. Nothing installs without your approval.

## Which skills actually get used

The ledger records a use count per entry. Native learning
does not surface that, LearnMuse does. From a clone:

```bash
python3 tools/ledger.py list --db <db>
python3 tools/ledger.py stats --db <db>
python3 tools/ledger.py use --db <db> --id <skill-id>
```

`list` shows `uses=` per entry. `stats` shows totals by
status and kind. `use` records one use of an entry, so the
count grows when a skill is actually used.

## Memory budgets

The 2,200 / 1,375 char budgets are for the injected
summary only, not for the full `MEMORY.md` file on disk.
The full file is never truncated to fit them, and the
budgets are configurable: record new numbers in a review
log and a `MEMORY.md` entry, and the review uses them.
See `learnmuse-memory` for the full rule, including the
token trade-off of a bigger summary.

## Safety

- Nothing is installed, written to a skill, or written to memory
  without your approval for that exact change. Hermes writes
  freely by default; LearnMuse inverts that.
- The verifier is a separate role, never the author of the skill
  it checks. A proposal the verifier rejects does not land.
- The curator never deletes. The worst outcome is archival, and
  archival is recoverable.
- No skill content is copied from Hermes or any other pack.
  Ideas are credited, wording is original.

## Skills

Eight skills in v0.1, one commit per skill, plus two more in v0.3 (10 total):

| Skill | What it does |
|---|---|
| `learnmuse-orchestrator` | Run a learning review end to end. Owns the approval gate, the review log, and the budgets. |
| `learnmuse-review` | Post-session background review. Proposes lessons, patch first, create last, never applies. |
| `learnmuse-learn` | Manual learn. Turn a workflow or source into a skill, iron contract, provenance guard. |
| `learnmuse-memory` | Bounded memory and session search. Facts go to memory, procedures go to skills. |
| `learnmuse-curator` | Weekly prune and archive, never delete. Stale 14d, archive 30d, pin and lock. |
| `learnmuse-verify` | Independent verifier for proposed skills. Verdicts verified, candidate, rejected, blocked. |
| `learnmuse-update` | Phase-0 freshness check. `sources.yaml` is the single source of truth. |
| `learnmuse-journey` | Build the learning graph over skills, memory entries, and proposals as a timeline, rendered as a web artifact. Read-only proposals, edits staged for approval, delete archives. |
| `learnmuse-community` | Turn a good experience into a star and a real problem into an issue. Opt-in, off by default, dedupe by title, max one issue per day. |
| `room-placement` | Place room items by real-room logic. Learned from the Basement Tycoon room-placement rule, the "use logic" rule, validated by room samples v5 verified by eye in all 4 themes, commit 221cdc6. |

Supporting pieces: `tools/ledger.py` (stdlib SQLite learning
ledger), `scripts/install.sh` (full install, or
`--verify-only` for the verifier alone),
`examples/sample-review.md` (a worked review with one
staged proposal and its verify verdict),
`examples/baseline-audit.md` (a worked baseline audit
with both classic bugs caught), and three workflows
(CI, auto-tag, release).

See [`docs/RESEARCH.md`](docs/RESEARCH.md) for the full research
and the build plan, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the Hermes-to-Muse mapping.

## Verify it yourself

```bash
git clone https://github.com/reblox01/LearnMuse.git
cd LearnMuse
./scripts/install.sh
python3 tools/ledger.py init --db /tmp/learnmuse-test.db
```

Then run a learning review on a real past session with a
known repeated mistake, stage the proposal, verify it, and
install it only after approval. Run the same task again in
a fresh session and check the mistake does not repeat.

## What is new in v0.2

- Verifier-only install: `./scripts/install.sh --verify-only`
  installs only `learnmuse-verify` plus `tools/ledger.py`.
- Coexistence check: the review scans the existing skill
  library before staging, and the verifier re-checks it.
  A lesson already covered is patched, not created twice.
- Baseline audit mode in `learnmuse-verify`: audit an
  existing library for a frozen retracted diagnosis,
  near-verbatim rule copies across skills, and stale rules.
  Worked example in `examples/baseline-audit.md`.
- Memory budgets are configurable, and the full
  `MEMORY.md` is never truncated to fit a summary budget.
- Opt-in tap-free and token-saver modes in
  `learnmuse-orchestrator`: batch approve, auto-install
  verified confidence 5 only, weekly digest, and a
  low-token mode (weekly review, max 3 proposals).
  Approval stays ON by default.

Thank you to Best_Caterpillar1682 for the verifier catch
and for the suggestions behind v0.2. He cloned the repo,
read the whole pack, wired the verifier in as a standalone
protocol, and within the hour it flagged a sourcing skill
that had frozen a wrong tool diagnosis as a permanent rule
three weeks after the diagnosis was retracted, plus a
second skill carrying near-verbatim copies of rules owned
by three others. He suggested the verifier-only install
and the coexistence check, and he called out the ledger
use counts as genuinely good.

## What is new in v0.3

- Computed nudge counter (Hermes gap 1): the review no
  longer hand-keeps counts that never move. A scheduled
  run counts user turns and tool iterations from the
  transcript database since the last review watermark.
  Honest limit: no live per-turn tick, a threshold crossed
  between runs fires at the next run.
- Session-end extraction (Hermes gap 2): the daily cron
  also reads all new messages since the last review
  watermark, regardless of chat, and runs the review
  extraction on them. Honest limit: extraction lags by up
  to a day, Muse has no session-end event.
- Central usage ledger (Hermes gap 3): one ledger,
  `skill-usage.db`, records each use at use time. Per-run
  ledger DBs record proposals, not usage. Honest limit:
  only LearnMuse-run loads are recorded, a low count is
  absence of evidence.
- New skill `learnmuse-journey`: the learning graph as a
  timeline, rendered as a web artifact, rebuilt on demand.
  Skills, memory entries, and read-only proposal nodes.
  Edits staged for approval, delete archives.
- New skill `learnmuse-community`: opt-in star and issue
  filing for verified problems, with bug and idea issue
  templates (see Community below).
- Tags are two-part now (v0.2, v0.3), not three-part.

## Status

v0.1 released 9 Nov 2026, live at
https://github.com/reblox01/LearnMuse. v0.2 released
11 Nov 2026. v0.3 is in progress locally, not pushed yet.
Research for v0.1 was done the same day in three tracks,
reports in `~/workspace/learnmuse-research/`.

## Community

`learnmuse-community` turns a good experience into a star,
and a real problem into an issue, without you having to
remember either. It is opt-in and off by default: it asks
once, only after a lesson lands and the next session
confirms it helped. On yes, it stars
[reblox01/LearnMuse](https://github.com/reblox01/LearnMuse)
once, and files issues for concrete verified problems
only, deduplicated by title, max one per day. It never
follows, comments, or opens PRs, and it never asks for a
token: it needs `gh` authenticated, and skips silently
without it.
