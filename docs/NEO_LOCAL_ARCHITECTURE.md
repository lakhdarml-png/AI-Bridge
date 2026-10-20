# NEO-LOCAL — Target Architecture

## Purpose
Build a practical, resumable, local-first AI agent that runs on Android through Termux. The system must take a user goal from intake through planning, controlled execution, verification, and delivery. It must not confuse successful code execution with successful completion of the user's goal.

## Engineering rules
1. Inspect and reuse the current implementation before replacing modules.
2. Keep changes small enough to review, but integrate by capability rather than endlessly polishing isolated functions.
3. Keep the stable branch untouched; develop on `neo-local-v1-integration`.
4. No claim of completion without evidence from the relevant end-to-end acceptance test.
5. Do not run the same side-effecting task through multiple runners.
6. Persist state before/after meaningful transitions; support recovery after interruption.
7. Default to deny: tools are allowlisted, arguments validated, and risky actions require explicit approval.
8. Avoid heavy dependencies unless a demonstrated need outweighs Termux installation cost.
9. Secrets, tokens, and private runtime data must not be committed.
10. Every tool has a declared input contract, output contract, side-effect level, and verification strategy.

## Target component boundaries
- **Core / persistence:** SQLite state, transactions, migrations, task and plan records, audit events.
- **Goal intake:** normalize a goal, classify it, capture constraints, and define a measurable final acceptance condition.
- **Planner:** produce a bounded plan with dependencies, required inputs, expected outputs, risk, and verification criteria per step.
- **Tool registry:** allowlisted tools with schemas, argument validation, timeouts, output limits, and side-effect metadata.
- **Runner / scheduler:** execute eligible steps exactly once where possible; record attempts, checkpoints, results, and failures.
- **Verifier:** verify tool output against the tool's own contract and the step's acceptance condition. Semantic checks must not substitute a different definition from the implementation.
- **Recovery:** resume from persisted state, detect incomplete/running steps, and avoid blind retries for non-idempotent actions.
- **Memory:** distinguish durable user/project facts from task logs and temporary working context; provide explicit provenance and bounded retrieval.
- **Termux bridge:** narrow allowlisted operations only; no arbitrary shell endpoint.
- **Interface:** CLI first for reliability; dashboard is a presentation layer over the same API and state, not a second workflow engine.
- **Observability:** concise task timeline, state transition log, tool output summaries, errors, and final delivery report.

## Canonical lifecycle
`received → clarified (if needed) → planned → awaiting_approval → ready → running → verifying → completed`
Failure paths must be explicit: `waiting_input`, `blocked`, `failed`, and `cancelled`. Terminal states must not be inferred from one successful step.

## Completion contract
A task is complete only when:
- all required plan steps are completed or explicitly waived with a recorded reason;
- each required output passes its defined verification;
- the goal-level acceptance criteria pass;
- the final artifact/result is stored and reported;
- no unresolved blocker is hidden.

## Safety boundaries
- No arbitrary shell command exposed through the bridge.
- Read-only inspection before file mutation or external side effects.
- Explicit approval before destructive, external, or irreversible operations.
- Bounded retries, timeouts, and output sizes.
- Redact secrets from logs and prevent secret files from entering Git.

## Integration approach
The existing local modules are the source of truth for implementation details until inspected. Known modules include `core.py`, `memory_manager.py`, `plan_manager.py`, `plan_runner.py`, `task_manager.py`, `task_runner.py`, `termux_bridge.py`, `tool_lab.py`, `web_dashboard.py`, and `workflow_engine.py`. Preserve working behavior and migrate only where an identified architectural gap requires it.

## Definition of done for the architecture phase
- Current modules and dependencies are mapped from actual source.
- Current state transitions and schemas are documented from actual source.
- A single end-to-end acceptance test is defined.
- Integration gaps are ranked by user impact and risk.
- No broad rewrite begins until the inventory is complete.
