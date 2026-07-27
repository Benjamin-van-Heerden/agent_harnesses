---
created_at: '2026-07-27T17:02:42.448728'
username: benjamin_van_heerden
---
Work Log - Standardized PR review and linear promotion workflow

## Overarching Goals

Design and implement a harness-owned pull request and protected-branch promotion workflow for the coding harness. The workflow needed to preserve a single linear ancestry across `dev → test → main`, prevent active promotion PRs from being polluted by later changes, standardize agent review and merge behavior, provide a deliberately guarded direct-promotion escape hatch, and keep temporary remote branches clean.

The interaction also clarified how this model scales: spec branches are the intended short-lived implementation branches, `dev` is the integration branch, and promotions are coordinated team release events rather than ordinary feature merges.

## What Was Accomplished

### Promotion lifecycle

Added a two-stage `promotion create <test|main>` workflow:

1. Preparation validates GitHub authentication and ensures no promotion is already open for the destination.
2. It synchronizes and checks out the actual source branch (`dev` for test or `test` for main).
3. It creates an ignored promotion-description draft under `.agent_core/tmp/` and prints explicit read-only inspection instructions.
4. `--execute` validates the completed description, creates a remote-only `promotion/<destination>/<timestamp>` snapshot from the inspected source checkout, opens the PR, removes the draft, and returns to `dev`.

Promotion execution verifies that the destination is an ancestor of the inspected source and refuses divergent or empty promotions. No local snapshot branch or merge commit is created.

Added an explicit `--no-pr` direct-promotion path. Its first invocation only prints the bypass warning and required confirmation. The follow-up option is hidden from CLI help and absent from `AGENTS.md`. Confirmed direct promotion still enforces clean state, ancestry, no-op checks, and the absence of another promotion PR.

### PR discovery, review, and actions

Added the unified `pr` command group:

- `pr review` discovers open PRs and requires the agent to ask which PR the user means.
- `pr review <ref>` generates complete local review context from the PR description, commits, checks, reviews, comments, changed files, and patches.
- `pr comment`, `pr approve`, and `pr request-changes` submit Markdown responses.
- `pr merge` owns all PR completion behavior.

Promotion PR merges require successful checks, a current approval, no outstanding change request, a valid promotion route, and fast-forward ancestry. Production merges require a separate confirmation revealed by the harness at runtime.

Normal/spec PRs continue to squash into `dev`. After a spec PR merges, the same command completes local spec state, removes the worktree and branches, closes the issue, and synchronizes mission control.

### Removed duplicate merge surface

Removed the legacy top-level `merge` command and its `src/commands/merge/` package. `pr merge` now resolves a PR once and directly owns normal/spec and promotion completion. `spec complete` and onboard merge-ready output now route agents through `pr review` instead of the retired merge command.

### Cleanup, installation, and guidance

Normal sync/onboard cleanup now deletes remote promotion branches associated with closed or merged PRs. Promotion merging attempts immediate deletion and retains a branch for later reconciliation if GitHub has not yet reported the PR merged.

Updated the installer regression coverage to prove that existing installations delete retired `src/commands/merge/main.py` files and the empty directory during managed harness updates.

Reworked `coding/AGENTS.md` so it contains promotion policy, interpretation rules, primary entry points, and review triggers without listing infrequent secondary commands or revealing confirmation override options. Replaced misleading “promotion artifact” wording with “promotion description draft” throughout the user-facing workflow.

Added focused PR/promotion tests. Final verification completed with 16 passing focused tests, Ruff, `ty`, CLI help inspection, and `git diff --check`.

## Key Files Affected

- `coding/.agent_core/harness/main.py` — registered `pr` and `promotion`; removed the legacy `merge` registration.
- `coding/.agent_core/harness/src/commands/promotion/` — added preparation, reviewed snapshot PR creation, direct promotion, validation, authentication preflight, branch switching, and detailed agent output.
- `coding/.agent_core/harness/src/commands/pr/` — added discovery, review-context generation, PR responses, normal/spec merging, promotion fast-forwards, confirmations, and cleanup.
- `coding/.agent_core/harness/src/commands/merge/` — removed the obsolete command package.
- `coding/.agent_core/harness/src/commands/sync/main.py` — added closed promotion-branch reconciliation.
- `coding/.agent_core/harness/src/commands/spec/complete.py` — changed final handoff from immediate merge to the review workflow.
- `coding/.agent_core/harness/src/commands/onboard/content.py` — changed merge-ready spec guidance to PR review.
- `coding/.agent_core/harness/src/utils/git.py` — added ancestry and commit-equality helpers used by promotions.
- `coding/.agent_core/harness/src/utils/github.py` — reduced normal PR merging to a single resolved pull-request primitive.
- `coding/AGENTS.md` — documented promotion policy, read-only source inspection, direct-promotion interpretation, and review triggers.
- `coding/README.md` — documented the consolidated PR and promotion model.
- `coding/tests/test_pull_request_workflow.py` — added focused workflow, safety, cleanup, branch-switching, and authentication tests.
- `coding/tests/test_setup.py` — added regression coverage for deleting the retired merge package from installed harnesses.

## What Comes Next

- Exercise the complete workflow against a disposable live GitHub repository to validate branch protection compatibility, token permissions, GitHub recognition of fast-forwarded PRs, review gates, and delayed branch cleanup.
- Consider strengthening admission into `dev`: normal/spec PRs conceptually need required checks, approvals, task completion validation, and eventually a merge queue.
- For growth beyond a small team, consider explicit promotion status, cancellation, ownership, queuing, atomic concurrency protection, recovery commands, and deployment/environment visibility. The existing one-active-promotion rule is intended to serialize a coordinated release event, while spec branches remain the short-lived development mechanism.
