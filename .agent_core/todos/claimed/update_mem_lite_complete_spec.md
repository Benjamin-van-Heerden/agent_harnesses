---
title: Update mem lite complete spec
status: claimed
issue_id: 100
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/100
created_at: '2026-03-13T14:53:14.451048'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-16T09:55:30.742233'
---
When we do the 'pr' workflow (should rename or think about this as we won't actually be creating a pr (we could though) - we should add instructions in the complete_spec command so that we push the merged commit as well. Think about this a bit, how do we really want to do this, I think we should go for the actual PR approach as it is more standard, but then we need another command c_clean_git which handles cleanup of branches, both local and remote for merged work.