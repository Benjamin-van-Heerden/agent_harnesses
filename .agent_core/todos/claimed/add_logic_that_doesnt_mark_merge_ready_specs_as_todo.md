---
title: Add logic that doesn't mark merge ready specs as todo
status: claimed
issue_id: 91
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/91
created_at: '2026-02-24T19:46:45.815605'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-03T12:26:05.915677'
---
When just finishing up a spec, going back to dev and performing 'mem sync' it appears that mem marks the merge ready spec as 'todo' again - this is more an inconvenience at the moment, since I run 'mem merge' directly afterwards and it fixes things again, but it shouldn't do this (it could cause problems in the future). Do research on why this is happening. Here is an example of what I mean:
❯ mem sync
🔄 Synchronizing with GitHub...
   Syncing protected branches...
   Pulling latest changes...
   Fetching GitHub issues...
   Loading local specs...
   Building sync plan...
   ✓ Plan ready (1 action(s) to perform)

🏷️  Syncing status labels...
   ✓ Updated issue #54 labels to 'todo'

============================================================
✅ Sync complete!
============================================================
   📊 Actions executed: 1

❯ mem merge
🔄 Fetching latest changes...
✅ Local branch is up to date.

🐙 Querying GitHub for merge-ready PRs...

✅ Ready to merge:
  1. #56 payments_and_billing (issue #54) [checks: none]
      Author: Benjamin-van-Heerden | Branch: dev-benjamin_van_heerden-payments_and_billing

🔀 Merging PR #56...

🔀 Merging 1 PR(s)...

🔀 Merging #56: payments_and_billing...
  ✅ Merged (SHA: c685799)
  🗑️ Deleted remote branch: dev-benjamin_van_heerden-payments_and_billing
  📂 Removed worktree: payments_and_billing
  🗑️ Deleted local branch: dev-benjamin_van_heerden-payments_and_billing

✅ Merged 1/1 PR(s).
🧹 Pruned stale remote tracking refs.

🔄 Running sync to update local state...
🔄 Synchronizing with GitHub...
   Syncing protected branches...
   ✓ Synced branches: dev (pulled)
   Pulling latest changes...
   Fetching GitHub issues...
   Loading local specs...
   Building sync plan...
   ✓ Plan ready (2 action(s) to perform)

🏷️  Syncing status labels...
   ✓ Updated issue #54 labels to 'merge_ready'

✅ Moving merged specs to completed...
   ✓ Moved "payments_and_billing" to completed/
   ✓ Closed issue #54

📤 Committing and pushing changes...
   ✓ Changes pushed to remote

============================================================
✅ Sync complete!
============================================================
   📊 Actions executed: 2

💡 Next step: mem merge into test