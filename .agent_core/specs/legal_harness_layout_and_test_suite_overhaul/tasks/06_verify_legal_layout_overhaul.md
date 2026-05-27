---
title: Verify legal layout overhaul
status: completed
created_at: '2026-05-26T14:35:22.613100'
updated_at: '2026-05-27T11:27:19.754080'
completed_at: '2026-05-27T11:27:19.754080'
---
Run focused verification for the changed legal harness files. At minimum run the reorganized legal tests relevant to setup/runtime/onboard/commands, focused ruff on edited Python files, focused ty on edited Python files, and git diff --check. Do not run unrelated full suites unless the implementation blast radius makes that necessary and the user approves.

## Completion Notes

Ran focused verification for the legal layout overhaul. Verified the reorganized legal test suite with uv run pytest legal/tests, which passed 20 tests. Ran focused ruff with uvx ruff check legal/.agent_core/harness legal/tests, which passed. Ran type checking with uv run ty check legal/.agent_core/harness legal/tests, which passed. Ran git diff --check, which passed. Noted that an initial uvx ty check failed because the isolated uvx environment lacked legal harness dependencies, then reran ty in the project environment successfully.
