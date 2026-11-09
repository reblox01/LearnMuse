# LearnMuse research

Date: 9 Nov 2026. Read-only research, no skill content copied.
Sources: Hermes Agent codebase at `~/workspace/hermes-agent-read`, commit
`aa5fb1cc` on main (262k stars); Muse skills inventory at
`~/workspace/learnmuse-research/muse-skills-inventory.md` (229 lines);
Hermes deep dive at `~/workspace/learnmuse-research/hermes-deep-dive.md`
(416 lines); community research at
`~/workspace/learnmuse-research/community-skills.md` (269 lines).

Goal: a Muse-native skill pack that gives Muse Hermes-style
auto-improvement, so Muse improves itself every time instead of
repeating the same issue. Original writing throughout. Hermes is
inspiration, credited like RedMuse credits Strix. No Hermes code
copied, no other skill copied verbatim.

## 1. What Hermes actually does (from its code, not articles)

- Learning is a post-turn background-review fork, not an in-turn loop.
  `agent/background_review.py` (1,392 lines) forks the agent after a
  turn, replays the conversation snapshot, and asks "should any skill
  or memory be saved or updated?" Writes go to memory and skill
  stores. The live conversation and prompt cache are never touched.
- Triggers are two counters, both 10 in code: memory every 10 user
  turns, skills every 10 tool iterations
  (`agent/agent_init.py:1160, 1236-1238`, `agent/turn_finalizer.py:864-875`).
  The example config says 15 for skills; articles saying 15 copied
  the example.
- The review prompt pressures it to save something: "Be ACTIVE, most
  sessions produce at least one skill update, even if small. A pass
  that does nothing is a missed learning opportunity."
  ("Nothing to save" is allowed but "should NOT be the default.")
- Patch first, create last. Preference order: patch a loaded skill,
  patch an existing umbrella, add a support file, only then create a
  new class-level skill. Never delete a skill in a review.
  Read-before-write is enforced.
- Memory vs skills split by kind. Memory is who the user is
  (`USER.md`, 1,375 chars) and environment facts (`MEMORY.md`,
  2,200 chars). Skills are how to do a class of task. One lesson
  lives in exactly one place. Memory is a frozen snapshot at session
  start. Session search (FTS5 in SQLite) is the real recall for old
  conversations.
- Skills load by progressive disclosure. Level 0: name plus a
  60-char description list. Level 1: full `SKILL.md` on demand.
  Level 2: one reference file on demand. Descriptions over 60 chars
  are silently truncated.
- Curator does not create skills, it is janitorial. `agent/curator.py`
  (1,234 lines): 7-day interval, 2h idle, stale 14d, archive 30d,
  never deletes, LLM consolidation OFF by default. It only manages
  `created_by: agent` skills, set only by the background-review fork.
  `/learn` skills are `created_by: learn` and are left alone.
- Safeguards exist but are OFF by default. `memory.write_approval`
  and `skills.write_approval` are both `false` by default, so the
  fork writes freely. Pin stops archival, lock stops all agent edits,
  every mutation goes to a JSONL ledger with content-addressed blobs
  for rollback.
- No independent verifier, no GEPA, no `skill_generation` flag in
  this commit. The fork is judged only by counting what it wrote.
  GEPA lives in a companion repo
  (`NousResearch/hermes-agent-self-evolution`), not in hermes-agent.
  The real switch is `auxiliary.background_review.enabled: true`,
  fail-open.

## 2. What Muse already has

Reuse directly:
- `publish_approval_gate`: draft vs publication are separate.
  Approval of content is not approval to publish or push. This
  becomes LearnMuse's core safety rule.
- `redmuse-verify`: independent verifier, verdicts verified /
  candidate / rejected / blocked, proof capsule, confidence 0-5.
  This fixes Hermes' self-evaluation weakness.
- `redmuse-findings` plus `tools/findings.py` (stdlib SQLite):
  template for the learning ledger.
- `redmuse-update` plus `sources.yaml`: phase-0 freshness check.
  Fast-forward pull only for the pack itself, reference sources
  never rewrite skill content, deltas become follow-up tasks.
- `redmuse-orchestrator`: gate plus run log plus budgets shape.
- `social-improve` (HeyMuse): closest existing Muse-native learning
  loop. Collect examples, extract pattern, propose, apply only after
  exact approval, track the next 10.
- `hermes-agent-skill-authoring`: Hermes' own SKILL.md rules
  (description max 1,024 chars, aim 8-14k, Overview / When to Use /
  Pitfalls / Checklist, prefer extending over a narrow sibling).
