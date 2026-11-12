# LearnMuse community

You turn a good experience into a star, and a real problem into
an issue, without the user having to remember to do either. The
repo learns what helps and what breaks, from the people actually
using it.

## When to use

- After a lesson lands (a proposal is installed) AND the next
  session confirms it helped: the mistake does not repeat, or
  the user says it helped. That is the help event, and the
  only moment the star is ever considered.
- When a concrete verified problem appears: a proposal the
  verifier rejected with a real cause, a lesson that did not
  land on re-test, a skill that failed in use. That is the
  only moment an issue is ever considered.
- Never on install, never on a quiet day, never because a
  day passed with nothing happening.

## Hard rules

- **Opt-in, OFF by default.** Nothing stars, nothing files,
  nothing asks, unless the user opted in in writing. The
  opt-in is recorded in the state file by the helper. The
  skill asks once, only after a real help event, never on
  install, never on a quiet day, and never again after the
  user answers. A "no" is final until the user changes it.
- **Requires `gh` authenticated.** If `gh auth status`
  fails, the helper skips silently and logs once. Never ask
  the user for a token, never store one, never work around
  a missing `gh`.
- **Star is once, idempotent.** The helper always checks
  the live API first and stars only if the check says not
  starred. The state file records the star; it never
  short-circuits the check, so a manual un-star followed by
  a re-opt-in still re-stars. Never star twice, never unstar.
- **Issues are for concrete verified problems only.** Never
  file a vague issue, never file a one-off, never file
  without evidence. The body names the LearnMuse version,
  what failed, what was tried, and the evidence.
- **Deduplicate.** The helper lists open issues on
  reblox01/LearnMuse and matches by title before filing.
  If an open issue covers it, do not file a second one.
  Dedupe matches open issues only: a closed duplicate does
  not block a re-file if the bug recurs. Comment only if the
  user explicitly asks.
- **Rate limit.** Max 1 issue per day per user. A second
  problem the same day waits for the next day, and is
  logged, not lost.
- **No secrets.** The issue body never contains
  credentials, paths with usernames, or private data. Run
  the same commit safety check on the body before calling
  the helper: read it once, grep it for API keys, tokens,
  credential values, absolute home paths, and .db
  filenames. The helper also refuses bodies with obvious
  secret markers; that is a safety net, not a substitute
  for checking first.
- **The skill advises, the user owns the account.** A star
  and an issue are public actions on the user's GitHub
  account. The opt-in covers them, and only them. Never
  expand that cover to anything else: no follows, no
  comments, no PRs.

## The opt-in ask

Ask once, only after a real help event, in the user's own
words, one question: LearnMuse helped here, do you want
your Muse to star the LearnMuse repo when it helps, and
file an issue when something verified breaks? Say yes or
no, and that it stays off unless you say yes.

Record the answer with the helper, `opt-in --yes` or
`opt-in --no`. Never ask again after an answer, in either
direction, until the user brings it up. If the user has
not opted in and a real problem appears, do not ask on
every problem: ask once, at most, and only alongside that
real problem, then file only on yes.

## The star trigger

A lesson lands AND the next session confirms it helped.
Both parts must be true:

1. A proposal was installed (status installed in the
   ledger, or the user confirmed the change is in place).
2. The next session shows the help: the mistake the lesson
   covers does not repeat, or the user says it helped.

If opted in, call `star --do`. If not opted in, ask the
opt-in question once, then star only on yes. If the user
says no, record it and never ask again. If the help is
not confirmed, do nothing: an unconfirmed lesson is not
a help event.

## The issue trigger

A concrete verified problem, one of these:

- A proposal the verifier rejected with a real cause.
- A lesson that did not land on re-test (the mistake
  repeated after install).
- A skill that failed in use, with the failure reproduced.

Write the body first, then check it, then file it:

1. Title: short, specific, the failure in a few words.
2. Body: the bug template's fields: LearnMuse version, what
   happened, what was expected, steps to reproduce, and the
   evidence (a quote, a command, a log line).
   No credentials, no home paths, no private data.
3. Run the commit safety check on the body.
4. Call `issue --create` with the structured flags, one per
   template field: `--title <title> --version <v>
   --what-happened <...> --expected <...> --steps <...>
   --evidence <...> --environment <...> --filed-by <...>`.
   The helper builds the body in the template's section
   order, dedupes by title, and enforces the 1-per-day
   limit. If it refuses, log the reason and stop. A refused
   issue is not re-filed by hand the same day.

## Issue templates

Auto-filed issues follow the repo's bug template
(`.github/ISSUE_TEMPLATE/bug_report.md`): the helper builds
the body in the template's section order from the structured
flags, and a plain `--body` still works, landing under "What
happened" with the rest marked "Not provided". Ideas use the
idea template (`.github/ISSUE_TEMPLATE/idea.md`); the skill
never files ideas on its own, they are for people. A question
is not an issue: point the user at the README first.

## Helper

`tools/community.py` wraps every `gh` call. The skill
calls the helper; it does not shell out to `gh` directly
except through the helper.

- `star --check`: report whether the repo is starred.
  Read-only probe: never stars, never writes state.
- `star --do`: star once, if opted in, idempotent. Always
  re-checks the live API first, even when the state file
  already says starred.
- `issue --check <title>`: report an open issue with
  this title. Read-only probe: never files, never writes
  state. Note the shape differs from `--create`, which
  takes `--title`; kept as is for backwards compatibility.
- `issue --create --title <t> --body <b>`: dedupe, rate
  limit, then create, with the `bug` label.
- `opt-in --yes` / `opt-in --no`: record the opt-in answer.
- `status`: print opt-in, starred, last issue date, and the
  LearnMuse version (latest git tag, or "unknown").

The skill only calls the `--check` probes after opt-in.
- `--dry-run` (global, before the command): print what
  would be done, touch nothing.

Every command fails safe: no `gh`, no auth, no network,
or a rate limit hit means skip and log, never retry in a
loop, never crash the review. A skip exits 0; it is not
an error.

## State file

`~/.config/learnmuse/community.json`, created by the
helper, never committed, never in the repo:

- `opt_in`: true, false, or absent (absent = off, never asked).
- `asked_at`: when the opt-in question was last asked.
- `starred`: true once the star is done.
- `last_issue_at`: date of the last filed issue, for the
  rate limit.

## What it is not

- Not a second review loop, not a second curator. It does
  not stage proposals or change skills.
- Not telemetry. No usage data leaves the machine except
  the star (a public GitHub action) and the issue body
  (which the user opted into filing).
- Not a growth hack. One star per user, once, only after
  real help. Issues only for real problems.

## Verification checklist

- [ ] Opt-in is OFF by default, asked once, only after a
  real help event, never on install or a quiet day.
- [ ] Star fires only when a lesson landed AND the next
  session confirmed it helped.
- [ ] Issue fires only for a concrete verified problem,
  with version, failure, attempts, and evidence in the body.
- [ ] Body passed the commit safety check before filing.
- [ ] No follows, no comments, no PRs, no token asked for
  or stored.
- [ ] A skip (no gh, no auth, rate limit, duplicate) is
  logged and never retried in a loop.
