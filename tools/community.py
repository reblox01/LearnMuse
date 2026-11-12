#!/usr/bin/env python3
"""LearnMuse community feedback helper. Standard library only.

Wraps the `gh` CLI so a user's Muse can star reblox01/LearnMuse
once after real help, and file issues for concrete verified
problems, without the skill shelling out to `gh` directly.

Opt-in, OFF by default. Nothing stars or files unless the user
opted in in writing; the opt-in lives in the state file. The
skill asks once, only after a real help event, and records the
answer with `opt-in`. A "no" is final until the user changes it.

Requires `gh` authenticated. Without it every command fails
safe: skip and log, exit 0, never retry in a loop, never crash
the review. Never asks the user for a token, never stores one.

State file: ~/.config/learnmuse/community.json (never committed,
never in the repo). Set LEARNMUSE_COMMUNITY_STATE to override
the path; that override exists for tests only.

Usage:
  python3 tools/community.py star --check
  python3 tools/community.py star --do
  python3 tools/community.py issue --check "title"
  python3 tools/community.py issue --create --title "t" --body "b"
  python3 tools/community.py issue --create --title "t" \
      --version v0.3 --what-happened "..." --expected "..." \
      --steps "..." --evidence "..." --environment "..." \
      --filed-by "a Muse automatically via learnmuse-community"
  python3 tools/community.py opt-in --yes | --no
  python3 tools/community.py status
  python3 tools/community.py --dry-run <any of the above>

`star --check` and `issue --check` are read-only probes: they
never star, never file, never write state, and the skill only
calls them after opt-in. Note the shapes differ: `--check`
takes the title as its value (`issue --check "title"`), while
`--create` takes `--title` (`issue --create --title "t"`).
Kept as is for backwards compatibility.

`issue --create` builds the body in the bug template's section
order (.github/ISSUE_TEMPLATE/bug_report.md). The structured
flags fill the template's sections; a plain --body still
works and goes under "What happened", the rest reading
"Not provided".

Exit codes: 0 means done or skipped safely. 2 means bad usage.
A skip is never an error: no gh, no auth, no network, a rate
limit hit, a duplicate title, or a refused body all exit 0
with a log line, and touch nothing.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone

REPO = "reblox01/LearnMuse"
GH_TIMEOUT = 30
ISSUE_LIST_LIMIT = 200
MAX_ISSUES_PER_DAY = 1

# High-signal markers that a body contains a credential. A refused
# body is never filed. This is a safety net, not a substitute for
# the skill checking the body before it calls the helper.
SECRET_MARKERS = (
    "ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_",
    "-----BEGIN", "PRIVATE KEY", "xoxb-", "xoxp-", "sk-proj-",
)


def default_state_path():
    override = os.environ.get("LEARNMUSE_COMMUNITY_STATE")
    if override:
        return override
    return os.path.join(
        os.path.expanduser("~"), ".config", "learnmuse", "community.json")


def load_state(path):
    """Read the state file. Missing or corrupt means defaults."""
    state = {"opt_in": None, "asked_at": None, "starred": False,
             "last_issue_at": None}
    try:
        with open(path) as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        return state
    except (OSError, ValueError):
        print(f"warning: state file {path} unreadable, using defaults",
              file=sys.stderr)
        return state
    if not isinstance(raw, dict):
        return state
    for key in state:
        if key in raw:
            state[key] = raw[key]
    return state


def save_state(path, state):
    """Write the state file atomically (temp file + rename)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_dir():
    # realpath, not abspath: a symlinked __file__, or a relative
    # one that resolves outside the repo, must still land on
    # the repo this file lives in.
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def learnmuse_version(repo=None):
    """Best-effort version: the latest git tag, else "unknown".

    Never invents a version: an install from a zip, a repo with
    no tags, or no git at all all read "unknown". The repo path
    is resolved through realpath first, so a call through a
    symlink still finds the tags.
    """
    target = repo or repo_dir()
    try:
        proc = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=target, capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return "unknown"
    tag = proc.stdout.strip()
    return tag if proc.returncode == 0 and tag else "unknown"


