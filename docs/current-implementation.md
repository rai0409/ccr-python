# ccr-python current implementation

## summary
`ccr-python` is currently at **Phase 2B implemented** status.

The repository contains a runnable clean-room headless runtime core with:
- CLI parsing and entry
- text / json / stream-json I/O handling
- deterministic event envelopes
- append-only transcript baseline
- session index baseline
- fake/scripted provider path
- read-only tool execution (Read / LS / Glob / Grep)
- minimal permission decisions (`auto_safe`, `hard_boundary_path_outside_root`, `ask_unavailable`)
- tool lifecycle event persistence
- interactive permission ask flow with one-shot stream-json decisions (`allow_once`, `deny_once`)

This repository does **not** yet implement the full runtime described by the broad spec.

## implemented now

### CLI
- `ccr.cli.main.run_cli`
- argument parsing
- input mode handling
- output mode handling
- basic validation for incompatible flag combinations
- stream-json control message type validation

### runtime core
- `SessionOrchestrator`
- minimal `TurnStateMachine`
- `EventBus`
- `EventEnvelope`
- run-scoped terminality guard

### persistence baseline
- append-only transcript JSONL writes
- `record_id == event_id` on persisted records
- `parent_id == parent_event_id` on persisted records
- `assistant_delta` remains stream-only and is never persisted
- minimal session index update

### model path
- provider abstraction
- fake / echo provider
- minimal stream adapter
- minimal retry/fallback seam with Phase 1 no-op behavior

## not yet implemented

### tools
Implemented:
- Tool contracts / registry / executor for read-only tools
- Read / LS / Glob / Grep runtime path

Not yet implemented:
- Bash / Edit / Write runtime path

### permission engine
Implemented (Phase 2B minimal):
- hard boundary deny
- auto_safe allow
- ask_unavailable deny
- askable intermediate decisions (`mode_ask`, `auto_requires_user`) for interactive resolution

Not yet implemented:
- rule store
- audit log
- session/persistent rule replay

### resume / recovery
Not yet implemented:
- full resume reconstruction
- interrupted turn reconciliation
- transcript tail truncation recovery
- fork-session behavior beyond minimal planning assumptions

### resilience
Not yet implemented:
- real retry policy
- fallback model behavior
- interrupt propagation
- timeout handling
- tool cancellation

### external integration
Not yet implemented:
- real provider client
- MCP runtime
- full sandbox runtime

## current correctness claims
The current implementation is intended to satisfy the Phase 2B active slice:
- text/json/stream-json CLI path
- one-turn assistant round-trip
- append-only transcript baseline
- session/run identity allocation
- stream-only assistant_delta behavior
- read-only tool lifecycle ordering and persistence
- minimal deterministic permission decisions
- deterministic interactive ask flow with `tool_permission_required` and one-shot resolution

## source of truth
The repository is governed by:
- `docs/spec.md` for broad intended runtime behavior
- `docs/golden-tests.yaml` for canonical golden test definitions
- `docs/status.md` for current execution phase and next implementation target

## next target
Next implementation target is **Phase 2C+** (frozen until activated).
