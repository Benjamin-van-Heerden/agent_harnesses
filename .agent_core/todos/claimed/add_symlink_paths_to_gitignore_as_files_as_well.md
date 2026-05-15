---
title: Add symlink paths to gitignore *as files* as well
status: claimed
issue_id: 70
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/70
created_at: '2026-02-02T10:38:12.753958'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-02T10:42:38.813074'
---
Git version control picks up symlinks as files, even if they symlink to directories - update gitignore to include both the folder and file variant of the symlink path e.g.
.gitignore

.mem/docs/data/
.mem/docs/data # <-- add this one for each of the symlink paths
