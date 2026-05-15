---
title: Add mem patch agents command
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 55
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/55
branch: dev-benjamin_van_heerden-add_mem_patch_agents_command
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/56
created_at: '2026-01-22T09:14:18.142847'
updated_at: '2026-01-22T09:48:22.398736'
completed_at: '2026-01-22T09:48:22.397833'
last_synced_at: '2026-01-22T09:15:34.450133'
local_content_hash: 503dcb4769dd9f99621ffcca5a385a18d79dd573c34a459d3123c62ef8f09e9f
remote_content_hash: 503dcb4769dd9f99621ffcca5a385a18d79dd573c34a459d3123c62ef8f09e9f
---
## Overview

Add `mem patch agents` command to update the mem-managed portion of AGENTS.md while preserving user-added content. Also add drift detection for AGENTS.md in `mem onboard`, with warnings displayed in the `[AGENT INSTRUCTION]` section.

## Goals

- Allow AGENTS.md to have both mem-managed content and user-specific content
- Detect when the mem-managed content is outdated
- Provide a command to update it while preserving user content
- Display all drift warnings (config AND agents) in the `[AGENT INSTRUCTION]` section so agents see them

## Technical Approach

### AGENTS.md Format

Use XML-style tags to separate mem-managed content from user content:

```
<MEMCONTENT>
{content from src/templates/AGENTS.md}
</MEMCONTENT>

{user-specific content here}
```

The `<MEMCONTENT>` tags are added programmatically, not stored in the template itself.

### Files to Modify

1. **`src/commands/init.py`**: Update `create_agents_files()` to wrap template content in `<MEMCONTENT>` tags when creating new AGENTS.md files.

2. **`src/commands/onboard.py`**: 
   - Add function to detect AGENTS.md drift (compare mem-managed section against current template)
   - Collect all drift warnings (config + agents) into a list
   - Display drift warnings in the `[AGENT INSTRUCTION]` section instead of printing to stderr early
   - Remove the early stderr printing of config drift

3. **`src/commands/patch.py`**: Add `agents` subcommand that:
   - Reads existing AGENTS.md
   - Extracts user content (everything outside `<MEMCONTENT>` tags)
   - Replaces mem-managed content with current template wrapped in tags
   - Preserves user content below the tags
   - Supports `--dry-run` flag
   - Handles edge cases: no tags (legacy file), missing file, etc.

### Edge Cases

- **Legacy AGENTS.md without tags**: Treat entire file as mem-managed content that will be replaced. Warn user that any customizations will be lost (or prompt for confirmation).
- **AGENTS.md doesn't exist**: Tell user to run `mem init` or create it.
- **Template content matches**: Report "already up to date".

## Success Criteria

- `mem patch agents` updates mem-managed content while preserving user content
- `mem patch agents --dry-run` shows what would change
- `mem onboard` detects AGENTS.md drift and shows warning in `[AGENT INSTRUCTION]` section
- Config drift warnings also moved to `[AGENT INSTRUCTION]` section
- New AGENTS.md files created by `mem init` have `<MEMCONTENT>` tags

## Notes

- The template file `src/templates/AGENTS.md` stays unchanged (no tags in it)
- Tags are added/managed programmatically
- User content goes AFTER the closing `</MEMCONTENT>` tag
