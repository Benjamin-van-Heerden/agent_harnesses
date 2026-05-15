---
title: Add .cursorrules symlink in create_agents_files
status: completed
created_at: '2026-01-23T12:14:51.234468'
updated_at: '2026-01-23T12:20:23.441123'
completed_at: '2026-01-23T12:20:23.441115'
---
In src/commands/init.py, update create_agents_files() to create a .cursorrules symlink pointing to AGENTS.md. Follow the same pattern as the CLAUDE.md symlink (lines 173-176): check if it doesn't exist, then create it with symlink_to('AGENTS.md'), and echo a success message.

## Completion Notes

Added .cursorrules symlink to create_agents_files() function in src/commands/init.py. The symlink points to AGENTS.md and follows the same pattern as the existing CLAUDE.md symlink - only created if it doesn't already exist and AGENTS.md exists.