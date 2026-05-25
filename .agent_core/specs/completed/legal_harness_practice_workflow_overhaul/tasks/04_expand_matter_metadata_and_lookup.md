---
title: Expand matter metadata and lookup
status: completed
created_at: '2026-05-25T15:15:47.413851'
updated_at: '2026-05-25T16:00:03.717660'
completed_at: '2026-05-25T16:00:03.717660'
---
Extend matter status frontmatter and typed models with physical_files: list[str], workflow: str | None, and last_touched_at: str | None. Physical file numbers are arbitrary strings and must not be forced through slug validation. Improve matter find and matter resolution to search matter directory names, client slug, client display name, matter type, status, case number, physical file numbers, tags, and workflow. Ambiguous lookup must list all matching matters and stop with guidance to ask the lawyer which matter to use. Add tests for file-number lookup, multi-match ambiguity, and richer search results.

## Completion Notes

Extended matter status frontmatter and typed models with physical_files, workflow, and last_touched_at, while preserving case_number and tags as searchable metadata. Reworked matter status parsing to read typed list/optional values from frontmatter. Improved matter lookup so matter find and resolver search case-insensitively across matter directory names, client slugs, client display names, matter type, matter status, case number, physical file numbers, tags, and workflow. Ambiguous single-matter resolution now lists every match and instructs the agent to ask the lawyer which matter to use. Updated matter focus and list-unparsed to catch resolver errors cleanly instead of surfacing tracebacks. Updated the status template, legal workflow docs, and focused tests for physical file lookup, workflow/client display search, ambiguity, and typed metadata parsing. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited matter files and tests, and uvx ruff check on edited files.
