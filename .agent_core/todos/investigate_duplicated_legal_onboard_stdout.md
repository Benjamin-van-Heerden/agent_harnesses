---
title: Investigate duplicated legal onboard stdout
status: open
issue_id: 28
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/28
created_at: '2026-05-28T17:52:19.870836'
claimed_by: null
claimed_at: null
---
Legal onboard on Windows printed the local git snapshot and onboard context path block twice for the same timestamp: Created local git snapshot: 2026-05-28 17:50:30, then Legal onboard context written to .praxis\tmp\onboard_20260528_175030.md, line count 1452, NB read instruction; the exact same block repeated immediately. Investigate whether Typer callback execution, auto-update reexec, command registration, or snapshot/output emission is causing duplicate stdout, and add a regression test once understood.