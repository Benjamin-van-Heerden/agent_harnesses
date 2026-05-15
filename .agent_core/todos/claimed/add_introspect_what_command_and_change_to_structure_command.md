---
title: Add introspect what command and change to structure command
status: claimed
issue_id: 89
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/89
created_at: '2026-02-24T10:54:53.286788'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-24T18:51:51.661169'
---
refactor the introspect.py command so that the current implementation is called via 'mem instrospect structure' (same functionality just an extra step), then introduce a 'mem introspect what' command - this command produces intructions for the agent to ask the user questions about the codebase's purpose, what are we trying to build/achieve. After these questions, the agent also goes through the codebase to ground itself and finally it produces a core doc 'what.md' meant to communicate this purpose and the overall goal of the project. The setup should be very similar in structure to how the current command works, but more goal oriented if that makes sense. Being a core document, this means that on every onboard.py the agent will have a very clear picture of what they are working with.