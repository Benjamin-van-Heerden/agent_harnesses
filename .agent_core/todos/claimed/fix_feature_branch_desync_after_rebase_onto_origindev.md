---
title: Fix feature branch desync after rebase onto origin/dev
status: claimed
issue_id: 68
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/68
created_at: '2026-01-27T11:19:24.220304'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-01-27T11:37:23.488869'
---
In sync.py git_fetch_and_pull(), after successfully rebasing a feature branch onto origin/dev, the local commit hashes change but the remote feature branch still has old hashes. This causes push rejections when the user later tries to push.

Problem flow:
1. User is on dev-feature-branch with commits A, B, C pushed to origin
2. mem onboard/sync runs, rebases onto origin/dev
3. Commits become A', B', C' (new hashes due to rebase)
4. User works, commits D', tries to push
5. Push rejected: origin has A, B, C but local has A', B', C', D'

Fix: After successful rebase onto origin/dev in git_fetch_and_pull(), add a force push with lease to update the remote feature branch:

After the rebase success block (around line 320), add:
- subprocess.run(['git', 'push', '--force-with-lease'], cwd=cwd, capture_output=True, text=True)
- Don't fail if push fails (remote branch might not exist yet for new specs)
- Log success/failure for debugging

This is safe because:
- Only affects dev-* feature branches (checked by is_feature_branch())
- --force-with-lease fails if someone else pushed since last fetch
- Protected branches (dev/test/main) use separate sync_protected_branches() with ff-only merges