#!/usr/bin/env python3
"""NEO-LOCAL Termux bridge: loopback-only, allowlisted maintenance actions.

This is a local control surface, not a remote access tunnel. It never accepts
shell commands or binds to a network interface other than 127.0.0.1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8766
MAX_BODY = 1024
TIMEOUT_SECONDS = 120

ACTIONS: dict[str, list[str]] = {
    "status": ["git", "status", "--short", "--branch"],
    "learn": [sys.executable, "tool_lab.py", "learn"],
    "list": [sys.executable, "tool_lab.py", "list"],
    "tests": [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
}


def run_action(action: str) -> dict[str, Any]:
    """Run one predefined command; never passes user text to a shell."""
    if action not in ACTIONS:
        raise ValueError("action not allowed")
    try:
        result = subprocess.run(
            ACTIONS[action],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            shell=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {
            "action": action,
            "returncode": result.returncode,
            "ok": result.returncode == 0,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "action": action,
            "returncode": None,
            "ok": False,
            "stdout": "",
            "stderr": f"Action timed out after {TIMEOUT_SECONDS} seconds.",
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "NEO-LOCAL-Bridge/0.1"

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send(200, {
                "service": "NEO-LOCAL Termux bridge",
                "version": "0.1",
                "host": HOST,
                "actions": sorted(ACTIONS),
                "remote_access": False,
                "arbitrary_commands": False,
            })
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/run":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"error": "invalid content length"})
            return
        if length < 1 or length > MAX_BODY:
            self._send(413, {"error": "request body must be 1-1024 bytes"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"error": "invalid JSON"})
            return
        if not isinstance(payload, dict) or set(payload) != {"action"} or not isinstance(payload["action"], str):
            self._send(400, {"error": "body must contain only an action string"})
            return
        try:
            result = run_action(payload["action"])
        except ValueError:
            self._send(400, {"error": "action not allowed", "actions": sorted(ACTIONS)})
            return
        self._send(200 if result["ok"] else 500, result)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep request logging minimal; action results are returned to the caller.
        return


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        print(json.dumps({"host": HOST, "port": PORT, "actions": sorted(ACTIONS)}))
        return 0
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"NEO-LOCAL bridge listening only on http://{HOST}:{PORT}")
    print("Allowed actions:", ", ".join(sorted(ACTIONS)))
    print("Stop with Ctrl+C. No remote access or arbitrary shell commands.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
