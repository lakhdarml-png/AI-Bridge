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
import task_manager
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
    with core.connect() as db:
        rows = db.execute(
            "SELECT id FROM tasks WHERE status='running' AND updated_at < ? ORDER BY id",
            (cutoff,),
        ).fetchall()
    count = 0
    for row in rows:
        try:
            task_manager.transition_status(
                int(row["id"]), "failed", expected_status="running",
                actor="recovery",
                details="stale task marked failed; execution is not automatically resumed",
                result="Recovered as failed: task was left running after an interruption.",
                execution_transition=True,
            )
            count += 1
        except ValueError:
            # A concurrent worker may have changed this task after the scan.
            continue
    return count


def execute_task(
    task_id: int, tool_name: str, input_text: str, *,
    runtime_approved: bool = False,
) -> Any:
    if task_id < 1:
        raise ValueError("task ID must be positive")
    with core.connect() as db:
        task = db.execute("SELECT id, goal, status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task is None:
            raise ValueError("task does not exist")
        if task["status"] != "queued":
            raise ValueError(f"task must be queued; current status is {task['status']}")
        # Require explicit approval before claiming a sensitive queued task.
    try:
        needs_approval = tool_lab.runtime_approval_required(tool_name)
    except ValueError:
        needs_approval = False

    if needs_approval and not runtime_approved:
        tool_lab.audit(
            "approval_denied", tool_name,
            f"task:{task_id}:runtime_approval_required",
        )
        raise ValueError("this task requires explicit runtime approval")

    # Leave the task result intact until the runner owns the transition.
    task_manager.transition_status(
        task_id, "running", expected_status="queued", actor="task_runner",
        details=f"tool={tool_name}", result=None, execution_transition=True,
    )
    try:
        result = tool_lab.run_approved(
            tool_name, input_text, runtime_approved=runtime_approved
        )
        result_text = json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        try:
            task_manager.transition_status(
                task_id, "failed", expected_status="running", actor="task_runner",
                details=f"tool={tool_name}; exception={type(exc).__name__}",
                result=f"{type(exc).__name__}: {exc}"[:2000],
                execution_transition=True,
            )
        except ValueError:
            # Preserve the original exception if another actor changed task state.
            pass
        try:
            tool_lab.audit("task_failed", tool_name, f"task:{task_id}")
        except OSError:
            pass
        raise
    task_manager.transition_status(
        task_id, "completed", expected_status="running", actor="task_runner",
        details=f"tool={tool_name}; tool execution succeeded",
        result=result_text[:12000], execution_transition=True,
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
    run.add_argument(
        "--approve-sensitive", action="store_true",
        help="explicitly approve a sensitive tool for this task",
    )
    recover = sub.add_parser("recover", help="mark old interrupted running tasks as failed; never resumes them")
    recover.add_argument("--older-than-minutes", type=int, default=60)
    args = parser.parse_args(argv)
    try:
        core.init_db()
        if args.command == "list":
            list_tasks()
        elif args.command == "run":
            result = execute_task(
                args.task_id, args.tool_name, args.input_text,
                runtime_approved=args.approve_sensitive,
            )
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
