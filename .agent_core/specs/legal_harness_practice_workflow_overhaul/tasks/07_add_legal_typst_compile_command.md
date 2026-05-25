---
title: Add legal Typst compile command
status: todo
created_at: '2026-05-25T15:16:13.683021'
updated_at: '2026-05-25T15:16:13.683021'
completed_at: null
---
Add a legal harness command that wraps Typst compilation instead of relying on agents to call typst compile directly. The command should compile a .typ source and write <source-stem>.p.pdf. Update legal .gitignore generation so *.p.pdf is ignored. matter focus should distinguish Typst sources, generated .p.pdf outputs, and other PDFs/source material. Add tests for output naming, gitignore coverage, missing Typst handling if applicable, and focus output classification.