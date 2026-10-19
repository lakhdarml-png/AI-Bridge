import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core
import plan_manager
import plan_runner
import tool_lab


class PlanRunnerTests(unittest.TestCase):
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
        for item in self.patches:
            item.start()
        tool_lab.paths()
        self.plan_id = plan_manager.create_plan("Count words in a sample")
        plan_manager.approve_plan(self.plan_id)
        tool_lab.create("count_demo", "word_count", "fixture", 20)
        tool_lab.approve("count_demo")
        plan_runner.ensure_schema()

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.temp.cleanup()

    def configure(self, step=1, text="hello world"):
        plan_runner.configure(self.plan_id, step, "count_demo", text)

    def step(self, number=1):
        return next(row for row in plan_runner.list_steps(self.plan_id)
                    if row["step_number"] == number)

    def test_migration_is_idempotent(self):
        first = len(plan_runner.list_steps(self.plan_id))
        plan_runner.ensure_schema()
        second = len(plan_runner.list_steps(self.plan_id))
        self.assertEqual(first, second)
        self.assertGreater(first, 0)

    def test_requires_approved_plan(self):
        draft = plan_manager.create_plan("Another plan")
        with self.assertRaisesRegex(ValueError, "approved"):
            plan_runner.configure(draft, 1, "count_demo", "x")

    def test_requires_approved_tool_and_input_limit(self):
        with self.assertRaises(ValueError):
            plan_runner.configure(self.plan_id, 1, "missing_tool", "x")
        with self.assertRaises(ValueError):
            plan_runner.configure(self.plan_id, 1, "count_demo", "x" * 4001)

    def test_run_saves_result_and_completed_state(self):
        self.configure()
        result = plan_runner.run_step(self.plan_id, 1)
        row = self.step()
        self.assertEqual(result, {"characters": 11, "words": 2, "lines": 1})
        self.assertEqual(row["status"], "completed")
        self.assertEqual(json.loads(row["result_json"]), result)

    def test_completed_step_cannot_run_twice(self):
        self.configure()
        plan_runner.run_step(self.plan_id, 1)
        with self.assertRaisesRegex(ValueError, "completed"):
            plan_runner.run_step(self.plan_id, 1)

    def test_pause_blocks_run_and_resume_does_not_execute(self):
        self.configure()
        plan_runner.pause(self.plan_id, True, "test")
        with self.assertRaisesRegex(ValueError, "paused"):
            plan_runner.run_step(self.plan_id, 1)
        self.assertEqual(self.step()["status"], "pending")
        plan_runner.pause(self.plan_id, False)
        self.assertEqual(self.step()["status"], "pending")

    def test_failure_is_saved_and_audited(self):
        self.configure()
        with patch.object(tool_lab, "run_approved", side_effect=RuntimeError("planned failure")):
            with self.assertRaisesRegex(RuntimeError, "planned failure"):
                plan_runner.run_step(self.plan_id, 1)
        row = self.step()
        self.assertEqual(row["status"], "failed")
        self.assertIn("planned failure", row["error"])
        with core.connect() as db:
            events = [r["event_type"] for r in db.execute(
                "SELECT event_type FROM audit_events WHERE entity_type='plan_step' AND entity_id='1:1'"
            )]
        self.assertIn("plan_step_started", events)
        self.assertIn("plan_step_failed", events)

    def test_skip_is_explicit_audited_and_never_executes(self):
        plan_runner.skip_step(self.plan_id, 1, "not needed")
        row = self.step()
        self.assertEqual(row["status"], "skipped")
        self.assertEqual(row["error"], "not needed")
        with core.connect() as db:
            events = [r["event_type"] for r in db.execute(
                "SELECT event_type FROM audit_events WHERE entity_type='plan_step' AND entity_id='1:1'"
            )]
        self.assertIn("plan_step_skipped", events)
        with self.assertRaisesRegex(ValueError, "skipped"):
            plan_runner.run_step(self.plan_id, 1)

    def test_skip_rejects_paused_plan_and_completed_step(self):
        plan_runner.pause(self.plan_id, True, "test")
        with self.assertRaisesRegex(ValueError, "paused"):
            plan_runner.skip_step(self.plan_id, 1)
        plan_runner.pause(self.plan_id, False)
        self.configure()
        plan_runner.run_step(self.plan_id, 1)
        with self.assertRaisesRegex(ValueError, "completed"):
            plan_runner.skip_step(self.plan_id, 1)

    def test_interrupted_step_requires_explicit_recovery(self):
        self.configure()
        with core.connect() as db:
            db.execute("UPDATE plan_steps SET status='running' WHERE plan_id=? AND step_number=1",
                       (self.plan_id,))
        with self.assertRaisesRegex(ValueError, "running"):
            plan_runner.run_step(self.plan_id, 1)
        plan_runner.recover_interrupted(self.plan_id, 1)
        self.assertEqual(self.step()["status"], "failed")
        self.assertIn("interrupted", self.step()["error"])

    def test_recovery_rejects_non_running_step(self):
        with self.assertRaisesRegex(ValueError, "running"):
            plan_runner.recover_interrupted(self.plan_id, 1)

    def test_missing_plan_or_step_rejected(self):
        with self.assertRaisesRegex(ValueError, "plan does not exist"):
            plan_runner.list_steps(999)
        with self.assertRaisesRegex(ValueError, "step does not exist"):
            plan_runner.configure(self.plan_id, 999, "count_demo", "x")


if __name__ == "__main__":
    unittest.main()
