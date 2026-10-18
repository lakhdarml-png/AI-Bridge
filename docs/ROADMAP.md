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
- [x] Rollback to previous approved manifest
- [x] Local audit log
- [x] No arbitrary generated-code execution

## v0.3 — controlled approved-tool runner
- [x] Run only the active approved manifest
- [x] Validate active pointer, manifest name, status, and version
- [x] Bound runtime input size
- [x] Audit tool runs and failures
- [x] Tests for approval gates, path traversal, and input limits
- [ ] Broader safe operation interface after review

## v0.4 — task orchestration
- [ ] Task listing and status transitions
- [ ] Explicit mapping from tasks to approved tools
- [ ] No unattended execution of queued tasks
- [ ] Execution receipts linked to task IDs

## Later
- [ ] Provider-neutral adapter (optional; no API required for local core)
- [ ] Explicit allowlist of data permitted to leave device
- [ ] Redaction and per-request consent
- [ ] Android UI and visible agent status
- [ ] Optional offline local model if hardware permits
- [ ] User-controlled emergency stop
- [ ] Restricted integration with selected local files
