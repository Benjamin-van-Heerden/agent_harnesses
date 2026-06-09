---
created_at: '2026-06-09T12:11:30.620913'
username: benjamin_van_heerden
---
Work Log - Coding Harness Runnable Onboard Context

## Overarching Goals

Add a coding harness configuration surface for command-generated onboard context. The target use case was a project-specific command such as a multiline Elixir `mix run -e` snippet that prints module documentation without dumping whole source files. The work also needed to correct onboard ordering so project docs appear before config-derived output, and confirm the local auto-update path applies the new config scaffold to existing projects.

## What Was Accomplished

### Added `[[runnables]]` Config Support

Added a new `RunnableConfig` model to the coding harness config schema:

```toml
[[runnables]]
command = """
python -m your_tool --print-context
"""
description = "Generated project context"
timeout_seconds = 60
```

Onboard now runs each configured command from the project root, captures stdout and stderr, and includes the output in a new `RUNNABLES` section. Runnable failures are nonfatal to onboarding: nonzero exits, timeouts, and OS errors are rendered into the onboard context instead of preventing the rest of the project briefing from being generated.

### Reordered Onboard Context

Changed the first onboard section ordering so `.agent_core/docs` output is shown before config-derived output. The resulting order is:

```text
CODEBASE AND CONVENTIONS
  PROJECT DOCS
  IMPORTANT FILES
  DIRECTORY TREES
  RUNNABLES
  PROJECT MEMORIES

ONBOARD OUTPUT
```

### Updated Config Defaults And Existing-Project Patching

Updated generated config templates to include commented `[[runnables]]` examples. Also updated coding `setup.py` so existing installed projects receive missing optional onboard config scaffolds during update without activating them. The updater now independently injects commented examples for missing `[[files]]`, `[[tree_dirs]]`, and `[[runnables]]` array tables.

After the change was committed, pushed, and merged through `test` and `main`, the local installed harness update path was tested with:

```bash
python -B .agent_core/harness/update.py --force
```

That command downloaded the latest `main/coding/setup.py`, refreshed the installed local harness, inserted the missing commented `[[runnables]]` block into `.agent_core/config.toml`, updated `last_updated_at`, and created/pushed the generated update commit `066f5c8 harness updated 20260609`.

### Verification

Focused verification completed:

```bash
uv run pytest coding/tests/test_onboard.py coding/tests/test_setup.py
uvx ruff check coding/.agent_core/harness/src/config/models.py coding/.agent_core/harness/src/config/main.py coding/.agent_core/harness/src/commands/onboard/content.py coding/setup.py coding/tests/test_setup.py coding/tests/test_onboard.py
uv run ty check coding/.agent_core/harness/src/config/models.py coding/.agent_core/harness/src/config/main.py coding/.agent_core/harness/src/commands/onboard/content.py coding/setup.py coding/tests/test_setup.py coding/tests/test_onboard.py
git diff --check
```

The final focused test run reported `24 passed`.

## Key Files Affected

The implementation was made under `coding/`, the source of truth for the coding harness:

- `coding/.agent_core/harness/src/config/models.py`: added `RunnableConfig` and `AgentCoreConfig.runnables`.
- `coding/.agent_core/harness/src/config/main.py`: added runnable support to `generate_default_config_toml`.
- `coding/.agent_core/harness/src/commands/onboard/content.py`: added runnable execution/capture and reordered docs/config-derived onboard sections.
- `coding/setup.py`: added commented runnable defaults for fresh installs and optional scaffold injection for existing installs.
- `coding/tests/test_onboard.py`: added regression coverage for runnable output and docs-before-config ordering.
- `coding/tests/test_setup.py`: added regression coverage for commented optional onboard config scaffold injection.

The local installed harness and `.agent_core/config.toml` were then refreshed through the normal local updater. The updater created commit `066f5c8 harness updated 20260609`.

## Errors and Barriers

The first attempted update used the direct remote bootstrap command. The user stopped that run and clarified that the desired test was the local auto-update wrapper, because that is what other installed repositories run on their periodic update cycle. The correct command was confirmed and used:

```bash
python -B .agent_core/harness/update.py --force
```

One behavior note remains: for an existing config that already had `[[files]]` and `[[tree_dirs]]` comments, the updater appended the newly missing commented `[[runnables]]` scaffold near the end of `.agent_core/config.toml`, after `[harness]`. This is valid TOML and works, but it is not as tidy as grouping it with the other onboard config scaffolds.

## What Comes Next

If desired, a future cleanup can make config scaffold insertion place missing optional onboard blocks adjacent to existing optional onboard comments instead of appending them at the end of the file.
