---
title: Clean up Agent Core tmp output and reporting workflow
status: open
issue_id: 10
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/10
created_at: '2026-05-20T17:06:37.001682'
claimed_by: null
claimed_at: null
---
Ensure .agent_core/tmp/ is always present in .gitignore for projects using the coding harness, and verify old onboard output files are cleared appropriately so context dumps do not accumulate indefinitely. Investigate where onboard writes large context files and add the smallest safe cleanup behavior, likely around new onboard output creation. Also review coding/.agent_core/harness/src/commands/report/main.py: the report command currently prints raw work log bodies for the current week. Plan and improve it into a useful work-summary command that summarizes what users did from their work logs, with appropriate username filtering, date boundaries, and agent-friendly stdout.