---
created_at: '2026-01-29T12:12:23.616583'
username: benjamin_van_heerden
---
# Work Log - Fix task show and spec show verbose output

## Overarching Goals

Improve the display formatting of `mem task show` and `mem spec show --verbose` commands to be more consistent with how paths and task details are displayed elsewhere in the codebase.

## What Was Accomplished

### Fixed `mem task show` file path formatting

The `File:` field was only showing the filename (e.g., `01_my_task.md`) instead of the full relative path. Updated to show the complete path like spec does:

```
File:      .mem/specs/{spec_slug}/tasks/{filename}
```

### Updated `mem spec show --verbose` task display

Changed the verbose task display to match the onboard output style:

- Completed tasks are now shown as a simple checklist: `[x] task title`
- Pending tasks in verbose mode show full details with title and body content
- Non-verbose mode retains the simple `[ ] title` / `[x] title` format

## Key Files Affected

- `src/commands/task.py` - Fixed file path in `show()` function (line 258)
- `src/commands/spec.py` - Updated task display logic in `show()` function (lines 320-355)

## What Comes Next

No immediate follow-up needed. The changes are ready to be committed.
