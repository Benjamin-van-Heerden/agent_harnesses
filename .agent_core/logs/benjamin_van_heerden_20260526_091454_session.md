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

Conclusion: the expected behavior is only partially correct. The design works after the first user's pushed update is pulled into the local checkout, and it works immediately when the stale local timestamp is not due. It does not fully self-heal when a behind user is also locally due for auto-update, because auto-update currently runs before the normal branch sync.

## Key Files Affected

No source files were changed.

- `.agent_core/todos/claimed/verify_multi_user_coding_harness_update_behavior.md`: todo claimed by the harness.
- `.agent_core/logs/benjamin_van_heerden_20260526_091454_session.md`: session log created.

## Errors and Barriers

The first local simulation accidentally read this repository's `.agent_core/config.toml` because the Python process stayed in the original working directory. It was rerun with `cwd` switched into the simulated second user's clone before importing and running the harness auto-update module.

One simulation also produced a byte-identical duplicate commit because both simulated users committed the same tree, parent, author, message, and timestamp within the same second. The scenario was rerun with distinct commit metadata to reflect real multi-user timing.

## What Comes Next

If the desired behavior is full automatic self-healing, adjust onboard so a behind main checkout fast-forwards from `origin/dev` before deciding whether auto-update is due, or make auto-update detect that the current branch is behind `origin/dev` and skip/defer to sync before attempting a setup update.
