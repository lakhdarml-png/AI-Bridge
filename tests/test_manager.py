import os
import tempfile
import unittest
from pathlib import Path
import core
import task_manager
import memory_manager

class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        core.APP_HOME=Path(self.temp.name)
        core.DB_PATH=core.APP_HOME/"test.sqlite3"
        core.init_db()
    def tearDown(self): self.temp.cleanup()

    def test_task_search_and_details(self):
        one=core.add_task("Prepare project report")
        core.add_task("Review local tests")
        self.assertEqual([r["id"] for r in task_manager.search_tasks("project")],[one])
        self.assertEqual(task_manager.show_task(one)["goal"],"Prepare project report")

    def test_safe_status_transitions_are_audited(self):
        task_id=core.add_task("Need clarification")
        task_manager.set_status(task_id,"waiting_input")
        task_manager.set_status(task_id,"queued")
        with core.connect() as db:
            events=db.execute("SELECT event_type,details FROM audit_events WHERE entity_id=? AND event_type='task_status_changed' ORDER BY id",(str(task_id),)).fetchall()
        self.assertEqual(len(events),2)
        self.assertEqual(events[0]["details"],"queued -> waiting_input; actor=manual")
        with self.assertRaises(ValueError): task_manager.set_status(task_id,"completed")
        with self.assertRaises(ValueError): task_manager.set_status(task_id,"running")

    def test_terminal_task_cannot_be_manually_reopened(self):
        task_id=core.add_task("Finished")
        with core.connect() as db: db.execute("UPDATE tasks SET status='completed' WHERE id=?",(task_id,))
        with self.assertRaises(ValueError): task_manager.set_status(task_id,"queued")


    def test_execution_transition_requires_runner_and_checks_expected_state(self):
        task_id=core.add_task("Controlled execution")
        with self.assertRaises(ValueError):
            task_manager.transition_status(task_id,"running")
        task_manager.transition_status(
            task_id,"running",expected_status="queued",actor="test",
            execution_transition=True,
        )
        with self.assertRaises(ValueError):
            task_manager.transition_status(
                task_id,"completed",expected_status="queued",actor="test",
                execution_transition=True,
            )
        with core.connect() as db:
            row=db.execute("SELECT status FROM tasks WHERE id=?",(task_id,)).fetchone()
            events=db.execute(
                "SELECT details FROM audit_events WHERE entity_id=? AND event_type='task_status_changed' ORDER BY id",
                (str(task_id),),
            ).fetchall()
        self.assertEqual(row["status"],"running")
        self.assertEqual(len(events),1)
        self.assertIn("actor=test",events[0]["details"])

    def test_memory_search_and_listing(self):
        core.remember("Termux setup","Keep commands short and test locally","workflow")
        self.assertEqual(memory_manager.list_memories("commands")[0]["title"],"Termux setup")
        self.assertEqual(len(memory_manager.list_memories()),1)

    def test_limits_and_missing_task(self):
        with self.assertRaises(ValueError): task_manager.search_tasks(limit=0)
        with self.assertRaises(ValueError): task_manager.show_task(999)

if __name__=="__main__": unittest.main()
