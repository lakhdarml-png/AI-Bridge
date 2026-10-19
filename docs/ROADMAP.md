# NEO-LOCAL roadmap

## v0.1 — local kernel
- [x] SQLite task and memory store
- [x] Minimal CLI
- [x] Deterministic built-in tool
- [x] Unit tests and CI workflow
- [x] No API or third-party dependencies

## v0.2 — safe declarative tool laboratory
- [x] Candidate manifests and versioned approved manifests
- [x] Deterministic fixture-based tests
- [x] Explicit manual approval after passing tests
- [x] Rollback and local audit log
- [x] No arbitrary generated-code execution

## v0.3 — controlled approved-tool runner
- [x] Run only the active approved manifest
- [x] Validate active pointer and manifest metadata
- [x] Bound runtime input and audit runs

## v0.4 — explicit task orchestration
- [x] List recent tasks
- [x] Require a queued task and explicit tool selection
- [x] Require the tool to have an active approved version
- [x] Save results and terminal status to SQLite
- [x] Prevent rerunning completed or failed tasks
- [x] Recover stale running tasks as failed without resuming them
- [x] Tests for success, failure, duplicate execution, and recovery

## v0.5 — memory and task management
- [x] Search and inspect tasks without executing them
- [x] Safe manual task transitions with terminal-state protection
- [x] Search and list local memories
- [x] SQLite audit events for task/memory creation and allowed task status changes
- [x] Tests for search, status rules, and audit records

## v0.6 — deterministic local planning (in progress)
- [x] Generate reviewable step-by-step draft plans from goal templates
- [x] Attach a plan to an existing task without changing its status
- [x] Explicit plan approval with audit event
- [x] No tool execution from planning or approval
- [x] Tests for classifications, validation, and audit records

## Later
- [ ] Better goal parsing and clarification questions
- [ ] Plan editing and per-step progress tracking
- [ ] Link plan steps to approved tools with explicit per-step approval
- [ ] Provider-neutral adapter (optional; local core does not require an API)
- [ ] Explicit data-egress consent and redaction before any remote provider
- [ ] Android UI and visible agent status
- [ ] Optional offline local model if hardware permits
- [ ] User-controlled emergency stop
- [ ] Restricted integration with selected local files
