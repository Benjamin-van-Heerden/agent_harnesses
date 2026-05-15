---
title: Add a memory system
status: claimed
issue_id: 79
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/79
created_at: '2026-02-11T10:57:14.194576'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-11T11:08:21.955589'
---
mem memory create/update/delete command that creates memory markdown files, a memory is a short, atomic note about a pattern, preference, convention, or useful reference in this codebase. Examples:
- 'We use X library for Y — see path/to/file for the pattern'
- 'When doing Z, always do it this way because...'
- 'If you need to do X, look at path/to/file to see how it was done before'

Memories can be created in two ways:
1. **User requests it** — the user explicitly asks to remember something.
2. **Agent suggests it** — during work, you notice a pattern, convention, or lesson worth preserving. Suggest it to the user and only create it if they agree.

Then crucially in 'onboard' all memories should be read and listed