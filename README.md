# NEO-LOCAL Core

Local-first Python and SQLite kernel for Android/Termux. No API and no third-party Python dependencies.

## Core
```bash
python core.py init
python core.py status
python -m unittest discover -s tests -v
```

## v0.2 Safe tool lab
The tool lab accepts **declarative JSON manifests**, not generated Python source. It only runs operations already implemented in an explicit allowlist. A separate folder is not a security sandbox, so arbitrary candidate code is deliberately not executed.

Create a candidate, test it, and only then explicitly approve it:

```bash
python tool_lab.py create count_demo --operation word_count --sample "hello world"
python tool_lab.py test count_demo
python tool_lab.py approve count_demo
python tool_lab.py list
```

Supported operations: `word_count`, `uppercase`, `prefix`. The prefix operation accepts `--limit 1..500`.

Approved versions are stored under `~/.neo_local/tool_lab/approved/`; candidates and an audit log are stored under `~/.neo_local/tool_lab/`. Approval is an explicit command and never happens automatically. Rollback switches the active-version pointer to the previous approved manifest:

```bash
python tool_lab.py rollback count_demo
```

This first lab proves the candidate/test/approval/version/rollback workflow. It does **not** dynamically load or execute newly generated code; expanding the operation allowlist requires a reviewed code change and tests.
