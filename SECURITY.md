# Security model

## v0.1 core
- No network client or API calls.
- Parameterized SQLite queries.
- No arbitrary shell command exposed by the CLI.
- Local database is not encrypted by this program.

## v0.2 tool laboratory
- Candidate tools are JSON manifests, not executable source code.
- Only explicitly allowlisted built-in operations can run.
- Candidate fixtures are compared against deterministic outputs.
- Approval requires a separate explicit command and passing tests.
- Approved manifests are versioned; rollback changes the active pointer.
- Audit events are appended locally.

## v0.3 approved runner
- Only the active version of a manifest marked approved can run.
- Active pointer is restricted to a version filename, not an arbitrary path.
- Manifest name, approval status, and version number are checked before execution.
- Each invocation accepts at most 4000 characters.
- Runs and failed operations are recorded in the local audit log.
- These controls reduce risk but are not an operating-system sandbox.

Never send secrets, private files, or API keys to a remote model unless the user explicitly approves the exact data flow.
