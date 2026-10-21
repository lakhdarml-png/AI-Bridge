import json
import tempfile
import unittest
from pathlib import Path

import core
import plan_manager


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        core.APP_HOME = Path(self.temp.name)
        core.DB_PATH = core.APP_HOME / "test.sqlite3"
        core.init_db()
        plan_manager.ensure_schema()

    def tearDown(self):
        self.temp.cleanup()

    def test_create_general_plan_as_draft_without_task_execution(self):
        task_id = core.add_task("Plan my day")
        plan_id = plan_manager.create_plan("Organize my personal work", task_id)
        plan = plan_manager.get_plan(plan_id)
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["task_id"], task_id)
        self.assertGreaterEqual(len(json.loads(plan["steps_json"])), 4)
        with core.connect() as db:
            status = db.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()["status"]
        self.assertEqual(status, "queued")

    def test_software_goal_gets_software_steps(self):
        plan_id = plan_manager.create_plan("Build an Android application")
        plan = plan_manager.get_plan(plan_id)
        self.assertEqual(plan["category"], "software_project")
        self.assertIn("اختبر", " ".join(json.loads(plan["steps_json"])))

    def test_safe_local_tool_goal_gets_specific_security_plan(self):
        plan_id = plan_manager.create_plan("بحث عن طرق آمنة لتطوير أدوات محلية")
        plan = plan_manager.get_plan(plan_id)
        steps = " ".join(json.loads(plan["steps_json"]))
        self.assertEqual(plan["category"], "safe_tool_development")
        self.assertIn("صلاحيات أقل", steps)
        self.assertIn("موافقة صريحة", steps)
        self.assertIn("التراجع", steps)
        self.assertEqual(plan["status"], "draft")

    def test_unrelated_research_goal_stays_research(self):
        plan_id = plan_manager.create_plan("بحث عن تاريخ العمارة")
        self.assertEqual(plan_manager.get_plan(plan_id)["category"], "research")

    def test_research_goal_is_classified(self):
        plan_id = plan_manager.create_plan("بحث عن طرق آمنة")
        self.assertEqual(plan_manager.get_plan(plan_id)["category"], "research")

    def test_approval_is_explicit_and_audited(self):
        plan_id = plan_manager.create_plan("Prepare a report")
        plan_manager.approve_plan(plan_id)
        self.assertEqual(plan_manager.get_plan(plan_id)["status"], "approved")
        with core.connect() as db:
            event = db.execute(
                "SELECT event_type,details FROM audit_events WHERE entity_type='plan' AND entity_id=? ORDER BY id DESC LIMIT 1",
                (str(plan_id),),
            ).fetchone()
        self.assertEqual(event["event_type"], "plan_approved")
        self.assertIn("no tools executed", event["details"])
        with self.assertRaises(ValueError):
            plan_manager.approve_plan(plan_id)

    def test_missing_task_and_plan_are_rejected(self):
        with self.assertRaises(ValueError):
            plan_manager.create_plan("Test", 999)
        with self.assertRaises(ValueError):
            plan_manager.get_plan(999)

    def test_invalid_goal_and_limit_rejected(self):
        with self.assertRaises(ValueError):
            plan_manager.create_plan("   ")
        with self.assertRaises(ValueError):
            plan_manager.list_plans(0)


if __name__ == "__main__":
    unittest.main()
