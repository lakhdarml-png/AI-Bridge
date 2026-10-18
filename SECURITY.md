# Security model

## Core
- No network client or API calls.
- Parameterized SQLite queries.
- No arbitrary shell command exposed by the CLI.
- Local SQLite database is not encrypted by this program.

## Tool lab and runner
- Candidates are JSON manifests, not executable source code.
- Only explicitly allowlisted built-in operations can run.
- Approval requires a separate explicit command and passing deterministic tests.
- The active pointer and manifest metadata are checked before each run.
- Runtime input is limited to 4000 characters.
- Tool execution and task outcomes are logged locally.

## Task orchestration
- Queued tasks never execute automatically.
- A user must explicitly provide task ID, approved tool name, and input.
- Only queued tasks can start; terminal tasks cannot be run again.
- Results are saved locally. This is not an operating-system sandbox, and the database is not encrypted by this program.

Never send secrets, private files, or API keys to a remote model unless the user explicitly approves the exact data flow.
