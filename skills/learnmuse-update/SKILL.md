# LearnMuse update

You run the phase-0 freshness check before any learning
review, curator pass, or install. The check runs once,
before any other work, and its result goes in the review
log. It answers one question: is this copy of LearnMuse
current, and are its reference sources current? It never
rewrites a skill, never updates mid-run, and never pushes
anything.

## When to use

- Before any learnmuse-orchestrator run, as phase 0.
- Before installing the pack on a new machine.
- When a review or a curator pass reports a staleness
  warning and you need to know what changed.

Do not run the check in the middle of a review. It is a
phase-0 check: once, at the start, then the run proceeds
with what it found.

## The single source of truth

`sources.yaml`, in this skill's folder, is the single source
of truth. To find where a skill comes from, look up its name
in the covers list of an entry. Adding a source here is
enough to have it checked; no script edit is needed.

Fields per source:

- name: short id used in check output.
- covers: skill names or layers this source is the origin of.
- repo: git URL, when the source is a git repo. Omitted for
  manual sources, which have no version endpoint.
- kind: self (this repo), reference (tracked, never vendored),
  manual (no version endpoint, reviewed by hand).
- check: git-head (compare upstream HEAD) or manual.
- auto_update: fast-forward-pull (LearnMuse itself only) or
  none. None means a delta becomes a follow-up task, never
  a rewrite.
- cli: command-line tools the skills use, or none. Recorded
  so the run machine can check availability; never
  auto-installed.

## How the check runs

1. Read `sources.yaml` and list every source.
2. For the self source (LearnMuse itself): record the local
   HEAD, then fetch upstream HEAD. If upstream is ahead and
   the local HEAD is an ancestor, fast-forward pull only.
   If the histories have diverged, do not pull, do not
   force, and log the divergence as a follow-up task. The
   run proceeds with the local copy, and the log says so.
3. For each reference source: record its upstream HEAD and
   compare it with the HEAD recorded at the last check. A
   delta is reported as one status line per source, and
   becomes a follow-up task. Reference sources never rewrite
   skill content. Hermes is a reference source: tracked,
   never vendored, never copied into the pack.
4. For each manual source: report its status as manual, and
   note the date it was last reviewed by hand.
5. Check the CLI tools listed in `sources.yaml` are
   available on this machine, and report which are missing.
   Missing tools are reported, never auto-installed.
6. Write the result into the review log: LearnMuse HEAD
   before and after any fast-forward pull, plus one status
   line per source.

## Rules

- The check runs once per run, before any other work.
  Nothing updates mid-run.
- Fast-forward pull only, for LearnMuse itself only. A
  diverged history is never force-pulled.
- Reference deltas become follow-up tasks. A new Hermes
  release does not rewrite a LearnMuse skill. A human reads
  the delta, decides what it means, and proposes a skill
  change through the normal review path: staged, verified,
  approved.
- Nothing pushes automatically. A check never creates a
  commit, a tag, or a push.
- A run that skipped the check, or proceeded under a
  staleness warning, says so in its review log.
- When a skill is added to the pack, add its name to the covers list of the
  source it belongs to in the same commit. The CI validate step fails the
  build when a skill has no covers entry, so a missing entry is a broken
  master, not a cosmetic gap, and a fix sitting uncommitted does not fix CI.
- The pack CI runs only on pushes to master/main and on pull requests. A
  branch push alone triggers no run; open a pull request to get the validate
  check on a branch.

## Outputs

- One status line per source in the review log.
- LearnMuse HEAD before and after any pull.
- A follow-up task list for any reference delta, any
  diverged history, and any missing CLI tool.

## Common pitfalls

- Pulling mid-run because a source moved. The check is
  phase 0, not a background sync.
- Treating a reference delta as a skill rewrite. A delta
  is a task, not a patch.
- Force-pulling a diverged history. That destroys local
  work. Log it and ask.
- Skipping the check and then wondering why a skill
  behaves like an old version. The log must say the check
  was skipped.

## Verification checklist

- [ ] Check ran once, before any other work in the run.
- [ ] `sources.yaml` parsed, every source has a status line.
- [ ] LearnMuse HEAD before and after recorded.
- [ ] Fast-forward only, no force pull, divergence logged.
- [ ] Reference deltas became follow-up tasks, never rewrites.
- [ ] Missing CLI tools reported, never auto-installed.
- [ ] Nothing pushed, nothing committed by the check.