def run_gh(argv, dry_run=False):
    """Run one gh command. Returns (returncode, stdout, stderr).

    Never raises: a missing gh, a timeout, or any other failure
    comes back as a return code. In dry-run mode nothing runs;
    the command is printed and a success is pretended.
    """
    if dry_run:
        print("[dry-run] would run: gh " +
              " ".join(shlex.quote(a) for a in argv))
        return (0, "", "")
    try:
        proc = subprocess.run(
            ["gh"] + argv, capture_output=True, text=True,
            timeout=GH_TIMEOUT)
        return (proc.returncode, proc.stdout, proc.stderr)
    except FileNotFoundError:
        return (127, "", "gh not found")
    except subprocess.TimeoutExpired:
        return (124, "", "gh timed out")


def check_auth(runner):
    """True when gh is authenticated. Fails safe to False.

    The runner takes argv only; dry_run is bound when the
    runner is created (main's lambda), never passed here.
    """
    rc, _, _ = runner(["auth", "status"])
    return rc == 0


def is_starred(runner):
    """True if starred, False if not, None if it cannot be told."""
    rc, out, err = runner(["api", f"user/starred/{REPO}"])
    if rc == 0:
        return True
    if "404" in err or "404" in out or "Not Found" in err:
        return False
    return None


def find_open_issue(runner, title):
    """(found, number) for an open issue with this title.

    Title match is exact after stripping whitespace, case
    insensitive. Open issues only, by design: a closed
    duplicate does not block a re-file if the bug recurs.
    Returns (None, None) when the list cannot be read, so the
    caller can fail safe instead of guessing.
    """
    rc, out, err = runner(
        ["issue", "list", "--repo", REPO, "--state", "open",
         "--limit", str(ISSUE_LIST_LIMIT), "--json", "title,number"])
    if rc != 0:
        return (None, None)
    try:
        issues = json.loads(out)
    except ValueError:
        return (None, None)
    wanted = title.strip().casefold()
    for issue in issues:
        if isinstance(issue, dict) and \
                str(issue.get("title", "")).strip().casefold() == wanted:
            return (True, issue.get("number"))
    return (False, None)


def find_secret_markers(body):
    """Secret markers present in a body, empty when clean."""
    return [m for m in SECRET_MARKERS if m in body]


# The bug template's sections, in the template's exact order.
# The helper builds every auto-filed body in this order, so a
# body is the template filled in, never a free-form paragraph.
# (.github/ISSUE_TEMPLATE/bug_report.md)
BUG_TEMPLATE_SECTIONS = (
    ("version", "LearnMuse version"),
    ("what_happened", "What happened"),
    ("expected", "What was expected"),
    ("steps", "Steps to reproduce"),
    ("evidence", "Evidence"),
    ("environment", "Environment"),
    ("filed_by", "Filed by"),
)

BUG_BODY_NOTE = (
    "**Do not paste secrets, credentials, or private paths.**\n"
    "No API keys, tokens, passwords, private keys, or absolute\n"
    "home paths. An issue with a secret in it will be edited\n"
    "or deleted, and the secret must be rotated."
)


def build_bug_body(fields):
    """Render a body in the bug template's section order.

    `fields` maps section keys to text. A missing or blank
    field reads "Not provided", never a blank section: a blank
    section looks like the reporter forgot it, and the template
    exists so nothing is forgotten silently.
    """
    parts = []
    for key, heading in BUG_TEMPLATE_SECTIONS:
        value = (fields or {}).get(key)
        text = value.strip() if isinstance(value, str) else ""
        if not text:
            text = "Not provided"
        parts.append(f"## {heading}\n\n{text}")
    parts.append(BUG_BODY_NOTE)
    return "\n\n".join(parts) + "\n"


def star_check(runner, dry_run=False):
    # Read-only probe: reports the star state, never stars,
    # never writes state. No opt-in gate here by design; the
    # skill only calls it after opt-in.
    if dry_run:
        print("[dry-run] would check: gh auth status")
        print(f"[dry-run] would check: gh api user/starred/{REPO}")
        print("[dry-run] would print starred: yes or no")
        return 0
    if not check_auth(runner):
        print("skip: gh not authenticated (or gh missing)", file=sys.stderr)
        return 0
    starred = is_starred(runner)
    if starred is None:
        print("skip: could not check star status", file=sys.stderr)
        return 0
    print(f"starred: {'yes' if starred else 'no'}")
    return 0


