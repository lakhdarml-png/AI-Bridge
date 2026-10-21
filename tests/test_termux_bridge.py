import unittest
from unittest.mock import patch
from types import SimpleNamespace

import termux_bridge


class TermuxBridgeTests(unittest.TestCase):
    def test_only_predefined_actions_are_accepted(self):
        with self.assertRaises(ValueError):
            termux_bridge.run_action("rm -rf /")
        with self.assertRaises(ValueError):
            termux_bridge.run_action("python -c 'print(1)'")

    def test_core_status_is_a_fixed_read_only_command(self):
        self.assertEqual(
            termux_bridge.ACTIONS["core_status"],
            [termux_bridge.sys.executable, "core.py", "status"],
        )

    @patch("termux_bridge.subprocess.run")
    def test_action_uses_no_shell_and_fixed_timeout(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout="ok", stderr="")
        result = termux_bridge.run_action("learn")
        self.assertTrue(result["ok"])
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], termux_bridge.TIMEOUT_SECONDS)
        self.assertEqual(kwargs["cwd"], termux_bridge.ROOT)
        self.assertEqual(run.call_args.args[0], termux_bridge.ACTIONS["learn"])

    @patch("termux_bridge.subprocess.run")
    def test_failed_action_is_reported(self, run):
        run.return_value = SimpleNamespace(returncode=1, stdout="", stderr="failure")
        result = termux_bridge.run_action("tests")
        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 1)
        self.assertEqual(result["stderr"], "failure")

    @patch("termux_bridge.subprocess.run")
    def test_timeout_is_reported_without_crashing(self, run):
        import subprocess
        run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=1)
        result = termux_bridge.run_action("tests")
        self.assertFalse(result["ok"])
        self.assertIsNone(result["returncode"])
        self.assertIn("timed out", result["stderr"])


if __name__ == "__main__":
    unittest.main()
