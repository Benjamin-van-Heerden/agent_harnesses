---
title: Add AGENTS.md drift detection to onboard.py
status: completed
created_at: '2026-01-22T09:14:48.696119'
updated_at: '2026-01-22T09:21:04.105860'
completed_at: '2026-01-22T09:21:04.105855'
---
Add a function to detect AGENTS.md drift by comparing the mem-managed section (content between <MEMCONTENT> tags) against the current template. Handle edge cases: file doesn't exist, file has no tags (legacy), content matches. Return a boolean or drift info that can be used later.

## Completion Notes

Added detect_agents_drift() function that checks if AGENTS.md exists, has MEMCONTENT tags, and if the content matches the current template