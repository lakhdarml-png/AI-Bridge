# NEO-LOCAL

A local-first personal agent with a dedicated Android control panel and a Python core.

> Active development branch: `neo-local-v1-five-layer-blueprint`. The stable branch remains unchanged.

## Purpose
NEO-LOCAL is intended to inspect project files, diagnose issues, plan work, execute narrowly allowlisted tasks, verify outcomes, and request explicit approval before sensitive changes. The Android app is a control panel for the NEO-LOCAL core, not a chat-copying utility.

## Architecture and plan
- [Target architecture](docs/NEO_LOCAL_ARCHITECTURE.md)
- [Five-phase delivery roadmap](docs/NEO_LOCAL_ROADMAP.md)
- [Five-layer implementation blueprint](docs/NEO_LOCAL_FIVE_LAYER_BLUEPRINT.md)
- [Reference-project review](docs/REFERENCE_PROJECTS.md)

## Current implementation
- Python core, planning/task modules, allowlisted tools, bridge, and tests.
- Android NEO-LOCAL control panel with **Start bridge**, **Stop bridge**, and **Check connection**.
- Starting and stopping requires confirmation in the Android app.
- The bridge binds only to `127.0.0.1:8766`; it does not accept arbitrary shell commands.
- The legacy copy/paste ChatGPT/Grok screen and its accessibility service have been removed from the Android app.
- GitHub Actions builds the debug APK and runs the Python test suite. A successful CI build does not replace physical-device verification.

## One-time Termux setup
The current Python core runs in Termux. To let the Android panel start it in the background without opening the Termux interface each time:

1. Keep Termux installed and make sure the project folder contains `termux_bridge.py` and `core.py`.
2. In Termux settings, enable **Allow external apps**.
3. Grant NEO-LOCAL the Termux `RUN_COMMAND` permission if Android requests it.
4. In the app, set the actual absolute project directory under Termux's home folder. The initial path shown is only a default and must match the folder on your phone.
5. Tap **تشغيل الجسر**, confirm, then tap **فحص اتصال الجسر والنواة**.
6. To stop the bridge, tap **إيقاف الجسر** and confirm.

If the permission is not enabled, the app must report the failure; it must not claim the bridge started. No arbitrary command execution is exposed by the bridge.

## Safety and development rules
- Preserve the stable branch; work on the development branch until changes are verified.
- Ask before sensitive changes, deletions, permission changes, or external actions.
- Prefer evidence over assumptions and avoid repeated low-value tests.
- Do not claim physical-device behavior is verified until it has been tested on the phone.
