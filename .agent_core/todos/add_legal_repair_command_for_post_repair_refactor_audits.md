---
title: Add legal repair command for post-repair refactor audits
status: open
issue_id: 25
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/25
created_at: '2026-05-27T16:59:53.243890'
claimed_by: null
claimed_at: null
---
Add a legal harness repair command that evaluates legal workspace changes since the last repair checkpoint. The command should use git history/status to identify files created or modified after the previous repair, then critically inspect those files for disorganized Typst, duplicated helpers, local one-off structures, weak soft typing, generated PDF rule violations, misplaced source material, and inconsistent layout conventions. It should run an aggressive refactor loop: extract reusable templates/components/types/constants where appropriate, standardize documents, preserve true source evidence, compile through the harness, and lint afterward. When choosing between conflicting patterns, the command should prioritize the style and setup of more recent clean documents over older imported/generated documents, while stopping for human input on legally ambiguous or destructive changes. The repair state should record when the repair last ran so future repairs only examine the new delta.