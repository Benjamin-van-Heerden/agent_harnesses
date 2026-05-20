---
created_at: '2026-05-20T14:51:52.970128'
username: benjamin_van_heerden
spec_slug: multi_user_spec_assignment
---
Work Log - Multi-user spec assignment

## Overarching Goals

Implement multi-user spec assignment support for the coding harness while preserving the existing current-user assignment workflow. The work needed to let one user assign a spec to another mapped GitHub username, push durable remote assignment state without creating a local worktree for the assigning user, and let the assignee receive the worktree during onboard.

## What Was Accomplished

### Shared user mapping support

Extracted `.agent_core/user_mappings.toml` parsing from log-specific code into a shared typed state module. Work-log username resolution now uses the shared helper, and assignment code can validate explicit assignees with a clear `.agent_core/user_mappings.toml` recovery message.

### Explicit assignee assignment flow

Extended `spec assign` with `--assignee <github_username>`. Bare `spec assign <slug>` still assigns to the authenticated GitHub user, creates a local worktree, pushes the spec branch from that worktree, and updates the GitHub issue assignee. Explicit remote assignment validates the username against user mappings, updates spec assignment metadata, creates and pushes the dev checkpoint when needed, pushes `HEAD` to the assigned remote branch, updates the GitHub issue assignee, and intentionally creates no local worktree for the assigning user.

### Assigned worktrees during onboard

Added an onboard helper that runs after successful normal sync and before context rendering. It detects active specs assigned to the authenticated GitHub user that have a recorded branch but no local worktree, fetches remote refs, validates `origin/<branch>` exists, and creates the local worktree from that remote branch. Onboard output now reports any worktrees created for assigned specs.

### Assignment guidance

Updated stdout guidance for `spec new`, `spec sync`, `spec assign`, and onboard created-worktree notices so the two assignment modes are explicit. The user also adjusted task workflow guidance so agents complete tasks serially, mark each one complete after approval, and continue to the next task instead of stopping unnecessarily.

### Tests

Added focused tests for current-user assignment regression, remote-user assignment with a mapped assignee, invalid explicit assignee guidance, onboard assigned-worktree creation from the recorded branch, remote worktree tracking behavior, and stdout snippets that distinguish assignment modes.

## Key Files Affected

- `coding/.agent_core/harness/src/state/user_mappings.py`: new shared typed user mapping loader, current username resolver, and explicit assignee validation helper.
- `coding/.agent_core/harness/src/state/logs.py`: removed local user mapping parsing and reused the shared helper.
- `coding/.agent_core/harness/src/commands/spec/assign.py`: split assignment into reusable validation, checkpoint, local assignment, and remote assignment helpers; added `--assignee`.
- `coding/.agent_core/harness/src/utils/git.py`: added `push_ref()` for pushing `HEAD` to an explicit remote branch.
- `coding/.agent_core/harness/src/utils/worktrees.py`: added `create_from_remote()` for creating a worktree from `origin/<branch>`.
- `coding/.agent_core/harness/src/commands/onboard/assigned_worktrees.py`: new onboard helper for assigned worktree detection and creation.
- `coding/.agent_core/harness/src/commands/onboard/main.py`: runs assigned-worktree creation after successful sync and before context rendering.
- `coding/.agent_core/harness/src/commands/onboard/content.py`: includes assigned-worktree notices and the updated task workflow wording.
- `coding/.agent_core/harness/src/commands/spec/new.py` and `coding/.agent_core/harness/src/commands/spec/sync.py`: updated assignment guidance.
- `coding/.agent_core/harness/src/commands/task/complete.py`: updated workflow output to direct agents to continue after task completion.
- `coding/tests/test_multi_user_assignment.py`: new focused test coverage for the multi-user assignment workflow.
