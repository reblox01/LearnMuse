# Changelog

## v0.3 (unreleased)

- Computed nudge counter (Hermes gap 1): counts user turns
  and tool iterations from the transcript DB since the last
  review watermark, replacing hand-kept counts.
- Session-end extraction (Hermes gap 2): the daily cron reads
  all new messages since the last review watermark,
  regardless of chat.
- Central usage ledger (Hermes gap 3): one `skill-usage.db`
  records each use at use time.
- New skill `learnmuse-journey`: learning graph timeline
  rendered as a web artifact.
- New skill `learnmuse-community`: opt-in star and issue
  filing, dedupe by title, max one issue per day, with
  `.github/ISSUE_TEMPLATE/` bug and idea templates.
- Tags are two-part (v0.2, v0.3), not three-part.

## v0.2 (11 Nov 2026)

- Verifier-only install (`./scripts/install.sh --verify-only`).
- Coexistence check in the review and the verifier.
- Baseline audit mode in `learnmuse-verify`, with the worked
  example in `examples/baseline-audit.md`.
- Memory budgets are configurable; the full `MEMORY.md` is
  never truncated to fit a summary budget.
- Opt-in tap-free and token-saver modes in
  `learnmuse-orchestrator`. Approval stays ON by default.