- `write-skill` sections 2-4: edit ladder, levels, diet rule.
- `self-awareness`, `forget`, `goals`: grounding, removal path,
  reflection on completion.

Adapt (good core, wrong host or defaults):
- `learn` (gstack): learning record shape and STALE / CONFLICT
  prune rules. Strip Claude binaries and preamble, re-back on SQLite.
- `skillify`: strongest pattern in the library. Iron contract
  (temp dir, test, rename only on pass plus explicit approval) and
  provenance guard (walk back max 10 turns, refuse if no validated
  result). Generalise from scrape-only to any workflow. Template
  for `learnmuse-learn`.
- `retro`: weekly cadence plus prune-ask-per-entry.
- `autoplan`: sequential review pipeline, but auto-decisions must
  become propose-then-approve.
- `verify` (gstack): self-test loop for a proposed skill.
- `context-save` / `context-restore`: file-based context restore
  for cron reviews, which have no live conversation.
- `dspy`: reference only for later prompt evolution.

Do not build on: `plan-tune` (observational only),
`codex-hermes` (unrelated Codex CLI skill, name trap),
`recovered-skill-notes` (self-declared unverified).

Muse-native adaptation per Hermes mechanism:
- Background-review fork: Muse has no daemon or hook. Emulate with
  three triggers: manual end-of-session review, an isolated review
  subagent spawned with a transcript excerpt, and a daily cron whose
  body reads the daily log and stages proposals. Cron is the only
  truly automatic trigger, and it works from files, not live chat.
- Nudge every 10: no iteration counter in Muse. Track approximately
  in a review-log state file, cron as backstop.
- `skill_manage`: Muse writes `SKILL.md` plus `skill.yaml` directly,
  staged in a proposals folder, installed after approval.
- Memory (2,200 / 1,375 chars, FTS5): `~/MEMORY.md` plus daily logs
  with skill-imposed budgets, recall via `muse.memory_search` and
  `muse.db`.
- Curator (7d / 2h idle, stale 14d, archive 30d, never delete,
  consolidate off): weekly cron, no idle detection, body exits
  quietly if no activity, same thresholds. Usage telemetry has no
  Muse equivalent, so counts must be approximated and labelled so.
- GEPA: not in Hermes main either. Do not promise it. Offline
  evolution is a later tier, PR-only, never live mutation.

## 3. Outside ideas worth stealing (original writing only)

1. Background review fork, Be ACTIVE, patch-first. From Hermes
   and OpenClaw experience review. Muse version: subagent or cron
   review, 10-iteration nudge, one-attempt rule.
2. Proposal-first Workshop with scan, hash bind and rollback.
   From OpenClaw Skill Workshop. Nothing auto-applies by default.
   Every learned skill is a proposal, scanned, bound to the current
   live skill hash, with prior contents captured for rollback,
   applied only on approval.
3. Offline GEPA and DSPy evolution with a held-out test set and
   PR-only deployment. From `NousResearch/hermes-agent-self-evolution`,
   `gepa-ai/gepa`, `stanfordnlp/dspy` (all MIT for the DSPy/GEPA
   parts). Optimize offline, gate on train / validation / holdout,
   ship as a diff for human review, never mutate live skills.
4. Ratchet governance: bounded active cap, contribution-score
   retirement, skill-level memory, never delete. From
   `amazon-science/Self-Evolving-Agents-Ratchet` (license to verify
   before fetching) and the Blind Curator paper. Retire on measured
   contribution with an unbiased judge, cap the active library so
   retrieval does not degrade, keep retired skills and evidence
   for rollback. Unmanaged libraries score plus 0.0 over a no-skill
   baseline. False-pass bias past a sharp threshold switches off
   retirement entirely, and no amount of data rescues it.
5. Skill-level memory plus a five-stage lifecycle with unit-test
   evaluation. From MUSE-Autoskill and Voyager. Each skill carries
   its own record of successes, failures and examples, separate
   from user memory. Created, used, evaluated by a test or live
   check, refined, only then kept. Verified-before-admit stops bad
   skills propagating.

Fetchable candidates (YES, read first, adapt, license and format
check first): Hermes self-evolution DSPy/GEPA part (MIT);
GEPA and DSPy (MIT, libraries not Muse skills); NVIDIA
SkillEvaluator Tier 1 and SkillSpector (Apache-2.0, CI gate and
proposal scan, 68-71 patterns, 17 categories); Ratchet
(read-only audit first, license unverified); `myths-labs/muse`
(MIT, `/distill` and dual-layer memory pattern, adapt, do not
copy its 65-68 skills wholesale).

