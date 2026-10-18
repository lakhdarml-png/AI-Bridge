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

## Later
- [ ] Provider-neutral adapter (optional; local core does not require an API)
- [ ] Explicit data-egress consent and redaction before any remote provider
- [ ] Android UI and visible agent status
- [ ] Optional offline local model if hardware permits
- [ ] User-controlled emergency stop
- [ ] Restricted integration with selected local files
