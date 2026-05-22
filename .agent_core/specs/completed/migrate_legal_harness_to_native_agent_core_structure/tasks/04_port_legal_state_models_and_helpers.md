---
title: Port legal state models and helpers
status: completed
created_at: '2026-05-21T09:49:19.581385'
updated_at: '2026-05-21T15:52:56.863985'
completed_at: '2026-05-21T15:52:56.863985'
---
Move the reusable behavior from legal/agent_rules/scripts/_lib.py and related scripts into typed native state/util modules. Add explicit typed records for client profiles, matter status, todos, memories, work logs, deadline entries, and any other state records command code needs. Implement slug validation, skeleton rendering, frontmatter parsing/updating, client resolution, matter resolution, record appending, deadline parsing, todo lookup, log creation helpers, and git snapshot helpers without raw dict state in command code. Preserve existing file formats unless a format change is explicitly justified and migrated.

## Completion Notes

Ported reusable legacy legal helper behavior into typed native state modules under legal/.agent_core/harness/src/state. Added dataclass records for client profiles, matter status and refs, deadline entries, chronology entries, todos, memories, and work logs. Added validation helpers for slugs, dates, priorities, todo priorities, and communication direction; time helpers; template rendering from .agent_core/practice/templates; markdown/frontmatter utilities; client creation/listing/resolution; matter creation/listing/resolution/closing; deadline parsing/addition/next_deadline updates/upcoming deadline listing; communication and note record appending; practice and matter todo creation/claiming/listing; memory and work log creation/listing; initial obligation record helpers; and legacy-compatible record append behavior. Added focused tests exercising the state helper layer end to end after installing the harness. Verified with uv run pytest legal/tests/test_setup.py, uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py, and uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py.
