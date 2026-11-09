# Sample review: a worked example

This is a worked example of one LearnMuse learning review,
end to end, on a real repeated mistake. Names and paths are
illustrative. The point is the shape: proposal, evidence,
verdict, approval, install.

## The session reviewed

Date: 2026-11-09. Work: deploying a small web app to a
staging server. The user walked Muse through the deploy
twice in one week, and both times Muse restarted the server
before running the database migration, which failed the
deploy and needed a manual fix.

Transcript excerpt, second deploy:

- User: "deploy the latest changes to staging"
- Muse: restarted the service, then ran the migration.
- User: "stop, migrate first, then restart, otherwise the
  new code starts against the old schema and crashes.
  Remember this."

## The proposal

File: `learnmuse-runs/sample-review/proposals/deploy-staging-order.md`

- Name: deploy-staging-order, action: patch the existing
  `deploy-staging` skill.
- Evidence: the transcript excerpt above, plus the first
  deploy on 2026-11-06, where the same order caused the
  same failure and the user corrected it the same way.
  Two independent corrections, same rule.
- Before: the `deploy-staging` skill listed the steps as
  "1. Push. 2. Restart the service. 3. Run migrations."
- After: "1. Push. 2. Run migrations. 3. Restart the
  service. Pitfall: restarting before migrating starts
  new code against the old schema and crashes the deploy.
  Migrate first, always."
- Why: the order is the mechanism. New code plus old
  schema equals a crash on first request.
- Kind: skill patch.

## The verifier's verdict

- Verdict: verified.
- Confidence: 5.
- Proof capsule: the verifier re-read the `deploy-staging`
  skill fresh, confirmed the old order was "restart, then
  migrate", re-read both transcript excerpts, confirmed
  the user corrected the order twice with the same words,
  and re-ran the corrected order on staging: migration
  passed, restart passed, app answered 200.
- Reason: proof re-ran unchanged, lesson is general (any
  deploy with a migration), in the right place (the deploy
  skill, not memory), not a duplicate, and the text is clean.

## Approval and install

The user approved the patch by name: "yes, apply the
deploy-staging patch". The patch was applied exactly as
shown, the ledger row was updated to installed with
confidence 5 and verdict verified, and the review log
recorded: 1 proposal, 1 verified, 1 installed, 0 rejected,
0 blocked.

## The next check

The next deploy is the test. If the deploy runs migrate
before restart without being told, the lesson landed. If
it repeats the old order, the lesson did not land, and the
next review must say so.

## What a "nothing to save" review looks like

For contrast: a session that ran smoothly, with no
corrections and no new technique, ends with one line in
the review log: "Nothing to save." No proposal is invented
to fill the budget.
