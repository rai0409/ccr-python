# ccr-python status

## current phase
Pre-implementation freeze complete. Next step: Prompt F (Phase 1 implementation).

## frozen decisions
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
  - seam/stub only if file tree must exist
- Golden source-of-truth:
  - docs/golden-tests.yaml is canonical
  - fixtures/golden/golden_inventory_v1.yaml is derived test input
  - fixture file must not become the authoritative source

## current state
- Clean-room / behavior-first direction fixed
- Unified spec (A+B+C) treated as source of truth
- Golden test spec (D) fixed
- Prompt E output reviewed
- Phase 1 scope narrowed and frozen

## next prompt
Prompt F:
Implement only the Phase 1 runnable core under the frozen decisions above.

## unresolved assumptions
- stream-json permission_decision payload shape finalization
- source priority ordering (cli/user/system) final confirmation
- tool concurrency policy final confirmation
- build/release metadata not yet fixed

## implementation order
1. Freeze status/spec/golden source-of-truth
2. Run Prompt F for Phase 1
3. Execute minimal Phase 1 test subset
4. Review diffs and invariants
5. Proceed to Phase 2 only after Phase 1 gates are green
