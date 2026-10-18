# Security model

## v0.1 guarantees and limits
- The core has no network client and makes no API calls.
- SQLite queries use parameters rather than string interpolation.
- The tool registry is hard-coded; files in the repository are not dynamically imported or executed.
- No arbitrary shell command is exposed by the CLI.
- Local memory is stored under `~/.neo_local` by default; the app attempts to restrict the directory to owner-only permissions.

## Important limits
- Termux and Android permissions still govern device access.
- A local database is not encrypted by this program. Device lock and Android storage protections matter.
- A static source-code scan cannot prove arbitrary Python code safe.
- Future generated tools must be tested in a separate, restricted process and must not be promoted automatically based only on successful syntax compilation.
- Never send secrets, private files, or the API key to a remote model unless the user explicitly approves the exact data flow.

## Promotion policy for future versions
1. Save generated code to the sandbox only.
2. Run syntax and policy checks.
3. Run tests using dummy data in a restricted environment.
4. Show the diff and test results.
5. Require explicit approval before promotion.
6. Keep the previous version for rollback.
