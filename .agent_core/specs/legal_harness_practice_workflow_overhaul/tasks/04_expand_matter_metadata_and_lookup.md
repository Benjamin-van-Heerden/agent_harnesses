---
title: Expand matter metadata and lookup
status: todo
created_at: '2026-05-25T15:15:47.413851'
updated_at: '2026-05-25T15:15:47.413851'
completed_at: null
---
Extend matter status frontmatter and typed models with physical_files: list[str], workflow: str | None, and last_touched_at: str | None. Physical file numbers are arbitrary strings and must not be forced through slug validation. Improve matter find and matter resolution to search matter directory names, client slug, client display name, matter type, status, case number, physical file numbers, tags, and workflow. Ambiguous lookup must list all matching matters and stop with guidance to ask the lawyer which matter to use. Add tests for file-number lookup, multi-match ambiguity, and richer search results.