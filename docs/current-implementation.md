# ccr-python current implementation

## purpose of this file

This file describes **what is actually implemented on `main`**.

It is intentionally narrower and more concrete than the broad spec.
It should be safe to use this file as the implementation-facing reference for code review, docs review, and planning.

## summary

`ccr-python` currently contains a runnable clean-room headless runtime core with:

- CLI parsing and entry
- text / json / stream-json I/O handling
- deterministic event envelopes
- append-only transcript persistence
- session continuity baseline
- fake/scripted provider path
- tool registry and tool executor
- built-in tools:
  - Read
  - LS
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
- deterministic permission decisions
- interactive ask flow
- session replay and persistent replay for permission decisions
- persistent permission rule storage

This repository does **not** yet implement the full runtime described by the broad spec.

## implemented now

### CLI
Implemented:
- `ccr.cli.main.run_cli`
- argument parsing
- input mode handling
- output mode handling
- validation for incompatible flag combinations
- stream-json control message type validation

### runtime core
Implemented:
- `SessionOrchestrator`
- minimal `TurnStateMachine`
- `EventBus`
- `EventEnvelope`
- run-scoped terminality guard
- deterministic tool lifecycle emission ordering

### persistence baseline
Implemented:
- append-only transcript JSONL writes
- `record_id == event_id` on persisted records
- `parent_id == parent_event_id` on persisted records
- `assistant_delta` remains stream-only and is never persisted
- minimal session index update
- permission metadata persistence on permission decision events
- lock-protected append behavior for transcript writes

### permission engine
Implemented:
- hard boundary deny
- auto_safe allow for safe read tools
- ask-mode intermediate decision
- ask_unavailable deny
- request hashing for permission replay matching

Replay behavior currently implemented:
- session allow replay
- session deny replay
- persistent allow replay
- persistent deny replay
- deny precedence over allow
- hard boundary precedence over replayed allow

Persistent storage currently implemented:
- append/load of persistent permission rules through `permission_rules.jsonl`

### tools
Implemented:
- tool contracts
- tool registry
- tool executor
- Read / LS / Glob / Grep runtime path
- Write runtime path
- Edit runtime path
- Bash runtime path

#### Read / LS / Glob / Grep
These remain the safe-read baseline tools and integrate with the same permission/lifecycle model as the rest of the tool stack.

#### Write
Implemented behavior:
- resolves relative path from `cwd`
- creates parent directories
- writes deterministic UTF-8 text output

#### Edit
Implemented behavior:
- resolves relative path from `cwd`
- rejects missing path
- rejects non-file path
- rejects empty `find`
- replaces the first occurrence only
- returns structured error codes for common failures

#### Bash
Implemented behavior:
- parses command with `shlex.split`
- executes with `subprocess.run(..., shell=False, cwd=context.cwd, capture_output=True, text=True, timeout=...)`
- returns structured timeout / execution / exit-code results
- rejects path-like arguments outside workspace root by the current narrow heuristic

Current Bash status:
- implemented
- test-backed
- intentionally narrow
- not a full sandbox
- not a full shell semantics layer

### model path
Implemented:
- provider abstraction
- fake / echo provider path
- minimal stream adapter seam
- minimal retry/fallback seam with no real fallback behavior yet

### recovery classification slice
Implemented:
- `classify_tool_call_recovery(records, tool_call_id)`
- recovery states are exactly: `completed`, `denied`, `interrupted`, `not_found`
- `classify_tool_call_recovery_from_transcript(store, session_id, tool_call_id)` which only:
  - loads persisted records via `store.load_records(session_id)`
  - delegates to `classify_tool_call_recovery(...)`
- `denied` is the deny terminal path (without execution start), while `interrupted` means execution started and did not finish
- `interrupted` classification means execution started with no execution-finished record; it does not resume execution
- pre-start partial records remain unclassifiable and raise `ValueError`

## implementation-backed correctness claims

The current implementation supports claims about:

- text/json/stream-json CLI execution
- append-only transcript persistence
- session/run identity allocation baseline
- stream-only `assistant_delta` behavior
- deterministic tool lifecycle ordering
- deterministic permission decision persistence
- interactive ask flow with one-shot / session / persistent decisions
- session replay and persistent replay behavior
- recovery classification for a single `tool_call_id` from in-memory records and persisted transcript records
- tool execution success/failure/deny flows for:
  - Read
  - LS
  - Glob
  - Grep
  - Write
  - Edit
  - Bash

## testing-backed areas

The current test surface includes:
- tool lifecycle ordering
- ask flow behavior
- allow_once / deny_once behavior
- allow_session / deny_session replay
- allow_persistent / deny_persistent replay
- deny precedence over allow
- hard-boundary override behavior
- Write success and deny behavior
- Edit success and failure behavior
- Bash success, path rejection, nonzero exit, invalid command, timeout, and deny behavior
- CLI stream-json replay behavior backed by transcript persistence

## commercially relevant interpretation

What is already commercially meaningful:
- a real runtime core exists
- audit-friendly transcript persistence exists
- permission-gated local tool execution exists
- replay semantics exist
- mutation-capable tool execution exists

What is not yet ready to claim as commercially complete:
- full security hardening
- full recovery semantics
- resumable interrupted execution
- automatic retry/re-execution recovery flows
- hosted deployment surface
- real provider parity
- sandbox-complete command execution

## not yet implemented

### resume / recovery
Not yet implemented:
- full resume reconstruction
- interrupted turn reconciliation
- transcript tail truncation recovery
- automatic retry/re-execution orchestration for interrupted tool calls
- richer fork-session behavior beyond current baseline

### resilience
Not yet implemented:
- real retry policy
- real fallback model behavior
- interrupt propagation
- tool cancellation

### external integration
Not yet implemented:
- real provider client
- MCP runtime
- full sandbox runtime

## source of truth

The repository is governed by:
- `docs/spec.md` for broad intended runtime behavior
- `docs/golden-tests.yaml` for canonical golden behavior definitions
- `docs/status.md` for current status and next priority

## immediate priorities

1. keep docs aligned with `main`
2. harden Bash confinement without widening scope
3. define the next resume/recovery slice
4. keep provider realism and retry/fallback as explicit later phases
