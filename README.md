# NEO-LOCAL

A local-first, resumable personal agent for Android/Termux. The target workflow is to understand a goal, plan, execute approved allowlisted tools, verify the result, recover safely from interruptions, and deliver a clear report.

> Active work branch: `neo-local-v1-five-layer-blueprint`. The stable branch remains unchanged. This branch contains the five-layer blueprint and the first source-level Android-to-Termux core-status connection; the connection has not yet been built or verified on a physical phone.

## Engineering principles
- Evidence over assumptions.
- End-to-end capability over file count.
- Reuse the existing Termux implementation before rewriting it.
- Explicit state transitions and goal-level acceptance criteria.
- Allowlisted tools, bounded execution, auditability, and approval for risky actions.
- No success claim without relevant test evidence.
- Local-only functionality remains independent of optional API providers.
- Explicit approval before sensitive changes, deletion, external actions, or permission changes.

## Architecture and plan
- [Target architecture](docs/NEO_LOCAL_ARCHITECTURE.md)
- [Five-phase delivery roadmap](docs/NEO_LOCAL_ROADMAP.md)
- [Five-layer implementation blueprint](docs/NEO_LOCAL_FIVE_LAYER_BLUEPRINT.md)
- [Reference-project review](docs/REFERENCE_PROJECTS.md)

## Current implementation snapshot
- Python core, planning/task modules, tools, bridge, and tests exist in this branch.
- The Termux bridge remains bound to `127.0.0.1:8766` and accepts only registered actions; a fixed read-only `core_status` action has been added.
- The Android UI now has a button to request core status from the local bridge and display the response or a connection error.
- Android network cleartext permission is scoped to the loopback address in a network security configuration.
- These source changes are **implemented in this branch**, but Android build, bridge-to-app integration, and physical-device behavior remain **not yet verified**.
- The GitHub snapshot may not include unpushed commits from the user's separate Termux working branch.

## First use of the new connection
1. In Termux, enter the project directory that contains `termux_bridge.py`.
2. Run `python termux_bridge.py` and leave that session running.
3. Open the built Android app and tap **فحص اتصال النواة المحلية**.
4. A connection failure should be reported clearly; do not treat a source edit as proof that the integration works.

## Development rule
Keep the stable branch intact. Use focused commits and verify changes on the phone before calling them complete. Do not expose arbitrary shell execution through the bridge.
