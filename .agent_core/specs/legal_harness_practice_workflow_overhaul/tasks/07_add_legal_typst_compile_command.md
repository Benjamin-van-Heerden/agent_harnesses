---
title: Add legal Typst compile command
status: completed
created_at: '2026-05-25T15:16:13.683021'
updated_at: '2026-05-25T16:38:43.621630'
completed_at: '2026-05-25T16:38:43.621630'
---
Add a legal harness command that wraps Typst compilation instead of relying on agents to call typst compile directly. The command should compile a .typ source and write <source-stem>.p.pdf. Update legal .gitignore generation so *.p.pdf is ignored. matter focus should distinguish Typst sources, generated .p.pdf outputs, and other PDFs/source material. Add tests for output naming, gitignore coverage, missing Typst handling if applicable, and focus output classification.

## Completion Notes

Added legal harness compile command that wraps typst compile and writes generated PDFs as <source-stem>.p.pdf. Added workspace-safe Typst source validation and command output identifying generated .p.pdf files. Updated legal gitignore generation to ignore *.p.pdf. Updated matter focus to distinguish Typst sources, generated .p.pdf outputs, and other PDFs. Added AGENTS.md instruction that legal Typst compilation must go through the harness command and must not call typst compile directly. Added behavior-focused tests for compile output naming, gitignore coverage, and focus classification, while removing brittle exact AGENTS wording assertions after user feedback. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited compile/test files, and uvx ruff check on edited files.
