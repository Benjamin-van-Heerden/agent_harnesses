---
title: Update legal workspace layout
status: todo
created_at: '2026-05-25T15:15:31.800766'
updated_at: '2026-05-25T15:15:31.800766'
completed_at: null
---
Change the legal harness source of truth under legal/ so new installs use ZZ_CLIENTS/ instead of clients/ and create root-level WIP/drafts/ and WIP/experiments/. Update path helpers, setup directory creation, docs, tests, and command output. Do not implement migration or backward compatibility for existing clients/ installs. Document WIP usage: drafting outside a matter, template/style experiments, workflow iteration, and keeping organized subfolders rather than loose files.