---
title: Port legal state models and helpers
status: todo
created_at: '2026-05-21T09:49:19.581385'
updated_at: '2026-05-21T09:49:19.581385'
completed_at: null
---
Move the reusable behavior from legal/agent_rules/scripts/_lib.py and related scripts into typed native state/util modules. Add explicit typed records for client profiles, matter status, todos, memories, work logs, deadline entries, and any other state records command code needs. Implement slug validation, skeleton rendering, frontmatter parsing/updating, client resolution, matter resolution, record appending, deadline parsing, todo lookup, log creation helpers, and git snapshot helpers without raw dict state in command code. Preserve existing file formats unless a format change is explicitly justified and migrated.