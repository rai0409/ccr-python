# CCR Python Runtime Specification
# CCR Python Runtime Specification

## SECTION 1 — SYSTEM GOAL

Purpose:
Build a Python clean-room CLI runtime that provides a high-fidelity headless coding-agent system with:

* deterministic event-driven orchestration
* local tool execution
* explicit permission model
* append-only transcript
* resumable sessions
* robust retry / fallback / interrupt handling

v1 scope:

* headless CLI only
* local tools only
* deterministic runtime guarantees

Excluded:

* TUI
* plugin ecosystem
* full MCP runtime
* OS-level sandbox

---

## SECTION 2 — PROJECT LAYOUT

ccr-python/
src/ccr/
cli/
runtime/
model/
tools/
policy/
storage/
sandbox/
mcp/
contracts/
util/
tests/
fixtures/
docs/

Rules:

* CLI contains no business logic
* runtime does not mutate filesystem directly
* tools are the only side-effect layer
* storage is append-only

---

## SECTION 3 — CORE PRINCIPLES

* event-driven architecture
* append-only persistence
* deterministic execution
* explicit permissions
* resumability by reconstruction

---

## SECTION 4 — CLI CONTRACT

Binary:
ccr

Commands:

* ccr [prompt]
* ccr --print [prompt]
* ccr sessions list
* ccr sessions show <id>

Flags:

* --permission-mode {ask,auto,bypass}
* --resume
* --continue
* --fork-session
* --session-id
* --output-format {text,json,stream-json}
* --input-format {text,stream-json}

Rules:

* invalid flag combinations = exit 2
* no-session-persistence cannot be used with resume/continue

---

## SECTION 5 — EVENT MODEL

All events include:

* event_id
* session_id
* run_id
* seq
* ts
* type
* turn_index

Terminality:

* session_completed / session_failed are run-scoped

Tool lifecycle:

1. tool_call_requested
2. tool_permission_required (optional)
3. tool_permission_decided (required)
4. tool_execution_started
5. tool_result (terminal payload)
6. tool_execution_finished

---

## SECTION 6 — TRANSCRIPT SCHEMA

JSONL (append-only)

Fields:

* record_id == event_id
* parent_id == parent_event_id
* session_id
* run_id
* seq
* payload

Guarantees:

* append-only
* fsync per write
* crash tail truncation
* dedupe by event_id

Resume rules:

* reconstruct last stable turn
* incomplete tool calls → cancelled

---

## SECTION 7 — PERMISSION MODEL

Modes:

* ask
* auto
* bypass

Precedence:

1. hard boundary
2. explicit deny
3. explicit allow
4. safe-read fastpath
5. bypass
6. classifier
7. default ask

Safe-read:

* read-only
* non-dangerous
* within workspace

Decision scopes:

* once
* session
* persist

---

## SECTION 8 — TOOL CONTRACT

All tools must:

* validate input schema
* return structured result
* never bypass permission

Envelope:

* status
* stdout/stderr
* files_read/write
* diff
* error
* permission metadata

---

## SECTION 9 — BUILT-IN TOOLS

* Read
* LS
* Glob
* Grep
* Bash
* Edit
* Write

Constraints:

* deterministic output
* bounded size
* strict ordering

---

## SECTION 10 — RETRY / FALLBACK

Retry:

* exponential backoff
* max 5 primary + 3 fallback

Fallback:

* triggered on 429/529
* emitted once per turn

Interrupt:

* cancels model + tools
* persists checkpoint
* resumable

---

## SECTION 11 — SANDBOX

v1:

* path boundary enforcement
* command guard

v2:

* full isolation (future)

---

## SECTION 12 — MCP PLAN

v1:

* disabled

v1.5:

* stdio integration

v2:

* full MCP runtime

---

## SECTION 13 — TEST STRATEGY

Includes:

* CLI tests
* permission tests
* tool tests
* golden transcripts
* fault injection
* resume tests

---

## SECTION 14 — IMPLEMENTATION PHASES

Phase 0: schema
Phase 1: runtime loop
Phase 2: tools + permission
Phase 3: transcript + resume
Phase 4: retry/interrupt
Phase 5: hardening

---

## SECTION 15 — NON-GOALS

* UI
* plugins
* distributed execution

---

## SECTION 16 — ASSUMPTIONS

* single-user local runtime
* deterministic classifier
* append-only storage

---

## SECTION 17 — SUMMARY

This system is a deterministic, resumable, headless coding-agent runtime with:

* strict event model
* explicit permission control
* reproducible execution
* durable transcripts

