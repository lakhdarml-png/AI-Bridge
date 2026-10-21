# NEO-LOCAL — Target Architecture

## Purpose
Build an independent, personal Android agent that can coordinate permitted local tools and, when explicitly connected, other apps and external services. It should take a user's goal through understanding, planning, controlled execution, verification, and delivery. It must not confuse successful code execution with successful completion of the user's goal.

The product is personal-use software, not a public multi-user service. Android sandbox limits remain real: access to other apps is only through supported Android APIs, user-enabled Accessibility where appropriate, exported/imported files, Termux, or explicitly configured integrations. The agent must never claim unrestricted access to private data in other apps.

## Approved five-phase plan and project weights
These weights describe the planned scope of the whole project, not measured completion:
1. **Existing core foundation — 15%**
2. **Independent Android app and core connection — 25%**
3. **Access, execution, and diagnostics — 25%**
4. **Self-development and extensions — 20%**
5. **Integrations, expansion, and stability — 15%**

Total: 100%. Completion percentages must be evidence-based and reported separately from these scope weights. No phase is considered complete merely because its documents or directories exist.

## Engineering rules
1. Inspect and reuse the current implementation before replacing modules.
2. Keep changes reviewable, but integrate by user-visible capability rather than endlessly polishing isolated functions.
3. Keep stable branches untouched; use a dedicated working branch.
4. No completion claim without evidence appropriate to the capability; distinguish code present, unit-tested, integration-tested, and verified on the phone.
5. Do not run the same side-effecting task through multiple runners.
6. Persist state before and after meaningful transitions; support safe recovery from interruption.
7. Default to deny: tools are allowlisted, arguments validated, and risky actions require explicit approval.
8. Avoid heavy dependencies unless a demonstrated need outweighs installation and maintenance costs on Android/Termux.
9. Secrets, tokens, private runtime data, and personal files must not be committed.
10. Every tool has an input contract, output contract, side-effect level, permission requirement, timeout/output bound, and verification strategy.
11. Inspection and analysis may run automatically only within permissions already granted by the user.
12. Explicit user approval is required before destructive changes, sensitive writes, irreversible actions, external submissions, or permission/security-policy changes.
13. The agent cannot grant itself new Android permissions or silently weaken its own security controls.

## Five architectural layers

### Layer 1 — Existing core foundation (15%)
Responsibilities: task and plan state, persistent memory, workflow coordination, audit trail, and durable task state.
Current source candidates: `core.py`, `task_manager.py`, `task_runner.py`, `plan_manager.py`, `plan_runner.py`, `workflow_engine.py`, and `memory_manager.py`.
Target contract: one canonical task/plan lifecycle, explicit state transitions, durable records, recoverable execution, and an auditable history. Existing files are implementation evidence, not proof that all target behaviors are complete.

### Layer 2 — Independent Android app and core connection (25%)
Responsibilities: a native Android application with a coherent home/workspace, conversation and task views, project selection, approvals, results, and a clear connection state to the local core.
Current source candidates: `app/src/main/java/com/aios/bridge/MainActivity.kt`, `activity_main.xml`, Android resources, manifest, and Gradle files. The current package identity and UI still use the older bridge identity and must be adapted gradually rather than replaced wholesale.
Target contract: the app can inspect core status and submit supported requests through a documented local protocol; disconnections and denied permissions are visible and do not freeze or misrepresent the app.

### Layer 3 — Access, execution, and diagnostics (25%)
Responsibilities: permitted file/project inspection, logs, tool registry, controlled Termux execution, build/test invocation, diagnostics, result verification, and safe recovery.
Current source candidates: `tool_lab.py`, `termux_bridge.py`, tests, and the existing task/plan runners.
Target contract: operations are explicitly registered and validated; read operations are separated from mutations; sensitive operations require a separate approval path; arbitrary shell input is not exposed by a general-purpose endpoint; outputs and execution time are bounded. Android access to other apps remains permission-limited.

### Layer 4 — Self-development and extensions (20%)
Responsibilities: a dedicated “التطوير الذاتي” area that displays layers, available tools, missing capabilities, extension candidates, configuration, approval status, and implementation progress.
Target contract: the agent may propose a new tool or layer, explain the gap it addresses, show its permission and risk profile, and prepare a reviewable change. Installation, activation, code modification, permission expansion, and security-policy changes require the user's explicit approval. A proposal or manifest alone is not an executable capability.

