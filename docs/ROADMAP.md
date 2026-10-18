# NEO-LOCAL roadmap

## v0.1 — local kernel
- [x] SQLite task and memory store
- [x] Minimal CLI
- [x] One deterministic built-in tool
- [x] Unit tests and CI workflow
- [x] No API or third-party dependencies

## v0.2 — safe tool laboratory
- [ ] Tool manifest and versioned candidate files
- [ ] Test harness with timeouts and fixture-only input
- [ ] Diff report and manual promotion
- [ ] Rollback to last approved tool
- [ ] Audit log for every tool run

## v0.3 — provider adapter
- [ ] Provider-neutral interface
- [ ] API key loaded from local environment/config, never committed
- [ ] Explicit allowlist of data permitted to leave device
- [ ] Redaction and per-request consent

## Later
- [ ] Android UI and visible agent status
- [ ] Optional offline local model if hardware permits
- [ ] User-controlled emergency stop
- [ ] Restricted integration with selected local files
