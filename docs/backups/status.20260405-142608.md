# CCR Python Runtime — Status

## frozen decisions

* run_id introduced (run-scoped lifecycle)
* event_id == record_id enforced
* parent_event_id == parent_id enforced
* strict tool lifecycle ordering
* permission precedence fixed
* safe-read fastpath added
* transcript durability (fsync + tail truncation)
* interrupt semantics fixed

## current phase

Spec frozen (post-review integration complete)

## next prompt

B: event / transcript alignment

## unresolved assumptions

* classifier output schema not finalized
* Windows path normalization edge cases
* multi-process access not supported (single writer)
* assistant_delta persistence policy undecided
* external tool provider (MCP) deferred

