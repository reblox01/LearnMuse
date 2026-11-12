# LearnMuse journey

You build the learning graph: a computed view over what
LearnMuse has already learned, laid out as a timeline the user
can open, inspect, edit, and prune from one place. You render
it as a web artifact (a page the user opens in the browser).
You read the curator's ledger and the review's proposals. You
re-decide nothing, and you never install anything on your own.

## When to use

- On demand, when the user asks to see the journey, the
  learning graph, or what was learned.
- After each daily review run, rebuild so the journey is never
  more than a day stale.

Do not run it as a live view mid-session. The graph is computed
on demand from files and databases. There is no daemon and no
auto-refresh: a node added five minutes ago is invisible until
the next build.

## Nodes (three kinds)

1. **Skill nodes.** Every skill in `~/workspace/custom-skills/`
   that LearnMuse manages or the user adopted. Fields: name,
   category (from `skill.yaml` or the folder), source
   (LearnMuse-created, adopted, bundled, hand-written),
   timestamp, use count, state (active, stale, archived),
   created by (agent, user, learn), pinned, locked. The
   timestamp rule: the ledger row's created date is canonical
   for any node with a corresponding proposal; file mtime is
   the fallback for nodes without one. A node earns its place
   by being agent-created, user-taught, or actually used.
   Bundled and hand-written skills that were never touched stay
   out.
2. **Memory nodes.** Entries of `~/MEMORY.md` (curated, small)
   as first-class nodes. Daily logs (`~/memory/YYYY-MM-DD.md`)
   are NOT nodes: they are the raw material the review reads,
   and making every daily line a node would drown the graph.
   Identity: `memory:<source>:<index>:<fingerprint>`,
   fingerprint `sha256(entry text)[:12]`, so a list that shifted
   under the user still resolves to the card they clicked.
3. **Proposal nodes (LearnMuse-only).** One node per ledger row
   in the per-run ledger DBs: the proposal id, its kind (skill
   patch, new skill, memory entry), status (staged, verified,
   installed, rejected, blocked), verdict, confidence,
   verified-by, and the run it came from. A proposal node is
   the learning event: it says what was learned, when, and
   whether it landed. Proposal nodes are **read-only**. A
   proposal is the audit trail of what was learned and decided.
   Deleting one would rewrite history. Withdrawing an installed
   change means archiving the skill it installed (or
   superseding the proposal in a later review), not deleting
   the row.

## Links (three rules: one exact, two derived)

- **Proposal to skill / memory: exact.** The ledger row names
  its target (proposal id encodes the skill). No guessing.
  This is the strongest link in the graph. Show exact links
  differently from derived ones, so the user can tell which
  is which.
- **Memory to skill: lexical overlap.** Top 4 overlapping
  skills per memory card, skill-name hit weighs 6, other
  shared tokens weigh 1, tokens of 3+ chars. Labelled
  approximate in the graph, because it is: shared words are
  not a proven relationship.
- **Skill to skill: shared review history.** Two skills patched
  in the same review run are linked (they were learned
  together). LearnMuse skills carry no `related_skills`
  frontmatter today, so there is no declared link to read. Do
  not invent one. This link is labelled derived, approximate
  in the graph and in the renderer, the same label as lexical
  overlap. It is a co-occurrence signal, not a declared
  relationship.

## What the user sees

A timeline, oldest at the top, newest at the bottom: date rows,
skill and memory bars, a cumulative trajectory line, and a
summary line ("N learned skills, M memories, K skill links").
Empty state: "No learning recorded yet. Keep working and the
journey will map itself out here."

Per-node detail on click or on request: for a skill, its use
count, state, pinned/locked flags; for a memory, its full text;
for a proposal, its before/after, evidence, verdict, and
confidence. When a skill has been patched in more than one run,
its incoming edges show all proposal nodes for that skill,
ordered by timestamp, and its detail panel shows the most
recent verdict.

The graph also shows a data-health line: which sources are live
and which are empty, so an empty dimension reads as "no data
yet", never as zero. The data-health line also states that
today's sessions are not visible until tomorrow's review,
because trigger 4 fires at most once per day. Per-node detail
shows the same honesty: use count absent reads "no usage data
yet", state absent reads "unknown", timestamp absent reads "no
date recorded". A blank field is never shown without a reason.

## Where it lives

The skill owns the build and the refresh. The page is rebuilt
on demand: when the user asks for it, and after each daily
review run, so the journey is never more than a day stale. The
skill stores the artifact URL in
`learnmuse-runs/journey-artifact.txt` on first publish, reads
it on later builds, and updates that artifact in place. If the
file does not exist, it publishes fresh and writes the URL.
There is one canonical journey URL, never a new link per build.
`journey-artifact.txt` is a runtime-only file, not committed,
and if it is lost (fresh clone, workspace reset) the skill
falls back to publishing fresh and writing a new URL.

## Data sources the graph reads

| Source | What it gives |
|---|---|
| `~/workspace/custom-skills/*/SKILL.md` + `skill.yaml` | Skill nodes: name, text, category, mtime |
| `~/workspace/learnmuse/skill-usage.db` (central ledger) | Use counts per skill, accumulated across runs |
| Per-run ledger DBs `learnmuse-runs/<run>/ledger.db` | Proposal nodes: id, kind, status, confidence, verdict, verified-by, title, evidence |
| `learnmuse-runs/review-state.md` | Last review watermark, computed counts |
| `learnmuse-runs/<run>/review-log.md` + `proposals/*.md` | Proposal before/after, evidence, why, coexistence |
| `~/MEMORY.md` | Memory nodes (curated entries) |
| `~/memory/YYYY-MM-DD.md` (daily logs) | Raw material only, NOT nodes |
| `runtime.messages` / `agent.context_items` via `muse.db` | The transcript the computed counter counts. The graph does not read the transcript directly; it reads the counts the cron writes to review-state.md. |

