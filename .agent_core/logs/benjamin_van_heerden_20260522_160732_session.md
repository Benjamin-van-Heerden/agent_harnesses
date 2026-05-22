---
created_at: '2026-05-22T16:07:32.999343'
username: benjamin_van_heerden
---
Work Log - Coding harness install and uninstall lifecycle hardening

## Overarching Goals

The session focused on tightening the coding harness setup lifecycle after a fresh install in another repository showed that setup left the user on `main` and only created `test`/`dev` branch refs, without ensuring those branches actually contained the installed harness state.

The goal was to make fresh install treat the protected branch sequence as part of the installation contract: install and commit on `main`, propagate the harness state through `test` and `dev`, and leave the checkout on `dev` for normal mission-control work. A second goal was to add a deliberately dangerous development-only uninstall path that can remove an installed harness and clean up harness-created GitHub issue labels.

## What Was Accomplished

### Hardened fresh install

Updated `coding/setup.py` so a fresh install now performs git preflight before writing files:

- requires an initialized git repository with at least one commit;
- requires a clean working tree;
- requires the current branch to be the configured `main` branch, defaulting to `main` before config exists;
- fetches `origin` when present;
- refuses install if local `main` and `origin/main` are not aligned;
- validates that configured `main`, `test`, and `dev` branch names are distinct.

Fresh install now writes the harness files, commits the harness-managed changes on `main` with `install agent harness`, pushes `main` when `origin` exists, then ensures:

- `test` exists and is based on `main`;
- `dev` exists and is based on `test`;
- both protected branches are pushed when `origin` exists;
- the final checkout is `dev` for remote-backed projects.

When no `origin` exists, the installer still supports local-only test/offline repositories and returns to `main` after creating/updating the local protected branches.

### Restricted setup commits to harness-owned paths

Added explicit checks so setup refuses to commit if the setup process produced changes outside harness-managed paths:

- `.agent_core`
- `AGENTS.md`
- `CLAUDE.md`
- `.gitignore`

This keeps the automated install/uninstall commits from sweeping unrelated project files into the harness lifecycle.

### Added guarded uninstall

Added `setup.py --uninstall` for development cleanup. The uninstall path now:

- requires a clean working tree;
- requires the command to run from configured `main`;
- fetches `origin` when present;
- refuses uninstall if local `main` and `origin/main` are not aligned;
- requires an exact confirmation phrase before mutating state;
- obscures that confirmation phrase in stdout so casual invocations are unlikely to succeed accidentally;
- removes `.agent_core`;
- removes the managed `AGENTS.md` block or deletes the file if it only contained managed instructions;
- removes managed `CLAUDE.md` symlink/copy;
- removes managed `.gitignore` entries, including the Agent Core worktree symlink comment;
- commits `uninstall agent harness` on `main`;
- pushes `main` when `origin` exists;
- deletes local and remote `dev` and `test` branch refs.

Added stdlib-only GitHub cleanup for uninstall. If `GITHUB_TOKEN` or `GH_TOKEN` is available and `origin` is a GitHub repository URL, uninstall closes open harness-created `spec` and `todo` issues and deletes the known harness labels:

- `spec`
- `todo`
- `status:todo`
- `status:merge-ready`
- `status:completed`
- `status:abandoned`

If no token is available, uninstall reports that GitHub issue and label cleanup was skipped.

### Updated tests for the new setup contract

Expanded setup tests to cover:

- remote-backed fresh install commits/pushes `main`, propagates to `test` and `dev`, and checks out `dev`;
- dirty fresh installs fail before writing `.agent_core`;
- fresh install from a non-`main` branch fails before writing `.agent_core`;
- uninstall requires the obscured confirmation;
- uninstall removes harness state and local protected branches;
- legacy `<AGENT_CORE>` blocks still migrate to `<core_instructions>`.

Updated affected tests and helpers so project files such as README or custom config are committed before fresh install, and so tests use `--update` for update-specific behavior after initial install.

Verification completed:

- `uv run pytest coding/tests/test_setup.py coding/tests/test_local_commands.py coding/tests/test_onboard.py coding/tests/test_worktrees.py`
- `uvx ruff check coding/setup.py coding/tests/test_setup.py coding/tests/test_local_commands.py coding/tests/test_onboard.py coding/tests/test_worktrees.py coding/tests/github_helpers.py`
- `uv run ty check coding/setup.py coding/tests/test_setup.py coding/tests/test_local_commands.py coding/tests/test_onboard.py coding/tests/test_worktrees.py coding/tests/github_helpers.py`
- `git diff --check`

## Key Files Affected

### `coding/setup.py`

Implemented the fresh install git lifecycle, setup-managed path guard, branch propagation, guarded uninstall, GitHub issue/label cleanup, and `--uninstall` CLI option.

### `coding/tests/test_setup.py`

Added coverage for remote-backed install, dirty/wrong-branch refusal, uninstall confirmation, uninstall cleanup, and adjusted update-oriented setup tests to use `--update`.

### `coding/tests/test_local_commands.py`

Updated the local smoke test to commit README before fresh install, then switch to `dev` for command workflow coverage.

### `coding/tests/test_onboard.py`

Updated onboard tests to commit README before fresh install, matching the new clean-worktree install requirement.

### `coding/tests/test_worktrees.py`

Removed the now-obsolete manual harness commit after setup, because fresh install now creates the install commit itself.

### `coding/tests/github_helpers.py`

Updated remote GitHub test setup to let `install_harness()` create/push the protected branch harness state instead of manually creating and pushing `dev`/`test` before install.

## Errors and Barriers

The first implementation pass let fresh install create `.agent_core` before failing when invoked from the wrong branch. This was corrected by moving the clean/main/aligned-remote preflight before any file writes.

The first uninstall implementation called a nonexistent `symlink_paths()` helper. This was corrected to use the existing `symlink_ignore_entries()` helper.

The first managed-path guard parsed `git status --porcelain` paths incorrectly by slicing from the wrong offset, producing paths such as `GENTS.md` and `agent_core/config.toml`. This was fixed by stripping from `line[2:]`.

Several existing tests assumed setup could run with uncommitted project files or from `dev`. Those tests were updated to match the new install contract.

## What Comes Next

The full coding test suite was not run. A future session should run broader tests before merging or pushing this change, especially remote GitHub lifecycle coverage because the helper behavior changed to rely on the new setup propagation flow.
