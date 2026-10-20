# NEO-LOCAL

A local-first, resumable AI agent for Android/Termux. The objective is an end-to-end workflow: accept a goal, plan, execute approved allowlisted tools, verify the result, recover safely from interruptions, and deliver a clear report.

> Development is underway on `neo-local-v1-integration`. This branch is an integration workspace; it does not claim that the complete runtime has already been imported or validated.

## Engineering principles
- Evidence over assumptions.
- End-to-end capability over file count.
- Reuse the existing Termux implementation before rewriting it.
- Explicit state transitions and goal-level acceptance criteria.
- Allowlisted tools, bounded execution, auditability, and approval for risky actions.
- No success claim without relevant test evidence.

## Documents
- [Target architecture](docs/NEO_LOCAL_ARCHITECTURE.md)
- [Delivery roadmap](docs/NEO_LOCAL_ROADMAP.md)
- [Reference-project review](docs/REFERENCE_PROJECTS.md)

## Current status
The branch establishes the target architecture and delivery gates. The next step is to inventory the actual NEO-LOCAL source from the Termux working directory, then implement the highest-impact integration gap. The source files must be transferred from the actual local project; they are not assumed to exist in this repository yet.

## Development rule
Keep the stable branch intact. Use focused commits and verify changes on the phone before calling them complete.
