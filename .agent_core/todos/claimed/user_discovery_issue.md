---
title: user discovery issue
status: claimed
issue_id: 93
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/93
created_at: '2026-02-25T16:00:50.741912'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-03T12:26:12.638479'
---
user_mappings.toml file is not being updated properly, investigate this, can do a check in sync and if the git.config.user.name is in the file then all fine, otherwise we need to add it. Do it in such a way that it does not first make the repo dirty and the rest of sync fails, this can happen last (and likely we should commit and push as well for 'updated user_mappings.toml with: {user_name}' or something.