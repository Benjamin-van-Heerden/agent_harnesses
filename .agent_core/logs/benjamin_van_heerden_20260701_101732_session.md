---
created_at: '2026-07-01T10:17:32.997793'
username: benjamin_van_heerden
---
Work Log - Coding harness user mapping maintenance and sync hardening

## Overarching Goals

Fix a coding harness issue where `.agent_core/user_mappings.toml` could remain empty and where onboard-driven sync could send unmapped assignees directly to GitHub. The work needed to preserve onboard sequencing so mapping maintenance would not dirty the worktree before git preflight, while still allowing normal synced onboard to maintain mappings as projects and teams grow.

## What Was Accomplished

### Repaired empty mapping file handling

Updated both runtime mapping maintenance and `coding/setup.py` so an existing zero-byte `.agent_core/user_mappings.toml` is treated as repairable state. Empty files are rewritten to the starter comment instead of being accepted as valid no-op TOML.

### Added current-user mapping maintenance in the correct sequence

Moved normal synced-onboard mapping maintenance into `sync_all()` after git preflight/sync has completed and after issue sync succeeds. This avoids the previous sequencing hazard where onboard could mutate tracked state before the dirty-tree preflight and block itself.

Normal `onboard --no-sync` still performs the lightweight empty-file repair early because that mode has no later sync/commit phase.

When normal synced onboard authenticates successfully, `sync_all()` now ensures the authenticated GitHub username exists in `.agent_core/user_mappings.toml`, using local git config for:

```text
name  <- git config user.name
email <- git config user.email
```

### Hardened issue sync around assignees and terminal specs

Updated spec issue sync so completed or abandoned local specs with `issue_id: null` are skipped instead of creating new GitHub issues for historical terminal specs.

Added local validation for non-current assignees before issue creation. If a spec is assigned to someone other than the authenticated GitHub user, that username must be present in `.agent_core/user_mappings.toml` before sync sends the assignee to GitHub. This changes bad historical assignee metadata from a GitHub 422 failure into a local harness validation failure.

### Improved missing-token onboard guidance

Expanded the onboard sync warning for `GITHUB_TOKEN is not set` so the generated onboard context tells the next agent that:

- GitHub sync did not run.
- The authenticated GitHub user could not be added to `.agent_core/user_mappings.toml`.
- The agent must explicitly warn the user before doing any other work.
- The user must configure a token with `repo` and `read:user` scopes, then rerun onboard so sync and mapping maintenance can complete.

### Added focused regression coverage

Added tests for:

- onboard repairing an empty `user_mappings.toml` in `--no-sync` mode;
- setup/update repairing an empty `user_mappings.toml`;
- sync skipping completed specs without issue ids;
- sync validating non-current assignees before issue creation;
- `sync_all()` running current-user mapping maintenance after issue sync;
- missing-token onboard warnings including explicit agent-facing guidance.

Verification completed:

```bash
uv run pytest coding/tests/test_sync_issues.py coding/tests/test_onboard.py::test_onboard_sync_warning_guides_agent_for_missing_github_token coding/tests/test_onboard.py::test_template_onboard_repairs_empty_user_mappings_file coding/tests/test_setup.py::test_template_setup_preserves_state_and_avoids_removed_surfaces
uvx ruff check coding/.agent_core/harness/src/state/user_mappings.py coding/.agent_core/harness/src/commands/sync/main.py coding/.agent_core/harness/src/commands/onboard/main.py coding/.agent_core/harness/src/commands/onboard/content.py coding/setup.py coding/tests/test_sync_issues.py coding/tests/test_onboard.py coding/tests/test_setup.py
uv run ty check coding/.agent_core/harness/src/state/user_mappings.py coding/.agent_core/harness/src/commands/sync/main.py coding/.agent_core/harness/src/commands/onboard/main.py coding/.agent_core/harness/src/commands/onboard/content.py coding/setup.py coding/tests/test_sync_issues.py coding/tests/test_onboard.py coding/tests/test_setup.py
git diff --check
```

The focused test run reported `8 passed`.

## Key Files Affected

- `coding/.agent_core/harness/src/state/user_mappings.py`: repairs empty files, adds git email lookup, and adds `ensure_current_user_mapping()`.
- `coding/.agent_core/harness/src/commands/sync/main.py`: centralizes issue sync, validates assignees, skips terminal no-issue specs, and updates current-user mappings after successful issue sync.
- `coding/.agent_core/harness/src/commands/onboard/main.py`: limits early mapping repair to `--no-sync` so normal onboard does not dirty the tree before preflight.
- `coding/.agent_core/harness/src/commands/onboard/content.py`: adds explicit missing-token guidance to the generated onboard sync warning section.
- `coding/setup.py`: repairs zero-byte `user_mappings.toml` during setup/update.
- `coding/tests/test_sync_issues.py`: adds sync regression coverage.
- `coding/tests/test_onboard.py`: adds empty-file and missing-token guidance coverage.
- `coding/tests/test_setup.py`: adds setup/update empty-file repair coverage.

## Errors and Barriers

The main design hazard was onboard sequencing. The first implementation strengthened mapping maintenance but left the existing early `ensure_user_mappings_file()` call in normal onboard, which would have made tracked `.agent_core/user_mappings.toml` dirty before git preflight. That was corrected by restricting early repair to `--no-sync` and using `sync_all()` for normal synced mapping maintenance.

## What Comes Next

After this reaches `main`, installed coding harnesses should pick it up through the normal update flow. Existing projects with zero-byte `.agent_core/user_mappings.toml` will be repaired during setup/update or during `onboard --no-sync`; normal synced onboard will also maintain the authenticated user mapping after sync succeeds.
