---
title: Add mem-todo label to mem init
status: completed
created_at: '2026-01-23T15:35:17.087854'
updated_at: '2026-01-24T18:21:45.064575'
completed_at: '2026-01-24T18:21:45.064569'
---
Update src/commands/init.py to create 'mem-todo' label on GitHub during initialization, similar to how 'mem-spec' label is created. Use green color (#22C55E) with description 'Standalone todos managed by mem CLI'.

## Completion Notes

Added mem-todo label creation to init.py alongside the existing mem-spec label. The label uses blue color (1D76DB) with description 'Standalone todos managed by mem CLI'. Also fixed test_init.py to remove legacy [vars] and github_token_env assertions, replacing them with current config format assertions ([project], [[files]], [worktree]). All init tests pass.