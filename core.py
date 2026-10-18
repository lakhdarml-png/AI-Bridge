#!/usr/bin/env python3
"""NEO-LOCAL Core v0.1 — local-first task and memory kernel."""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

APP_HOME = Path(os.environ.get("NEO_LOCAL_HOME", str(Path.home() / ".neo_local"))).expanduser()
DB_PATH = APP_HOME / "memory.sqlite3"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    APP_HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(APP_HOME, 0o700)
    except OSError:
        pass
    db = sqlite3.connect(DB_PATH, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    return db


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued'
                CHECK(status IN ('queued','running','waiting_input','completed','failed')),
            result TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
        CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
        """)


def add_task(goal: str) -> int:
    goal = goal.strip()
    if not goal:
        raise ValueError("الهدف لا يمكن أن يكون فارغاً.")
    if len(goal) > 4000:
        raise ValueError("الهدف أطول من الحد المسموح (4000 حرف).")
    stamp = now()
    with connect() as db:
        cur = db.execute(
            "INSERT INTO tasks(goal, status, created_at, updated_at) VALUES(?, 'queued', ?, ?)",
            (goal, stamp, stamp),
        )
        return int(cur.lastrowid)


def remember(title: str, content: str, tags: str = "") -> int:
    title, content = title.strip(), content.strip()
    if not title or not content:
        raise ValueError("العنوان والمحتوى مطلوبان.")
    with connect() as db:
        cur = db.execute(
            "INSERT INTO memories(title, content, tags, created_at) VALUES(?,?,?,?)",
            (title[:200], content[:12000], tags[:500], now()),
        )
        return int(cur.lastrowid)


def recall(query: str, limit: int = 10) -> list[sqlite3.Row]:
    terms = [term for term in re.findall(r"[^\W_]+", query.casefold(), flags=re.UNICODE) if len(term) > 1]
    with connect() as db:
        rows = db.execute(
            "SELECT id,title,content,tags,created_at FROM memories ORDER BY id DESC LIMIT 500"
        ).fetchall()
    if not terms:
        return rows[:limit]
    scored = []
    for row in rows:
        haystack = f"{row['title']} {row['content']} {row['tags']}".casefold()
        score = sum(haystack.count(term) for term in terms)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda pair: (pair[0], pair[1]["id"]), reverse=True)
    return [row for _, row in scored[:limit]]


def tool_word_count(text: str) -> dict[str, int]:
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    return {"characters": len(text), "words": len(words), "lines": len(text.splitlines()) if text else 0}


TOOLS = {
    "word_count": {
        "description": "عدّ الأحرف والكلمات والأسطر في نص.",
        "handler": tool_word_count,
    }
}


def status() -> None:
    with connect() as db:
        tasks = db.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status").fetchall()
        memories = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        total_tasks = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    print("NEO-LOCAL Core v0.1")
    print(f"قاعدة البيانات: {DB_PATH}")
    print(f"المهام: {total_tasks} | الذكريات: {memories}")
    print("حالات المهام: " + (", ".join(f"{r['status']}={r['n']}" for r in tasks) or "لا توجد مهام"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEO-LOCAL: نواة محلية مستقلة عن مزود API")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="إنشاء قاعدة البيانات")
    sub.add_parser("status", help="عرض حالة النواة")
    task_p = sub.add_parser("task", help="تسجيل مهمة محلية")
    task_p.add_argument("goal")
    mem_p = sub.add_parser("remember", help="حفظ خبرة محلية")
    mem_p.add_argument("title")
    mem_p.add_argument("content")
    mem_p.add_argument("--tags", default="")
    recall_p = sub.add_parser("recall", help="البحث في الذاكرة")
    recall_p.add_argument("query", nargs="?", default="")
    tools_p = sub.add_parser("tools", help="عرض الأدوات المدمجة")
    run_p = sub.add_parser("run-tool", help="تشغيل أداة مدمجة محددة")
    run_p.add_argument("name", choices=sorted(TOOLS))
    run_p.add_argument("text")
    args = parser.parse_args(argv)

    try:
        init_db()
        if args.command == "init":
            print(f"تم إعداد النواة. قاعدة البيانات: {DB_PATH}")
        elif args.command == "status":
            status()
        elif args.command == "task":
            task_id = add_task(args.goal)
            print(f"تم تسجيل المهمة #{task_id} بالحالة queued.")
        elif args.command == "remember":
            memory_id = remember(args.title, args.content, args.tags)
            print(f"تم حفظ الخبرة #{memory_id} محلياً.")
        elif args.command == "recall":
            results = recall(args.query)
            if not results:
                print("لا توجد ذكريات مطابقة.")
            for row in results:
                print(f"#{row['id']} — {row['title']}\n{row['content']}\n")
        elif args.command == "tools":
            for name, item in TOOLS.items():
                print(f"{name}: {item['description']}")
        elif args.command == "run-tool":
            print(TOOLS[args.name]["handler"](args.text))
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"خطأ: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
