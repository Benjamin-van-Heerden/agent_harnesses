---
title: Retire legacy legal command surface
status: completed
created_at: '2026-05-21T09:49:47.869096'
updated_at: '2026-05-22T11:31:06.394363'
completed_at: '2026-05-22T11:31:06.394363'
---
After the native runtime covers the legal workflows, remove or clearly deprecate the legacy command-dispatch surface. The final documented path must not require agents to read legal/agent_rules/commands/*.md or run python agent_rules/scripts/*.py. If compatibility wrappers are kept, they should delegate to native commands or be marked legacy in a way that cannot confuse agents. Ensure setup/update no longer depends on mem-lite, and ensure obsolete files are removed only when their behavior is covered by native commands and tests.

## Completion Notes

Retired the legacy legal command-dispatch surface after native runtime coverage was implemented. Removed legal/bash_setup.sh, removed template-level legal/agent_rules/commands markdown playbooks, and removed standalone legal/agent_rules/scripts command helpers. Relocated remaining reusable template assets into native legal/.agent_core locations: docs under legal/.agent_core/docs, lawyer profile under legal/.agent_core/practice/lawyer_profile.md, and markdown skeletons under legal/.agent_core/practice/templates. Updated legal/setup.py to install practice defaults and managed docs from the native template tree while preserving migration support for existing installed projects that still have agent_rules state. Updated focused tests to assert the old template command surface is gone and native docs are the source of install/update truth. Verified legal/tests/test_setup.py plus Ruff and ty on touched Python files.
