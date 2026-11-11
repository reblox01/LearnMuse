# Baseline audit: a worked example

This is a worked example of the learnmuse-verify baseline
audit mode, on a small existing library. Names, tools, and
paths are illustrative. The two bugs are modeled on a real
report from Best_Caterpillar1682 on 11 Nov 2026: his
standalone verifier audit flagged, within the hour, a
sourcing skill that had frozen a wrong tool diagnosis as
a permanent rule three weeks after the diagnosis was
retracted, plus a second skill carrying near-verbatim
copies of rules owned by three others. Both were fixed
and re-verified. Thank you to Best_Caterpillar1682 for
the catch and for the report.

## The library audited

Five skills, each read fresh:

- `sourcing`: fetching supplier data with Tool X.
- `reporting`: building a weekly report.
- `deploy-staging`: deploying a web app to staging.
- `billing`: invoicing a client.
- `notes`: saving a short note after a call.

Retraction evidence, dated three weeks before the audit:

- "Tool X cache bug was a misread config on our side.
  The cache is correct. The stale data diagnosis is
  retracted."

## Finding A: frozen retracted diagnosis, confirmed

- Skill: `sourcing`, rule quoted: "Tool X always returns stale data. Never trust its cache. Always re-fetch by hand."
- The same rule also appears in `reporting`.
- Retraction quoted above: the cache is correct, the
  diagnosis is retracted.
- Action: remove the rule from both skills. In `sourcing`,
  replace it with: "Trust the Tool X cache. The stale data
  diagnosis was retracted, it was a misread config."

## Finding B: near-verbatim copies, confirmed

- Skill: `reporting` carries three copied rules:
  - "Run migrations before restart, otherwise the new code starts against the old schema and crashes the deploy. Migrate first, always." Owner: `deploy-staging`.
  - "Invoice in EUR, never USD." Owner: `billing`.
  - "Tool X always returns stale data. Never trust its cache. Always re-fetch by hand." Owner: `sourcing`, and that rule is also Finding A, already retracted.
- That is how the bad rule survived: fixing one copy
  leaves the others in place.
- Action: keep each rule in its owner only. In `reporting`,
  remove all three copied rules and add one pointer line:
  "Deploy order: see deploy-staging. Invoicing: see
  billing. Tool X cache: see sourcing."

## Finding C: stale rules

- None in this library. No rule names a tool, a path, a
  version, or a workflow that no longer exists, and no
  rule contradicts a newer rule. No finding, no false
  positive.

## Clean skill

- `notes`: no findings. Its only rule is "Write the date,
  the caller, and one line on what was agreed." It is
  listed clean, not skipped.

## Fixes and re-verification

Each fix was staged as a proposal, verified separately,
and applied only after the user approved that exact
change. The audit itself applied no fix.

Re-audit after the fixes:

- The Tool X stale data rule appears nowhere in its old
  form. `sourcing` now says to trust the cache.
- The migrate rule appears only in `deploy-staging`.
  The invoice rule appears only in `billing`.
- `reporting` points to the three owners instead of
  copying their rules.
- `notes` is still clean.

The audit verdict after the fixes: clean, with the
findings above recorded in the ledger.
