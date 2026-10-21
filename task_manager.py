#!/usr/bin/env python3
"""Search, inspect, and safely manage NEO-LOCAL tasks."""
from __future__ import annotations
import argparse
import sqlite3
import sys
from datetime import datetime, timezone
import core

TRANSITIONS = {
    "queued": {"running", "waiting_input", "failed"},
    "running": {"completed", "failed"},
    "waiting_input": {"queued", "failed"},
    "completed": set(),
    "failed": set(),
}
def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def search_tasks(query: str = "", limit: int = 50):
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    with core.connect() as db:
        if query.strip():
            pattern = "%" + query.strip() + "%"
            return db.execute(
                "SELECT id,goal,status,result,created_at,updated_at FROM tasks "
                "WHERE goal LIKE ? ORDER BY id DESC LIMIT ?", (pattern, limit)
            ).fetchall()
        return db.execute(
            "SELECT id,goal,status,result,created_at,updated_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

def show_task(task_id: int):
    if task_id < 1:
        raise ValueError("task ID must be positive")
    with core.connect() as db:
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        raise ValueError("task does not exist")
    return row

def transition_status(
    task_id: int,
    new_status: str,
    *,
    expected_status: str | None = None,
    actor: str = "system",
    details: str = "",
    result: str | None = None,
    execution_transition: bool = False,
):
    """Apply one validated state change and its audit event atomically."""
    if task_id < 1:
        raise ValueError("task ID must be positive")
    if new_status not in TRANSITIONS:
        raise ValueError(f"unknown task status: {new_status}")
    if new_status in {"running", "completed"} and not execution_transition:
        raise ValueError("execution states may only be changed by the task runner")
    stamp = now()
    with core.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError("task does not exist")
        old_status = row["status"]
        if expected_status is not None and old_status != expected_status:
            raise ValueError(f"task state changed: expected {expected_status}, found {old_status}")
        if new_status not in TRANSITIONS.get(old_status, set()):
            raise ValueError(f"transition not allowed: {old_status} -> {new_status}")
        cur = db.execute(
            "UPDATE tasks SET status=?, result=?, updated_at=? WHERE id=? AND status=?",
            (new_status, result, stamp, task_id, old_status),
        )
        if cur.rowcount != 1:
            raise ValueError("task state changed; refusing transition")
        audit_details = f"{old_status} -> {new_status}; actor={actor}"
        if details:
            audit_details += f"; {details}"
        db.execute(
            "INSERT INTO audit_events(event_type, entity_type, entity_id, details, created_at) VALUES(?,?,?,?,?)",
            ("task_status_changed", "task", str(task_id), audit_details[:2000], stamp),
        )
    return old_status


def set_status(task_id: int, new_status: str):
    if new_status not in {"queued", "waiting_input", "failed"}:
        raise ValueError("manual status may only be queued, waiting_input, or failed")
    return transition_status(task_id, new_status, actor="manual")

def main(argv=None):
    parser=argparse.ArgumentParser(description="Search and manage tasks without executing them")
    sub=parser.add_subparsers(dest="command", required=True)
    listing=sub.add_parser("list"); listing.add_argument("--search", default=""); listing.add_argument("--limit", type=int, default=50)
    show=sub.add_parser("show"); show.add_argument("task_id", type=int)
    change=sub.add_parser("status"); change.add_argument("task_id", type=int); change.add_argument("new_status", choices=["queued","waiting_input","failed"])
    args=parser.parse_args(argv)
    try:
        core.init_db()
        if args.command=="list":
            rows=search_tasks(args.search,args.limit)
            for r in rows: print(f"#{r['id']} [{r['status']}] {r['goal']}")
            if not rows: print("No matching tasks.")
        elif args.command=="show":
            r=show_task(args.task_id)
            for key in r.keys(): print(f"{key}: {r[key]}")
        else:
            old=set_status(args.task_id,args.new_status)
            print(f"Task #{args.task_id}: {old} -> {args.new_status}")
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Error: {exc}",file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
