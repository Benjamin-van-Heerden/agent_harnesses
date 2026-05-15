---
title: Re-order sync
status: claimed
issue_id: 75
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/75
created_at: '2026-02-06T09:51:44.879021'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-06T11:59:53.976738'
---
Currently sync does some 'patching' - we need to change this so that either it does not do explicit patching (likely better, just display a warning) or that the order of events is different. What currently happens is we mem sync, it adds something to .gitignore (now our repo is dirty) and the rest of the sync fails with the warning that there are unstaged local changes.