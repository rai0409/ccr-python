# ccr-python status

## current phase
Phase 1 implemented. Next step: Phase 2A (read-only tools + minimal permission engine).

## frozen decisions
- Broad spec is intentionally maintained.
- Broad golden-tests inventory is intentionally maintained.
- Active implementation must proceed by narrow subsets only.
- Phase 1 includes transcript durability:
  - append-only transcript write
  - seq allocation
  - parent linkage
  - assistant_delta is stream-only and never persisted
  - minimal single-writer safety
  - session index update
  - full resume reconstruction is out of Phase 1
- provider_client.py is not part of Phase 1:
  - use provider abstraction + fake/scripted provider only
  - create no concrete network client in Phase 1
  - seam/stub only if the file tree requires it
- Golden source-of-truth:
  - docs/golden-tests.yaml is canonical
  - fixtures/golden/golden_inventory_v1.yaml is derived test input
  - derived fixture files must not become the authoritative source

## current state
- Clean-room / behavior-first direction fixed
- Unified spec treated as source of truth
- Golden test spec treated as source of truth
- Phase 1 runnable core implemented
- Current implemented core includes:
  - CLI parser and entry
  - text/json/stream-json I/O modes
  - SessionOrchestrator
  - EventEnvelope / EventBus
  - append-only transcript baseline
  - session index update / continue baseline
  - fake provider path
- Not yet implemented:
  - tool stack
  - permission engine behavior
  - full resume reconstruction
  - real provider client
  - full retry/fallback/interrupt behavior

## next implementation target
Phase 2A:
- Tool contracts
- Tool registry
- Tool executor
- Read / LS / Glob / Grep
- Minimal permission engine
  - hard boundary deny
  - auto_safe allow
  - ask_unavailable deny
- Tool lifecycle event persistence

## unresolved assumptions
- stream-json permission_decision payload finalization beyond Phase 2A
- full source priority ordering final confirmation
- tool concurrency policy beyond read-only group behavior
- build/release metadata not yet fixed

## implementation order
1. Maintain broad spec and broad golden inventory unchanged
2. Introduce current-implementation document
3. Introduce Phase 2A active-scope document
4. Tag or subset golden tests for Phase 2A
5. Implement Phase 2A only
6. Run Phase 2A subset
7. Audit lifecycle invariants before moving to Phase 2B

## stop conditions
Do not begin:
- Bash
- Edit
- Write
- persistent/session rule persistence
- audit log fail-closed
- full resume loader
- retry/fallback parity
- interrupt propagation
until Phase 2A gates are green
