---
title: Commit and push automatically when todos are claimed
status: open
issue_id: 11
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/11
created_at: '2026-05-20T17:06:54.915908'
claimed_by: null
claimed_at: null
---
Update the coding harness todo claim flow so claiming a todo records and publishes the state change. Today todos are used to hand work off for later; when a todo is claimed, the local todo state and linked GitHub issue should not be left only in the working tree. Investigate coding/.agent_core/harness/src/commands/todo/claim.py and related state/GitHub helpers, then make the claim command commit and push the todo state after a successful claim, matching the project-local harness expectation that durable task/todo state is shared through git. Preserve clear stdout that tells the agent what changed and what to do next.