def star_do(runner, state_path, dry_run=False):
    if dry_run:
        print("[dry-run] would check: opt-in is true in the state file")
        print("[dry-run] would check: gh auth status")
        print(f"[dry-run] would check: gh api user/starred/{REPO}")
        print(f"[dry-run] would star: gh api -X PUT user/starred/{REPO} "
              "(only if not already starred)")
        print("[dry-run] would record starred=true in the state file")
        return 0
    state = load_state(state_path)
    if state.get("opt_in") is not True:
        print("skip: not opted in (opt-in is off by default)",
              file=sys.stderr)
        return 0
    # No short-circuit on state["starred"]: the live API check
    # always runs. The flag records, it never decides. If the
    # user manually un-starred and re-opts in, the star fires
    # again instead of trusting a stale flag.
    if not check_auth(runner):
        print("skip: gh not authenticated (or gh missing)", file=sys.stderr)
        return 0
    starred = is_starred(runner)
    if starred is None:
        print("skip: could not check star status", file=sys.stderr)
        return 0
    if starred:
        state["starred"] = True
        save_state(state_path, state)
        print("already starred (recorded)")
        return 0
    rc, _, err = runner(["api", "-X", "PUT", f"user/starred/{REPO}"])
    if rc != 0:
        print(f"skip: star request failed: {err.strip() or 'unknown'}",
              file=sys.stderr)
        return 0
    state["starred"] = True
    save_state(state_path, state)
    print(f"starred {REPO}")
    return 0


def issue_check(runner, title, dry_run=False):
    # Read-only probe: reports a matching open issue, never
    # files, never writes state. No opt-in gate here by design;
    # the skill only calls it after opt-in.
    if dry_run:
        print("[dry-run] would check: gh auth status")
        print(f"[dry-run] would list open issues on {REPO} and match "
              f"title {title!r}")
        print("[dry-run] would print duplicate or no match")
        return 0
    if not check_auth(runner):
        print("skip: gh not authenticated (or gh missing)", file=sys.stderr)
        return 0
    found, number = find_open_issue(runner, title)
    if found is None:
        print("skip: could not list open issues", file=sys.stderr)
        return 0
    if found:
        print(f"duplicate: open issue #{number} has this title")
    else:
        print("no open issue with this title")
    return 0


def issue_create(runner, state_path, title, body, dry_run=False):
    if dry_run:
        print("[dry-run] would check: opt-in is true in the state file")
        print("[dry-run] would check: body has no secret markers")
        print("[dry-run] would check: no issue filed today (max 1/day)")
        print("[dry-run] would check: gh auth status")
        print(f"[dry-run] would list open issues on {REPO} and match "
              f"title {title!r}")
        print("[dry-run] would create the issue with label bug only if "
              "no duplicate and no rate limit hit")
        print("[dry-run] would record last_issue_at=today in the state "
              "file")
        print(f"[dry-run] body that would be filed (title {title!r}):")
        print(body.rstrip())
        return 0
    state = load_state(state_path)
    if state.get("opt_in") is not True:
        print("skip: not opted in (opt-in is off by default)",
              file=sys.stderr)
        return 0
    markers = find_secret_markers(body)
    if markers:
        print(f"refused: body contains possible secret markers: "
              f"{', '.join(markers)}", file=sys.stderr)
        return 0
    if state.get("last_issue_at") == today_str():
        # A wall-clock UTC date, not a 24-hour window: one issue
        # per calendar day, and the next day is a fresh day even
        # if the last issue was an hour ago.
        print("skip: already filed an issue today (max 1 per day)",
              file=sys.stderr)
        return 0
    if not check_auth(runner):
        print("skip: gh not authenticated (or gh missing)", file=sys.stderr)
        return 0
    found, number = find_open_issue(runner, title)
    if found is None:
        print("skip: could not list open issues", file=sys.stderr)
        return 0
    if found:
        print(f"duplicate: open issue #{number} has this title, "
              "not filing a second one")
        return 0
    rc, out, err = runner(
        ["issue", "create", "--repo", REPO, "--label", "bug",
         "--title", title, "--body", body])
    if rc != 0:
        print(f"skip: issue create failed: {err.strip() or 'unknown'}",
              file=sys.stderr)
        return 0
    state["last_issue_at"] = today_str()
    save_state(state_path, state)
    url = out.strip().splitlines()[0] if out.strip() else ""
    print(f"filed issue {url}".rstrip())
    return 0


