#!/usr/bin/env python3
"""LearnMuse learning ledger. Standard library only, no dependencies.

A SQLite store for everything the learning loop proposes, verifies,
installs, archives, or rejects, so a lesson survives the session
that found it, can be queried by status and verdict, and can be
handed off between runs. One database per review folder, or one
shared database for the whole skill library, your choice.

Never store secrets, tokens, passwords, session cookies, or other
users' real data in it. A ledger row holds the evidence reference
and the proof capsule, not the credential.

Usage:
  python3 tools/ledger.py init --db learnmuse-runs/demo/ledger.db
  python3 tools/ledger.py add --db <db> --id deploy-staging \\
      --title "Deploy staging: run migrate before restart" --kind skill \\
      --status proposed --confidence 3 \\
      --evidence "chat 2026-11-09: user corrected order of steps"
  python3 tools/ledger.py list --db <db> --status proposed
  python3 tools/ledger.py stats --db <db>
  python3 tools/ledger.py export --db <db> --out ledger.json
  python3 tools/ledger.py use --db <db> --id deploy-staging
"""
import argparse
import json
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    confidence INTEGER NOT NULL DEFAULT 0,
    verdict TEXT,
    evidence TEXT,
    use_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

KINDS = {"skill", "memory", "support-file"}
STATUSES = {"proposed", "verified", "candidate", "rejected", "blocked",
            "installed", "archived", "restored"}
VERDICTS = {"verified", "candidate", "rejected", "blocked", None}


def connect(db):
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    return conn


def cmd_init(args):
    connect(args.db)
    print(f"initialised {args.db}")
    return 0


def cmd_add(args):
    if args.kind not in KINDS:
        print(f"bad kind: {args.kind}", file=sys.stderr)
        return 2
    if args.status not in STATUSES:
        print(f"bad status: {args.status}", file=sys.stderr)
        return 2
    if args.verdict not in VERDICTS:
        print(f"bad verdict: {args.verdict}", file=sys.stderr)
        return 2
    if not 0 <= args.confidence <= 5:
        print("confidence must be 0-5", file=sys.stderr)
        return 2
    conn = connect(args.db)
    conn.execute(
        "INSERT OR REPLACE INTO entries "
        "(id, title, kind, status, confidence, verdict, evidence) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (args.id, args.title, args.kind, args.status,
         args.confidence, args.verdict, args.evidence),
    )
    conn.commit()
    print(f"stored {args.id} ({args.status}, confidence {args.confidence})")
    return 0


def cmd_list(args):
    conn = connect(args.db)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM entries"
    params = []
    if args.status:
        query += " WHERE status = ?"
        params.append(args.status)
    if args.kind:
        query += " AND kind = ?" if params else " WHERE kind = ?"
        params.append(args.kind)
    query += " ORDER BY created_at"
    for row in conn.execute(query, params):
        print(f"{row['id']} [{row['kind']}] {row['status']} "
              f"conf={row['confidence']} verdict={row['verdict'] or '-'} "
              f"uses={row['use_count']} :: {row['title']}")
    return 0


def cmd_stats(args):
    conn = connect(args.db)
    total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    print(f"total entries: {total}")
    for status, count in conn.execute(
            "SELECT status, COUNT(*) FROM entries GROUP BY status "
            "ORDER BY status"):
        print(f"  {status}: {count}")
    for kind, count in conn.execute(
            "SELECT kind, COUNT(*) FROM entries GROUP BY kind "
            "ORDER BY kind"):
        print(f"  {kind}: {count}")
    return 0


def cmd_export(args):
    conn = connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM entries ORDER BY created_at")]
    with open(args.out, "w") as fh:
        json.dump(rows, fh, indent=2)
    print(f"exported {len(rows)} entries to {args.out}")
    return 0


def cmd_use(args):
    conn = connect(args.db)
    cur = conn.execute(
        "UPDATE entries SET use_count = use_count + 1, "
        "last_used_at = datetime('now') WHERE id = ?", (args.id,))
    conn.commit()
    if cur.rowcount == 0:
        print(f"no entry: {args.id}", file=sys.stderr)
        return 2
    print(f"recorded use of {args.id}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="LearnMuse learning ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create the ledger database")
    p.add_argument("--db", required=True)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add", help="add or replace a ledger entry")
    p.add_argument("--db", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--kind", required=True, choices=sorted(KINDS))
    p.add_argument("--status", default="proposed",
                   choices=sorted(STATUSES))
    p.add_argument("--confidence", type=int, default=0)
    p.add_argument("--verdict", default=None,
                   choices=["verified", "candidate", "rejected", "blocked"])
    p.add_argument("--evidence", default="")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="list ledger entries")
    p.add_argument("--db", required=True)
    p.add_argument("--status", default=None, choices=sorted(STATUSES))
    p.add_argument("--kind", default=None, choices=sorted(KINDS))
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("stats", help="counts by status and kind")
    p.add_argument("--db", required=True)
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("export", help="export all entries as JSON")
    p.add_argument("--db", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("use", help="record one use of an entry")
    p.add_argument("--db", required=True)
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_use)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
