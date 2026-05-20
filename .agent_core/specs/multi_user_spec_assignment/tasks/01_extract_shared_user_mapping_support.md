---
title: Extract shared user mapping support
status: completed
created_at: '2026-05-20T13:11:08.206873'
updated_at: '2026-05-20T13:34:27.721204'
completed_at: '2026-05-20T13:34:27.721204'
---
Move .agent_core/user_mappings.toml loading out of logs-only code into a shared typed helper or state module under the coding harness. Preserve the existing mapping shape with GitHub usernames as TOML sections containing name and optional email. Update work-log username resolution to use the shared helper, and expose a validation function that explicit spec assignees can use to fail fast with clear guidance when a username is not mapped.

## Completion Notes

Extracted shared typed user mapping support into src/state/user_mappings.py, preserved work-log current username resolution through the shared helper, and added require_mapped_user for explicit assignee validation.
