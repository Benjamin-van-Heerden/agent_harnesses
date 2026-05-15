---
title: Implement mem patch agents command
status: completed
created_at: '2026-01-22T09:15:00.399240'
updated_at: '2026-01-22T09:24:43.335548'
completed_at: '2026-01-22T09:24:43.335541'
---
Add the 'agents' subcommand to src/commands/patch.py. It should: (1) Read existing AGENTS.md, (2) Extract user content (everything after </MEMCONTENT> tag), (3) Read current template from src/templates/AGENTS.md, (4) Write new file with template wrapped in <MEMCONTENT> tags followed by preserved user content, (5) Support --dry-run flag. Handle edge cases: no tags (legacy file - warn that customizations will be lost), missing file (tell user to run mem init), content already matches (report up to date).

## Completion Notes

Added patch_agents() function to src/commands/patch.py. Handles legacy files without tags, extracts and preserves user content, replaces mem-managed content with current template, supports --dry-run flag. Tested successfully.