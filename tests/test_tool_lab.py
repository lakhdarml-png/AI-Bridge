import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tool_lab


class ToolLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state = root / "state"
        self.candidates = self.state / "candidates"
        self.approved = self.state / "approved"
        self.audit = self.state / "audit.jsonl"
        self.patchers = [
            patch.object(tool_lab, "STATE", self.state),
            patch.object(tool_lab, "CANDIDATES", self.candidates),
            patch.object(tool_lab, "APPROVED", self.approved),
            patch.object(tool_lab, "AUDIT", self.audit),
        ]
        for p in self.patchers:
            p.start()
        tool_lab.paths()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        self.temp.cleanup()

    def test_skill_suggestions_are_local_and_non_executing(self):
        result = tool_lab.suggest_skill("أريد حساب عدد الكلمات في النص")
        self.assertEqual(result["status"], "suggested_only")
        self.assertIn("word_count", [item["operation"] for item in result["suggestions"]])
        word_skill = next(item for item in result["suggestions"] if item["operation"] == "word_count")
        self.assertIn("python tool_lab.py create skill_word_count", word_skill["create_command"])
        self.assertEqual(word_skill["workflow"], ["create", "test", "approve"])
        self.assertIn("لا تُنشأ أو تُنفّذ شيفرة", result["limits"])
        self.assertEqual(result["status"], "suggested_only")

    def test_skill_suggestion_rejects_empty_or_oversized_goal(self):
        with self.assertRaises(ValueError):
            tool_lab.suggest_skill("   ")
        with self.assertRaises(ValueError):
            tool_lab.suggest_skill("x" * 4001)

    def test_create_and_test_candidate(self):
        path = tool_lab.create("count_demo", "word_count", "hello world", 20)
        self.assertTrue(path.exists())
        self.assertTrue(tool_lab.test_candidate("count_demo"))

    def test_unknown_operation_rejected(self):
        with self.assertRaises(ValueError):
            tool_lab.create("unsafe", "__import__", "x", 20)

    def test_python_source_is_not_loaded_or_executed(self):
        manifest = {"name": "demo", "operation": "word_count", "sample_input": "x",
                    "expected": {}, "options": {}}
        with self.assertRaises(ValueError):
            tool_lab.validate(manifest | {"operation": "python_exec"})

    def test_approval_requires_passing_fixture(self):
        tool_lab.create("uppercase_demo", "uppercase", "abc", 20)
        path = tool_lab.candidate_path("uppercase_demo")
        item = json.loads(path.read_text(encoding="utf-8"))
        item["expected"] = "not the expected output"
        path.write_text(json.dumps(item), encoding="utf-8")
        with self.assertRaises(ValueError):
            tool_lab.approve("uppercase_demo")

    def test_rollback_selects_previous_version(self):
        tool_lab.create("prefix_demo", "prefix", "first sample", 5)
        tool_lab.approve("prefix_demo")
        path = tool_lab.candidate_path("prefix_demo")
        item = json.loads(path.read_text(encoding="utf-8"))
        item["sample_input"] = "second sample"
        item["expected"] = "secon"
        path.write_text(json.dumps(item), encoding="utf-8")
        tool_lab.approve("prefix_demo")
        active = self.approved / "prefix_demo" / "active.json"
        self.assertEqual(active.read_text().strip(), "v2.json")
        tool_lab.rollback("prefix_demo")
        self.assertEqual(active.read_text().strip(), "v1.json")

    def test_only_approved_active_tool_can_run(self):
        with self.assertRaises(ValueError):
            tool_lab.run_approved("count_demo", "hello world")
        tool_lab.create("count_demo", "word_count", "fixture", 20)
        with self.assertRaises(ValueError):
            tool_lab.run_approved("count_demo", "hello world")
        tool_lab.approve("count_demo")
        result = tool_lab.run_approved("count_demo", "hello world")
        self.assertEqual(result, {"characters": 11, "words": 2, "lines": 1})

    def test_active_pointer_cannot_escape_approved_folder(self):
        tool_lab.create("count_demo", "word_count", "fixture", 20)
        tool_lab.approve("count_demo")
        active = self.approved / "count_demo" / "active.json"
        active.write_text("../../outside.json")
        with self.assertRaises(ValueError):
            tool_lab.run_approved("count_demo", "x")

    def test_input_limit_enforced(self):
        tool_lab.create("upper_demo", "uppercase", "x", 20)
        tool_lab.approve("upper_demo")
        with self.assertRaises(ValueError):
            tool_lab.run_approved("upper_demo", "x" * 4001)


if __name__ == "__main__":
    unittest.main()
