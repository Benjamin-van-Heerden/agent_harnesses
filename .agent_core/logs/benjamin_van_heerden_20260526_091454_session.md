---
created_at: '2026-05-26T09:14:54.155216'
username: benjamin_van_heerden
---
Work Log - Multi-user coding harness update verification

## Overarching Goals

Verify the open todo about multi-user coding harness auto-update behavior. The expected behavior was that when one user runs an update and commits/pushes the refreshed installed runtime plus `.agent_core/config.toml` timestamp, other users should pick that state up on their next onboard through the normal fetch/sync path.

## What Was Accomplished

### Claimed the todo

Claimed `Verify multi-user coding harness update behavior` through the harness. The command moved the todo to `.agent_core/todos/claimed/`, committed the claim on `dev`, pushed it, and closed GitHub issue #19.

### Verified the update flow

Inspected the coding harness onboard path:

- `onboard` runs `run_git_preflight()` first, which fetches and refuses dirty worktrees.
- `onboard` then runs `auto_update.maybe_update()` before `sync_all()`.
- `sync_all()` is the step that fast-forwards a behind `dev` branch through `protected_branch_sync()`.
- `auto_update.update()` reads the local stale `.agent_core/config.toml` before the branch fast-forward happens.

Ran local two-clone simulations against a bare repository to verify both relevant cases:

- If the second user's stale local `last_updated_at` is not due, `auto_update` skips and the later protected-branch sync fast-forwards `dev` to `origin/dev`. This matches the expected multi-user behavior.
- If the second user's stale local `last_updated_at` is due, `auto_update` runs before the fast-forward. It can create a duplicate local `harness updated YYYYMMDD` commit and then fail to push because `origin/dev` already contains the first user's update. The simulated result was a non-fast-forward push rejection with local `dev` ahead 1 and behind 1.

Conclusion: the expected behavior was only partially correct before the follow-up implementation. The design worked after the first user's pushed update was pulled into the local checkout, and it worked immediately when the stale local timestamp was not due. It did not fully self-heal when a behind user was also locally due for auto-update, because auto-update ran before the normal branch sync.

### Implemented remote harness update handoff

Updated the coding harness onboard preflight so, after the existing fetch and dirty-worktree gate, it checks whether `origin/dev` is ahead and carries a different `.agent_core/config.toml` `[harness].last_updated_at` value. When that condition is true from the configured `dev` branch, onboard now fast-forwards to `origin/dev`, prints a direct rerun instruction, and exits before building context:

"An update to the .agent_core harness has taken place. You must run `python -B .agent_core/harness/main.py onboard` again."

This preserves the existing clean-worktree requirement. Dirty worktrees still stop before sync/rebase and now include an explicit escape hatch: if the user chooses to ignore git/GitHub sync and continue with local context, the agent can run `python -B .agent_core/harness/main.py onboard --no-sync`.

Added a focused regression test covering the remote harness update handoff with two local clones and a bare remote. Also expanded the dirty-worktree onboard test to assert the new `--no-sync` escape-hatch guidance.

Ran `python -B coding/setup.py --update` to propagate the coding template changes into the installed `.agent_core/harness` runtime and managed root `AGENTS.md`.

## Key Files Affected

- `.agent_core/todos/claimed/verify_multi_user_coding_harness_update_behavior.md`: todo claimed by the harness.
- `coding/.agent_core/harness/src/commands/onboard/preflight.py`: added remote harness timestamp detection, fast-forward handoff, rerun instruction, and shared `--no-sync` escape-hatch guidance.
- `coding/.agent_core/harness/src/commands/onboard/main.py`: handles the restart-required preflight result and reuses the shared escape-hatch guidance for later git-sync failures.
- `coding/tests/test_onboard.py`: added regression coverage for the remote update handoff and dirty-worktree escape-hatch text.
- `coding/AGENTS.md`: included the user-provided update requiring permission before creating work logs.
- `.agent_core/harness/src/commands/onboard/preflight.py` and `.agent_core/harness/src/commands/onboard/main.py`: refreshed installed runtime copies via `python -B coding/setup.py --update`.
- `AGENTS.md`: refreshed installed managed instructions from the coding template.
- `.agent_core/config.toml`: updated harness `last_updated_at` during local harness update.
- `.agent_core/logs/benjamin_van_heerden_20260526_091454_session.md`: session log created and updated.

## Errors and Barriers

The first local simulation accidentally read this repository's `.agent_core/config.toml` because the Python process stayed in the original working directory. It was rerun with `cwd` switched into the simulated second user's clone before importing and running the harness auto-update module.

One simulation also produced a byte-identical duplicate commit because both simulated users committed the same tree, parent, author, message, and timestamp within the same second. The scenario was rerun with distinct commit metadata to reflect real multi-user timing.

The first `python -B coding/setup.py --update` attempt failed inside the default sandbox because setup fetches origin while validating protected branches. It was rerun with elevated network access and completed successfully.
