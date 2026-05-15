---
created_at: '2026-05-14T16:00:08.730372'
username: benjamin_van_heerden
spec_slug: project_local_harness_migration
---
# Work Log - Optional Docs and Test Cleanup

## Overarching Goals

Continue tightening the project-local harness migration by improving the quality
of harness tests and replacing the old global-template dependency with
repo-local optional docs that can be copied into `.agent_core/docs/`.

## What Was Accomplished

### Test Cleanup

Reviewed the harness tests added during the migration work and removed weak
substring-only checks where they did not prove meaningful behavior.

- Setup now verifies `AGENTS.md` exists and has content instead of checking a
  few incidental phrases.
- Config checks now parse TOML via a shared `read_toml` helper.
- Markdown state checks now use `read_frontmatter` and `markdown_body` helpers
  instead of scanning raw text for status/body fragments.
- Kept stdout assertions where stdout is the actual user-facing behavior under
  test, such as onboard output and the mem-lite two-step migration message.

### Optional Docs

Added optional docs management to `harnesses/mem/setup.sh`.

- `setup.sh docs list` lists every markdown file in
  `harnesses/mem/optional_docs/` by slug.
- `setup.sh docs add <slug> [slug ...]` copies selected optional docs into
  `.agent_core/docs/`.
- `setup.sh docs update [slug ...]` overwrites selected installed docs from the
  current template.
- `setup.sh docs update` without slugs updates all installed optional docs whose
  filenames still exist in `optional_docs/`.

This makes reusable guidance repo-local and removes reliance on global
`generic_templates` from `~/.config/mem`.

### Verification

Ran and passed:

- `uvx ruff check harnesses/mem/tests`
- `uv run pytest harnesses/mem/tests/test_setup.py harnesses/mem/tests/test_onboard.py harnesses/mem/tests/test_local_commands.py harnesses/mem/tests/test_worktrees.py harnesses/mem/tests/test_migration.py -v`
- `uv run pytest harnesses/mem/tests/test_remote_migration.py -v`

## Key Files Affected

- `harnesses/mem/setup.sh`: Added `docs list`, `docs add`, and `docs update`
  subcommands for project-local optional docs.
- `harnesses/mem/AGENTS.md`: Documented the optional docs commands in the
  installed harness guidance.
- `harnesses/mem/tests/helpers.py`: Added TOML/frontmatter/body parsing helpers
  for stronger tests.
- `harnesses/mem/tests/test_setup.py`: Added optional docs command coverage and
  removed weak AGENTS substring checks.
- `harnesses/mem/tests/test_local_commands.py`: Replaced markdown substring
  checks with frontmatter/body assertions.
- `harnesses/mem/tests/test_migration.py`: Removed incidental migration prose
  assertions where exit code and filesystem state were sufficient.
- `harnesses/mem/tests/test_remote_migration.py`: Replaced config substring
  checks with TOML assertions.

## What Comes Next

The harness migration work is in a reviewable state. The next step is to review
the full diff and decide whether to complete the
`project_local_harness_migration` spec.
