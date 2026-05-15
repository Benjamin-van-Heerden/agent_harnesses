---
title: Implement spec migration
status: completed
created_at: '2026-02-11T14:59:29.088024'
updated_at: '2026-02-11T17:22:30.029914'
completed_at: '2026-02-11T17:22:30.029906'
---
Add a function _migrate_specs(mem_dir: Path, agent_rules_dir: Path) that migrates all specs from .mem/specs/ to agent_rules/spec/. For each spec directory (excluding completed/ and abandoned/): (1) Read spec.md, parse frontmatter. (2) Read all task files from tasks/ subdir, parse each. (3) Build filename: s_{YYYYMMDD from created_at}_{assigned_to or git user lowercased with underscores}__{slug}.md. (4) Build mem light spec format with title, status marker (todo->Draft, merge_ready->In Progress, completed->Completed, abandoned->Abandoned), description (spec body), tasks inlined as sections with checkboxes ([x] for completed, [ ] for todo), and placeholder Completion Report/Final Review sections. (5) Write to agent_rules/spec/. Repeat for specs/completed/ -> agent_rules/spec/completed/ and specs/abandoned/ -> agent_rules/spec/abandoned/. Uses the frontmatter parser from task 3.

## Completion Notes

Added _get_git_user(), _migrate_specs_from_dir(), _migrate_specs(), and STATUS_MAP. Handles active/completed/abandoned specs, inlines tasks with checkboxes, builds mem light format with status markers and correct filenames.