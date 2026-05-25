---
title: Implement surname-first client creation
status: completed
created_at: '2026-05-25T15:15:40.251685'
updated_at: '2026-05-25T15:56:14.078871'
completed_at: '2026-05-25T15:56:14.078871'
---
Rework legal client creation so natural person clients can be created surname-first with deterministic slug generation, e.g. Van Heerden, Benjamin -> van_heerden_benjamin. Support explicit entity/non-person clients. Add explicit suffix handling for generated slug collisions; do not guess suffixes. Collision errors must instruct the agent to ask the lawyer for a distinguishing suffix such as location, ID hint, company, or role. Update typed client state, command interface, docs, and tests.

## Completion Notes

Reworked legal client creation so client new defaults to natural person creation from surname-first display names such as Van Heerden, Benjamin, generating deterministic slugs like van_heerden_benjamin. Added explicit entity/non-person creation by client type, kept --slug for lawyer-provided explicit slugs, and added --suffix for collision-safe generated slugs such as van_heerden_benjamin_pretoria. Updated collision errors to instruct the agent to ask the lawyer for a distinguishing suffix such as location, ID hint, company, or role instead of guessing. Updated legal workflow docs and focused tests. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited client files and tests, and uvx ruff check on edited files.
