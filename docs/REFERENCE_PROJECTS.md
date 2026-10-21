# Reference Projects — What to Reuse

The goal is to learn from mature implementations without importing incompatible stacks wholesale.

## Neo (owainlewis/neo)
Repository: https://github.com/owainlewis/neo
Potential lessons: provider-neutral agent loop; composition root; small interfaces; tool registry; explicit approval barriers; resumable local sessions; documented limitations.
Adaptation caution: this project is Go-oriented and designed for repository coding workflows; NEO-LOCAL remains Python/Termux-first unless evidence justifies a language change.

## Termux-AI (opsonusdh/Termux-AI)
Repository: https://github.com/opsonusdh/Termux-AI
Potential lessons: Termux-aware layout; explicit state manager, planner, executor, validator, and memory boundaries.
Adaptation caution: inspect source, license, maintenance, dependencies, and security before borrowing any code.

## Android Local AI Agent (AbuZar-Ansarii/local-AI-Agent)
Repository: https://github.com/AbuZar-Ansarii/local-AI-Agent
Potential lessons: separation between agent logic, Android integration, memory, configuration, and tests.
Adaptation caution: features requiring Ollama, Telegram, or Shizuku are not assumed to be requirements for NEO-LOCAL.

## Evaluation checklist before adopting code
- License permits the intended reuse.
- Repository is maintained enough for the feature being considered.
- Dependencies are viable on Termux/Android ARM.
- Security model matches NEO-LOCAL's allowlist-only bridge.
- A concrete gap in our code is addressed.
- Integration cost is lower than maintaining a small native implementation.
- Any adopted behavior has a test and attribution where required.
