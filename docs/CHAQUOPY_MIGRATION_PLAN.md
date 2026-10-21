# Chaquopy Migration Plan — NEO-LOCAL

**Status:** first embedded-runtime implementation committed to the development branch; CI and phone verification are pending.  
**Working branch:** `neo-local-v1-five-layer-blueprint`  
**Reviewed branch head:** `fd7ee4ad41d5d9e2722790e26f7ae16e3804495b`  
**Stable `main` head at review:** `cf66c77adf7e07dc08305e20aa382e4d05212b96` (must remain unchanged).

## Decision under review

Embed Python in the Android process with Chaquopy, so Kotlin calls the core directly. Do not start an HTTP server or require Termux for core status, task planning, memory, or other supported in-process operations. Termux may remain an optional future integration for tools that genuinely require external executables, but it is not the core transport.

## Compatibility findings

- Android Gradle Plugin is `8.7.3`; app `minSdk` is `26`. Chaquopy's current documentation lists AGP 7.3–9.4 and minimum API 24, so these settings are within the documented range.
- Current app uses Kotlin 2.0.21 and Gradle 8.9 in CI. Keep these unchanged during the first integration unless an actual build failure demonstrates a need to change them.
- Chaquopy 17.1 is the current documented release as of 2026-10-21. It supports Python 3.10–3.15 and AGP 7.3–9.4. Select Python 3.13 for the initial compatibility trial, then pin it explicitly; the core currently uses standard-library modules and does not list third-party Python dependencies.
- Core persistence uses `sqlite3`. The app must set `NEO_LOCAL_HOME` to an app-private directory before importing core modules, so data is persisted under the Android app sandbox and not in Termux's home directory.
- Existing CLI entry points (`argparse`, `sys.argv`, `print`) should not be the Android API. Add a small structured Python facade that returns dictionaries/JSON-safe objects and raises typed errors. Kotlin will invoke these functions on a background executor and render actual returned results.
- The existing bridge and web dashboard rely on HTTP server behavior; these should not be packaged as the core's Android request path. External-process execution, shell commands, and Termux-specific operations are outside the first embedded-core milestone.
- Python's filesystem APIs do not bypass Android's sandbox. App-private files are directly accessible; user-selected project folders should be accessed through Android's Storage Access Framework (SAF), with persisted URI permissions and a Kotlin file adapter exposed to Python if needed. Do not promise arbitrary access to `/data/data/com.termux` or another app's private directory.
- Existing tests use temporary directories and directly mutate core paths. Keep host-side unit tests, add facade and storage-path tests, and add Android instrumentation/smoke tests for Python startup and SQLite persistence.

## Target architecture

```text
Android UI (Kotlin)
  -> CoreFacade (typed request/result, background execution)
      -> Chaquopy Python runtime
          -> neo_local package
              -> task / plan / memory / audit services
              -> allowlisted pure-Python tools
              -> SQLite in app-private storage
  -> Android SAF adapter for explicitly selected project folders
```

No loopback HTTP bridge is needed between the UI and the in-process core. Any future integration that needs another process must be an explicitly separate tool adapter, not a dependency for core operation.

## Migration sequence

### Step 1 — Preserve and map
- Keep this work on `neo-local-v1-five-layer-blueprint`; do not merge or push changes to `main`.
- Record current module dependencies and separate importable core services from CLI/server launchers.
- Preserve a rollback point at the reviewed branch head above.

### Step 2 — Add a canonical Python package
- Introduce `app/src/main/python/neo_local/` as the canonical in-app package.
- Move/refactor the reusable core, task, plan, memory, audit and allowlisted tool logic into package modules.
- Keep thin root-level compatibility entry points temporarily where existing host tests and CLI workflows need them; avoid maintaining two independently edited copies of core logic.
- Exclude the HTTP bridge, web dashboard and CLI-only launchers from the in-process call path.

### Step 3 — Integrate Chaquopy
- Add the Chaquopy plugin version explicitly in the root Gradle plugin declarations and apply it only to `:app`.
- Set Python version explicitly and restrict native ABIs to those required for the target phone, while documenting any device coverage trade-off.
- Keep Android Gradle Plugin, Kotlin, SDK levels and unrelated dependencies unchanged initially.
- Add a small `CoreFacade` which initializes Python once, sets the app-private data directory before importing `neo_local`, and calls only named functions.
- Execute Python calls off the UI thread; bound inputs and outputs; return structured success/error results.

### Step 4 — Define safe project-file access
- Store memory/database/audit data in the app-private files directory.
- For projects outside the app sandbox, use Android's Storage Access Framework and explicit folder selection. Persist only the URI permissions the user grants.
- Provide a narrow file adapter (list/read/search first). Do not expose arbitrary paths or shell commands through the Python facade.
- Require an explicit approval step before any file mutation, deletion, build, or external side effect. Read-only inspection must remain separate from writes.

### Step 5 — Validate before expanding
- CI: run existing Python unit tests, new package/facade tests, and Gradle debug build.
- Android test: initialize Python, query real core status, create/read a task, write/read a memory record, restart the app, and verify persistence.
- Permission test: denied SAF access must produce a clear error and no unauthorized file access.
- Regression test: no bridge process is required for core status or local task/memory functions.
- Only report success for checks that actually ran; physical-device verification remains separate from CI success.

## Implementation notes (first slice)

- Chaquopy `17.1.0` and Python `3.13` are enabled only in the Android app module. The app ABI is initially restricted to `arm64-v8a` for a modern ARM64 phone; this is a build-coverage choice, not a claim of universal device support.
- The existing root `core.py` implementation now lives canonically at `neo_local/core.py`; root `core.py` is a compatibility entry point so existing host imports continue to work.
- `neo_local/android_facade.py` exposes only structured status, task creation, memory creation, and read-only listing. Kotlin sets `NEO_LOCAL_HOME` before importing the core and stores SQLite under the app-private files directory.
- The Android UI no longer requires Termux or a loopback server for these operations. Project-folder SAF access and plan/runner integration remain later steps; no arbitrary shell or filesystem mutation endpoint was added.

## Acceptance gate

The migration is accepted only when the installed app can initialize the embedded Python runtime, call the real core directly, receive structured results, persist its state across restarts, and report permission/runtime failures truthfully—without launching `termux_bridge.py` or contacting `127.0.0.1:8766`.

## Known limitations and decisions

1. Chaquopy embeds Python, not a general-purpose Android permission bypass.
2. The first milestone is local core functions and approved read-only project inspection; launching arbitrary programs or controlling other apps is not implied.
3. Third-party Python packages must be checked individually for Android wheels and ABI compatibility before adding them.
4. No destructive file removal is part of this plan. Existing bridge and dashboard files remain available for rollback until the embedded path is verified and a later removal is explicitly reviewed.

## References

- Chaquopy version compatibility: https://chaquo.com/chaquopy/doc/current/versions.html
- Chaquopy Android/Gradle setup: https://chaquo.com/chaquopy/doc/current/android.html
- Chaquopy project repository: https://github.com/chaquo/chaquopy