def record_opt_in(state_path, value, dry_run=False):
    if dry_run:
        print(f"[dry-run] would record opt_in={str(value).lower()} and "
              "asked_at=now in the state file")
        return 0
    state = load_state(state_path)
    state["opt_in"] = value
    state["asked_at"] = now_iso()
    save_state(state_path, state)
    print(f"opt-in recorded: {'yes' if value else 'no'}")
    return 0


def show_status(state_path):
    state = load_state(state_path)
    opt_in = state.get("opt_in")
    opt_text = ("yes" if opt_in is True else
                "no" if opt_in is False else "not asked")
    print(f"opt-in: {opt_text}")
    print(f"starred: {'yes' if state.get('starred') else 'no'}")
    last = state.get("last_issue_at")
    print(f"last issue: {last if last else 'none'}")
    print(f"LearnMuse version: {learnmuse_version()}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="LearnMuse community feedback helper")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be done, touch nothing")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("star", help="check or do the repo star")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="report whether the repo is starred")
    group.add_argument("--do", action="store_true",
                       help="star the repo once, if opted in")

    p = sub.add_parser("issue", help="check or file an issue")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="TITLE",
                       help="report an open issue with this title")
    group.add_argument("--create", action="store_true",
                       help="file an issue (dedupe + rate limit first)")
    p.add_argument("--title", default=None)
    p.add_argument("--body", default=None)
    # Bug template fields (.github/ISSUE_TEMPLATE/bug_report.md).
    # When any is given, the body is built in the template's
    # section order. A plain --body still works: it goes under
    # "What happened" and the rest read "Not provided".
    p.add_argument("--version", default=None,
                   help="bug template field: LearnMuse version")
    p.add_argument("--what-happened", default=None,
                   help="bug template field: what happened")
    p.add_argument("--expected", default=None,
                   help="bug template field: what was expected")
    p.add_argument("--steps", default=None,
                   help="bug template field: steps to reproduce")
    p.add_argument("--evidence", default=None,
                   help="bug template field: evidence")
    p.add_argument("--environment", default=None,
                   help="bug template field: environment")
    p.add_argument("--filed-by", default=None,
                   help="bug template field: filed by")

    p = sub.add_parser("opt-in", help="record the opt-in answer")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--yes", action="store_true")
    group.add_argument("--no", action="store_true")

    sub.add_parser("status", help="print opt-in, starred, last issue")

    args = parser.parse_args(argv)
    runner = lambda argv: run_gh(argv, args.dry_run)
    state_path = default_state_path()

    if args.command == "star":
        if args.check:
            return star_check(runner, args.dry_run)
        return star_do(runner, state_path, args.dry_run)
    if args.command == "issue":
        if args.check is not None:
            return issue_check(runner, args.check, args.dry_run)
        structured = {
            "version": args.version,
            "what_happened": args.what_happened,
            "expected": args.expected,
            "steps": args.steps,
            "evidence": args.evidence,
            "environment": args.environment,
            "filed_by": args.filed_by,
        }
        has_structured = any(v is not None
                             for v in structured.values())
        if not args.title or (not args.body and not has_structured):
            parser.error(
                "issue --create needs --title and --body, or the bug "
                "template fields (--version, --what-happened, "
                "--expected, --steps, --evidence, --environment, "
                "--filed-by)")
        if args.body and not has_structured:
            # Backwards compatible: a plain --body goes under
            # "What happened", the rest read "Not provided".
            body = build_bug_body({"what_happened": args.body})
        else:
            if args.body and structured["what_happened"]:
                # Both given: --what-happened wins and --body is
                # dropped. Say so instead of dropping it silently.
                print("warning: --body ignored because --what-happened "
                      "was given", file=sys.stderr)
            elif args.body:
                structured["what_happened"] = args.body
            body = build_bug_body(structured)
        return issue_create(runner, state_path, args.title, body,
                            args.dry_run)
    if args.command == "opt-in":
        return record_opt_in(state_path, bool(args.yes), args.dry_run)
    if args.command == "status":
        return show_status(state_path)
    parser.error("unknown command")


if __name__ == "__main__":
    sys.exit(main())
