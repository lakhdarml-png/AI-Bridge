import json
import tempfile
import unittest
from pathlib import Path

from neo_local import core
from neo_local import android_facade


class AndroidFacadeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_home, self.old_db = core.APP_HOME, core.DB_PATH
        core.APP_HOME = Path(self.temp.name)
        core.DB_PATH = core.APP_HOME / "facade-test.sqlite3"
        core.init_db()

    def tearDown(self):
        core.APP_HOME, core.DB_PATH = self.old_home, self.old_db
        self.temp.cleanup()

    def test_status_is_structured_and_uses_local_database(self):
        result = json.loads(android_facade.status_json())
        self.assertTrue(result["ok"])
        self.assertEqual(result["runtime"], "embedded-python")
        self.assertEqual(result["tasks"], 0)
        self.assertEqual(result["memories"], 0)

    def test_task_and_memory_round_trip(self):
        task = json.loads(android_facade.add_task_json("Inspect local project"))
        memory = json.loads(android_facade.remember_json("Safety rule", "Ask before writes"))
        listing = json.loads(android_facade.list_data_json())
        self.assertTrue(task["ok"])
        self.assertTrue(memory["ok"])
        self.assertEqual(listing["tasks"][0]["goal"], "Inspect local project")
        self.assertEqual(listing["memories"][0]["title"], "Safety rule")

    def test_invalid_task_returns_error_not_exception(self):
        result = json.loads(android_facade.add_task_json("   "))
        self.assertFalse(result["ok"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
