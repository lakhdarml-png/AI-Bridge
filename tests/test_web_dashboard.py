import tempfile
import unittest
from pathlib import Path

import core
import web_dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_home = core.APP_HOME
        self.old_db_path = core.DB_PATH
        core.APP_HOME = Path(self.temp.name)
        core.DB_PATH = core.APP_HOME / "memory.sqlite3"
        core.init_db()

    def tearDown(self):
        core.APP_HOME = self.old_home
        core.DB_PATH = self.old_db_path
        self.temp.cleanup()

    def test_goal_creates_draft_without_execution(self):
        result = web_dashboard.dispatch(
            "/api/plan/create", {"goal": "Dashboard test plan"}
        )
        self.assertIn("مسودة", result["message"])
        with core.connect() as db:
            plan = db.execute("SELECT id,status FROM plans").fetchone()
            self.assertEqual(plan["status"], "draft")
            steps = db.execute(
                "SELECT status FROM plan_steps WHERE plan_id=?", (plan["id"],)
            ).fetchall()
            self.assertEqual(len(steps), 6)
            self.assertTrue(all(row["status"] == "pending" for row in steps))

    def test_approval_is_separate_from_execution(self):
        web_dashboard.dispatch("/api/plan/create", {"goal": "Dashboard approval"})
        web_dashboard.dispatch("/api/plan/approve", {"plan_id": 1})
        with core.connect() as db:
            self.assertEqual(
                db.execute("SELECT status FROM plans WHERE id=1").fetchone()["status"],
                "approved",
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM plan_steps WHERE status='completed'").fetchone()[0],
                0,
            )

    def test_pause_and_resume_only_change_control_state(self):
        web_dashboard.dispatch("/api/plan/create", {"goal": "Dashboard pause"})
        web_dashboard.dispatch("/api/plan/approve", {"plan_id": 1})
        web_dashboard.dispatch(
            "/api/plan/pause", {"plan_id": 1, "reason": "dashboard test"}
        )
        with core.connect() as db:
            self.assertEqual(
                db.execute("SELECT paused FROM plan_controls WHERE plan_id=1").fetchone()[0],
                1,
            )
        web_dashboard.dispatch("/api/plan/resume", {"plan_id": 1})
        with core.connect() as db:
            self.assertEqual(
                db.execute("SELECT paused FROM plan_controls WHERE plan_id=1").fetchone()[0],
                0,
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM plan_steps WHERE status='completed'").fetchone()[0],
                0,
            )

    def test_invalid_ids_and_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            web_dashboard.positive_int(True, "plan_id")
        with self.assertRaises(ValueError):
            web_dashboard.string_value({"goal": " "}, "goal", 20, False)
        with self.assertRaises(ValueError):
            web_dashboard.dispatch("/api/step/run", {"plan_id": 1, "step_number": 0})

    def test_page_explains_local_and_explicit_execution(self):
        self.assertIn('lang="ar" dir="rtl"', web_dashboard.PAGE)
        self.assertIn("تنفيذ هذه الخطوة", web_dashboard.PAGE)
        self.assertIn("لا تتصل بنموذج ذكاء اصطناعي", web_dashboard.PAGE)


if __name__ == "__main__":
    unittest.main()
