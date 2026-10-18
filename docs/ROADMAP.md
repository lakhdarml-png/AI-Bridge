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
- [ ] Broader safe operation interface after review

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
