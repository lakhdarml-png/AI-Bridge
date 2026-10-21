#!/usr/bin/env python3
"""NEO-LOCAL v0.3 approved tool runner.

Candidates are declarative JSON manifests, never Python source. Only operations
implemented in this file can run. This is not a general-purpose code sandbox.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE = Path.home() / ".neo_local" / "tool_lab"
CANDIDATES = STATE / "candidates"
APPROVED = STATE / "approved"
AUDIT = STATE / "audit.jsonl"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
OPERATIONS = {"word_count", "uppercase", "prefix"}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def paths() -> None:
    for path in (CANDIDATES, APPROVED):
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            path.chmod(0o700)
        except OSError:
            pass


def audit(action: str, name: str, detail: str = "") -> None:
    paths()
    AUDIT.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        AUDIT.chmod(0o600)
    except OSError:
        pass
    with AUDIT.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"time": stamp(), "action": action, "name": name, "detail": detail}, ensure_ascii=False) + "\n")


def apply_operation(operation: str, text: str, options: dict[str, Any] | None = None) -> Any:
    options = options or {}
    if operation == "word_count":
        return {"characters": len(text), "words": len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)), "lines": len(text.splitlines()) if text else 0}
    if operation == "uppercase":
        return text.upper()
    if operation == "prefix":
        limit = options.get("limit", 20)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError("prefix limit must be an integer from 1 to 500")
        return text[:limit]
    raise ValueError("operation is not in the built-in allowlist")


def validate(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    name = manifest.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("invalid tool name")
    if manifest.get("operation") not in OPERATIONS:
        raise ValueError("operation is not in the built-in allowlist")
    if not isinstance(manifest.get("sample_input"), str) or len(manifest["sample_input"]) > 4000:
        raise ValueError("sample_input must be text of at most 4000 characters")
    expected = manifest.get("expected")
    if isinstance(expected, bool) or not isinstance(expected, (str, dict, int, list, type(None))):
        raise ValueError("unsupported expected result type")
    options = manifest.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("options must be an object")
    apply_operation(manifest["operation"], manifest["sample_input"], options)


def candidate_path(name: str) -> Path:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("invalid tool name")
    return CANDIDATES / f"{name}.json"


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    return data


def create(name: str, operation: str, sample: str, limit: int) -> Path:
    paths()
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("name must start with a lowercase letter and contain only a-z, 0-9, _")
    if operation not in OPERATIONS:
        raise ValueError(f"operation must be one of: {', '.join(sorted(OPERATIONS))}")
    if not isinstance(sample, str) or len(sample) > 4000:
        raise ValueError("sample must be text of at most 4000 characters")
    options = {"limit": limit} if operation == "prefix" else {}
    expected = apply_operation(operation, sample, options)
    manifest = {
        "schema_version": 1, "name": name, "version": 1, "operation": operation,
        "options": options, "sample_input": sample, "expected": expected,
        "created_at": stamp(), "status": "candidate",
        "notice": "Declarative manifest only; no generated code is executed."
    }
    path = candidate_path(name)
    if path.exists():
        raise ValueError(f"candidate already exists: {path}")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit("create", name, operation)
    return path


def test_candidate(name: str) -> bool:
    path = candidate_path(name)
    manifest = load_manifest(path)
    actual = apply_operation(manifest["operation"], manifest["sample_input"], manifest.get("options"))
    passed = actual == manifest.get("expected")
    audit("test", name, "passed" if passed else "failed")
    print(f"Candidate: {name}")
    print(f"Operation: {manifest['operation']}")
    print(f"Expected:  {json.dumps(manifest.get('expected'), ensure_ascii=False)}")
    print(f"Actual:    {json.dumps(actual, ensure_ascii=False)}")
    print("Result: " + ("PASS" if passed else "FAIL"))
    return passed


def approve(name: str) -> Path:
    if not test_candidate(name):
        raise ValueError("candidate tests failed; approval refused")
    manifest = load_manifest(candidate_path(name))
    folder = APPROVED / name
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    versions = sorted(folder.glob("v*.json"))
    version = max((int(p.stem[1:]) for p in versions if p.stem[1:].isdigit()), default=0) + 1
    manifest["version"] = version
    manifest["status"] = "approved"
    manifest["approved_at"] = stamp()
    target = folder / f"v{version}.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "active.json").write_text(target.name + "\n", encoding="utf-8")
    audit("approve", name, f"v{version}")
    return target


def active_manifest(name: str) -> tuple[dict[str, Any], Path]:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("invalid tool name")
    folder = APPROVED / name
    active_file = folder / "active.json"
    if not active_file.is_file():
        raise ValueError("tool has no active approved version")
    version_name = active_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"v[1-9][0-9]*\.json", version_name):
        raise ValueError("invalid active version pointer")
    version_path = folder / version_name
    if not version_path.is_file():
        raise ValueError("active version file is missing")
    manifest = load_manifest(version_path)
    if manifest.get("name") != name or manifest.get("status") != "approved":
        raise ValueError("active manifest is not approved for this tool")
    if manifest.get("version") != int(version_name[1:-5]):
        raise ValueError("active manifest version does not match its filename")
    return manifest, version_path


def run_approved(name: str, text: str) -> Any:
    if not isinstance(text, str) or len(text) > 4000:
        raise ValueError("input must be text of at most 4000 characters")
    manifest, path = active_manifest(name)
    try:
        result = apply_operation(manifest["operation"], text, manifest.get("options"))
    except Exception:
        audit("run", name, f"{path.name}:failed")
        raise
    audit("run", name, f"{path.name}:passed")
    return result


def rollback(name: str) -> Path:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("invalid tool name")
    folder = APPROVED / name
    if not folder.is_dir():
        raise ValueError("no approved tool with that name")
    versions = sorted((p for p in folder.glob("v*.json") if p.stem[1:].isdigit()), key=lambda p: int(p.stem[1:]))
    if len(versions) < 2:
        raise ValueError("rollback needs at least two approved versions")
    target = versions[-2]
    manifest = load_manifest(target)
    if manifest.get("name") != name or manifest.get("status") != "approved":
        raise ValueError("previous version is not a valid approved manifest")
    (folder / "active.json").write_text(target.name + "\n", encoding="utf-8")
    audit("rollback", name, target.stem)
    return target


def list_tools() -> None:
    paths()
    print("Candidates:")
    candidates = sorted(CANDIDATES.glob("*.json"))
    for path in candidates:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            print(f"  {item.get('name')} [{item.get('operation')}]")
        except (OSError, json.JSONDecodeError):
            print(f"  INVALID: {path.name}")
    if not candidates:
        print("  (none)")
    print("Approved:")
    found = False
    for active in sorted(APPROVED.glob("*/active.json")):
        found = True
        try:
            manifest, version_path = active_manifest(active.parent.name)
            print(f"  {active.parent.name}: {version_path.name} [{manifest['operation']}]")
        except (OSError, ValueError, json.JSONDecodeError):
            print(f"  {active.parent.name}: INVALID active version")
    if not found:
        print("  (none)")


def suggest_skill(goal: str) -> dict[str, Any]:
    """Suggest a safe built-in capability from a goal; never executes or writes code."""
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 4000:
        raise ValueError("goal must be non-empty text of at most 4000 characters")
    text_goal = goal.casefold()
    rules = [
        (("count", "word", "words", "عدد", "كلمات", "كلمة"), "word_count", "تحليل عدد الأحرف والكلمات والأسطر"),
        (("uppercase", "upper", "capital", "حروف كبيرة", "تكبير الحروف"), "uppercase", "تحويل النص إلى أحرف كبيرة"),
        (("prefix", "first characters", "بداية النص", "أول أحرف", "مقدمة"), "prefix", "استخراج بداية النص"),
    ]
    matches = []
    for terms, operation, description in rules:
        if any(term in text_goal for term in terms):
            matches.append({"operation": operation, "description": description})
    if not matches:
        matches = [
            {"operation": "word_count", "description": "تحليل بنية النص"},
            {"operation": "prefix", "description": "استخراج جزء من النص"},
        ]
    prepared = []
    for item in matches:
        operation = item["operation"]
        sample = "مثال نصي للتجربة"
        if operation == "word_count":
            sample = "مرحبا بك في NEO-LOCAL"
        elif operation == "uppercase":
            sample = "neo-local sample"
        elif operation == "prefix":
            sample = "مثال نصي للتجربة"
        prepared.append({
            **item,
            "candidate_name": f"skill_{operation}",
            "create_command": (
                f'python tool_lab.py create skill_{operation} '
                f'--operation {operation} --sample "{sample}"'
            ),
            "workflow": ["create", "test", "approve"],
        })
    return {
        "goal": goal.strip(),
        "suggestions": prepared,
        "status": "suggested_only",
        "next_step": "انسخ أمر create المناسب، راجع المرشح، ثم نفّذ test وapprove يدويًا إذا كانت النتيجة صحيحة.",
        "limits": "أوامر مقترحة فقط؛ لا يُنفّذ أي أمر تلقائيًا، ولا تُنشأ أو تُنفّذ شيفرة ولا يوجد اتصال بالشبكة."
    }



def learning_report() -> dict[str, Any]:
    """Summarize recorded tool-lab outcomes and identify conservative next steps."""
    counts: dict[str, int] = {}
    outcomes: dict[str, dict[str, int]] = {}
    recent: list[dict[str, str]] = []
    if AUDIT.is_file():
        try:
            lines = AUDIT.read_text(encoding="utf-8").splitlines()[-500:]
        except OSError:
            lines = []
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            action = str(event.get("action", "unknown"))
            name = str(event.get("name", "unknown"))
            detail = str(event.get("detail", ""))
            counts[action] = counts.get(action, 0) + 1
            if action == "test":
                outcome = "passed" if detail == "passed" else "failed"
                bucket = outcomes.setdefault(name, {"passed": 0, "failed": 0})
                bucket[outcome] += 1
            if action in {"create", "test", "approve", "rollback", "run"}:
                recent.append({"action": action, "name": name, "detail": detail,
                               "time": str(event.get("time", ""))})
    recent = recent[-10:]
    suggestions = []
    for name, result in sorted(outcomes.items()):
        if result["failed"]:
            suggestions.append({
                "candidate": name,
                "reason": "Se han registrado pruebas fallidas.",
                "next_action": "Revisar sample_input y expected; crear un nuevo candidato corregido y probarlo antes de aprobarlo."
            })
    if not suggestions:
        suggestions.append({
            "candidate": None,
            "reason": "No hay fallos registrados en el historial disponible." if outcomes else "Aún no hay resultados de pruebas registrados.",
            "next_action": "Ejecutar pruebas representativas para cada candidato y conservar los resultados en el historial."
        })
    return {
        "status": "local_history_review",
        "events_counted": sum(counts.values()),
        "action_counts": counts,
        "test_outcomes": outcomes,
        "improvement_suggestions": suggestions,
        "recent_activity": recent,
        "limits": "Resumen basado solo en el historial local disponible; no modifica herramientas, no ejecuta código y no demuestra aprendizaje de un modelo."
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEO-LOCAL safe declarative tool laboratory")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("create", help="create a candidate manifest")
    new.add_argument("name")
    new.add_argument("--operation", required=True, choices=sorted(OPERATIONS))
    new.add_argument("--sample", required=True)
    new.add_argument("--limit", type=int, default=20)
    test = sub.add_parser("test", help="test a candidate against its fixture")
    test.add_argument("name")
    promotion = sub.add_parser("approve", help="approve a passing candidate (explicit action)")
    promotion.add_argument("name")
    rb = sub.add_parser("rollback", help="point active version to the previous approved version")
    rb.add_argument("name")
    run = sub.add_parser("run", help="run the active approved tool on text")
    run.add_argument("name")
    run.add_argument("text")
    suggest = sub.add_parser("suggest", help="suggest built-in skills for a goal without executing anything")
    suggest.add_argument("goal")
    sub.add_parser("list", help="list candidates and active approved versions")
    sub.add_parser("learn", help="review local tool history and suggest improvements")
    args = parser.parse_args(argv)
    try:
        paths()
        if args.command == "create":
            print(f"Candidate saved: {create(args.name, args.operation, args.sample, args.limit)}")
        elif args.command == "test":
            return 0 if test_candidate(args.name) else 1
        elif args.command == "approve":
            print(f"Approved version saved: {approve(args.name)}")
        elif args.command == "rollback":
            print(f"Active version switched to: {rollback(args.name)}")
        elif args.command == "run":
            result = run_approved(args.name, args.text)
            print(json.dumps(result, ensure_ascii=False))
        elif args.command == "suggest":
            print(json.dumps(suggest_skill(args.goal), ensure_ascii=False, indent=2))
            audit("suggest", "skill_discovery", args.goal[:160])
        elif args.command == "learn":
            print(json.dumps(learning_report(), ensure_ascii=False, indent=2))
            audit("learn", "tool_lab", "local history summarized")
        elif args.command == "list":
            list_tools()
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
