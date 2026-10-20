import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import core
import tool_lab
import task_runner


class TaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        core.APP_HOME = root / "db"
        core.DB_PATH = core.APP_HOME / "test.sqlite3"
        core.init_db()
        self.state = root / "tools"
        self.patches = [
            patch.object(tool_lab, "STATE", self.state),
            patch.object(tool_lab, "CANDIDATES", self.state / "candidates"),
            patch.object(tool_lab, "APPROVED", self.state / "approved"),
            patch.object(tool_lab, "AUDIT", self.state / "audit.jsonl"),
        ]
        for p in self.patches:
            p.start()
        tool_lab.paths()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def make_approved_tool(self):
        tool_lab.create("count_demo", "word_count", "fixture", 20)
        tool_lab.approve("count_demo")

    def task_status(self, task_id):
        with core.connect() as db:
            return db.execute("SELECT status,result FROM tasks WHERE id=?", (task_id,)).fetchone()

    def test_explicit_run_completes_task_and_saves_result(self):
        self.make_approved_tool()
        task_id = core.add_task("Count words in the provided text")
        result = task_runner.execute_task(task_id, "count_demo", "hello world")
        row = self.task_status(task_id)
        self.assertEqual(result, {"characters": 11, "words": 2, "lines": 1})
        self.assertEqual(row["status"], "completed")
        self.assertEqual(json.loads(row["result"]), result)


    def test_execution_transitions_are_audited_atomically(self):
        self.make_approved_tool()
        task_id = core.add_task("Audit transitions")
        task_runner.execute_task(task_id, "count_demo", "audit me")
        with core.connect() as db:
            events = db.execute(
                "SELECT details FROM audit_events WHERE entity_id=? AND event_type='task_status_changed' ORDER BY id",
                (str(task_id),),
            ).fetchall()
        self.assertEqual(len(events), 2)
        self.assertIn("queued -> running; actor=task_runner", events[0]["details"])
        self.assertIn("running -> completed; actor=task_runner", events[1]["details"])

    def test_unapproved_tool_fails_task_safely(self):
        task_id = core.add_task("Try tool")
        with self.assertRaises(ValueError):
            task_runner.execute_task(task_id, "missing_tool", "text")
        row = self.task_status(task_id)
        self.assertEqual(row["status"], "failed")
        self.assertIn("no active approved version", row["result"])

    def test_completed_task_cannot_be_run_twice(self):
        self.make_approved_tool()
        task_id = core.add_task("Run once")
        task_runner.execute_task(task_id, "count_demo", "x")
        with self.assertRaises(ValueError):
            task_runner.execute_task(task_id, "count_demo", "x")

    def test_missing_task_rejected(self):
        with self.assertRaises(ValueError):
            task_runner.execute_task(999, "count_demo", "x")

    def test_recover_only_old_running_tasks_and_never_resumes_them(self):
        task_id = core.add_task("Possibly interrupted")
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(timespec="seconds")
        with core.connect() as db:
            db.execute("UPDATE tasks SET status='running', updated_at=? WHERE id=?", (old, task_id))
        count = task_runner.recover_stale_tasks(older_than_minutes=60)
        row = self.task_status(task_id)
        self.assertEqual(count, 1)
        self.assertEqual(row["status"], "failed")
        self.assertIn("left running", row["result"])

    def test_recovery_rejects_unreasonable_threshold(self):
        with self.assertRaises(ValueError):
            task_runner.recover_stale_tasks(0)


if __name__ == "__main__":
    unittest.main()