### Layer 5 — Integrations, expansion, and stability (15%)
Responsibilities: optional model/API providers, GitHub and future app integrations, import/export and backups, restore procedures, compatibility checks, privacy, operational status, and release quality.
Target contract: local functionality remains usable without API keys or paid providers. Each integration is optional, least-privilege, independently disableable, and has a documented data flow and failure behavior. No provider is assumed connected until verified.

## Current repository map (observed on the integration branch)
- Android shell: `app/` with `MainActivity.kt`, `BridgeAccessibilityService.kt`, resources, manifest, and Gradle configuration.
- Core and state: `core.py`, `task_manager.py`, `memory_manager.py`.
- Planning and execution: `plan_manager.py`, `plan_runner.py`, `task_runner.py`, `workflow_engine.py`.
- Tool system and local bridge: `tool_lab.py`, `termux_bridge.py`.
- Secondary interface: `web_dashboard.py`.
- Tests: `tests/test_*.py`.
- Architecture and reference docs: `docs/NEO_LOCAL_ARCHITECTURE.md`, `docs/NEO_LOCAL_ROADMAP.md`, `docs/REFERENCE_PROJECTS.md`.

This is a repository-level inventory only. It does not prove that the local Termux working tree is identical to this branch. The last reported local branch name was not present in the GitHub branch list during this review; local-only commits must be pushed or selectively transferred before GitHub can verify them.

## Component contracts
- **Core/persistence:** SQLite state, task/plan records, audit events, and safe schema evolution.
- **Intake:** normalize a goal, retain constraints, ask only for essential missing information, and define acceptance criteria.
- **Planner:** produce a bounded plan with dependencies, inputs, expected outputs, risk, and verification criteria per step.
- **Tool registry:** allowlisted tools with schemas, validation, side-effect metadata, permission checks, timeouts, and output limits.
- **Runner/scheduler:** a single execution owner per step, attempt records, checkpoints, and explicit failures.
- **Verifier:** verify outputs against declared contracts and goal-level acceptance criteria.
- **Recovery:** inspect persisted state and recover safely without blindly retrying non-idempotent actions.
- **Memory:** distinguish durable user-approved facts, project context, task logs, and temporary working context; include provenance and bounded retrieval.
- **Android connector:** expose only documented operations and report permission, connectivity, and capability status accurately.
- **Termux bridge:** local-only, allowlisted operations; no arbitrary shell endpoint.
- **Interface:** Android app is the primary user interface; CLI/dashboard remain useful operational surfaces and must not become competing workflow engines.
- **Observability:** task timeline, transitions, approval requests, tool summaries, errors, verification evidence, and final report.

## Canonical lifecycle
`received → clarified (if needed) → planned → awaiting_approval (when required) → ready → running → verifying → completed`

Failure/hold states must be explicit, including `waiting_input`, `blocked`, `failed`, and `cancelled`. Never infer terminal success from one successful step.

## Completion contract
A task is complete only when:
- all required steps completed or were explicitly waived with a recorded reason;
- required outputs pass their declared verification;
- goal-level acceptance criteria pass;
- the resulting artifact/output is stored and reported;
- unresolved blockers and limitations are visible.

## Safety boundaries
- No arbitrary shell command exposed through the bridge.
- Read-only inspection before file mutation or external side effects.
- Explicit approval before destructive, sensitive, external, or irreversible operations.
- No silent permission expansion or self-modification of security rules.
- Bounded retries, timeouts, and output sizes.
- Redact secrets from logs and prevent secret files from entering Git.
- Accessibility access, if used, must be separately enabled by the user and restricted to a disclosed purpose.

## Integration approach
Treat existing source as the implementation source of truth after inspection. Preserve working behavior and migrate only where an identified gap requires it. Build the documented boundaries first, then implement one layer at a time in the approved order. Do not create empty code modules solely to make the architecture look complete.

## Definition of done for architecture and skeleton
- The five layers, their responsibilities, current source mapping, and boundaries are documented.
- Existing versus planned capabilities are clearly distinguished.
- Each layer has a verifiable acceptance gate in the roadmap.
- No stable branch or working source is replaced as part of documentation work.
