# Phase 2A active scope

## objective
Implement the smallest high-quality vertical slice that extends the Phase 1 runtime into tool execution without widening into later-phase complexity.

## in scope

### tool stack
- `tools/base.py`
- `tools/registry.py`
- `tools/executor.py`
- built-in read-only tools:
  - Read
  - LS
  - Glob
  - Grep

### permission engine (minimal)
Implement only:
- hard boundary deny
- auto_safe allow
- ask_unavailable deny

### event flow
Add support for:
- `tool_call_requested`
- `tool_permission_decided`
- `tool_execution_started`
- `tool_result`
- `tool_execution_finished`

### transcript behavior
Persist the above tool lifecycle events using existing append-only transcript rules.

### tests
Implement and pass only the Phase 2A subset needed for:
- read-only tool lifecycle
- minimal permission decisions
- deterministic ordering
- transcript persistence shape

## explicitly out of scope
Do not implement yet:
- Bash
- Edit
- Write
- `tool_permission_required`
- persistent rule writes
- session rule replay
- audit log fail-closed
- retry/fallback behavior
- interrupt propagation
- ResumeLoader
- MCP
- real provider client
- full sandbox runtime

## allowed decision reasons in Phase 2A
- `auto_safe`
- `hard_boundary_path_outside_root`
- `ask_unavailable`

## minimum golden targets for Phase 2A
- `event_tool_lifecycle_allow_order`
- `event_tool_lifecycle_deny_order`
- `permission_auto_read_allow`
- `tool_read_truncation`
- `tool_ls_sorted`
- `tool_glob_sorted`
- `tool_grep_ordering`

## implementation rule
If a broad spec or golden item is not in this active scope, it remains frozen but unimplemented for now.
