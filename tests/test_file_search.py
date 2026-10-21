import json
import tempfile
import unittest
from pathlib import Path

import tool_lab


class FileSearchTests(unittest.TestCase):
    def test_requires_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("NEO-LOCAL\nsafe tools\n", encoding="utf-8")
            request = json.dumps({"path": str(path), "query": "NEO-LOCAL"})
            with self.assertRaisesRegex(ValueError, "approval"):
                tool_lab.apply_operation("file_search", request)

    def test_search_returns_matching_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("first\nNEO-LOCAL works\nlast\n", encoding="utf-8")
            request = json.dumps({"path": str(path), "query": "NEO-LOCAL"})
            result = tool_lab.apply_operation(
                "file_search", request, runtime_approved=True
            )
            self.assertEqual(result["total_matches"], 1)
            self.assertEqual(result["matches"][0]["line"], 2)

    def test_rejects_file_over_size_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large.txt"
            path.write_bytes(b"x" * (1_048_577))
            request = json.dumps({"path": str(path), "query": "x"})
            with self.assertRaisesRegex(ValueError, "1 MiB"):
                tool_lab.apply_operation(
                    "file_search", request, runtime_approved=True
                )


if __name__ == "__main__":
    unittest.main()
