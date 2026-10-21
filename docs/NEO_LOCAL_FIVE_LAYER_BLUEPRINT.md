# NEO-LOCAL — Five-Layer Blueprint

**Status:** architecture skeleton plus first source-level Android-to-Termux status connection; not yet built or verified on a physical phone.  
**Base reviewed:** `neo-local-v1-integration`, commit `1dbed0675854c17cdb85e7adc4fff3ecd0ff75a4`.  
**Blueprint branch:** `neo-local-v1-five-layer-blueprint`.

## Product target
A personal, independent Android agent that helps the user inspect, reason about, and safely work on their apps and projects. It may later connect to more apps or providers, but local operation must not depend on API keys. User approval is required before sensitive modifications, deletion, external actions, permission expansion, or security-policy changes.

## Layer map

| Layer | Weight | Existing source | Target boundary | Status from repository inspection |
|---|---:|---|---|---|
| 1. Core foundation | 15% | `core.py`, `task_manager.py`, `task_runner.py`, `plan_manager.py`, `plan_runner.py`, `workflow_engine.py`, `memory_manager.py` | Persistent state, memory, task/plan lifecycle, audit, recovery | Source exists; full canonical end-to-end lifecycle not yet established by this review |
| 2. Android app + core connection | 25% | `app/`, `MainActivity.kt`, `BridgeAccessibilityService.kt`, manifest/resources | Native workspace, connection status, task/plan views, approvals, results | Source-level core-status button and fixed bridge action added on this branch; build and on-device connection are not yet verified |
| 3. Access, execution, diagnostics | 25% | `tool_lab.py`, `termux_bridge.py`, task/plan runners, `tests/` | Allowlisted inspection, build/test execution, diagnosis, verification, recovery | Several local tools and tests exist; bridge currently exposes only a small fixed action allowlist |
| 4. Self-development/extensions | 20% | No dedicated implementation identified in this branch | “التطوير الذاتي” screen, layer/tool inventory, capability proposals, reviewed activation and rollback | Planned; no dedicated UI/module identified |
| 5. Integrations/stability | 15% | Existing Android app declarations, Termux bridge, docs and tests | Optional providers/connectors, GitHub, backups, restore, privacy and release checks | Partial building blocks exist; full integration/recovery/release gates are not verified |

## Public contracts between layers
1. **Android → Core:** versioned local request/response protocol; bounded payloads; explicit connection status; no general shell-command field.
2. **Core → Tools:** tool identifier plus schema-validated arguments; each tool declares read/write/external side effects, permission and approval needs, limits, and verification.
3. **Tools → Core:** structured result with success/failure, bounded output, error detail, and evidence; never return success merely because a process exited zero if the goal failed.
4. **Core → Android:** task state, required user input, approval request, progress, verification outcome, and final report.
5. **Self-development → Extension registry:** proposal and review metadata first; activation is a separate user-approved operation.
6. **Optional integrations → Core:** least-privilege adapter interface; provider unavailable must not disable local core functions.

## Safety and permission model
- Read/inspect/analyze only within permissions already granted.
- Ask for explicit approval before sensitive writes, deletion, external submission, irreversible actions, or permission changes.
- Never silently expand access or weaken the safety policy.
- Keep Termux bridge bound to loopback and allowlisted actions; never expose arbitrary shell execution through HTTP.
- Treat Accessibility as optional and user-enabled. It does not grant unrestricted access to another app's private data.
- Keep secrets and private runtime data out of Git and redact them from logs.

## Suggested package/directory boundaries
This is a target map, not an instruction to create empty source files now:
- `app/`: Android presentation, user approvals, connection UI, and user-visible status.
- `core/` (future package only if migration is justified): task lifecycle, planner coordination, verification, and persistence contracts.
- `tools/` (future package only if migration is justified): registered tool contracts and built-in handlers.
- `integrations/` (future package only if migration is justified): optional adapters for GitHub and providers.
- `docs/`: architecture, phase roadmap, contracts, security decisions, and acceptance evidence.
- `tests/`: contract, failure-path, and end-to-end acceptance checks.

Do not duplicate existing Python modules into these directories just to match the diagram. Introduce packages only as part of a narrow, tested migration.

## First end-to-end acceptance scenario
1. User selects a permitted project folder or an already configured project.
2. Agent reads a requested file/log and summarizes a concrete issue with evidence.
3. Agent proposes a minimal change and names affected files, risks, and verification steps.
4. No write occurs until the user explicitly approves.
5. The approved change is applied through a registered tool; the original content is preserved or rollback is available.
6. A focused test/build runs within bounded limits.
7. Agent reports changed files, command/test evidence, remaining errors, and whether the requested outcome is actually verified.
8. If approval is declined or the tool is unavailable, the task stops safely and reports that state.

## Immediate implementation order
1. Complete the core inventory from source and define the single canonical workflow contract.
2. Build and verify the new Android core-status button against the local bridge; repair any build or network-policy issue before adding more features.
3. Connect one safe read-only operation through the bridge and show its real response in Android.
4. Add a separate approval path for one bounded mutation only after read-only integration works.
5. Build the self-development screen from real registry/status data, not hard-coded claims.
6. Add optional external integrations only after local end-to-end operation is reliable.

## Evidence discipline
A repository listing proves a file exists, not that a capability works. Use these labels consistently:
- **Planned:** described, not implemented.
- **Implemented:** code exists.
- **Unit-tested:** focused tests pass.
- **Integration-tested:** connected components were exercised together.
- **Verified on phone:** actual Android-device evidence exists.

The branch reviewed here is a GitHub snapshot. The previously reported local Termux branch `neo-local-v1-real-search-tests` was not listed among remote branches during this review; its newest local-only commits are therefore not represented by this snapshot unless pushed or transferred.
