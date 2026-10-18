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
        for path, value in (("STATE", self.state), ("CANDIDATES", self.candidates), ("APPROVED", self.approved), ("AUDIT", self.audit)):
            self.enter_patch = getattr(self, "patchers", None)
            if self.enter_patch is None:
                self.patchers = []
            p = patch.object(tool_lab, path, value)
            p.start()
            self.patchers.append(p)
        tool_lab.paths()

    def tearDown(self):
        for p in getattr(self, "patchers", []):
            p.stop()
        self.temp.cleanup()

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
        # Make and approve a second candidate version with a different fixture.
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


if __name__ == "__main__":
    unittest.main()