## Mutations the user gets

- **Edit a skill node:** prefill with the full `SKILL.md`. The
  change is staged as a proposal and approved by name before
  it lands. A direct edit does not carry over: approval is ON
  by default and an edit from the graph is still an install.
- **Edit a memory node:** prefill with the raw entry text.
  Same staging rule. An empty body is refused ("empty memory
  — use delete to remove it"). The budget cap is enforced on
  replace, never on remove.
- **Delete a skill node:** **archives it, never deletes it.**
  Restorable with the curator's restore. Pinned skills refuse
  ("pinned — unpin it first"). Locked skills refuse any change.
- **Delete a memory node:** removes the entry from
  `~/MEMORY.md`, rewriting the file under the same care as the
  curator takes (re-read under lock, snapshot, refuse a stale
  id).
- **Proposal nodes: read-only.** The graph shows proposals; it
  does not let the user erase them.

Node ids: skills by name (stable); memories by
`memory:<source>:<index>:<fingerprint>`; proposals by
`<run>/<proposal-id>` (stable, from the ledger row).

## Honest limits

- **No live graph.** Computed on demand from files and DBs.
  No daemon, no auto-refresh.
- **No usage dimension until the central ledger has data.**
  Until LearnMuse runs record uses, skill nodes show "use
  count: no data yet". A low or absent count is absence of
  evidence, not proof of disuse: the curator's never-used
  grace floor and zero-uses rule still apply, and the graph
  must say so on the node, not print a bare 0.
- **No computed counts until the cron rewrites
  review-state.md.** Until then the graph's "last review" line
  is the last review on record and its counts are whatever
  that file says. Label them stale, do not present them as
  computed.
- **No transcript-sourced proposals until trigger 4 has
  fired.** Until then the graph's proposal nodes are all
  file-based reviews.
- **Lexical links are approximate.** A shared word is not a
  proven relationship. The graph labels memory-to-skill and
  skill-to-skill links as derived, and shows the exact
  proposal links differently from the derived ones.
- **Memory nodes are curated entries only.** The daily logs
  are not graphed. A lesson that lives only in a daily log
  and never reached `~/MEMORY.md` is invisible to the graph,
  which is exactly why trigger 4 exists: it is the path that
  turns log-only lessons into reviewed proposals.
- **Batch nudge, not live.** The computed counter fires at the
  next run, not at the turn. A long session is caught only
  the next morning. This is the structural gap that separates
  LearnMuse from a live-nudge loop; it may need a background
  process or a mid-session hook, not a patch.
- **Human-in-the-loop, not autonomous self-improvement.**
  LearnMuse delivers supervised improvement with approval ON:
  a review proposes, the user approves, the curator monitors.
  "Skills improve themselves" is not accurate. Reducing that
  friction is a future decision for the user, not something
  this skill delivers.
- **Curator handoff.** The curator's stale logic reads the
  central ledger (`skill-usage.db`), not per-run ledger rows.
- **The graph is a view, not a second curator or a second
  review.** It reads the curator's ledger and the review's
  proposals. It re-decides nothing. Stale/archived transitions
  stay the curator's job; staging stays the review's job.

## Fallbacks when a dimension has no data

If a dimension has not landed, the graph still builds from the
per-run ledgers, the skill files, and `~/MEMORY.md`, and the
dimension is marked "no data yet" instead of populated. Never
invent counts to fill them.

- Counts not computed yet: the count line reads "counts not
  computed yet — see review-state.md" and the timeline leans
  on proposal dates from the ledger rows instead.
- No transcript pass yet: the graph shows only file-based
  proposals and labels the transcript dimension "no transcript
  pass yet".
- No ledger data yet: skills are shown without use counts
  ("usage recording not started"), and the "used" filter
  cannot fire, so the graph includes skills by agent-created
  / user-taught only.

## Hard rules

- The graph reads; it never installs. Every edit or archive
  from the graph goes through the same approval gate as any
  other change.
- Proposal nodes are read-only.
- Delete archives, never deletes.
- Never invent a count, a link, or a node to fill an empty
  dimension.
- Never copy Hermes code or text verbatim. Ideas are credited,
  wording is original.
- The builder script is Python, stdlib only, reading ledger
  DBs, skill files, and memory. It produces the payload; the
  artifact renders it.

## Outputs

- The journey artifact at the canonical URL recorded in
  `learnmuse-runs/journey-artifact.txt`.
- A build line in the run log: what was built, which sources
  were live, which dimensions were empty.

## Verification checklist

- [ ] Three node kinds present, proposal nodes read-only.
- [ ] Exact links shown differently from derived links; both
  derived links labelled approximate.
- [ ] Repeat-patch skill shows all proposal edges ordered by
  timestamp; detail panel shows the most recent verdict.
- [ ] Data-health line names live vs empty sources and the
  today-sessions lag.
- [ ] Absent fields read "no usage data yet" / "unknown" /
  "no date recorded", never blank.
- [ ] Artifact URL persisted in `journey-artifact.txt`;
  rebuild updates in place; fresh-publish fallback on a
  missing file.
- [ ] No invented counts, links, or nodes.
- [ ] No install happens from the graph without approval by
  name.
