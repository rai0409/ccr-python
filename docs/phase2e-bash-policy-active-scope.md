# objective
- Define the active scope for Phase 2E as the smallest viable Bash policy/confinement increment on top of the already hardened Bash tool path.
- Lock boundaries before implementation so Phase 2E remains policy/confinement only.

# current baseline
- Phase 2B Prompt A behavior is present: `allow_session` / `deny_session` with session-id scoped, process-local in-memory replay.
- Phase 2B Prompt B behavior is present: `allow_persistent` / `deny_persistent` with minimal file-based persistent replay.
- Mixed-source replay precedence and deny-over-allow behavior are already covered by existing tests.
- Phase 2D tool runtime coverage is present for `Write`, `Edit`, and `Bash`.
- `Bash` already uses argv-style execution (`shlex.split(command)` + `subprocess.run(..., shell=False, cwd=context.cwd, timeout=fixed)`).
- Shell metacharacter compatibility is already intentionally reduced by the argv-only execution model.
- Bash timeout handling and basic execution-failure normalization are already implemented.

# in scope
- Clarify Bash as minimal argv execution, not a full shell abstraction.
- Define what Bash is allowed to do in this repository under current policy expectations.
- Clarify the next required degree of workspace confinement for Bash in a narrow, incremental way.
- Clarify which command surface remains intentionally unsupported in Phase 2E.
- Define what is boundary-setting for this phase versus deferred work.
- Preserve existing permission and replay flow unchanged while tightening policy/confinement boundaries.

# out of scope
- Turning Bash into a full shell abstraction.
- Shell UX redesign.
- PTY support.
- Interactive terminal support.
- Shell session state.
- Streaming subprocess output.
- Background jobs.
- Job control.
- Full sandbox subsystem.
- Broad OS-level isolation platform.
- Broad allowlist/denylist command policy framework.
- Provider redesign.
- Runtime redesign.
- Transcript or event model changes.
- Retry/fallback redesign.
- Repo context integration.
- Git integration.
- Planning/task systems.
- Broad mutation redesign.

# required behavior
- Phase 2E is policy/confinement only and must not become a Bash redesign.
- Existing `allow_once` / `deny_once` behavior must remain unchanged.
- Existing `allow_session` / `deny_session` behavior must remain unchanged.
- Existing `allow_persistent` / `deny_persistent` behavior must remain unchanged.
- Existing replay semantics and mixed-source precedence behavior must remain unchanged.
- Existing transcript/event invariants must remain unchanged.
- Existing `Write` / `Edit` behavior must remain unchanged.
- Existing Bash hardening must be preserved: argv-style execution, reduced metachar behavior, timeout, and normalized failure paths.

# confinement boundary
- Current `cwd`-based execution is not equivalent to full workspace confinement.
- Bash remains higher-risk than `Write`/`Edit` because command strings can express broader actions.
- Phase 2E must stay narrow and incremental rather than complete.
- Phase 2E must not attempt full OS-level isolation.
- Any confinement improvement in this phase must avoid broad infrastructure or platform redesign.
- Narrow, explicit boundary-setting is preferred over broad coverage.

# stop conditions
- Stop if scope drifts into concrete implementation architecture.
- Stop if scope expands into future phases beyond Phase 2E.
- Stop if scope expands into sandbox platform engineering, terminal UX, repo/git integration, or orchestration redesign.
- Stop if changes would alter permission semantics, replay semantics, transcript/event invariants, or mutation-tool behavior.

# acceptance criteria
- Bash policy/confinement scope is narrowed with no broad redesign.
- Existing Bash hardening remains intact.
- No `shell=True` execution behavior is introduced.
- No PTY or interactive terminal support is introduced.
- No background job model or job control is introduced.
- Existing permission behavior (`allow_once/deny_once`, `allow_session/deny_session`, `allow_persistent/deny_persistent`) remains unchanged.
- Existing replay behavior and mixed-source precedence remain unchanged.
- Existing transcript/event invariants remain unchanged.
- `Write` and `Edit` behavior remains unchanged.
- No broad sandbox/runtime subsystem is introduced.
- Repository tests remain green.
