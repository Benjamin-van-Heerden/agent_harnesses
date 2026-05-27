---
title: Improve legal onboard output and work log hygiene
status: open
issue_id: 27
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/27
created_at: '2026-05-27T17:12:01.793955'
claimed_by: null
claimed_at: null
---
Drastically improve the legal harness onboard output in legal/main.py and related onboard code. Take inspiration from coding/'s onboard behavior: provide clearer context about what happened, when it happened, what changed recently, what live matters/todos/obligations need attention, and practical suggestions for what the agent should do next. The onboard output should be more useful as an operational briefing rather than a flat state dump. Also confirm and harden session work-log behavior at onboard time: make it explicit when a work log is created, ensure the current session log path is surfaced clearly, and prune/remove empty work logs so stale empty logs do not accumulate. Preserve the legal harness rule that onboard stays concise and does not become matter analysis.