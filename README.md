# NEO-LOCAL Core

Local-first Python and SQLite kernel for Android/Termux. No API and no third-party Python dependencies.

## Core
```bash
python core.py init
python core.py status
python -m unittest discover -s tests -v
```

## Safe tool lab
Candidates are declarative JSON manifests, not generated Python source. Only operations in the built-in allowlist can run.

```bash
python tool_lab.py create count_demo --operation word_count --sample "hello world"
python tool_lab.py test count_demo
python tool_lab.py approve count_demo
python tool_lab.py list
python tool_lab.py run count_demo "hello from NEO-LOCAL"
```

Supported operations: `word_count`, `uppercase`, `prefix`. Inputs are limited to 4000 characters. Only the active approved version runs; approval is explicit and rollback is available.

Discover a likely built-in capability from a goal without running it:
```bash
python tool_lab.py suggest "أريد حساب عدد الكلمات في النص"
python tool_lab.py learn

The `learn` command reviews recent local tool-lab audit events, summarizes candidate test outcomes, and suggests review steps when failures are recorded. It only analyzes existing history; it does not change tools, execute generated code, or provide model-based learning. The report covers up to the latest 500 audit lines and shows recent activity.

``
The result includes a suggested candidate name, a ready-to-copy `create` command, and the manual `create → test → approve` workflow for each match. These are suggestions only: NEO-LOCAL does not execute the displayed command, generate or execute code, contact a model, or approve a tool. Inspect the proposed sample and command before running them.

## Explicit task execution
Tasks are never run automatically. Create a task, inspect the task list, and explicitly select an approved tool and input:

```bash
python core.py task "Count words in a text"
python task_runner.py list
python task_runner.py run 1 count_demo "hello world"
python core.py status
```

Replace `1` with the ID printed when the task was created. Success saves the result and marks the task completed; failure marks it failed. Terminal tasks cannot be run again.

If Termux or Python is interrupted and leaves a task in `running`, inspect the list first, then explicitly mark tasks older than one hour as failed:
```bash
python task_runner.py recover --older-than-minutes 60
```
Recovery never resumes or executes tasks. The threshold can be 1 to 10080 minutes.

## Task and memory management (v0.5)
```bash
python task_manager.py list
python task_manager.py list --search "report"
python task_manager.py show 1
python task_manager.py status 1 waiting_input
python memory_manager.py
python memory_manager.py "local tests"
```
Manual status changes are limited to safe transitions. Task/memory creation and permitted task status changes are recorded in SQLite.

## Local planner (v0.6)
Create a draft plan without executing a task or tool:
```bash
python plan_manager.py create "Build an Android application"
python plan_manager.py list
python plan_manager.py show 1
python plan_manager.py approve 1
```
Attach a plan to an existing task by passing its ID:
```bash
python plan_manager.py create "Improve the local tool lab" --task-id 1
```
The planner uses deterministic local templates, so it works without an API but is not a general-purpose language model. Approval only marks the plan approved; it never starts execution. Plan creation and approval are audited.

## Mobile dashboard (v0.8)
Start the local-only, phone-friendly dashboard from Termux:
```bash
python web_dashboard.py
```
Then open `http://127.0.0.1:8765` in the browser on the same phone. Keep Termux running while using it; stop the server with Ctrl+C. If the port is occupied, use `python web_dashboard.py --port 8766` and open that port instead.

The dashboard can create draft plans, explicitly approve a plan, configure a step with an active approved tool, run one step only after confirmation, skip a step, record a stranded running step as failed, and pause/resume a plan. It never auto-approves plans or runs subsequent steps. The emergency-stop control prevents later steps from starting; it cannot interrupt a tool that is already running. The refreshed dashboard adds a plan progress bar, an expanded status pulse (including failed-step attention), and a conversation-style local goal panel. Sending a message creates a draft plan and displays its proposed steps in the page session; this is a deterministic local planner, not a live AI conversation, and the message history is not persisted. Progress counts completed and explicitly skipped steps as resolved; failed steps remain visible for attention. The dashboard refreshes its status automatically every five seconds while the page is visible, shows a local connection indicator, and avoids rebuilding step inputs while the user is editing them.

The server binds only to `127.0.0.1` and uses Python's standard library. It is intended for the same device, not LAN access. The goal box creates a deterministic local plan; it is not a live AI chat and does not call a model or network service.

## Security boundary
This is a guarded local workflow, not an OS-level sandbox. Do not pass private information to tools unless you intend to process it locally. The local SQLite database is not encrypted by this program.
