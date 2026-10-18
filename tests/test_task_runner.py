import json
import os
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
