"""Structured, in-process API for the Android application."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _core():
    # Android sets this before the first import; keep a safe default for host tests.
    try:
        from . import core  # Host-side package import.
    except ImportError:
        import core  # Chaquopy loads this directory as the Python source root.
    core.init_db()
    return core


def _plain(value):
    if hasattr(value, "keys") and callable(value.keys):
        return {key: _plain(value[key]) for key in value.keys()}
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def status_json():
    try:
        core = _core()
        with core.connect() as db:
            task_count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            memory_count = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            statuses = {row["status"]: row["n"] for row in db.execute(
                "SELECT status, COUNT(*) AS n FROM tasks GROUP BY status"
            ).fetchall()}
        return json.dumps({
            "ok": True, "runtime": "embedded-python", "database": str(core.DB_PATH),
            "tasks": task_count, "memories": memory_count, "task_statuses": statuses,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)


def add_task_json(goal):
    try:
        core = _core()
        task_id = core.add_task(str(goal))
        return json.dumps({"ok": True, "task_id": task_id, "status": "queued"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)


def remember_json(title, content):
    try:
        core = _core()
        memory_id = core.remember(str(title), str(content))
        return json.dumps({"ok": True, "memory_id": memory_id}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)


def list_data_json():
    try:
        core = _core()
        with core.connect() as db:
            tasks = db.execute(
                "SELECT id,goal,status,created_at FROM tasks ORDER BY id DESC LIMIT 30"
            ).fetchall()
        memories = core.recall("", limit=30)
        return json.dumps({
            "ok": True, "tasks": _plain(tasks), "memories": _plain(memories)
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