Traps:
- Auto-apply by default, and self-evaluation as the verifier.
  Hermes self-evaluation almost always passes.
- Unbounded libraries with no retirement, and age-only pruning.
- AGPL code in an MIT pack: Honcho is AGPL-3.0, and the Darwinian
  Evolver in hermes-agent-self-evolution is AGPL v3. Excluded.
- Paid or retired memory APIs presented as free: Zep retired
  self-hosting in 2025, Mem0 graph memory is locked behind the
  249 dollar Pro plan, Supermemory and Zep are metered.
- Public registries as trusted sources, and paste-into-chat
  presented as an install. Snyk found critical issues in 13.4
  percent of 3,984 public skills, with 76 confirmed malicious
  payloads. Trail of Bits bypassed five scanners. A scanner pass
  is a first filter, not approval. A real Muse install is a folder
  in `~/workspace/custom-skills/` with `SKILL.md` plus `skill.yaml`,
  not a chat paste.
- Every external agentskills.io skill needs a Muse `skill.yaml`
  added, with `include_in_prompt: false` for library skills, and
  a tool-call check, before it works as a Muse skill.

## 4. Build plan: LearnMuse v0.1

Name: LearnMuse. Slogan: "LearnMuse - Muse that learns, built
for Muse.ai." Public repo `reblox01/LearnMuse` is free. Local:
`~/workspace/learnmuse`. Rules: local commits per step, GitHub
pushes need Sohail's approval for that exact push, original
writing, no Docker, no LLM key, no spending.

Skills (6 plus update):
1. `learnmuse-orchestrator`: run a learning review end to end.
   Owns the approval gate, the review log, and budgets (max
   proposals per review, max tool iterations).
2. `learnmuse-review`: post-session background review. The Hermes
   background-review prompt, adapted to Muse: Be ACTIVE, patch
   a loaded skill first, then an umbrella, then a support file,
   create a new class-level skill last. Do-not-capture list:
   one-off narratives, transient errors that resolved, unresolved
   failures dressed up as a reliable workflow. Triggers: manual
   end-of-session, review subagent, daily cron from the daily log.
3. `learnmuse-learn`: manual `/learn`. Turn a workflow or source
   into a skill, using the `skillify` iron contract and provenance
   guard (walk back max 10 turns, refuse if no validated result).
4. `learnmuse-memory`: bounded memory. What to save and skip,
   `MEMORY.md` and `USER.md` discipline, session search via
   `muse.memory_search`, memory vs skill split (one lesson lives
   in exactly one place).
5. `learnmuse-curator`: weekly maintenance. Stale 14d, archive
   30d, never delete, pin and lock, ledger with rollback, LLM
   consolidation off by default. Only LearnMuse-created skills
   are managed by default; adoption is explicit for others.
6. `learnmuse-verify`: independent verifier for proposed skills.
   Separate role, never the author. Verdicts verified / candidate /
   rejected / blocked, proof capsule, confidence 0-5, verified
   needs 4-5. A proposed skill must pass verification before it
   lands. This is the fix for Hermes' self-eval weakness.
7. `learnmuse-update`: phase-0 freshness check, `sources.yaml`
   as single source of truth. Hermes is a reference source
   (tracked, never vendored). Fast-forward pull only for the pack
   itself, nothing updates mid-run, nothing pushes automatically.

Supporting pieces: `tools/ledger.py` (stdlib SQLite, init / add /
list / stats / export, modelled on `redmuse-findings`),
`scripts/install.sh`, `skills/*/skill.yaml`, three workflows
(CI, auto-tag, release) copied in shape from RedMuse, never
copying a file that contains a real token.

Later tiers, not v0.1: offline evolve with DSPy/GEPA (PR-only,
held-out test set, needs an LLM key and a metric, cost stated
up front); skill-level memory per skill; Ratchet-style
contribution retirement once usage counting is honest.

Risks: the loop starves if lessons are not written to the daily
log; usage counts in Muse are approximate and must be labelled
so; gstack skills need their Claude preamble stripped; skill
bloat is the failure mode the curator exists to fight; Hermes
wording must be original, credited as inspiration.

## 5. How to tell v0.1 works

A real test, not a claim: run a learning review on a real past
session with a known repeated mistake, stage the proposed skill,
run `learnmuse-verify` on it, install it only after approval,
then run the same task again in a fresh session and check the
mistake does not repeat. Record the before/after in
`examples/` with the proof capsule. A review that finds nothing
to save says so, it does not invent a skill.
