---
created_at: '2026-01-23T12:20:55.021712'
username: benjamin_van_heerden
spec_slug: add_cursorrules_symlink_to_init
---
# Work Log - Add .cursorrules symlink to init

## Overarching Goals

Add `.cursorrules` symlink creation to `mem init` so that Cursor IDE users automatically get the same agent instructions as Claude Code users (who get `CLAUDE.md`).

## What Was Accomplished

Updated `create_agents_files()` in `src/commands/init.py` to create a `.cursorrules` symlink pointing to `AGENTS.md`:

1. Added `cursorrules_file` path variable
2. Added conditional symlink creation following the same pattern as `CLAUDE.md`
3. Updated function docstring to reflect both symlinks

The implementation:
```python
cursorrules_file = project_root / ".cursorrules"

if not cursorrules_file.exists() and agents_file.exists():
    cursorrules_file.symlink_to("AGENTS.md")
    typer.echo("✅ Created .cursorrules -> AGENTS.md symlink")
```

## Key Files Affected

- `src/commands/init.py`: Added `.cursorrules` symlink creation in `create_agents_files()` function (lines 158-179)

## What Comes Next

Spec is complete. All tasks finished:
- [x] Add .cursorrules symlink in create_agents_files

Ready for PR creation via `mem spec complete`.
