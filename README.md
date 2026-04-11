# ccr-python

Commercial-grade clean-room runtime core for headless coding agents in Python.

## What this is

`ccr-python` is a clean-room implementation project for a **headless coding-agent runtime** with a strong emphasis on:

- deterministic runtime behavior
- append-only transcript persistence
- explicit permission decisions
- auditable tool execution lifecycle
- narrow, testable implementation slices

This repository is designed as the foundation for **commercial agent infrastructure**, not just a toy CLI wrapper.

Its intended use cases include:
- backend execution cores for coding agents
- internal automation runtimes
- auditable tool-calling systems
- permission-gated local development assistants
- future multi-tenant or policy-constrained agent platforms

This project does **not** attempt a direct structural port from an existing TypeScript implementation.
It follows a behavior-first, spec-first, clean-room approach.

## Why it matters

Most agent repos can demo a prompt loop.
Far fewer provide a serious runtime core with:

- append-only event persistence
- deterministic lifecycle ordering
- replayable permission decisions
- explicit workspace boundaries
- mutation-capable local tools
- test-backed runtime invariants

`ccr-python` is aimed at that layer.

## Current Status

Current repository status on `main`:

**A deterministic runtime core with transcript persistence, permission replay, and built-in mutation tools is implemented.**

Implemented now:
- CLI entry and machine-readable I/O modes
- event-driven runtime baseline
- append-only transcript persistence
- session continuity baseline
- permission engine with hard workspace boundary checks
- interactive permission decisions
- session-scoped permission replay
- persistent permission replay
- persistent permission rule storage
- built-in tools:
  - Read
  - LS
  - Glob
  - Grep
  - Write
  - Edit
  - Bash

What is important here:
- the runtime core is real
- the persistence model is real
- the permission/replay model is real
- mutation-capable tool execution is already present

Not complete yet:
- full resume reconstruction
- interrupted turn reconciliation
- real provider client integration
- production-grade retry/fallback/interrupt behavior
- MCP runtime
- full sandbox runtime
- hardened Bash confinement beyond the current narrow baseline

## Product posture

This repository should be read as:

- **usable runtime core** for controlled local agent execution
- **strong internal foundation** for commercial tooling
- **not yet a complete end-user product**
- **not yet a security-complete sandbox**

In other words:
the core is meaningful and real, but some productization and hardening layers are still intentionally unfinished.

## Core capabilities

### 1. Deterministic event-driven runtime
The runtime is built around explicit event envelopes and lifecycle ordering rather than ad hoc callback behavior.

This matters for:
- debugging
- auditability
- replayability
- future recovery/resume behavior

### 2. Append-only transcript persistence
Transcript records are persisted as append-only JSONL events.

The implementation preserves key invariants such as:
- persisted records map directly to event ids
- parent linkage is retained
- stream-only deltas are not incorrectly persisted as transcript records

This is the foundation for:
- audit trails
- session continuity
- future resume/recovery work
- operational debugging

### 3. Permission-gated tool execution
Tool execution is not treated as an unstructured side effect.

The runtime includes:
- hard boundary denial for paths outside workspace root
- allow/deny decisions with structured reason codes
- interactive permission requests
- one-shot decisions
- session replay
- persistent replay

This is the part that turns a CLI demo into a controllable runtime.

### 4. Built-in local tools
The built-in tool stack already includes both read-only and mutation-capable tools:

Read-only:
- Read
- LS
- Glob
- Grep

Mutation / execution:
- Write
- Edit
- Bash

These are integrated through a single executor and lifecycle model.

### 5. Test-backed runtime integrity
The repository already includes tests that cover:
- lifecycle ordering
- permission ask flow
- replay behavior
- precedence rules
- mutation tool behavior
- Bash success/error/timeout paths
- transcript-backed CLI replay behavior

## Current architecture

### Runtime
- `SessionOrchestrator`
- `EventEnvelope`
- `EventBus`
- turn/state baseline
- deterministic lifecycle emission

### Persistence
- append-only transcript store
- session index baseline
- persistent permission rule store

### Policy
- permission engine
- request hashing
- hard-boundary enforcement
- replay precedence

### Tools
- tool registry
- tool executor
- built-in local filesystem and command tools

### Model/provider path
- provider abstraction
- fake/scripted provider path
- minimal stream adapter seam

## What is implemented today

Implemented on `main`:
- CLI parser and entry
- text / json / stream-json I/O modes
- append-only transcript JSONL persistence
- tool lifecycle event persistence
- permission decision persistence
- session and persistent permission replay
- persistent permission rule storage
- Write/Edit/Bash runtime path
- deterministic error handling for common local tool failure paths

## What is intentionally not claimed yet

This repository does **not** yet claim:
- full production recovery semantics
- fully hardened command sandboxing
- real provider parity
- complete commercial deployment packaging
- multi-tenant product surface
- hosted control plane features

Those are future productization layers, not current claims.

## Roadmap direction

The highest-value next steps are:

1. keep docs aligned with `main`
2. harden Bash confinement without widening scope
3. implement the next resume/recovery slice
4. add stronger provider realism later
5. expand retry/fallback/interrupt behavior after recovery boundaries are fixed

## Repository structure

Important paths:

- `src/ccr/cli/`
  CLI parsing and I/O handling

- `src/ccr/runtime/`
  orchestration, events, FSM, event bus

- `src/ccr/storage/`
  transcript persistence, session indexing, permission rule storage

- `src/ccr/policy/`
  permission decision logic

- `src/ccr/tools/`
  tool contracts, registry, executor, built-in tools

- `src/ccr/model/`
  provider abstraction and stream adaptation seams

- `tests/`
  runtime, CLI, storage, and integrity tests

- `docs/`
  specification, current status, and implementation notes

## Development philosophy

This project prioritizes:
- deterministic behavior over cleverness
- append-only persistence over mutable hidden state
- explicit policy over implicit trust
- narrow implementation slices over vague completeness
- test-backed claims over aspirational documentation

## Install

Create a virtual environment and install the project with test dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'

Run tests
pytest -q
Example usage

Text mode:

python -m ccr.cli.main -p "hello"

JSON output mode:

python -m ccr.cli.main -p "hello" --output-format json

Stream-json mode:

printf '{"type":"user_message","content":"hello"}\n' | python -m ccr.cli.main -p --input-format stream-json --output-format stream-json
Limitations

Important current limitations:

provider behavior is still fake/scripted
resume/recovery is incomplete
Bash execution is a narrow baseline, not a full sandbox
real provider integration is incomplete
retry/fallback/interrupt behavior is not yet production-complete
License

This repository is source-available for personal study, research, and evaluation.
Commercial use requires prior written permission and a separate paid license.
See LICENSE for details.
