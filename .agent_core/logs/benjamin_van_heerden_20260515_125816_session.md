---
created_at: '2026-05-15T12:58:16.577181'
username: benjamin_van_heerden
---
# Work Log - Onboard Sync, Branch Config, and Typed State Records

## Overarching Goals

Improve the project-local coding harness so onboarding gives complete actionable
context, protected branches are explicit and validated, and domain state is
represented by typed objects instead of raw dictionaries.

## What Was Accomplished

- Installed missing local harness dependencies so onboarding could run.
- Investigated why onboard did not fail when `dev` and `test` branches were absent.
- Confirmed project-local `onboard` was only building static context and was not running sync.
- Updated the coding harness template so `onboard` runs sync by default and added a `--no-sync` escape hatch for tests/offline diagnostics.
- Added explicit `dev`, `test`, and `main` branch configuration and removed the hardcoded `dev` branch path.
- Added branch validation to `setup.sh` so configured protected branches must exist before installation/update.
- Reworked `setup.sh` toward remote use by cloning the canonical template repository when no local template checkout is available.
- Expanded onboard work-log output in full rather than only listing filenames.
- Limited completed spec noise to recent summaries.
- Added a project memory requiring typed state records and no raw dict domain records in `coding/`.
- Added explicit state models for specs, tasks, todos, memories, and work logs.
- Migrated state APIs and command formatting code to use typed objects.
- Fixed the reported six `ty` diagnostics by adding CLI status parsers, model type narrowing, and a non-optional branch value before checkout.
- Improved the `log new` command output so future sessions are told to read and fill in the generated log file.

## Key Files Affected

- `coding/setup.sh`
- `coding/setup_support/upsert_config.py`
- `coding/.agent_core/harness/src/commands/onboard.py`
- `coding/.agent_core/harness/src/commands/log/new.py`
- `coding/.agent_core/harness/src/commands/sync/main.py`
- `coding/.agent_core/harness/src/config/models.py`
- `coding/.agent_core/harness/src/config/main.py`
- `coding/.agent_core/harness/src/config/branches.py`
- `coding/.agent_core/harness/src/state/models.py`
- `coding/.agent_core/harness/src/state/specs.py`
- `coding/.agent_core/harness/src/state/tasks.py`
- `coding/.agent_core/harness/src/state/todos.py`
- `coding/.agent_core/harness/src/state/memories.py`
- `coding/.agent_core/harness/src/state/logs.py`
- `coding/.agent_core/harness/src/utils/git.py`
- `coding/.agent_core/harness/src/utils/markdown.py`
- `coding/tests/test_setup.py`
- `coding/tests/test_onboard.py`
- `coding/tests/test_local_commands.py`
- `coding/tests/test_worktrees.py`
- `.agent_core/memories/typed_state_records_only.md`

## What Comes Next

- Review the full diff, especially the setup/onboard sync behavior and branch validation semantics.
- Decide whether the unrelated/user-owned working tree changes should be kept, adjusted, or committed separately.
- Run the full test suite, including GitHub integration tests if a valid token and disposable repository are available.
- Commit the accepted harness changes and push.
