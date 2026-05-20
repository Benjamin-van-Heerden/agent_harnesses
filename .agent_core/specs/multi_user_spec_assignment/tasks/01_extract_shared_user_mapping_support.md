---
title: Extract shared user mapping support
status: todo
created_at: '2026-05-20T13:11:08.206873'
updated_at: '2026-05-20T13:11:08.206873'
completed_at: null
---
Move .agent_core/user_mappings.toml loading out of logs-only code into a shared typed helper or state module under the coding harness. Preserve the existing mapping shape with GitHub usernames as TOML sections containing name and optional email. Update work-log username resolution to use the shared helper, and expose a validation function that explicit spec assignees can use to fail fast with clear guidance when a username is not mapped.