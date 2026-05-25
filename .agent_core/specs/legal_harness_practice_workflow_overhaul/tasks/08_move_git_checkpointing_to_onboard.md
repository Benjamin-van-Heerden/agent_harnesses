---
title: Move Git checkpointing to onboard
status: completed
created_at: '2026-05-25T15:16:22.194077'
updated_at: '2026-05-25T16:43:17.128193'
completed_at: '2026-05-25T16:43:17.128193'
---
Change legal harness local Git snapshot behavior so onboard creates a local Git checkpoint after it creates or cleans session logs and refreshes generated state such as .agent_core/client_matter_index.toml. Automatic snapshotting after every harness command is not required and should be removed unless a specific retained behavior is documented. Setup must require Git, so onboard can assume local git is available after install. Add focused tests that onboard creates a checkpoint when it mutates session/generated state and that ordinary non-onboard commands do not snapshot just because main.py exits.

## Completion Notes

Removed automatic legal harness git snapshotting from main.py finalization so ordinary commands no longer create checkpoints just because they exit. Removed the separate auto-update snapshot call. Moved checkpointing explicitly into onboard after onboard refreshes generated/session state such as .agent_core/client_matter_index.toml and creates/cleans session logs. Added a behavior test proving onboard creates a local git snapshot while a later ordinary client command leaves changes uncommitted and does not advance HEAD. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited checkpoint files and tests, and uvx ruff check on edited files.
