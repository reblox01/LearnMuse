#!/usr/bin/env python3
"""Tests for tools/community.py. Standard library only, no network.

The helper is exercised through its own functions with a fake
`gh` runner and a temporary state file, so no real star is ever
sent and no real issue is ever filed.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import community

TODAY = datetime.now(timezone.utc).date().isoformat()


class FakeRunner:
    """A stand-in for run_gh. Maps exact argv to (rc, out, err)."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, argv, dry_run=False):
        self.calls.append(list(argv))
        if dry_run:
            return (0, "", "")
        key = tuple(argv)
        if key in self.responses:
            return self.responses[key]
        return (1, "", "unexpected call: " + " ".join(argv))


def auth_ok():
    return {("auth", "status"): (0, "", "")}


def issue_list(issues):
    return {("issue", "list", "--repo", "reblox01/LearnMuse",
             "--state", "open", "--limit", "200",
             "--json", "title,number"): (0, json.dumps(issues), "")}


def star_not_starred():
    return {("api", "user/starred/reblox01/LearnMuse"):
            (1, "", "HTTP 404: Not Found")}


def star_starred():
    return {("api", "user/starred/reblox01/LearnMuse"): (0, "", "")}


def section_text(body, heading):
    """Text under one ## heading, up to the next ## heading."""
    start = body.index(f"## {heading}\n")
    rest = body[start + len(f"## {heading}\n"):]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def template_path(name):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..",
        ".github", "ISSUE_TEMPLATE", name)


class CommunityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = os.path.join(self.tmp.name, "community.json")
        self.opted_in = {"opt_in": True, "asked_at": "2026-11-12T00:00:00Z",
                         "starred": False, "last_issue_at": None}

    def tearDown(self):
        self.tmp.cleanup()

    def write_state(self, state):
        with open(self.state_path, "w") as fh:
            json.dump(state, fh)

    def read_state(self):
        with open(self.state_path) as fh:
            return json.load(fh)

    # Required: duplicate-title refusal.
    def test_duplicate_title_refused(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([{"title": "Crash on install", "number": 12}]),
        })
        rc = community.issue_create(
            runner, self.state_path, "crash on install",
            "Version v0.3. The skill fails on install. Tried twice.")
        self.assertEqual(rc, 0)
        create_calls = [c for c in runner.calls
                        if c[:2] == ["issue", "create"]]
        self.assertEqual(create_calls, [])
        self.assertIsNone(self.read_state()["last_issue_at"])

    def test_duplicate_title_case_and_space_insensitive(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([{"title": "  Crash On Install ", "number": 7}]),
        })
        rc = community.issue_create(
            runner, self.state_path, "crash on install", "Body.")
        self.assertEqual(rc, 0)
        self.assertEqual([c for c in runner.calls
                          if c[:2] == ["issue", "create"]], [])

    def test_issue_check_reports_duplicate(self):
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([{"title": "Crash on install", "number": 12}]),
        })
        rc = community.issue_check(runner, "Crash on install")
        self.assertEqual(rc, 0)

    def test_issue_check_reports_no_match(self):
        runner = FakeRunner({**auth_ok(), **issue_list([])})
        rc = community.issue_check(runner, "Something new")
        self.assertEqual(rc, 0)

    # Required: rate-limit refusal.
    def test_rate_limit_refused(self):
        state = dict(self.opted_in, last_issue_at=TODAY)
        self.write_state(state)
        runner = FakeRunner({**auth_ok(), **issue_list([])})
        rc = community.issue_create(
            runner, self.state_path, "A new problem", "Body.")
        self.assertEqual(rc, 0)
        self.assertEqual([c for c in runner.calls
                          if c[:2] == ["issue", "create"]], [])
        self.assertEqual(self.read_state()["last_issue_at"], TODAY)

    def test_issue_create_success_records_date(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([]),
            ("issue", "create", "--repo", "reblox01/LearnMuse",
             "--label", "bug",
             "--title", "A new problem", "--body", "Body."):
            (0, "https://github.com/reblox01/LearnMuse/issues/42\n", ""),
        })
        rc = community.issue_create(
            runner, self.state_path, "A new problem", "Body.")
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_state()["last_issue_at"], TODAY)

    def test_issue_create_passes_bug_label(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([]),
            ("issue", "create", "--repo", "reblox01/LearnMuse",
             "--label", "bug",
             "--title", "A new problem", "--body", "Body."):
            (0, "https://github.com/reblox01/LearnMuse/issues/42\n", ""),
        })
        rc = community.issue_create(
            runner, self.state_path, "A new problem", "Body.")
        self.assertEqual(rc, 0)
        creates = [c for c in runner.calls
                   if c[:2] == ["issue", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertIn("bug", creates[0])
        self.assertEqual(creates[0][creates[0].index("--label") + 1],
                         "bug")

    # Required: dry-run touches nothing.
    def test_dry_run_touches_nothing(self):
        self.write_state(self.opted_in)
        before = open(self.state_path, "rb").read()
        runner = FakeRunner({})
        rc1 = community.star_do(runner, self.state_path, dry_run=True)
        rc2 = community.issue_create(
            runner, self.state_path, "A new problem", "Body.",
            dry_run=True)
        self.assertEqual((rc1, rc2), (0, 0))
        self.assertEqual(runner.calls, [])
        self.assertEqual(open(self.state_path, "rb").read(), before)

    def test_dry_run_creates_no_state_file(self):
        runner = FakeRunner({})
        rc = community.star_do(runner, self.state_path, dry_run=True)
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(self.state_path))
        self.assertEqual(runner.calls, [])

    # Required: state file read/write.
    def test_state_read_write(self):
        rc = community.record_opt_in(self.state_path, True)
        self.assertEqual(rc, 0)
        state = community.load_state(self.state_path)
        self.assertIs(state["opt_in"], True)
        self.assertIsNotNone(state["asked_at"])
        self.assertIs(state["starred"], False)
        self.assertIsNone(state["last_issue_at"])

    def test_state_missing_file_returns_defaults(self):
        state = community.load_state(self.state_path)
        self.assertIsNone(state["opt_in"])
        self.assertIsNone(state["asked_at"])
        self.assertIs(state["starred"], False)
        self.assertIsNone(state["last_issue_at"])

    def test_state_corrupt_file_returns_defaults(self):
        with open(self.state_path, "w") as fh:
            fh.write("{not json")
        state = community.load_state(self.state_path)
        self.assertIsNone(state["opt_in"])
        self.assertIs(state["starred"], False)

    def test_opt_in_no_recorded(self):
        rc = community.record_opt_in(self.state_path, False)
        self.assertEqual(rc, 0)
        self.assertIs(community.load_state(self.state_path)["opt_in"],
                      False)

    # Star paths.
    def test_star_idempotent_when_already_starred(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({**auth_ok(), **star_starred()})
        rc = community.star_do(runner, self.state_path)
        self.assertEqual(rc, 0)
        puts = [c for c in runner.calls if "-X" in c]
        self.assertEqual(puts, [])
        self.assertIs(self.read_state()["starred"], True)

    def test_star_success_when_not_starred(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **star_not_starred(),
            ("api", "-X", "PUT", "user/starred/reblox01/LearnMuse"):
            (0, "", ""),
        })
        rc = community.star_do(runner, self.state_path)
        self.assertEqual(rc, 0)
        self.assertIs(self.read_state()["starred"], True)

    def test_star_do_rechecks_api_when_state_says_starred(self):
        # The state flag records, it never short-circuits the
        # live check: a manual un-star followed by a re-opt-in
        # still re-stars.
        state = dict(self.opted_in, starred=True)
        self.write_state(state)
        runner = FakeRunner({
            **auth_ok(),
            **star_not_starred(),
            ("api", "-X", "PUT", "user/starred/reblox01/LearnMuse"):
            (0, "", ""),
        })
        rc = community.star_do(runner, self.state_path)
        self.assertEqual(rc, 0)
        puts = [c for c in runner.calls if "-X" in c]
        self.assertEqual(len(puts), 1)
        self.assertIs(self.read_state()["starred"], True)

    def test_star_refused_when_not_opted_in(self):
        self.write_state({"opt_in": None, "asked_at": None,
                          "starred": False, "last_issue_at": None})
        runner = FakeRunner({})
        rc = community.star_do(runner, self.state_path)
        self.assertEqual(rc, 0)
        self.assertEqual(runner.calls, [])
        self.assertIs(self.read_state()["starred"], False)

    def test_star_fails_safe_without_auth(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({("auth", "status"): (1, "", "not logged in")})
        rc = community.star_do(runner, self.state_path)
        self.assertEqual(rc, 0)
        self.assertEqual(len(runner.calls), 1)
        self.assertIs(self.read_state()["starred"], False)

    def test_star_check_unknown_when_api_errors(self):
        runner = FakeRunner({
            **auth_ok(),
            ("api", "user/starred/reblox01/LearnMuse"):
            (1, "", "HTTP 500: Server Error"),
        })
        rc = community.star_check(runner)
        self.assertEqual(rc, 0)

    # Issue gates.
    def test_issue_refused_when_not_opted_in(self):
        self.write_state({"opt_in": False, "asked_at": "2026-11-12T00:00:00Z",
                          "starred": False, "last_issue_at": None})
        runner = FakeRunner({})
        rc = community.issue_create(
            runner, self.state_path, "A problem", "Body.")
        self.assertEqual(rc, 0)
        self.assertEqual(runner.calls, [])

    def test_issue_refused_when_body_has_secret_marker(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({})
        rc = community.issue_create(
            runner, self.state_path, "A problem",
            "The token was ghp_abc123 in the log.")
        self.assertEqual(rc, 0)
        self.assertEqual(runner.calls, [])
        self.assertIsNone(self.read_state()["last_issue_at"])

    def test_issue_fails_safe_when_list_unreadable(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            ("issue", "list", "--repo", "reblox01/LearnMuse",
             "--state", "open", "--limit", "200",
             "--json", "title,number"): (1, "", "network error"),
        })
        rc = community.issue_create(
            runner, self.state_path, "A problem", "Body.")
        self.assertEqual(rc, 0)
        self.assertEqual([c for c in runner.calls
                          if c[:2] == ["issue", "create"]], [])

    def test_secret_markers(self):
        self.assertEqual(
            community.find_secret_markers("clean body"), [])
        self.assertIn(
            "ghp_", community.find_secret_markers("key ghp_x"))
        self.assertIn(
            "PRIVATE KEY",
            community.find_secret_markers("-----BEGIN PRIVATE KEY-----"))

    def test_status_runs(self):
        self.write_state(self.opted_in)
        self.assertEqual(community.show_status(self.state_path), 0)

    def test_status_prints_version_line(self):
        self.write_state(self.opted_in)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = community.show_status(self.state_path)
        self.assertEqual(rc, 0)
        lines = [l for l in buf.getvalue().splitlines()
                 if l.startswith("LearnMuse version: ")]
        self.assertEqual(len(lines), 1)
        version = lines[0].split("LearnMuse version: ", 1)[1]
        self.assertTrue(version == "unknown" or
                        version.startswith("v"), version)

    def test_learnmuse_version_unknown_for_non_git_dir(self):
        self.assertEqual(
            community.learnmuse_version(self.tmp.name), "unknown")

    def test_learnmuse_version_returns_repo_tag(self):
        # The repo this file lives in has tags (v0.1.1 latest
        # at the time of writing). The function reads the tag,
        # it never invents one.
        version = community.learnmuse_version()
        self.assertTrue(version.startswith("v"), version)

    # Bug template wiring: the body is the template filled in.
    def test_bug_body_section_order(self):
        body = community.build_bug_body({
            "version": "v0.3", "what_happened": "It broke.",
            "expected": "It should work.", "steps": "1. Run it.",
            "evidence": "log line", "environment": "Linux",
            "filed_by": "a person",
        })
        headings = [h for _, h in community.BUG_TEMPLATE_SECTIONS]
        positions = [body.index(f"## {h}\n") for h in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(set(positions)), len(positions))

    def test_bug_body_matches_template_file_order(self):
        with open(template_path("bug_report.md")) as fh:
            text = fh.read()
        headings = [line[3:].strip() for line in text.splitlines()
                    if line.startswith("## ")]
        expected = [h for _, h in community.BUG_TEMPLATE_SECTIONS]
        self.assertEqual(headings, expected)

    def test_bug_body_fields_land_in_right_sections(self):
        values = {
            "version": "v0.3", "what_happened": "It broke.",
            "expected": "It should work.", "steps": "1. Run it.",
            "evidence": "log line", "environment": "Linux",
            "filed_by": "a person",
        }
        body = community.build_bug_body(values)
        for key, heading in community.BUG_TEMPLATE_SECTIONS:
            section = section_text(body, heading)
            self.assertIn(values[key], section)
            for other_key, other_value in values.items():
                if other_key != key:
                    self.assertNotIn(other_value, section)

    def test_bug_body_note_matches_template(self):
        # The helper appends the same note as the template:
        # a bold warning line, not a blockquote, same words.
        body = community.build_bug_body({"what_happened": "It broke."})
        self.assertIn("**Do not paste secrets, credentials, or private "
                      "paths.**", body)
        self.assertNotIn("> **Do not paste", body)
        with open(template_path("bug_report.md")) as fh:
            text = fh.read()
        template_note = text.rsplit("-->\n\n", 1)[1].strip()
        self.assertEqual(template_note, community.BUG_BODY_NOTE)

    def test_bug_body_missing_fields_not_provided(self):
        body = community.build_bug_body({"what_happened": "It broke."})
        for key, heading in community.BUG_TEMPLATE_SECTIONS:
            section = section_text(body, heading)
            if key == "what_happened":
                self.assertIn("It broke.", section)
            else:
                self.assertIn("Not provided", section)

    def run_main_dry(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = community.main(argv)
        return rc, buf.getvalue()

    def test_main_body_only_maps_to_what_happened(self):
        rc, out = self.run_main_dry([
            "--dry-run", "issue", "--create", "--title", "A problem",
            "--body", "Plain body."])
        self.assertEqual(rc, 0)
        headings = [h for _, h in community.BUG_TEMPLATE_SECTIONS]
        positions = [out.index(f"## {h}\n") for h in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Plain body.",
                      section_text(out, "What happened"))
        for _, heading in community.BUG_TEMPLATE_SECTIONS:
            if heading != "What happened":
                self.assertIn("Not provided",
                              section_text(out, heading))

    def test_main_structured_flags_land_in_sections(self):
        rc, out = self.run_main_dry([
            "--dry-run", "issue", "--create", "--title", "A problem",
            "--version", "v0.3", "--what-happened", "It broke.",
            "--expected", "It should work.", "--steps", "1. Run it.",
            "--evidence", "log line", "--environment", "Linux",
            "--filed-by",
            "a Muse automatically via learnmuse-community"])
        self.assertEqual(rc, 0)
        self.assertIn("v0.3",
                      section_text(out, "LearnMuse version"))
        self.assertIn("It broke.", section_text(out, "What happened"))
        self.assertIn("It should work.",
                      section_text(out, "What was expected"))
        self.assertIn("1. Run it.",
                      section_text(out, "Steps to reproduce"))
        self.assertIn("log line", section_text(out, "Evidence"))
        self.assertIn("Linux", section_text(out, "Environment"))
        self.assertIn("a Muse automatically via learnmuse-community",
                      section_text(out, "Filed by"))

    def test_main_what_happened_wins_over_body(self):
        rc, out = self.run_main_dry([
            "--dry-run", "issue", "--create", "--title", "A problem",
            "--body", "Plain body.",
            "--what-happened", "Structured happened."])
        self.assertEqual(rc, 0)
        self.assertIn("Structured happened.",
                      section_text(out, "What happened"))
        self.assertNotIn("Plain body.",
                         section_text(out, "What happened"))

    def run_main_dry_err(self, argv):
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with contextlib.redirect_stdout(out_buf), \
                contextlib.redirect_stderr(err_buf):
            rc = community.main(argv)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def test_main_body_ignored_warning_when_both_flags(self):
        rc, out, err = self.run_main_dry_err([
            "--dry-run", "issue", "--create", "--title", "A problem",
            "--body", "Plain body.",
            "--what-happened", "Structured happened."])
        self.assertEqual(rc, 0)
        self.assertIn("warning", err)
        self.assertIn("--body", err)
        self.assertIn("ignored", err)
        self.assertNotIn("Plain body.",
                         section_text(out, "What happened"))

    def test_main_no_warning_when_body_fills_what_happened(self):
        # --body with other structured flags but no
        # --what-happened fills that section; nothing is
        # dropped, so no warning.
        rc, out, err = self.run_main_dry_err([
            "--dry-run", "issue", "--create", "--title", "A problem",
            "--body", "Plain body.", "--version", "v0.3"])
        self.assertEqual(rc, 0)
        self.assertNotIn("warning", err)
        self.assertIn("Plain body.",
                      section_text(out, "What happened"))

    def test_main_create_needs_body_or_fields(self):
        with self.assertRaises(SystemExit) as ctx:
            community.main(["issue", "--create", "--title", "A problem"])
        self.assertEqual(ctx.exception.code, 2)

    # Round 2 regression: the real path through main, non-dry-run.
    # main's runner is a one-argument lambda, but check_auth,
    # is_starred, and find_open_issue called it with two. In
    # dry-run mode the callers return early, so the bug never
    # fired there and the old tests never caught it. In
    # non-dry-run mode the first real star or issue call crashed
    # with TypeError the moment check_auth ran. These tests drive
    # main() itself, so they fail on the old code and pass on
    # the fix.
    def run_main_patched(self, argv, runner):
        """Run main() with run_gh patched and a temp state file."""
        with mock.patch.dict(
                os.environ,
                {"LEARNMUSE_COMMUNITY_STATE": self.state_path}), \
             mock.patch.object(community, "run_gh", runner):
            return community.main(argv)

    def test_main_star_do_non_dry_run(self):
        self.write_state(self.opted_in)
        runner = FakeRunner({
            **auth_ok(),
            **star_not_starred(),
            ("api", "-X", "PUT", "user/starred/reblox01/LearnMuse"):
            (0, "", ""),
        })
        rc = self.run_main_patched(["star", "--do"], runner)
        self.assertEqual(rc, 0)
        self.assertEqual(runner.calls, [
            ["auth", "status"],
            ["api", "user/starred/reblox01/LearnMuse"],
            ["api", "-X", "PUT", "user/starred/reblox01/LearnMuse"],
        ])
        self.assertIs(self.read_state()["starred"], True)

    def test_main_issue_create_non_dry_run_structured(self):
        self.write_state(self.opted_in)
        fields = {
            "version": "v0.3", "what_happened": "It broke.",
            "expected": "It should work.", "steps": "1. Run it.",
            "evidence": "log line", "environment": "Linux",
            "filed_by": "a Muse automatically via learnmuse-community",
        }
        body = community.build_bug_body(fields)
        runner = FakeRunner({
            **auth_ok(),
            **issue_list([]),
            ("issue", "create", "--repo", "reblox01/LearnMuse",
             "--label", "bug", "--title", "A new problem",
             "--body", body):
            (0, "https://github.com/reblox01/LearnMuse/issues/42\n", ""),
        })
        rc = self.run_main_patched([
            "issue", "--create", "--title", "A new problem",
            "--version", "v0.3", "--what-happened", "It broke.",
            "--expected", "It should work.",
            "--steps", "1. Run it.", "--evidence", "log line",
            "--environment", "Linux", "--filed-by",
            "a Muse automatically via learnmuse-community"], runner)
        self.assertEqual(rc, 0)
        creates = [c for c in runner.calls
                   if c[:2] == ["issue", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0][creates[0].index("--label") + 1],
                         "bug")
        filed_body = creates[0][creates[0].index("--body") + 1]
        self.assertIn("It broke.",
                      section_text(filed_body, "What happened"))
        self.assertIn("v0.3",
                      section_text(filed_body, "LearnMuse version"))
        self.assertEqual(self.read_state()["last_issue_at"], TODAY)

    def test_main_runner_takes_one_argument(self):
        # A runner that raises if called with more than one
        # argument, driven through main. The helpers call the
        # runner main builds (the lambda), and the lambda
        # forwards its single argv to run_gh, so what strict
        # sees is what the helpers passed to the runner. On
        # the old code a helper's two-argument runner call
        # raised TypeError in the lambda before run_gh ran.
        responses = {**auth_ok(), **star_not_starred(),
                     ("api", "-X", "PUT",
                      "user/starred/reblox01/LearnMuse"): (0, "", "")}
        seen = []

        def strict(argv):
            # One positional argument only. Called with two,
            # Python raises TypeError, exactly as main's
            # lambda would on the old two-argument call.
            seen.append(list(argv))
            key = tuple(argv)
            if key in responses:
                return responses[key]
            return (1, "", "unexpected call: " + " ".join(argv))

        def fake_run_gh(argv, dry_run=False):
            return strict(argv)

        self.write_state(self.opted_in)
        rc = self.run_main_patched(["star", "--do"], fake_run_gh)
        self.assertEqual(rc, 0)
        self.assertEqual(seen, [
            ["auth", "status"],
            ["api", "user/starred/reblox01/LearnMuse"],
            ["api", "-X", "PUT", "user/starred/reblox01/LearnMuse"],
        ])
        self.assertIs(self.read_state()["starred"], True)
        # The strict runner itself refuses a second argument.
        with self.assertRaises(TypeError):
            strict(["auth", "status"], False)

    def test_helpers_call_runner_with_one_argument(self):
        # The same contract at the helper level: check_auth,
        # is_starred, and find_open_issue take a one-argument
        # runner and call it with one argument.
        responses = {**auth_ok(), **star_not_starred(),
                     **issue_list([])}

        def strict(argv):
            key = tuple(argv)
            if key in responses:
                return responses[key]
            return (1, "", "unexpected call: " + " ".join(argv))

        self.assertIs(community.check_auth(strict), True)
        self.assertIs(community.is_starred(strict), False)
        self.assertEqual(
            community.find_open_issue(strict, "Something new"),
            (False, None))
        with self.assertRaises(TypeError):
            strict(["auth", "status"], False)

    def test_main_star_do_fails_safe_when_gh_missing(self):
        # Non-dry-run through main with gh missing: skip and
        # log, exit 0, no crash. The old two-argument runner
        # call crashed here too, before gh was even reached.
        def missing(argv, dry_run=False):
            return (127, "", "gh not found")

        self.write_state(self.opted_in)
        rc = self.run_main_patched(["star", "--do"], missing)
        self.assertEqual(rc, 0)
        self.assertIs(self.read_state()["starred"], False)

    def test_issue_templates_parse(self):
        import yaml
        for name, title_prefix in (("bug_report.md", "[Bug] "),
                                   ("idea.md", "[Idea] ")):
            with open(template_path(name)) as fh:
                text = fh.read()
            self.assertTrue(text.startswith("---\n"))
            front, _sep, _body = text[4:].partition("\n---\n")
            data = yaml.safe_load(front)
            for key in ("name", "about", "title", "labels"):
                self.assertIn(key, data, f"{name} missing {key}")
            self.assertTrue(data["title"].startswith(title_prefix))
            self.assertTrue(data["labels"])
        with open(template_path("config.yml")) as fh:
            config = yaml.safe_load(fh)
        self.assertIs(config.get("blank_issues_enabled"), False)
        links = config.get("contact_links") or []
        self.assertTrue(any("readme" in str(link.get("url", "")).lower()
                            for link in links))


if __name__ == "__main__":
    unittest.main()
