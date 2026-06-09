---
title: Add coding harness onboard refresh command
status: open
issue_id: 30
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/30
created_at: '2026-06-09T16:25:09.563859'
claimed_by: null
claimed_at: null
---
Add an onboard refresh command for the coding/ harness intended to be run immediately after context compaction events. The goal is to get an agent back on track with the current work: where we are, what branch/spec/todo/log state matters, what we are working on, and what the next harness-aligned action should be. Investigate whether this should be a lightweight command that emits only the existing onboard output section starting at the ONBOARD OUTPUT heading, excluding broader codebase docs/conventions/memories/config-derived context, or whether a full onboard is required to preserve session and harness coherence. The command should revise the agent instruction for refresh semantics: it should orient the agent after compaction rather than behave like first-session onboarding. Consider naming, stdout/file-output behavior, whether git/GitHub sync or auto-update should run, whether assigned worktree creation is appropriate, and how to avoid agents flailing or losing alignment after compaction.