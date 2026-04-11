# Phase 2C Prompt A active scope

## objective
Add the smallest vertical slice for session-scoped interactive permission replay.

## in scope
- accept `allow_session` / `deny_session` from stream-json `permission_decision`
- apply immediate decision to the current tool call
- keep session-local replay rules in memory only
- replay matching session rules for later compatible checks in the same session
- preserve existing Phase 2B behavior (`allow_once` / `deny_once`, ask-unavailable fallback)

## out of scope
- `allow_persistent` / `deny_persistent`
- persistent rule files, persistent replay, or transcript-backed reconstruction
- audit log system
- tool capability expansion (Bash/Edit/Write runtime widening)
- resume/recovery redesign

## required behavior
- `allow_session`: allow now and replay allow for matching later requests in this session
- `deny_session`: deny now and replay deny for matching later requests in this session
- replay is deterministic and session-local only
- hard boundary deny remains higher priority than replayed allow
- if both replayed deny and allow could match, deny wins

## stop conditions
- do not add persistent storage or persistent replay
- do not redesign transcript/event model
- do not broaden policy architecture beyond session-local replay

## acceptance criteria
- all existing Phase 2B behavior remains green
- session replay works for `allow_session` / `deny_session`
- no persistent scope is introduced
- full test suite remains green
