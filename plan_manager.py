#!/usr/bin/env python3
"""Deterministic local planning; plans never execute tools."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone

import core

MAX_GOAL_LENGTH = 4000


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema() -> None:
    with core.connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                goal TEXT NOT NULL,
                category TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK(status IN ('draft','approved')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_plans_task ON plans(task_id, id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_plans_created ON plans(created_at)")


def classify_goal(goal: str) -> tuple[str, list[str]]:
    text = goal.casefold()
    software_terms = ("app", "application", "code", "software", "bug", "برمج", "تطبيق", "كود", "خطأ", "أداة", "اداة", "مشروع")
    research_terms = ("research", "learn", "study", "compare", "بحث", "تعلم", "تعلّم", "دراسة", "قارن", "افهم")
    writing_terms = ("write", "draft", "document", "report", "رسالة", "اكتب", "كتابة", "تقرير", "وثيقة")
    if any(term in text for term in software_terms):
        return "software_project", [
            "حدد النتيجة المطلوبة ومعايير نجاحها.",
            "اجمع المتطلبات والقيود والملفات ذات الصلة.",
            "قسّم العمل إلى تغييرات صغيرة يمكن اختبار كل منها.",
            "نفّذ خطوة واحدة فقط بعد مراجعة الخطة والموافقة عليها.",
            "اختبر التغيير، وافحص الأخطاء، واحتفظ بإمكانية التراجع.",
            "راجع النتيجة مقابل معايير النجاح وسجّل ما تعلمته.",
        ]
    if any(term in text for term in research_terms):
        return "research", [
            "صغ سؤالًا واضحًا وحدّد ما الذي سيُعد إجابة كافية.",
            "حدد المعلومات المعروفة وما يزال مجهولًا.",
            "اجمع الأدلة من مصادر مناسبة مع تسجيل مصدر كل ادعاء.",
            "قارن النتائج وابحث عن التعارضات والثغرات.",
            "اكتب خلاصة تميّز الحقائق عن الافتراضات.",
            "راجع الخلاصة وحدد الأسئلة التي بقيت دون جواب.",
        ]
    if any(term in text for term in writing_terms):
        return "writing", [
            "حدد الجمهور والغرض والنبرة المطلوبة.",
            "اجمع النقاط الأساسية والقيود التي يجب احترامها.",
            "أنشئ مخططًا موجزًا قبل كتابة المسودة.",
            "اكتب المسودة الأولى دون تنفيذ أي إجراء خارجي.",
            "راجع الدقة والوضوح والاكتمال ثم حسّن المسودة.",
            "اعرض النسخة النهائية للمستخدم للمراجعة.",
        ]
    return "general", [
        "حوّل الهدف إلى نتيجة نهائية قابلة للتحقق.",
        "حدد المعلومات الناقصة والقيود والمخاطر المحتملة.",
        "قسّم العمل إلى خطوات صغيرة مرتبة.",
        "حدد لكل خطوة طريقة تحقق واضحة.",
        "اطلب توضيحًا أو موافقة المستخدم قبل أي إجراء مؤثر.",
        "راجع النتيجة وسجّل الدروس المستفادة.",
    ]


def create_plan(goal: str, task_id: int | None = None) -> int:
    goal = goal.strip()
    if not goal:
        raise ValueError("goal cannot be empty")
    if len(goal) > MAX_GOAL_LENGTH:
        raise ValueError(f"goal exceeds {MAX_GOAL_LENGTH} characters")
    ensure_schema()
    category, steps = classify_goal(goal)
    stamp = now()
    with core.connect() as db:
        if task_id is not None:
            if task_id < 1 or db.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone() is None:
                raise ValueError("task does not exist")
        cur = db.execute(
            "INSERT INTO plans(task_id,goal,category,steps_json,status,created_at,updated_at) VALUES(?,?,?,?, 'draft', ?, ?)",
            (task_id, goal, category, json.dumps(steps, ensure_ascii=False), stamp, stamp),
        )
        plan_id = int(cur.lastrowid)
        db.execute(
            "INSERT INTO audit_events(event_type,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)",
            ("plan_created", "plan", str(plan_id), f"task_id={task_id}; category={category}", stamp),
        )
        return plan_id


def get_plan(plan_id: int):
    if plan_id < 1:
        raise ValueError("plan ID must be positive")
    ensure_schema()
    with core.connect() as db:
        row = db.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
    if row is None:
        raise ValueError("plan does not exist")
    return row


def list_plans(limit: int = 50):
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    ensure_schema()
    with core.connect() as db:
        return db.execute(
            "SELECT id,task_id,goal,category,status,created_at FROM plans ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def approve_plan(plan_id: int) -> None:
    stamp = now()
    ensure_schema()
    with core.connect() as db:
        row = db.execute("SELECT status FROM plans WHERE id=?", (plan_id,)).fetchone()
        if row is None:
            raise ValueError("plan does not exist")
        if row["status"] != "draft":
            raise ValueError("only draft plans can be approved")
        db.execute("UPDATE plans SET status='approved', updated_at=? WHERE id=? AND status='draft'", (stamp, plan_id))
        db.execute(
            "INSERT INTO audit_events(event_type,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)",
            ("plan_approved", "plan", str(plan_id), "approved by explicit user command; no tools executed", stamp),
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create and review local plans; never executes tools")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("goal")
    create.add_argument("--task-id", type=int)
    show = sub.add_parser("show")
    show.add_argument("plan_id", type=int)
    listing = sub.add_parser("list")
    listing.add_argument("--limit", type=int, default=50)
    approve = sub.add_parser("approve")
    approve.add_argument("plan_id", type=int)
    args = parser.parse_args(argv)
    try:
        ensure_schema()
        if args.command == "create":
            plan_id = create_plan(args.goal, args.task_id)
            print(f"Plan #{plan_id} created as draft. No task or tool was executed.")
        elif args.command == "show":
            row = get_plan(args.plan_id)
            print(f"Plan #{row['id']} [{row['status']}]")
            print(f"Task: {row['task_id']}")
            print(f"Category: {row['category']}")
            print(f"Goal: {row['goal']}")
            for i, step in enumerate(json.loads(row["steps_json"]), 1):
                print(f"{i}. {step}")
        elif args.command == "list":
            rows = list_plans(args.limit)
            for row in rows:
                print(f"#{row['id']} [{row['status']}] ({row['category']}) {row['goal']}")
            if not rows:
                print("No plans found.")
        else:
            approve_plan(args.plan_id)
            print(f"Plan #{args.plan_id} approved. Approval does not execute tasks or tools.")
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
