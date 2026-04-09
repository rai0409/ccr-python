# ccr-python

Python clean-room headless coding-agent runtime.

## Overview

`ccr-python` is a clean-room implementation project for a headless coding-agent runtime in Python.

The project is aimed at reconstructing the behavior of a practical coding-agent core through:
- deterministic event-driven runtime behavior
- append-only transcript persistence
- resumable session-oriented execution
- machine-readable stream output
- narrow, phase-scoped implementation against a broad frozen specification

This repository does **not** attempt a direct structural port from an existing TypeScript implementation.
Instead, it follows a behavior-first and specification-first approach.

## Current Status

Current repository status: **Phase 2B implemented**.

Implemented now:
- CLI parser and entry
- text / json / stream-json I/O modes
- SessionOrchestrator
- EventEnvelope / EventBus
- append-only transcript baseline
- session index baseline
- fake/scripted provider path
- read-only tool execution (Read / LS / Glob / Grep)
- minimal permission decisions (`auto_safe`, `hard_boundary_path_outside_root`, `ask_unavailable`)
- tool lifecycle event persistence
- interactive permission ask flow (`tool_permission_required`) with one-shot `allow_once` / `deny_once`

Not implemented yet:
- interactive permission ask flow
- Bash / Edit / Write execution
- full resume reconstruction
- real provider client
- retry / fallback / interrupt parity
- MCP runtime

## Project Direction

This repository follows a **clean-room runtime** path.

That means:
- the broad intended system behavior is frozen in repository docs
- the broad golden test inventory is also retained
- actual implementation proceeds through **narrow active subsets**
- each implementation phase is intentionally constrained
- later-phase functionality is not implemented early just because the broader spec already defines it

The goal is to keep the long-range runtime design intact while still shipping high-quality incremental slices.

## What Is Implemented Today

### CLI
Implemented:
- `ccr.cli.main.run_cli`
- argument parsing
- input mode selection
- output mode selection
- strict handling for incompatible flag combinations
- basic stream-json control message validation

### Runtime Core
Implemented:
- `SessionOrchestrator`
- `TurnStateMachine` baseline
- `EventBus`
- deterministic event envelope creation
- run-scoped terminality guard
- deterministic tool lifecycle event ordering

### Persistence
Implemented:
- append-only JSONL transcript writing
- `record_id == event_id` for persisted events
- `parent_id == parent_event_id` for persisted events
- `assistant_delta` remains stream-only and is never persisted
- minimal session index update behavior

### Model Path
Implemented:
- provider abstraction
- fake / echo provider
- stream adapter baseline
- minimal retry/fallback seam with no real fallback behavior yet

## What Is Not Implemented Yet

Not yet implemented:
- interactive permission ask flow and rule persistence
- Bash/Edit/Write tool execution
- session and persistent rule handling
- audit log behavior
- full resume reconstruction
- retry/fallback parity
- interrupt propagation
- real provider client integration
- MCP runtime
- full sandbox runtime

## Source of Truth

This repository is governed by the following documents:

- `docs/spec.md`  
  Broad intended runtime specification

- `docs/golden-tests.yaml`  
  Canonical golden behavior inventory

- `docs/status.md`  
  Current execution phase and next implementation target

- `docs/current-implementation.md`  
  What is actually implemented in the repository today

- `docs/phase2-active-scope.md`  
  The next narrow implementation slice

## Repository Structure

Current important paths:

- `src/ccr/cli/`  
  CLI parsing and I/O handling

- `src/ccr/runtime/`  
  orchestration, events, FSM, event bus

- `src/ccr/storage/`  
  transcript persistence and session index baseline

- `src/ccr/model/`  
  provider abstraction and stream adaptation baseline

- `src/ccr/contracts/`  
  schema files used by contract tests

- `tests/`  
  contract, CLI, runtime, storage, and golden tests

- `docs/`  
  broad specification, status, and active scope docs

## Development Philosophy

This project prioritizes:
- deterministic runtime behavior
- append-only state transitions
- narrow implementation scope per phase
- explicit persistence invariants
- spec-first and golden-first iteration
- avoiding speculative future-phase implementation

The broad specification remains intentionally larger than the currently implemented subset.

## Install

Create a virtual environment and install the project with test dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

## Run Tests

Run the full current test suite:

```bash
pytest -q
```

## Example Usage

Text mode:

```bash
python -m ccr.cli.main -p "hello"
```

JSON output mode:

```bash
python -m ccr.cli.main -p "hello" --output-format json
```

Stream-json mode:

```bash
printf '{"type":"user_message","content":"hello"}\n' | python -m ccr.cli.main -p --input-format stream-json --output-format stream-json
```

## Current Limitations

Important current limitations:
- provider behavior is still fake/scripted
- only read-only local filesystem tools are implemented (Read / LS / Glob / Grep)
- permission behavior is intentionally minimal for Phase 2A only
- no full resume loader exists yet
- current correctness claims apply to the Phase 2A active slice only

## Next Step

The next implementation target is **Phase 2B+**.
Phase 2B remains intentionally limited to:
- Read
- LS
- Glob
- Grep
- hard boundary deny
- auto_safe allow
- ask_unavailable deny
- one-shot interactive permission resolution (`allow_once`, `deny_once`)

## Notes

This repository is meant to evolve through constrained, auditable phases.
If you are reading the broad spec, treat it as the intended destination, not as a claim that all features are already implemented.


## License

This repository is source-available for personal study, research, and evaluation.
Commercial use requires prior written permission and a separate paid license.
See `LICENSE` for details.
