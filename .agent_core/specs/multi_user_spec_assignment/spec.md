---
title: Multi-user spec assignment
status: todo
assigned_to: null
issue_id: 7
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/7
branch: null
pr_url: null
created_at: '2026-05-20T13:09:52.754930'
updated_at: '2026-05-20T13:13:47.223340'
completed_at: null
last_synced_at: null
local_content_hash: null
remote_content_hash: null
---
## Overview

Add multi-user spec assignment support to the coding harness. Today `spec assign <slug>` is a single-user flow: it always assigns to the authenticated GitHub user, writes that username to spec frontmatter, creates a local worktree immediately, pushes the spec branch from that worktree, and assigns the linked GitHub issue to the same user.

The new behavior should preserve that default for bare `spec assign <slug>`, while adding an explicit assignee path for assigning work to another GitHub username. Assigning to another user must create durable assignment state and a remote spec branch, but it must not create a local worktree for the assigning user. When the assignee later runs onboard, the harness should detect specs assigned to that authenticated user that do not have local worktrees yet, create the worktrees from the assigned remote branches, and mention what happened without disrupting the broader onboarding flow.

This is a coding harness change. Source edits belong under `coding/`; installed `.agent_core/harness` runtime changes are generated propagation artifacts only.

## Goals

- Preserve the existing current-user assignment workflow for `spec assign <slug>`.
- Add an explicit assignee option for assigning a spec to another GitHub username.
- Require explicit assignees to exist in `.agent_core/user_mappings.toml` before assignment.
- For remote-user assignment, write spec assignment metadata, commit and push the assignment checkpoint on the configured dev branch, create and push the assigned spec branch, sync the GitHub issue assignee, and avoid creating a local worktree for the assigning user.
- During onboard, detect specs assigned to the authenticated GitHub user that have a remote spec branch but no local worktree, then create the local worktree from the remote branch.
- Keep assigned-worktree detection modular enough to expose later as a dedicated command such as `spec sync-assigned` if automatic onboard creation proves too invasive.
- Make command stdout authoritative, clear, and workflow-guiding, especially after spec creation and assignment.

## Technical Approach

Refactor user mapping loading out of `src/state/logs.py` into a shared typed module so assignment validation and work-log username derivation use the same parser. Keep the mapping shape compatible with the current TOML structure:

```toml
[github_username]
name = "Git User Name"
email = "user@example.com"
```

Extend `spec assign` with an optional explicit assignee flag. The exact Typer option name should favor clarity at call sites, for example `--assignee <github_username>`. Bare `spec assign <slug>` must continue to resolve the authenticated GitHub user and run the existing local-worktree flow.

Split assignment into reusable operations:

- validate command context: main repo, configured dev branch, synced dev state, synced GitHub issue;
- resolve current user and explicit assignee;
- validate explicit assignees against `.agent_core/user_mappings.toml`;
- derive the assignment branch as `dev-<slugified_assignee>-<spec_slug>` unless an existing compatible branch is already recorded;
- update spec frontmatter;
- create and push the assignment checkpoint on dev;
- create and push the remote spec branch for remote-user assignments without creating a local worktree;
- create the local worktree and push the branch for current-user assignments;
- update the linked GitHub issue assignee.

Add a worktree helper that can create a local worktree from an existing remote branch. The current `worktrees.create()` creates a missing local branch from the current checkout; that is not safe for onboard-created worktrees where the branch already exists on `origin`. The new helper should explicitly track or check out `origin/<branch>` so the assignee receives the assigned branch state.

Add an onboard helper that runs after the normal sync step and before context rendering. It should:

- resolve the authenticated GitHub username;
- inspect active specs assigned to that username;
- skip specs without a recorded branch;
- skip specs whose local worktree already exists;
- fetch remote branches if needed;
- create missing worktrees from `origin/<record.branch>`;
- return typed results for onboard output.

Onboard output should quietly report any created worktrees near the available-spec/worktree context. It should not force a stop unless creation fails in a way that invalidates the user’s workspace state. If creation fails because a remote branch is missing, stdout/stderr must give a direct recovery instruction.

Stdout requirements are part of the implementation, not polish:

- `spec new` output should explain both assignment modes once a spec is ready: `spec assign <slug>` assigns to the authenticated user and creates a local worktree; `spec assign <slug> --assignee <github_username>` assigns to another mapped user, pushes the remote branch, and does not create a local worktree for the current user.
- `spec assign <slug>` output should continue to end with the “start a new session in the worktree” instruction.
- `spec assign <slug> --assignee <github_username>` output should explicitly say that no local worktree was created, name the assignee, name the pushed branch, and say the assignee will receive/create the worktree on onboard.
- Validation failures should be assertive and actionable: unknown explicit assignees must point to `.agent_core/user_mappings.toml`; missing GitHub issue state must point to `spec sync`; unsynced dev must keep the existing sync/push guidance.
- Onboard output should include a short notice such as: `Spec <slug> was assigned to you; a worktree has been created at <path>.`

## Success Criteria

- Bare `spec assign <slug>` behaves as it does now for current-user assignment.
- `spec assign <slug> --assignee <github_username>` refuses usernames missing from `.agent_core/user_mappings.toml`.
- Remote-user assignment updates spec frontmatter, creates and pushes the dev checkpoint, creates and pushes the remote spec branch, updates the GitHub issue assignee, and leaves no local worktree for the assigning user.
- Onboard creates a missing local worktree for a spec assigned to the authenticated user when the remote branch exists and no local worktree is present.
- Onboard-created worktrees are based on the assigned remote branch, not accidentally on the current dev checkout.
- Command stdout clearly distinguishes current-user assignment from remote-user assignment and tells the next agent exactly what to do.
- Focused tests cover current-user assignment, remote-user assignment, invalid explicit assignee handling, and onboard-created assigned worktrees.

## Notes

The claimed todo that motivated this spec is `.agent_core/todos/claimed/support_assigning_specs_to_other_users.md`.

Relevant current implementation points:

- `coding/.agent_core/harness/src/commands/spec/assign.py` owns the single-user assignment flow.
- `coding/.agent_core/harness/src/utils/worktrees.py` owns local worktree creation and needs an explicit create-from-remote path.
- `coding/.agent_core/harness/src/commands/onboard/main.py` runs sync before context rendering; assigned-worktree detection belongs after sync and before rendering.
- `coding/.agent_core/harness/src/state/logs.py` currently parses `.agent_core/user_mappings.toml`; that parser should become shared.
