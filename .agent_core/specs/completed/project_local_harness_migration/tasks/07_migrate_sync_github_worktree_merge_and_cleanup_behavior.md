---
title: Migrate sync GitHub worktree merge and cleanup behavior
status: completed
created_at: '2026-05-12T16:26:35.278757'
updated_at: '2026-05-13T10:23:10.433236'
completed_at: '2026-05-13T10:23:10.433227'
---
Move sync, GitHub, worktree, merge, and cleanup behavior into typed subapps/modules with clear shared boundaries. GitHub token checks must happen only when GitHub calls are required. Preserve protected branch sync, issue sync, PR creation/merge behavior, worktree detection, branch aliases for main/test, dev branch invariants, and cleanup behavior. Shared Git/GitHub/worktree helpers should live under src/utils only when used by multiple command families. Verify with focused command-level checks rather than a full-suite loop.

## Completion Notes

Migrated sync, GitHub, worktree, merge, and cleanup behavior into the project-local harness template. Added neutral shared utilities for git operations, explicit GitHub-token-authenticated helpers, worktree operations, errors, and branch config. Added sync commands for status, branch sync, GitHub user lookup, issue sync, and default sync with local state commit/push. Added issue sync for local specs/todos to GitHub issues and remote issue import, preserving compatibility labels at runtime. Migrated spec assign to assign the authenticated GitHub user, record branch metadata, create a worktree, push the branch, and sync issue assignment. Migrated spec complete to validate tasks, commit/push/rebase, mark merge_ready, update issue labels, create a PR, record PR URL, and push metadata. Migrated merge to merge recorded PRs, close/relabel issues, mark specs completed, delete branches, remove worktrees, and sync dev. Added cleanup commands for pruning refs, protected-branch-safe branch deletion, and completed worktree cleanup. Verified with focused Ruff, no standalone product-word usage in harness code/setup/support scripts, no generated cache files, local git smoke tests, command import/help checks, and token gating checks showing non-GitHub commands work without GITHUB_TOKEN while GitHub paths fail with actionable guidance.