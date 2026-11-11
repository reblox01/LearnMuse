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

v0.1, eight skills, one commit per skill:

| Skill | What it does |
|---|---|
| `learnmuse-orchestrator` | Run a learning review end to end. Owns the approval gate, the review log, and the budgets. |
| `learnmuse-review` | Post-session background review. Proposes lessons, patch first, create last, never applies. |
| `learnmuse-learn` | Manual learn. Turn a workflow or source into a skill, iron contract, provenance guard. |
| `learnmuse-memory` | Bounded memory and session search. Facts go to memory, procedures go to skills. |
| `learnmuse-curator` | Weekly prune and archive, never delete. Stale 14d, archive 30d, pin and lock. |
| `learnmuse-verify` | Independent verifier for proposed skills. Verdicts verified, candidate, rejected, blocked. |
| `learnmuse-update` | Phase-0 freshness check. `sources.yaml` is the single source of truth. |
| `room-placement` | Place room items by real-room logic. Learned from the Basement Tycoon room-placement rule, the "use logic" rule, validated by room samples v5 verified by eye in all 4 themes, commit 221cdc6. |

Supporting pieces: `tools/ledger.py` (stdlib SQLite learning
ledger), `scripts/install.sh`, `examples/sample-review.md`
(a worked review with one staged proposal and its verify
verdict), and three workflows (CI, auto-tag, release).

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

## Status

v0.1 built 9 Nov 2026, local only. Research done the same
day in three tracks, reports in `~/workspace/learnmuse-research/`.
All 8 skills, the ledger tool, the install script, and the
worked example are committed, one commit per step. Nothing
pushed, no GitHub repo created yet.
