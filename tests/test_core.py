import os
import tempfile
import unittest
from pathlib import Path

import core


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ["NEO_LOCAL_HOME"] = self.temp.name
        core.APP_HOME = Path(self.temp.name)
        core.DB_PATH = core.APP_HOME / "test.sqlite3"
        core.init_db()

    def tearDown(self):
        self.temp.cleanup()
        os.environ.pop("NEO_LOCAL_HOME", None)

    def test_task_saved_as_queued(self):
        task_id = core.add_task("test goal")
        with core.connect() as db:
            row = db.execute("SELECT goal,status FROM tasks WHERE id=?", (task_id,)).fetchone()
        self.assertEqual(row["goal"], "test goal")
        self.assertEqual(row["status"], "queued")

    def test_memory_recall(self):
        core.remember("Python tool", "Keep the tool local and test it first", "security")
        results = core.recall("test local")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python tool")

    def test_empty_goal_rejected(self):
        with self.assertRaises(ValueError):
            core.add_task("  ")

    def test_word_count_tool(self):
        result = core.tool_word_count("hello world\nsecond line")
        self.assertEqual(result, {"characters": 23, "words": 4, "lines": 2})

    def test_unknown_tool_not_in_registry(self):
        self.assertNotIn("shell", core.TOOLS)


if __name__ == "__main__":
    unittest.main()
