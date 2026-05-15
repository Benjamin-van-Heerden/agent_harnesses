---
created_at: '2026-05-14T14:35:21.692892'
username: benjamin_van_heerden
spec_slug: project_local_harness_migration
---
# Work Log - Harness Migration Finalization

## Overarching Goals

Finalize the transition from legacy project state to the project-local harness.
The focus was the migration command and installed guidance: base `.mem/`
projects should migrate deterministically into `.agent_core/`, GitHub issue
labels should move to the neutral harness labels, mem lite should remain a
reviewable two-step path, and installed `AGENTS.md` should carry the important
operational instructions from the original project guidance.

## What Was Accomplished

### Migration Behavior

Implemented the remaining `.mem/` to project-local harness migration behavior in
`src/utils/migrate.py`.

- Real `--to-harness` migrations now require `GITHUB_TOKEN` and a GitHub
  `origin` remote before writing project state.
- Failed `--to-harness` precondition checks now exit non-zero.
- Linked spec and todo issues are relabeled to neutral harness labels:
  `spec`, `todo`, `status:todo`, `status:merge-ready`, `status:completed`,
  and `status:abandoned`.
- Core docs from `.mem/docs/core/` now migrate into `.agent_core/docs/` so they
  are read during onboard.
- Non-core docs from `.mem/docs/` now migrate into top-level `docs/`.
- `.mem/docs/data/` is still skipped as generated/index cache data.
- `--to-harness` now gives an explicit two-step message for mem lite projects:
  run `--lite-to-mem`, review the generated `.mem/` state, then run
  `--to-harness`.

### Installed Harness Guidance

Expanded `harnesses/mem/AGENTS.md` so installed projects receive the important
operational and behavioral guidance in harness-native terms.

- Added first-action trigger guidance.
- Added core concepts, command examples, todos, memories, logs, docs, and
  worktree rules.
- Added interruption, GitHub timeout, task/spec creation, commit-message, and
  onboard discipline notes.
- Added the behavioral guidelines for thinking before coding, simplicity,
  surgical changes, and goal-driven execution.
- Added guidance that optional repo-local docs are managed through
  `setup.sh docs list`, `setup.sh docs add`, and `setup.sh docs update`.

### Optional Docs

Added project-local optional docs management to `harnesses/mem/setup.sh`.

- `setup.sh docs list` lists optional docs available from
  `harnesses/mem/optional_docs/`.
- `setup.sh docs add <slug> [slug ...]` copies selected docs into
  `.agent_core/docs/`.
- `setup.sh docs update [slug ...]` overwrites selected installed docs from the
  harness template, or updates all installed optional docs when no slugs are
  provided.
- This removes the need for `generic_templates` or global template lookup for
  these reusable docs.

### Harness Tests

Updated the harness-owned test suite under `harnesses/mem/tests/`.

- Added shared legacy-state setup in `helpers.py`.
- Split local migration assertions into dry-run, GitHub-required, and lite
  two-step tests.
- Added a GitHub-backed migration test that clears/recreates the disposable
  `mem-test` repo, creates linked issues, runs real migration, verifies labels,
  verifies docs placement, and verifies onboard only reads core docs.
- Added setup assertions that installed `AGENTS.md` includes the expanded
  guidance.
- Reworked weak substring-only assertions into structural checks where possible:
  AGENTS setup now verifies the file exists with content, config assertions parse
  TOML, and generated markdown assertions parse frontmatter/body instead of
  scanning arbitrary text.

### Verification

Ran and passed:

- `uvx ruff check harnesses/mem/tests src/commands/migrate.py src/utils/migrate.py harnesses/mem/.agent_core/harness harnesses/mem/setup_support/upsert_config.py`
- `uv run pytest harnesses/mem/tests/test_setup.py harnesses/mem/tests/test_onboard.py harnesses/mem/tests/test_local_commands.py harnesses/mem/tests/test_worktrees.py harnesses/mem/tests/test_migration.py -v`
- `uv run pytest harnesses/mem/tests/test_github_flow.py harnesses/mem/tests/test_remote_migration.py -v`
- After tightening failed migration exit codes, reran
  `uv run pytest harnesses/mem/tests/test_migration.py -v` and
  `uv run pytest harnesses/mem/tests/test_remote_migration.py -v`.
- After removing weak setup/config/frontmatter assertions, reran
  `uvx ruff check harnesses/mem/tests`,
  `uv run pytest harnesses/mem/tests/test_setup.py harnesses/mem/tests/test_onboard.py harnesses/mem/tests/test_local_commands.py harnesses/mem/tests/test_worktrees.py harnesses/mem/tests/test_migration.py -v`,
  and `uv run pytest harnesses/mem/tests/test_remote_migration.py -v`.
- After adding setup docs commands, reran `uvx ruff check harnesses/mem/tests`
  and
  `uv run pytest harnesses/mem/tests/test_setup.py harnesses/mem/tests/test_onboard.py harnesses/mem/tests/test_local_commands.py harnesses/mem/tests/test_worktrees.py harnesses/mem/tests/test_migration.py -v`.

## Key Files Affected

- `src/utils/migrate.py`: Added harness migration helpers for config
  conversion, docs splitting, GitHub remote detection, label creation, linked
  issue relabeling, and mem-lite two-step messaging.
- `harnesses/mem/AGENTS.md`: Expanded installed guidance.
- `harnesses/mem/setup.sh`: Added optional docs list/add/update commands.
- `harnesses/mem/tests/helpers.py`: Added shared legacy `.mem/` test fixture.
- `harnesses/mem/tests/test_migration.py`: Added local migration contract tests.
- `harnesses/mem/tests/test_remote_migration.py`: Added real GitHub-backed
  migration test.
- `harnesses/mem/tests/test_setup.py`: Added installed guidance assertions.

## What Comes Next

The implementation is in a good state for review. The next logical step is to
review the total diff and decide whether to complete the spec.
