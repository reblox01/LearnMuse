# LearnMuse memory

You manage Muse's bounded, curated memory so it remembers
across sessions without bloating. Memory holds who the user
is and facts about the environment. Skills hold how to do a
class of task. One lesson lives in exactly one place: if it
is a procedure, it belongs in a skill, not in memory.

## When to use

- The user says "remember this", or corrects a fact about
  themselves, their setup, or their project.
- The background review proposes a memory entry instead of
  a skill change.
- Memory is full, stale, or contradictory, and needs a prune.
- A session starts and you need to recall what was learned
  before: search memory first, before asking the user again.

Do not use memory as a diary. A session-specific detail, a
temporary path, or a one-off debugging note does not belong
in memory.

## The two stores

| Store | Purpose | Budget |
|---|---|---|
| `MEMORY.md` | Agent notes: environment facts, conventions, lessons learned, completed work | Keep tight, 8-15 entries, each one or two lines |
| `USER.md` | User profile: preferences, communication style, expectations, pet peeves | Keep tight, 5-10 entries, each one or two lines |

Both live in `~/MEMORY.md` and `~/memory/`, and are loaded
into the session. Entries are compact and information-dense.
A good entry packs several related facts:

- Good: "User runs macOS 14, Homebrew, Docker Desktop.
  Shell: zsh. Editor: VS Code with Vim keybindings."
- Good: "Project ~/code/api uses Go 1.22, sqlc, chi router.
  Run tests with 'make test'. CI via GitHub Actions."
- Good: "Staging server (10.0.1.50) needs SSH port 2222,
  not 22. Key is at ~/.ssh/staging_ed25519."
- Bad: "User has a project." Too vague to be useful.
- Bad: a paragraph of dated narrative. Dates and stories
  belong in the daily log, not in memory.

Memory is a snapshot: entries saved in the current session
become visible to the next session, not to one already
running. Start a new session after a memory write for it to
take effect.

## What to save

Save proactively, when you learn it:

- User preferences: "I prefer TypeScript over JavaScript"
  goes to the user profile.
- Environment facts: "This server runs Debian 12 with
  PostgreSQL 16" goes to memory.
- Corrections: "Do not use sudo for Docker, the user is in
  the docker group" goes to memory.
- Conventions: "Project uses tabs, 120-char lines,
  Google-style docstrings" goes to memory.
- Completed work: "Migrated the database from MySQL to
  PostgreSQL on 2026-01-15" goes to memory.
- Explicit requests: "Remember that my API key rotation
  happens monthly" goes to memory.

## What to skip

- Trivial or obvious info: "User asked about Python".
- Facts easily re-discovered: "Python 3.12 supports f-string
  nesting". A web search finds this.
- Raw data dumps: large code blocks, logs, tables.
- Session-specific ephemera: temporary file paths, one-off
  debugging context.
- Information already in context files: `SOUL.md` and
  `AGENTS.md` content.
- Anything that is really a procedure. That belongs in a
  skill, via learnmuse-learn or learnmuse-review.

## How to save

Every memory write is staged first, like every other
LearnMuse change, and applied only after the user approves
that exact entry. Approval is ON by default. The background
review may propose memory entries, but it never writes them
directly.

To save an entry:

1. Check for a duplicate first. An exact duplicate is not
   added. A near-duplicate is merged into the existing entry,
   not added beside it.
2. Check the budget. If the store is above 80 percent of its
   budget, consolidate before adding: merge three separate
   "project uses X" entries into one comprehensive entry.
3. Write the entry in one or two lines, with the fact and
   its context, no story.
4. Record the write in the ledger via `tools/ledger.py`,
   with kind memory, status, and evidence.

To change an entry, patch the span that is wrong and keep
the rest. To remove an entry that is no longer true, remove
it and log the removal. Never rewrite a whole entry to fix
one fact: that wipes the other facts in a multi-fact entry.

## Session search

Beyond the two stores, recall past conversations with
`muse.memory_search` and, when you need exact records,
`muse.db`. Memory is for critical facts that should always
be in context. Session search is for "did we discuss X last
week?" queries where you need specifics from past
conversations. Search before you ask the user to repeat
something they already told you.

If you told the user something is remembered and the next
session does not know it, check in order: did the write
actually happen (is the entry in the file?), was it staged
for approval and never approved, are you reading the same
profile's memory, and was a new session started after the
write? A sentence like "I have added that to my memory" is
just text: the entry in the file is the proof.

## Prune rules

Memory entries go stale or conflict. On a review, flag
each entry as keep, update, or remove, and ask the user
per entry. Never infer approval.

- STALE: the file, path, or project it names no longer
  exists. Remove it, or update it to the new location.
- CONFLICT: two entries say opposite things. Keep the
  newer one only if the evidence supports it, and remove
  or correct the older one. Ask the user when the evidence
  is unclear.
- DUPLICATE: the same fact in two entries. Merge them.

A forget request from the user is honoured completely:
remove the entry, remove any ledger row that could bring
it back, and say what was removed. An archived skill is
not a deleted one, and a forgotten fact must not survive
in the ledger.

## Security

Memory entries are injected into the system prompt, so they
are scanned before they are accepted. Content matching
injection or exfiltration patterns, or containing invisible
Unicode characters, is blocked. Never store secrets, tokens,
passwords, or session cookies in memory. A credential belongs
in the secure vault, never in a memory file.

## Hard rules

- Approval is ON by default. A memory write is staged and
  approved for that exact entry, like any other change.
- One lesson lives in exactly one place. Procedures go to
  skills, facts go to memory.
- Keep it tight. If the store grows past its budget,
  consolidate before adding.
- Never store a secret in memory.

## Verification checklist

- [ ] Entry is a fact or a preference, not a procedure.
- [ ] Entry is one or two lines, no story, no date narrative.
- [ ] No duplicate: checked, and merged if near-duplicate.
- [ ] Budget checked: store is within budget, or entries
  were consolidated first.
- [ ] Entry staged, user approved that exact entry.
- [ ] Ledger row exists for the write.
- [ ] Session search was tried before asking the user to
  repeat something.
