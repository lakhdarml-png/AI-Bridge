# NEO-LOCAL — Delivery Roadmap

This roadmap measures delivered capabilities, not file count. Percentages are not assigned until scope and evidence are recorded.

## Phase 0 — Baseline and architecture inventory
- [ ] Identify repository/branch and record baseline commit.
- [ ] Inventory actual local modules, imports, public functions, state tables, and CLI entry points.
- [ ] Map task/plan state transitions and identify duplicate execution paths.
- [ ] Inspect bridge allowlist and dashboard/API boundary.
- [ ] Define one end-to-end acceptance scenario and its expected artifact.
**Exit condition:** an evidence-backed architecture map and prioritized gap list.

## Phase 1 — Reliable workflow core
- [ ] One canonical task lifecycle and transition validator.
- [ ] Plan-step dependency and input/output contracts.
- [ ] One execution owner per step; idempotency/attempt tracking where appropriate.
- [ ] Atomic persistence/checkpoints and interrupted-run recovery.
- [ ] Goal-level verification separate from step-level verification.
**Exit condition:** interrupted and failed tasks recover without duplicate side effects.

## Phase 2 — Safe tool system
- [ ] Explicit tool registry and schemas.
- [ ] Validate arguments and tool output; bound time and output.
- [ ] Record side effects and approval requirements.
- [ ] Keep bridge allowlist-only; deny unknown operations.
- [ ] Tool contract tests plus failure-path tests.
**Exit condition:** allowed tools work, malformed requests fail closed, and side effects are auditable.

## Phase 3 — Memory and context
- [ ] Separate project memory, user-approved durable facts, and task/event history.
- [ ] Record source/provenance and timestamps.
- [ ] Retrieval limits and privacy-aware logging.
- [ ] Resume context without treating old outputs as current truth.
**Exit condition:** a resumed task retrieves relevant state without exposing unrelated data.

## Phase 4 — End-to-end agent loop
- [ ] Goal intake and clarification when essential constraints are missing.
- [ ] Plan → approval → execute → verify → repair/replan within bounded limits.
- [ ] Final report identifies deliverables, verification evidence, and unresolved limitations.
- [ ] No false completion on partial success.
**Exit condition:** the acceptance scenario completes from a clean start and from an interrupted state.

## Phase 5 — Interface and operational quality
- [ ] CLI commands and error messages are consistent.
- [ ] Dashboard consumes the canonical engine/state.
- [ ] Health/status view shows blocked work, pending approvals, and recent failures.
- [ ] Backup/export and safe upgrade instructions.
**Exit condition:** a user can run, inspect, resume, and diagnose a task on Termux.

## Phase 6 — Release candidate on Android
- [ ] Fresh-install instructions tested on Termux.
- [ ] Dependency and storage requirements documented.
- [ ] Security boundary review and secret scan.
- [ ] Regression suite and end-to-end acceptance scenario pass.
- [ ] Known limitations and rollback procedure documented.
**Exit condition:** a tagged, reproducible release candidate can be installed and verified on the phone.

## Reporting rules
- Report completed items only with direct evidence.
- Keep “implemented”, “unit-tested”, “integration-tested”, and “verified on Android” as separate statuses.
- Do not report 98% based on source files or a passing syntax check.
- Prefer one meaningful end-to-end test over repeated low-value checks.
