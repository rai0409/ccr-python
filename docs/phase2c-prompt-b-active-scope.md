# Phase 2C Prompt B active scope

## objective
Define the smallest viable vertical slice for persistent permission replay on top of Prompt A, without widening architecture or runtime surface.

## in scope
- accept `allow_persistent` and `deny_persistent` interactive permission decisions
- apply the immediate decision to the current tool call
- write a replayable persistent rule using the smallest viable persistent store
- replay matching persistent rules on later compatible permission checks
- preserve Prompt A behavior (`allow_once` / `deny_once`, `allow_session` / `deny_session`, session replay)
- preserve deterministic ordering and existing transcript invariants

## out of scope
- broad persistent authorization architecture
- generalized policy language or wildcard-heavy matching expansion
- persistent rule management UI/UX
- deletion or editing of stored rules unless strictly required for this slice
- audit log system
- transcript format changes or transcript-backed rule reconstruction
- session reconstruction/resume redesign
- runtime/provider/tool refactors unrelated to Prompt B
- speculative abstractions for later phases

## required behavior
- `allow_persistent`:
  - immediate tool call is allowed
  - a persistent replayable allow rule is stored
  - later compatible checks can reuse that allow rule
- `deny_persistent`:
  - immediate tool call is denied
  - a persistent replayable deny rule is stored
  - later compatible checks can reuse that deny rule
- precedence remains unchanged:
  - hard boundary deny overrides replayed allow
  - deny wins over allow when both could apply
- existing one-shot and session-scoped decisions remain unchanged:
  - `allow_once` / `deny_once`
  - `allow_session` / `deny_session`

## persistence boundary
- prefer the smallest viable persistent store with minimal write/read path and minimal replay matching
- keep deterministic behavior and narrow scope over extensibility
- do not redesign the policy engine; extend only where required for this slice
- explicitly forbidden in Prompt B:
  - transcript-backed rule reconstruction
  - database adoption
  - broad audit/authorization infrastructure
  - generalized policy language expansion
  - resume/recovery redesign
  - provider/tool capability expansion
  - Bash/Edit/Write runtime expansion
  - MCP or sandbox runtime expansion
  - retry/fallback parity work
  - interrupt propagation
  - multi-turn planning

## stop conditions
- stop if implementation drifts into broad infrastructure or future-phase architecture
- stop if transcript persistence must be redesigned to support Prompt B
- stop if scope expands beyond minimal persistent allow/deny replay behavior

## acceptance criteria
- persistent replay works for `allow_persistent` and `deny_persistent`
- immediate decision behavior and later compatible replay both function deterministically
- hard boundary and deny-over-allow precedence remain correct
- Prompt A behavior remains green with no regressions
- no scope expansion beyond Prompt B active slice
- full test suite remains green without transcript redesign
