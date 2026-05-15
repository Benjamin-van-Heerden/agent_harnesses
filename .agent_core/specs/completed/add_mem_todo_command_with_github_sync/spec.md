---
title: Add mem todo command with GitHub sync
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 59
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/59
branch: dev-benjamin_van_heerden-add_mem_todo_command_with_github_sync
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/60
created_at: '2026-01-23T15:34:40.865709'
updated_at: '2026-01-24T19:35:46.155715'
completed_at: '2026-01-24T19:35:46.153539'
last_synced_at: '2026-01-23T15:39:46.126390'
local_content_hash: bb2b3ffaa4992a0a8a91fd321733fa70ba051d0d3c0c69de897ecb8405c69493
remote_content_hash: bb2b3ffaa4992a0a8a91fd321733fa70ba051d0d3c0c69de897ecb8405c69493
---
## Overview

Add a formal `mem todo` command for managing standalone work items that sync with GitHub issues. Todos are lightweight reminders/tasks that exist outside of specs - they can be addressed ad-hoc or incorporated into specs later.

## Goals

- Provide a CLI for creating and managing todos: `mem todo new`, `mem todo list`, `mem todo claim`
- Sync todos bidirectionally with GitHub issues using `mem-todo` label
- Show open todos in `mem onboard` output when no spec is active
- Update `mem spec new` output to remind users about claiming related todos

## Technical Approach

### Commands

1. **`mem todo new "title" "description"`**
   - Creates a todo file in `.mem/todos/{slug}.md` with YAML frontmatter
   - Creates a GitHub issue with `mem-todo` label
   - Stores `issue_id` and `issue_url` in frontmatter

2. **`mem todo list`**
   - Lists all open todos (not claimed)
   - Shows title, created date, and GitHub issue link

3. **`mem todo claim "title"`**
   - Marks todo as claimed by current user with timestamp
   - Closes the linked GitHub issue with a comment
   - Updates frontmatter: `claimed_by`, `claimed_at`

### File Format

```yaml
---
title: "Fix login timeout issue"
status: open  # or "claimed"
issue_id: 123
issue_url: https://github.com/owner/repo/issues/123
created_at: '2026-01-23T10:00:00'
claimed_by: null  # GitHub username when claimed
claimed_at: null  # Timestamp when claimed
---
Description of the todo item...
```

### GitHub Integration

- **Label**: `mem-todo` (green color, created during `mem init`)
- **Sync**: 
  - Outbound: `mem todo new` creates GitHub issue
  - Inbound: `mem sync` pulls GitHub issues with `mem-todo` label as local todos
  - Claiming closes the GitHub issue

### Onboard Integration

- When no spec is active, show open todos prominently in the onboard output
- Section: "OPEN TODOS" with title, description preview, and issue link

### Spec New Reminder

Update `mem spec new` output to include:
```
💡 Check if any existing todos relate to this spec:
   Run 'mem todo list' to see open todos
   Use 'mem todo claim "title"' to mark them as addressed
```

## Success Criteria

- `mem todo new "title" "desc"` creates local file and GitHub issue with `mem-todo` label
- `mem todo list` shows all open todos
- `mem todo claim "title"` marks todo as claimed, closes GitHub issue
- `mem sync` pulls new GitHub issues with `mem-todo` label as local todos
- `mem onboard` shows open todos when no spec is active
- `mem spec new` reminds about checking/claiming todos
- `mem init` creates the `mem-todo` label on GitHub

## Notes

- Existing todo infrastructure in `src/utils/todos.py` should be leveraged/extended
- Current sync already creates todos from non-spec GitHub issues - this formalizes that behavior
- Todos are simpler than specs: no branches, no worktrees, no tasks - just a single work item
