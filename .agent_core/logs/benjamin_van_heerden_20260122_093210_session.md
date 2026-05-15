---
created_at: '2026-01-22T09:32:10.606405'
username: benjamin_van_heerden
spec_slug: add_mem_patch_agents_command
---
# Work Log - Implement mem patch agents command

## Overarching Goals

Add `mem patch agents` command to update the mem-managed portion of AGENTS.md while preserving user-added content. Also add drift detection for AGENTS.md in `mem onboard`, with warnings displayed in the `[AGENT INSTRUCTION]` section.

## What Was Accomplished

### 1. Updated init.py to wrap AGENTS.md in MEMCONTENT tags

Modified `create_agents_files()` in `src/commands/init.py` to wrap template content in `<MEMCONTENT>` tags when creating new AGENTS.md files:

```python
template_content = template_path.read_text()
wrapped_content = f"<MEMCONTENT>\n{template_content}</MEMCONTENT>\n"
agents_file.write_text(wrapped_content)
```

### 2. Added AGENTS.md drift detection to onboard.py

Added `detect_agents_drift()` function that:
- Checks if AGENTS.md exists
- Checks if it has `<MEMCONTENT>` tags (legacy format detection)
- Compares mem-managed content against current template
- Returns `(has_drift, reason)` tuple

### 3. Moved drift warnings to AGENT INSTRUCTION section

- Replaced early stderr printing with a `drift_warnings` list
- Collects both config drift and AGENTS.md drift warnings
- Displays warnings prominently in the `[AGENT INSTRUCTION]` section

### 4. Implemented mem patch agents command

Added `patch_agents()` function to `src/commands/patch.py`:
- Handles legacy files without tags (wraps entire file)
- Extracts and preserves user content after `</MEMCONTENT>`
- Replaces mem-managed content with current template
- Supports `--dry-run` flag
- Reports "already up to date" when no changes needed

### 5. Added comprehensive tests

Created `tests/test_agents_drift.py` with 13 tests covering:
- Drift detection (6 tests): missing file, no tags, outdated, up to date, with user content, missing template
- Patch command (5 tests): adds tags, preserves user content, dry run, idempotent, up to date
- Init command (2 tests): wraps in tags, no overwrite

## Key Files Affected

- `src/commands/init.py` - Modified `create_agents_files()` to wrap content in MEMCONTENT tags
- `src/commands/onboard.py` - Added `detect_agents_drift()`, refactored drift warnings to display in AGENT INSTRUCTION section
- `src/commands/patch.py` - Added `patch_agents()` command with `--dry-run` support
- `tests/test_agents_drift.py` - New test file with 13 tests

## What Comes Next

All spec tasks have been completed. The spec is ready for completion and PR creation.
