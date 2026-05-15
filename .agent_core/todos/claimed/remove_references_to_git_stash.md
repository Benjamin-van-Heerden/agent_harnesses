---
title: Remove references to git stash
status: claimed
issue_id: 74
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/74
created_at: '2026-02-06T09:49:23.607128'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-06T11:59:59.997302'
---
If sync errors occur we should never git stash, add commit push should be the default (in fact I think we should explicitly say something like 'don't stash, you should always add commit push when resolving sync issues'