---
title: Update legal workspace layout
status: completed
created_at: '2026-05-25T15:15:31.800766'
updated_at: '2026-05-25T15:52:40.150663'
completed_at: '2026-05-25T15:52:40.150663'
---
Change the legal harness source of truth under legal/ so new installs use ZZ_CLIENTS/ instead of clients/ and create root-level WIP/drafts/ and WIP/experiments/. Update path helpers, setup directory creation, docs, tests, and command output. Do not implement migration or backward compatibility for existing clients/ installs. Document WIP usage: drafting outside a matter, template/style experiments, workflow iteration, and keeping organized subfolders rather than loose files.

## Completion Notes

Changed the legal harness source of truth so new installs create ZZ_CLIENTS/ instead of clients/ and create WIP/drafts/ plus WIP/experiments/. Updated runtime path helpers to resolve clients from ZZ_CLIENTS, added WIP root fields and paths output, and added WIP/README.md guidance for non-matter drafting, template/style experiments, workflow iteration, and avoiding loose files in WIP. Updated legal README, installed .agent_core README, optional legal harness function docs, and tests to use ZZ_CLIENTS and assert WIP layout/guidance. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited layout Python files, and uvx ruff check on edited files.
