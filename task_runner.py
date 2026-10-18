#!/usr/bin/env python3
"""Explicit task-to-approved-tool runner for NEO-LOCAL.

Queued tasks never run automatically. A user must invoke this command with a
task ID, an approved tool name, and the input text.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import core
import tool_lab


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_tasks() -> None:
    with core.connect() as db:
        rows = db.execute(
            "SELECT id, goal, status, created_at, updated_at FROM tasks ORDER BY id DESC LIMIT 50"
        ).fetchall()
    if not rows:
        print("No tasks.")
        return
    for row in rows:
        print(f"#{row['id']} [{row['status']}] {row['goal']}")


def recover_stale_tasks(older_than_minutes: int = 60) -> int:
    """Explicitly mark long-stuck running tasks failed; never resumes them."""
    if not isinstance(older_than_minutes, int) or isinstance(older_than_minutes, bool) or not 1 <= older_than_minutes <= 10080:
        raise ValueError("older-than-minutes must be between 1 and 10080")
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)).isoformat(timespec="seconds")
    stamp = now()
    with core.connect() as db:
        cur = db.execute(
            """UPDATE tasks
               SET status='failed', result=?, updated_at=?
               WHERE status='running' AND updated_at < ?""",
            ("Recovered as failed: task was left running after an interruption.", stamp, cutoff),
        )
        count = cur.rowcount
    return count


def execute_task(task_id: int, tool_name: str, input_text: str) -> Any:
    if task_id < 1:
        raise ValueError("task ID must be positive")
    with core.connect() as db:
        task = db.execute("SELECT id, goal, status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task is None:
            raise ValueError("task does not exist")
        if task["status"] != "queued":
            raise ValueError(f"task must be queued; current status is {task['status']}")
        stamp = now()
        db.execute(
            "UPDATE tasks SET status='running', result=NULL, updated_at=? WHERE id=? AND status='queued'",
            (stamp, task_id),
        )
        if db.execute("SELECT changes()").fetchone()[0] != 1:
            raise ValueError("task state changed; refusing to run")
    try:
        result = tool_lab.run_approved(tool_name, input_text)
        result_text = json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        with core.connect() as db:
            db.execute(
                "UPDATE tasks SET status='failed', result=?, updated_at=? WHERE id=? AND status='running'",
                (f"{type(exc).__name__}: {exc}"[:2000], now(), task_id),
            )
        try:
            tool_lab.audit("task_failed", tool_name, f"task:{task_id}")
        except OSError:
            pass
        raise
    with core.connect() as db:
        db.execute(
            "UPDATE tasks SET status='completed', result=?, updated_at=? WHERE id=? AND status='running'",
            (result_text[:12000], now(), task_id),
        )
    tool_lab.audit("task_completed", tool_name, f"task:{task_id}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a queued task with an approved NEO-LOCAL tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list recent tasks")
    run = sub.add_parser("run", help="explicitly run one queued task with an approved tool")
    run.add_argument("task_id", type=int)
    run.add_argument("tool_name")
    run.add_argument("input_text")
    recover = sub.add_parser("recover", help="mark old interrupted running tasks as failed; never resumes them")
    recover.add_argument("--older-than-minutes", type=int, default=60)
    args = parser.parse_args(argv)
    try:
        core.init_db()
        if args.command == "list":
            list_tasks()
        elif args.command == "run":
            result = execute_task(args.task_id, args.tool_name, args.input_text)
            print(json.dumps(result, ensure_ascii=False))
        elif args.command == "recover":
            count = recover_stale_tasks(args.older_than_minutes)
            print(f"Recovered {count} stale task(s) as failed.")
        return 0
    except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
