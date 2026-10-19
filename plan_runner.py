#!/usr/bin/env python3
"""Controlled progress tracking and explicit execution for approved plans."""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone

import core
import plan_manager
import tool_lab


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema():
    plan_manager.ensure_schema()
    with core.connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS plan_steps (
          plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
          step_number INTEGER NOT NULL CHECK(step_number > 0),
          description TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending'
            CHECK(status IN ('pending','running','completed','failed','skipped')),
          tool_name TEXT, input_text TEXT, result_json TEXT, error TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          PRIMARY KEY(plan_id,step_number)
        );
        CREATE TABLE IF NOT EXISTS plan_controls (
          plan_id INTEGER PRIMARY KEY REFERENCES plans(id) ON DELETE CASCADE,
          paused INTEGER NOT NULL DEFAULT 0 CHECK(paused IN (0,1)),
          reason TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
        );
        """)
        stamp = now()
        plans = db.execute("SELECT id,steps_json FROM plans").fetchall()
        for plan in plans:
            steps = json.loads(plan["steps_json"])
            if not isinstance(steps, list) or not all(isinstance(s, str) and s.strip() for s in steps):
                raise ValueError(f"invalid step data in plan #{plan['id']}")
            for number, description in enumerate(steps, 1):
                db.execute(
                    "INSERT OR IGNORE INTO plan_steps(plan_id,step_number,description,created_at,updated_at) VALUES(?,?,?,?,?)",
                    (plan["id"], number, description, stamp, stamp),
                )
            db.execute(
                "INSERT OR IGNORE INTO plan_controls(plan_id,updated_at) VALUES(?,?)",
                (plan["id"], stamp),
            )


def audit(db, event, plan_id, step_no, details=""):
    db.execute(
        "INSERT INTO audit_events(event_type,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)",
        (event, "plan_step" if step_no else "plan",
         f"{plan_id}:{step_no}" if step_no else str(plan_id), details[:2000], now()),
    )


def list_steps(plan_id):
    ensure_schema()
    with core.connect() as db:
        if not db.execute("SELECT 1 FROM plans WHERE id=?", (plan_id,)).fetchone():
            raise ValueError("plan does not exist")
        return db.execute(
            "SELECT * FROM plan_steps WHERE plan_id=? ORDER BY step_number", (plan_id,)
        ).fetchall()


def configure(plan_id, step_no, tool_name, input_text):
    if not isinstance(input_text, str) or len(input_text) > 4000:
        raise ValueError("input must be text of at most 4000 characters")
    ensure_schema()
    # Validate the approved tool before changing persisted configuration.
    tool_lab.active_manifest(tool_name)
    with core.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        plan = db.execute("SELECT status FROM plans WHERE id=?", (plan_id,)).fetchone()
        if not plan:
            raise ValueError("plan does not exist")
        if plan["status"] != "approved":
            raise ValueError("plan must be approved first")
        control = db.execute("SELECT paused FROM plan_controls WHERE plan_id=?", (plan_id,)).fetchone()
        if control["paused"]:
            raise ValueError("plan is paused")
        step = db.execute(
            "SELECT status FROM plan_steps WHERE plan_id=? AND step_number=?", (plan_id, step_no)
        ).fetchone()
        if not step:
            raise ValueError("step does not exist")
        if step["status"] not in ("pending", "failed"):
            raise ValueError("step cannot be configured in current state")
        db.execute(
            "UPDATE plan_steps SET tool_name=?,input_text=?,status='pending',result_json=NULL,error=NULL,updated_at=? WHERE plan_id=? AND step_number=?",
            (tool_name, input_text, now(), plan_id, step_no),
        )
        audit(db, "plan_step_configured", plan_id, step_no, f"tool={tool_name}")


def run_step(plan_id, step_no):
    ensure_schema()
    # Serialize the check-and-claim transaction so two callers cannot both start one step.
    with core.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        plan = db.execute("SELECT status FROM plans WHERE id=?", (plan_id,)).fetchone()
        if not plan:
            raise ValueError("plan does not exist")
        if plan["status"] != "approved":
            raise ValueError("plan must be approved first")
        control = db.execute("SELECT paused FROM plan_controls WHERE plan_id=?", (plan_id,)).fetchone()
        if control["paused"]:
            raise ValueError("plan is paused")
        step = db.execute(
            "SELECT * FROM plan_steps WHERE plan_id=? AND step_number=?", (plan_id, step_no)
        ).fetchone()
        if not step:
            raise ValueError("step does not exist")
        if step["status"] not in ("pending", "failed"):
            raise ValueError(f"step cannot run from {step['status']} state")
        if not step["tool_name"] or step["input_text"] is None:
            raise ValueError("configure an approved tool and input first")
        tool_name, input_text = step["tool_name"], step["input_text"]
        changed = db.execute(
            "UPDATE plan_steps SET status='running',error=NULL,updated_at=? WHERE plan_id=? AND step_number=? AND status IN ('pending','failed')",
            (now(), plan_id, step_no),
        ).rowcount
        if changed != 1:
            raise ValueError("step state changed; reload the plan and try again")
        audit(db, "plan_step_started", plan_id, step_no, f"tool={tool_name}")

    try:
        result = tool_lab.run_approved(tool_name, input_text)
        encoded = json.dumps(result, ensure_ascii=False)
        if len(encoded) > 12000:
            raise ValueError("tool result exceeds 12000 characters")
        with core.connect() as db:
            changed = db.execute(
                "UPDATE plan_steps SET status='completed',result_json=?,error=NULL,updated_at=? WHERE plan_id=? AND step_number=? AND status='running'",
                (encoded, now(), plan_id, step_no),
            ).rowcount
            if changed != 1:
                raise ValueError("step state changed before result could be saved")
            audit(db, "plan_step_completed", plan_id, step_no, f"tool={tool_name}")
        return result
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"[:2000]
        with core.connect() as db:
            changed = db.execute(
                "UPDATE plan_steps SET status='failed',error=?,updated_at=? WHERE plan_id=? AND step_number=? AND status='running'",
                (error, now(), plan_id, step_no),
            ).rowcount
            if changed:
                audit(db, "plan_step_failed", plan_id, step_no, error)
        raise


def recover_interrupted(plan_id, step_no):
    """Mark a stranded running step failed; never re-execute it automatically."""
    ensure_schema()
    with core.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        step = db.execute(
            "SELECT status FROM plan_steps WHERE plan_id=? AND step_number=?", (plan_id, step_no)
        ).fetchone()
        if not step:
            raise ValueError("step does not exist")
        if step["status"] != "running":
            raise ValueError("only a running step can be recovered")
        message = "interrupted run; inspect state before explicitly retrying"
        db.execute(
            "UPDATE plan_steps SET status='failed',error=?,updated_at=? WHERE plan_id=? AND step_number=? AND status='running'",
            (message, now(), plan_id, step_no),
        )
        audit(db, "plan_step_recovered_as_failed", plan_id, step_no, message)


def pause(plan_id, paused, reason="user requested pause"):
    ensure_schema()
    with core.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM plans WHERE id=?", (plan_id,)).fetchone():
            raise ValueError("plan does not exist")
        db.execute(
            "UPDATE plan_controls SET paused=?,reason=?,updated_at=? WHERE plan_id=?",
            (int(paused), reason[:500] if paused else "", now(), plan_id),
        )
        audit(db, "plan_paused" if paused else "plan_resumed", plan_id, None, reason if paused else "")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Track and explicitly run approved plan steps")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("plan_id", type=int)
    p = sub.add_parser("configure"); p.add_argument("plan_id", type=int); p.add_argument("step_number", type=int); p.add_argument("tool_name"); p.add_argument("input_text")
    p = sub.add_parser("run"); p.add_argument("plan_id", type=int); p.add_argument("step_number", type=int)
    p = sub.add_parser("recover"); p.add_argument("plan_id", type=int); p.add_argument("step_number", type=int)
    p = sub.add_parser("pause"); p.add_argument("plan_id", type=int); p.add_argument("--reason", default="user requested pause")
    p = sub.add_parser("resume"); p.add_argument("plan_id", type=int)
    args = parser.parse_args(argv)
    try:
        core.init_db()
        ensure_schema()
        if args.cmd == "list":
            rows = list_steps(args.plan_id)
            with core.connect() as db:
                control = db.execute("SELECT paused FROM plan_controls WHERE plan_id=?", (args.plan_id,)).fetchone()
            print(f"Plan #{args.plan_id} | {'PAUSED' if control['paused'] else 'ACTIVE'}")
            for step in rows:
                print(f"{step['step_number']}. [{step['status']}] {step['description']}")
                if step["tool_name"]:
                    print(f"   Tool: {step['tool_name']} | Input: {step['input_text']!r}")
                if step["result_json"] is not None:
                    print(f"   Result: {step['result_json']}")
                if step["error"]:
                    print(f"   Error: {step['error']}")
        elif args.cmd == "configure":
            configure(args.plan_id, args.step_number, args.tool_name, args.input_text)
            print("Configured; nothing executed.")
        elif args.cmd == "run":
            print(json.dumps(run_step(args.plan_id, args.step_number), ensure_ascii=False))
        elif args.cmd == "recover":
            recover_interrupted(args.plan_id, args.step_number)
            print("Interrupted step marked failed; inspect before explicitly retrying.")
        elif args.cmd == "pause":
            pause(args.plan_id, True, args.reason); print("Paused.")
        else:
            pause(args.plan_id, False); print("Resumed; no step runs automatically.")
        return 0
    except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
