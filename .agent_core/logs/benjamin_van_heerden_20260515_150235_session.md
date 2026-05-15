---
created_at: '2026-05-15T15:02:35.237607'
username: benjamin_van_heerden
---
# Work Log - Setup Branches, Default Docs, and Merge Commands

## Overarching Goals

Improve the coding harness setup and merge workflows while keeping implementation
changes in the `coding/` harness template.

## What Was Accomplished

- Ran project onboarding and read the generated onboard context.
- Updated onboard work-log rendering so selected logs display oldest first.
- Investigated why `README.md` appeared in onboard output and confirmed the
  active `[[files]]` entry in `.agent_core/config.toml` caused it.
- Updated `coding/setup.sh` so missing configured protected branches are created
  instead of hard-failing. The setup flow now lists existing branches, prompts
  interactively for `dev`/`test`/`main` mappings, updates config if needed, and
  creates missing local and remote protected branches.
- Updated setup optional-doc behavior so `general.md` and `testing.md` are
  included by default, and remaining optional docs are offered interactively.
- Discussed direnv and project-scoped aliases, then removed the attempted
  direnv/wrapper setup because it was only a human convenience and not reliable
  for non-interactive agent shells.
- Reworked merge command semantics in the coding harness:
  - `merge pr [pr_ref]` lists PRs targeting configured dev when no ref is given,
    and merges a PR number, PR URL, or spec slug from configured dev.
  - `merge into test dev` promotes configured dev into configured test.
  - `merge into test pr [pr_ref]` lists or merges PRs targeting configured test.
  - `merge into main test --force` promotes configured test into configured main.
  - `merge into main pr [pr_ref] --force` lists or merges PRs targeting
    configured main, with all logical main operations requiring `--force`.
- Split merge command implementation to match the harness command pattern:
  `main.py` now wires commands only, with `pr.py`, `into.py`, and `utils.py`
  holding command and shared logic.
- Added `git.merge_ff_only()` for fast-forward protected branch promotion.
- Updated the GitHub flow test command to use the new `merge pr` form.
- Committed and pushed the merge command workflow changes to `dev` in commit
  `5febb63`.
- Investigated why `setup.sh --update` activated a commented README
  `[[files]]` config entry. Confirmed the updater was not preservation-idempotent:
  it treated commented config as missing and could activate or insert defaults.
- Refactored `coding/setup_support/upsert_config.py` so existing configs are
  updated conservatively: active or commented sections/keys count as declared,
  and commented config is not activated. Brand-new configs still get a complete
  default template.
- Updated `coding/setup.sh` to read configured `worktree.symlink_paths` and
  ensure each path is present in `.gitignore` both with and without a trailing
  slash.
- Added setup regression coverage for commented config staying commented and
  symlink paths being ignored without duplication.
- Discussed a transient `ty` unresolved import diagnostic for the new merge
  utility module. Temporarily switched sibling imports to relative form, then
  the issue was confirmed to be a caching problem by the user.
- Verified shell syntax and Python module compilation for touched code, and
  checked merge command help output.

## Key Files Affected

- `coding/.agent_core/harness/src/commands/onboard.py`
- `coding/setup.sh`
- `coding/setup_support/upsert_config.py`
- `coding/tests/test_setup.py`
- `coding/.agent_core/harness/src/commands/merge/main.py`
- `coding/.agent_core/harness/src/commands/merge/pr.py`
- `coding/.agent_core/harness/src/commands/merge/into.py`
- `coding/.agent_core/harness/src/commands/merge/utils.py`
- `coding/.agent_core/harness/src/utils/git.py`
- `coding/tests/test_github_flow.py`
- `.agent_core/logs/benjamin_van_heerden_20260515_150235_session.md`

## What Comes Next

- Review the merge command behavior carefully, especially PR listing/merge
  behavior for configured `test` and `main` branches.
- Run focused tests when requested, likely setup tests and merge/GitHub flow
  tests if a suitable GitHub test environment is available.
- Decide whether to keep the relative sibling imports in merge subcommands or
  restore full `src.commands.merge.utils` imports now that the diagnostic appears
  to have been cache-related.
- Commit and push the latest setup idempotence and `.gitignore` changes.
- Install/update the project-local harness from `coding/` when ready so root
  `.agent_core/harness/` receives the template updates.
