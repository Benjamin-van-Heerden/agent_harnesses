---
title: Retire legacy legal command surface
status: todo
created_at: '2026-05-21T09:49:47.869096'
updated_at: '2026-05-21T09:49:47.869096'
completed_at: null
---
After the native runtime covers the legal workflows, remove or clearly deprecate the legacy command-dispatch surface. The final documented path must not require agents to read legal/agent_rules/commands/*.md or run python agent_rules/scripts/*.py. If compatibility wrappers are kept, they should delegate to native commands or be marked legacy in a way that cannot confuse agents. Ensure setup/update no longer depends on mem-lite, and ensure obsolete files are removed only when their behavior is covered by native commands and tests.