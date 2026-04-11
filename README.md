# ccr-python

Clean-room runtime core for production-oriented headless coding agents in Python.

## TL;DR

- deterministic runtime core
- append-only transcript persistence
- permission-gated tool execution
- replayable decisions (session / persistent)
- mutation-capable local tools (Write / Edit / Bash)

---

## What this is

`ccr-python` is a clean-room implementation of a **headless coding-agent runtime core** with a strong focus on:

- deterministic runtime behavior
- append-only event persistence
- explicit permission decisions
- auditable tool execution lifecycle
- narrow, testable implementation slices

This is not a prompt loop or wrapper.
It is a **runtime layer** intended to sit underneath agent systems.

---

## Who this is for

- engineers building coding-agent backends
- teams building internal automation systems
- developers needing auditable tool execution
- systems requiring permission-gated local execution

---

## Why it matters

Most agent repositories provide:
- chat loop
- tool calling

Very few provide:
- deterministic lifecycle ordering
- replayable permission decisions
- append-only audit trail
- workspace boundary enforcement
- mutation-capable tools with policy control

`ccr-python` is focused on that missing layer.

---

## Current Status

The repository currently contains a **deterministic runtime core with integrated execution, persistence, and policy layers**.

### Implemented

- CLI (text / json / stream-json)
- SessionOrchestrator
- EventEnvelope / EventBus
- append-only transcript persistence
- session continuity baseline
- tool registry + executor

### Built-in tools

Read:
- Read
- LS
- Glob
- Grep

Mutation / execution:
- Write
- Edit
- Bash

### Permission system

- hard boundary deny (workspace root)
- auto_safe allow (read tools)
- ask flow
- ask_unavailable deny

Decision types:
- allow_once / deny_once
- allow_session / deny_session
- allow_persistent / deny_persistent

Replay:
- session replay
- persistent replay
- deny precedence
- hard-boundary precedence

### Persistence

- append-only JSONL transcript
- `record_id == event_id`
- `parent_id == parent_event_id`
- permission decision persistence
- persistent permission rule store

---

## What this means

This runtime already supports:

- controlled local tool execution
- audit-friendly execution logs
- deterministic behavior
- replayable decisions
- mutation-capable workflows

---

## What this does NOT mean (important)

This repository does **not** yet provide:

- full security sandbox
- full recovery/resume semantics
- real provider integration
- production deployment layer
- multi-tenant runtime

Bash execution is intentionally narrow and **not a security sandbox**.

---

## Core capabilities

### 1. Deterministic runtime

Explicit event-driven lifecycle.
No hidden execution paths.

---

### 2. Append-only transcript

- JSONL persistence
- immutable history
- replay-friendly structure

---

### 3. Permission-gated execution

- explicit allow/deny decisions
- replayable policy
- workspace boundary enforcement

---

### 4. Local tool execution

Unified execution model for:

- filesystem tools
- mutation tools
- command execution (Bash)

---

### 5. Test-backed behavior

Coverage includes:

- lifecycle ordering
- permission flow
- replay semantics
- precedence rules
- tool success/failure paths
- Bash timeout/error handling

---

## Architecture

### Runtime
- SessionOrchestrator
- EventEnvelope
- EventBus

### Persistence
- transcript store (append-only)
- session index
- permission rule store

### Policy
- permission engine
- replay matching
- boundary enforcement

### Tools
- registry
- executor
- built-in tools

### Provider
- abstraction layer
- fake/scripted provider

---

## Source of truth

- `docs/spec.md` → full intended behavior
- `docs/status.md` → current implementation state
- `docs/current-implementation.md` → implemented details

---

## Development philosophy

- deterministic over clever
- append-only over mutable state
- explicit policy over implicit trust
- implementation-backed claims only
- narrow scope per iteration

---

## Roadmap direction

1. keep docs aligned with main
2. harden Bash confinement
3. implement resume/recovery slice
4. add provider realism
5. expand retry/fallback later

---

## Install & Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'

Run tests:

pytest -q

Text mode:

python -m ccr.cli.main -p "hello"

Stream-json mode:

printf '{"type":"user_message","content":"hello"}\n' \
| python -m ccr.cli.main -p --input-format stream-json --output-format stream-json
Limitations
provider is fake/scripted
resume/recovery incomplete
Bash is not a sandbox
no hosted runtime layer
License

Source-available for research and evaluation.

Commercial use requires a separate license.
