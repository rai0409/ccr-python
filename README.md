# ccr-python

Clean-room runtime core for commercial headless coding agents in Python.

## What this is

`ccr-python` is a clean-room implementation project for a **headless coding-agent runtime** built with a strong emphasis on:

- deterministic runtime behavior
- append-only transcript persistence
- explicit permission decisions
- auditable tool execution lifecycle
- narrow, testable implementation slices

This repository is designed as a serious runtime foundation for agent systems, not just a prompt loop or toy CLI wrapper.

It is intended to support use cases such as:
- backend execution cores for coding agents
- internal automation runtimes
- auditable tool-calling systems
- permission-gated local development assistants
- future policy-constrained or multi-tenant agent platforms

This project does **not** attempt a direct structural port from an existing TypeScript implementation.
Instead, it follows a behavior-first, spec-first, clean-room approach.

## Why it matters

Many agent repositories can demonstrate a conversation loop.
Far fewer provide a runtime core with:

- append-only event persistence
- deterministic lifecycle ordering
- replayable permission decisions
- explicit workspace boundaries
- mutation-capable local tools
- implementation-backed test coverage

`ccr-python` is aimed at that layer.

## Current Status

The repository currently contains a **credible deterministic runtime core** on `main`.

Implemented now:
- CLI parser and entry
- text / json / stream-json I/O modes
- SessionOrchestrator
- EventEnvelope / EventBus
- append-only transcript persistence
- session continuity baseline
- fake/scripted provider path
- tool registry and executor
- built-in tool execution for:
  - Read
  - LS
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
- deterministic tool lifecycle persistence
- permission decisions with:
  - hard boundary deny
  - auto_safe allow for safe read tools
  - ask flow
  - ask_unavailable deny
- interactive permission resolution with:
  - allow_once
  - deny_once
  - allow_session
  - deny_session
  - allow_persistent
  - deny_persistent
- session replay of permission decisions
- persistent replay of permission decisions
- persistent permission rule storage

What this means today:
- local tool execution is integrated
- transcript persistence is integrated
- permission gating is integrated
- replay semantics are integrated

What this does **not** mean yet:
- security hardening is complete
- productization is complete
- hosted/runtime operations are complete
- provider realism is complete
- Bash is a full sandbox

## Product posture

This repository should be read as:

- a **usable runtime core** for controlled local agent execution
- a **strong internal foundation** for commercial tooling
- **not yet a complete end-user product**
- **not yet a security-complete sandbox**

The core is real and meaningful, but several hardening and productization layers remain intentionally unfinished.

## Core capabilities

### 1. Deterministic event-driven runtime

The runtime is organized around explicit event envelopes and deterministic lifecycle ordering rather than ad hoc callback behavior.

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

This is the layer that turns a prompt loop into a controllable runtime.

### 4. Built-in local tools

The built-in tool stack already includes both read-only and mutation-capable tools.

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

## What is intentionally not claimed yet

This repository does **not** yet claim:
- full production recovery semantics
- fully hardened command sandboxing
- real provider parity
- complete commercial deployment packaging
- multi-tenant product surface
- hosted control plane features

Those are future productization layers, not current claims.

## Source of truth

This repository is governed by the following documents:

- `docs/spec.md`  
  Broad intended runtime specification

- `docs/golden-tests.yaml`  
  Canonical golden behavior inventory

- `docs/status.md`  
  Current implementation status on `main` and next execution priority

- `docs/current-implementation.md`  
  What is actually implemented on `main`

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
  specification, status, and implementation notes

## Development philosophy

This project prioritizes:
- deterministic behavior over cleverness
- append-only persistence over hidden mutable state
- explicit policy over implicit trust
- narrow implementation slices over vague completeness
- implementation-backed claims over aspirational documentation

## Roadmap direction

The highest-value next steps are:

1. keep docs aligned with `main`
2. harden Bash confinement without widening scope
3. implement the next resume/recovery slice
4. add stronger provider realism later
5. expand retry/fallback/interrupt behavior after recovery boundaries are fixed

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
full resume/recovery is incomplete
Bash execution is intentionally narrow and is not a full sandbox
real provider integration is incomplete
retry/fallback/interrupt behavior is not yet production-complete
License

This repository is source-available for personal study, research, and evaluation.
Commercial use requires prior written permission and a separate paid license.
See LICENSE for details.