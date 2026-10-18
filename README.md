# NEO-LOCAL Core

Local-first Python and SQLite kernel for Android/Termux. No API and no third-party Python dependencies.

## Core
```bash
python core.py init
python core.py status
python -m unittest discover -s tests -v
```

## Safe tool lab
Candidates are declarative JSON manifests, not generated Python source. Only operations in the built-in allowlist can run.

```bash
python tool_lab.py create count_demo --operation word_count --sample "hello world"
python tool_lab.py test count_demo
python tool_lab.py approve count_demo
python tool_lab.py list
python tool_lab.py run count_demo "hello from NEO-LOCAL"
```

Supported operations: `word_count`, `uppercase`, `prefix`. Inputs are limited to 4000 characters. Only the active approved version runs; approval is explicit and rollback is available.

## Explicit task execution
Tasks are never run automatically. Create a task, inspect the task list, and explicitly select an approved tool and input:

```bash
python core.py task "Count words in a text"
python task_runner.py list
python task_runner.py run 1 count_demo "hello world"
python core.py status
```

Replace `1` with the ID printed when your task was created. A successful run saves the result and marks the task completed. A failed run marks it failed. A task that is not queued cannot run again. No arbitrary shell or generated Python is executed.

## Security boundary
This is a guarded local workflow, not an OS-level sandbox. Do not pass private information to tools unless you intend to process it locally. The local SQLite database is not encrypted by this program.
