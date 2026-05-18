---
created_at: '2026-05-18T17:36:52.266842'
username: benjamin_van_heerden
---
# Work Log - Onboard and Spec Lifecycle Workflow

## Overarching Goals

Bring the project-local coding harness closer to the original mem workflow where
that workflow had already proven useful, while preserving the newer explicit
project-local command shape.

The main goals were:

- Make onboarding trustworthy by resolving git state before generating context.
- Restore spec-aware onboard output for worktree sessions.
- Make task commands infer the active spec when run from a spec worktree.
- Tighten the spec creation, sync, assignment, completion, merge, and sync
  lifecycle around `dev` as mission control.
- Preserve strong, directive stdout guidance throughout the workflow.

## What Was Accomplished

- Updated `onboard` so it fetches before context generation, blocks dirty
  worktrees before producing context, supports `--continue`, and prints recovery
  guidance when git state must be resolved first.
- Restored much of the original spec-aware onboard shape:
  - project info and current branch context;
  - active spec details when on a spec branch;
  - pending task bodies and completed task summaries;
  - diff stat versus dev for active specs;
  - spec-specific work logs in worktrees;
  - main-repo available specs, active worktrees, open todos, memories, recent
    work logs, workflow hints, and next steps.
- Made task commands active-spec aware by default when run from a spec worktree:
  - `task new`;
  - `task list`;
  - `task show`;
  - `task complete`;
  - `task amend`;
  - `task rename`.
- Added `--spec <slug>` to task commands as the explicit escape hatch for
  managing another spec outside its worktree.
- Added `spec sync <slug>` as the spec-preparation command for creating or
  updating the linked GitHub issue, committing/pushing issue metadata, and
  guiding the next step to `spec assign`.
- Expanded `spec new` stdout to restore the original workflow guidance around
  writing detailed spec bodies/tasks before assignment and starting a new agent
  session in the worktree after assignment.
- Tightened `spec assign`:
  - must run from the main repository on `dev`;
  - refuses worktree execution;
  - requires the spec to already have a GitHub issue from `spec sync`;
  - refuses specs assigned to someone else;
  - creates/pushes the worktree branch;
  - syncs GitHub assignment;
  - prints strong “start a new session in the worktree” guidance.
- Tightened `spec complete`:
  - must run from the active spec worktree branch;
  - requires all tasks to be complete;
  - requires at least one work log;
  - requires synced GitHub issue state;
  - commits and pushes implementation work before rebasing;
  - rebases onto `origin/dev`;
  - prints explicit manual recovery steps on rebase failure;
  - creates the PR before mutating local spec status;
  - records `merge_ready` and PR URL together, commits and force-pushes that
    metadata, then updates the GitHub issue label.
- Updated merge commands:
  - `merge pr` now runs from clean `dev`;
  - PR URL is the preferred reference, while PR numbers and spec slugs still
    work;
  - spec cleanup resolves from PR URL or PR head branch;
  - after PR merge, local `dev` is pulled, spec state is moved to completed,
    completed state is committed/pushed, then remote issue/branch cleanup runs;
  - promotion commands run from clean `dev` and return to `dev`;
  - `merge into main test` is dry-run by default and requires `--force`.
- Updated `sync all`:
  - main repo sync must run from `dev`;
  - worktree sync only rebases the current spec/noswitch branch against its
    configured upstream and does not attempt protected branch checkout;
  - dirty tracked changes and rebase failures print explicit recovery guidance;
  - merged `merge_ready` specs can be completed from clean `dev`;
  - `sync issues` remains the broad issue reconciliation command.
- Verified the changed command modules with focused static checks:
  - `uvx ruff check`;
  - `uv run ty check`;
  - `python -B -m py_compile`;
  - command help smoke checks;
  - `git diff --check`.

## Key Files Affected

- `coding/.agent_core/harness/src/commands/onboard.py`
- `coding/.agent_core/harness/src/commands/task/utils/active.py`
- `coding/.agent_core/harness/src/commands/task/new.py`
- `coding/.agent_core/harness/src/commands/task/list.py`
- `coding/.agent_core/harness/src/commands/task/show.py`
- `coding/.agent_core/harness/src/commands/task/complete.py`
- `coding/.agent_core/harness/src/commands/task/amend.py`
- `coding/.agent_core/harness/src/commands/task/rename.py`
- `coding/.agent_core/harness/src/commands/spec/new.py`
- `coding/.agent_core/harness/src/commands/spec/sync.py`
- `coding/.agent_core/harness/src/commands/spec/main.py`
- `coding/.agent_core/harness/src/commands/spec/assign.py`
- `coding/.agent_core/harness/src/commands/spec/complete.py`
- `coding/.agent_core/harness/src/commands/merge/pr.py`
- `coding/.agent_core/harness/src/commands/merge/into.py`
- `coding/.agent_core/harness/src/commands/merge/utils.py`
- `coding/.agent_core/harness/src/commands/sync/main.py`
- `.agent_core/logs/benjamin_van_heerden_20260518_173652_session.md`

## What Comes Next

- Update focused tests that still encode the old behavior, especially:
  - onboard dirty-sync behavior;
  - task commands requiring explicit spec slugs;
  - spec lifecycle and merge flow expectations.
- Review and, if needed, further polish stdout wording against the original mem
  implementation.
- Consider reintroducing manual merge in a separate focused pass.
- Commit and push the accumulated changes, then run the normal harness update
  loop when ready so the installed `.agent_core/harness` copy receives the
  template changes.
