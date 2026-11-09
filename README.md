# LearnMuse

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
it fetches the skills from the repo. Paste this:

```text
Install the LearnMuse skill pack from https://github.com/reblox01/LearnMuse
and run a learning review on my last session.
Stage every proposal, verify each one, and install nothing
without my approval for that exact change.
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

v0.1, in build order, one commit per skill:

- `learnmuse-orchestrator`: run a learning review end to end.
- `learnmuse-review`: post-session background review.
- `learnmuse-learn`: manual learn, turn a workflow into a skill.
- `learnmuse-memory`: bounded memory and session search.
- `learnmuse-curator`: weekly prune and archive, never delete.
- `learnmuse-verify`: independent verifier for proposed skills.
- `learnmuse-update`: phase-0 freshness check.

See [`docs/RESEARCH.md`](docs/RESEARCH.md) for the full research
and the build plan, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the Hermes-to-Muse mapping.

## Status

Research done 9 Nov 2026, three tracks, reports in
`~/workspace/learnmuse-research/`. Build has not started yet
beyond this scaffold and the research doc. Nothing pushed.
