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
        for plan in db.execute("SELECT id,steps_json FROM plans").fetchall():
            steps = json.loads(plan["steps_json"])
            if not isinstance(steps,list) or not all(isinstance(s,str) and s.strip() for s in steps):
                raise ValueError(f"invalid step data in plan #{plan['id']}")
            for n, description in enumerate(steps,1):
                db.execute("INSERT OR IGNORE INTO plan_steps(plan_id,step_number,description,created_at,updated_at) VALUES(?,?,?,?,?)",
                           (plan["id"],n,description,stamp,stamp))
            db.execute("INSERT OR IGNORE INTO plan_controls(plan_id,updated_at) VALUES(?,?)",(plan["id"],stamp))

def audit(db, event, plan_id, step_no, details=""):
    stamp=now()
    db.execute("INSERT INTO audit_events(event_type,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)",
       (event,"plan_step" if step_no else "plan",f"{plan_id}:{step_no}" if step_no else str(plan_id),details[:2000],stamp))

def list_steps(plan_id):
    ensure_schema()
    with core.connect() as db:
        if not db.execute("SELECT 1 FROM plans WHERE id=?",(plan_id,)).fetchone(): raise ValueError("plan does not exist")
        return db.execute("SELECT * FROM plan_steps WHERE plan_id=? ORDER BY step_number",(plan_id,)).fetchall()

def configure(plan_id, step_no, tool_name, input_text):
    if len(input_text)>4000: raise ValueError("input must be at most 4000 characters")
    ensure_schema()
    with core.connect() as db:
        p=db.execute("SELECT status FROM plans WHERE id=?",(plan_id,)).fetchone()
        if not p: raise ValueError("plan does not exist")
        if p["status"]!="approved": raise ValueError("plan must be approved first")
        control=db.execute("SELECT paused FROM plan_controls WHERE plan_id=?",(plan_id,)).fetchone()
        if control["paused"]: raise ValueError("plan is paused")
        s=db.execute("SELECT status FROM plan_steps WHERE plan_id=? AND step_number=?",(plan_id,step_no)).fetchone()
        if not s: raise ValueError("step does not exist")
        if s["status"] not in ("pending","failed"): raise ValueError("step cannot be configured in current state")
        tool_lab.active_manifest(tool_name)
        stamp=now()
        db.execute("UPDATE plan_steps SET tool_name=?,input_text=?,status='pending',result_json=NULL,error=NULL,updated_at=? WHERE plan_id=? AND step_number=?",
                   (tool_name,input_text,stamp,plan_id,step_no))
        audit(db,"plan_step_configured",plan_id,step_no,f"tool={tool_name}")

def run_step(plan_id, step_no):
    ensure_schema()
    with core.connect() as db:
        p=db.execute("SELECT status FROM plans WHERE id=?",(plan_id,)).fetchone()
        if not p: raise ValueError("plan does not exist")
        if p["status"]!="approved": raise ValueError("plan must be approved first")
        c=db.execute("SELECT paused FROM plan_controls WHERE plan_id=?",(plan_id,)).fetchone()
        if c["paused"]: raise ValueError("plan is paused")
        s=db.execute("SELECT * FROM plan_steps WHERE plan_id=? AND step_number=?",(plan_id,step_no)).fetchone()
        if not s: raise ValueError("step does not exist")
        if s["status"] not in ("pending","failed"): raise ValueError(f"step cannot run from {s['status']} state")
        if not s["tool_name"] or s["input_text"] is None: raise ValueError("configure an approved tool and input first")
        tool_name,input_text=s["tool_name"],s["input_text"]
        stamp=now()
        db.execute("UPDATE plan_steps SET status='running',error=NULL,updated_at=? WHERE plan_id=? AND step_number=?",(stamp,plan_id,step_no))
        audit(db,"plan_step_started",plan_id,step_no,f"tool={tool_name}")
    try:
        result=tool_lab.run_approved(tool_name,input_text)
        encoded=json.dumps(result,ensure_ascii=False)[:12000]
        with core.connect() as db:
            db.execute("UPDATE plan_steps SET status='completed',result_json=?,error=NULL,updated_at=? WHERE plan_id=? AND step_number=? AND status='running'",
                       (encoded,now(),plan_id,step_no))
            audit(db,"plan_step_completed",plan_id,step_no,f"tool={tool_name}")
        return result
    except Exception as exc:
        error=f"{type(exc).__name__}: {exc}"[:2000]
        with core.connect() as db:
            db.execute("UPDATE plan_steps SET status='failed',error=?,updated_at=? WHERE plan_id=? AND step_number=? AND status='running'",
                       (error,now(),plan_id,step_no))
            audit(db,"plan_step_failed",plan_id,step_no,error)
        raise

def pause(plan_id, paused, reason="user requested pause"):
    ensure_schema()
    with core.connect() as db:
        if not db.execute("SELECT 1 FROM plans WHERE id=?",(plan_id,)).fetchone(): raise ValueError("plan does not exist")
        db.execute("UPDATE plan_controls SET paused=?,reason=?,updated_at=? WHERE plan_id=?",(int(paused),reason[:500] if paused else "",now(),plan_id))
        audit(db,"plan_paused" if paused else "plan_resumed",plan_id,None,reason if paused else "")

def main(argv=None):
    parser=argparse.ArgumentParser(description="Track and explicitly run approved plan steps")
    sub=parser.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("list"); p.add_argument("plan_id",type=int)
    p=sub.add_parser("configure"); p.add_argument("plan_id",type=int); p.add_argument("step_number",type=int); p.add_argument("tool_name"); p.add_argument("input_text")
    p=sub.add_parser("run"); p.add_argument("plan_id",type=int); p.add_argument("step_number",type=int)
    p=sub.add_parser("pause"); p.add_argument("plan_id",type=int); p.add_argument("--reason",default="user requested pause")
    p=sub.add_parser("resume"); p.add_argument("plan_id",type=int)
    a=parser.parse_args(argv)
    try:
        core.init_db(); ensure_schema()
        if a.cmd=="list":
            rows=list_steps(a.plan_id)
            with core.connect() as db: c=db.execute("SELECT paused FROM plan_controls WHERE plan_id=?",(a.plan_id,)).fetchone()
            print(f"Plan #{a.plan_id} | {'PAUSED' if c['paused'] else 'ACTIVE'}")
            for s in rows:
                print(f"{s['step_number']}. [{s['status']}] {s['description']}")
                if s["tool_name"]: print(f"   Tool: {s['tool_name']} | Input: {s['input_text']!r}")
                if s["result_json"] is not None: print(f"   Result: {s['result_json']}")
                if s["error"]: print(f"   Error: {s['error']}")
        elif a.cmd=="configure": configure(a.plan_id,a.step_number,a.tool_name,a.input_text); print("Configured; nothing executed.")
        elif a.cmd=="run": print(json.dumps(run_step(a.plan_id,a.step_number),ensure_ascii=False))
        elif a.cmd=="pause": pause(a.plan_id,True,a.reason); print("Paused.")
        else: pause(a.plan_id,False); print("Resumed; no step runs automatically.")
        return 0
    except (OSError,sqlite3.Error,ValueError,json.JSONDecodeError) as exc:
        print(f"Error: {exc}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
