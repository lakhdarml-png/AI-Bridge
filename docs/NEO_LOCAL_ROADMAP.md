# NEO-LOCAL — Five-Phase Delivery Roadmap

This is the approved project structure. The percentages are scope weights for the whole project, not completion estimates. Report actual completion only from repository evidence and device-level verification where required.

## Phase 1 — Existing core foundation (15%)
Scope:
- [ ] Inventory the actual task, plan, memory, audit, and workflow APIs.
- [ ] Establish one canonical task lifecycle and validate legal transitions.
- [ ] Confirm task/plan persistence and state recovery behavior.
- [ ] Define input/output and acceptance contracts for planned steps.
- [ ] Keep memory, project context, and event history distinct.
- [ ] Record baseline commit and a concise list of known gaps.

Acceptance gate: one task can be created, planned, executed through the approved path, verified, and reported without competing execution paths or a false success state.

## Phase 2 — Independent Android app and core connection (25%)
Scope:
- [ ] Evolve the existing Android app incrementally; preserve useful UI and resources.
- [x] Add a first fixed-action local request/response path for core status; versioned protocol and broader task APIs remain open.
- [ ] Verify the new core connection/status UI on a physical phone; expand later to current project, task state, and actionable errors.
- [ ] Provide task submission, plan review, explicit approval prompts, progress, and results.
- [ ] Keep Android sandbox and user-granted permission boundaries explicit.
- [ ] Handle unavailable Termux/core and denied permissions without crashes or misleading success.

Acceptance gate: on the phone, the user can open the app, see the real core status, submit a supported request, and receive a truthful result or actionable connection error.

## Phase 3 — Access, execution, and diagnostics (25%)
Scope:
- [ ] Inspect permitted project files, logs, build output, and test results.
- [ ] Maintain a registered tool catalog with contracts, risk, permissions, and verification.
- [ ] Separate read-only inspection from file mutation, execution, and external side effects.
- [ ] Support bounded, allowlisted build/test/diagnostic workflows through Termux.
- [ ] Require explicit approval for sensitive or destructive operations.
- [ ] Verify results against the requested outcome; report remaining faults and blockers.
- [ ] Recover interrupted work safely without blind retries of non-idempotent operations.

Acceptance gate: a representative project fault can be inspected, diagnosed, proposed as a bounded change, approved, applied through an allowed tool, and verified with evidence; without approval, the mutation does not occur.

## Phase 4 — Self-development and extensions (20%)
Scope:
- [ ] Add a dedicated “التطوير الذاتي” area in the Android app.
- [ ] Display all five layers, current tools, connection states, gaps, and progress.
- [ ] Let the agent explain a missing capability and propose a tool/connector with a contract.
- [ ] Review extension source, permissions, side effects, dependencies, and rollback plan.
- [ ] Require explicit user approval before installing, activating, modifying code, or changing permissions.
- [ ] Track extension versions and preserve a way to disable/revert them.

Acceptance gate: the user can review a proposed extension, understand its effect, approve or reject it, and see its actual activation state; proposals never execute merely because they exist.

## Phase 5 — Integrations, expansion, and stability (15%)
Scope:
- [ ] Keep API/model providers optional and preserve local-only workflows.
- [ ] Add GitHub and other connectors only behind explicit, least-privilege authorization.
- [ ] Provide backup/export, restore, upgrade, and rollback procedures.
- [ ] Show integration status, data flow, limits, and failures transparently.
- [ ] Review privacy, secrets, accessibility usage, and Android sandbox constraints.
- [ ] Document install requirements, known limitations, and release steps.
- [ ] Run a focused end-to-end acceptance scenario and targeted regression checks.

Acceptance gate: the app can be installed and recovered on the target phone, local functions work without provider credentials, optional integrations can be disabled, and the documented end-to-end scenario passes.

## Cross-phase rules
- Build and document the five-layer skeleton before filling layers sequentially.
- Reuse existing code; do not rewrite a working component without an evidenced reason.
- Keep the stable branch untouched and use focused commits.
- Mark each capability separately as **planned**, **implemented**, **unit-tested**, **integration-tested**, or **verified on phone**.
- A passing unit test does not prove Android integration; a file or directory does not prove a feature exists.
- Do not repeat broad test suites when a narrow, relevant check is sufficient.
- Report blockers honestly and prioritize the next action by user impact and risk.

## Current status at this revision
The GitHub working branch contains the Python core/tooling, tests, documentation, and an Android shell. A first source-level Android-to-Termux core-status request and fixed read-only bridge action are now implemented on `neo-local-v1-five-layer-blueprint`; they are not yet build- or device-verified. The task/plan workflow in Android, five-layer self-development interface, and end-to-end fault-repair workflow remain planned until their acceptance gates are evidenced. The local Termux branch previously reported by the user is not currently listed as a remote GitHub branch, so its newest commits cannot be verified from GitHub yet.
