---
title: Fold legal operating model into AGENTS.md
status: completed
created_at: '2026-05-26T14:34:47.987638'
updated_at: '2026-05-26T14:49:45.157289'
completed_at: '2026-05-26T14:49:45.157289'
---
Move the practical content from legal/optional_docs/legal_harness_function.md into the managed block in legal/AGENTS.md. Installed guidance must use python -B .praxis/harness/main.py onboard and python -B .praxis/harness/main.py compile <source.typ>. Preserve the lawyer-facing contract, command hierarchy, state model, action triggers, chronology/obligation/todo/memory distinctions, drafting rules, WIP rules, Typst compile rule, and confidentiality guidance. Do not make tests assert the entire prose exactly; use stable contract markers instead.

## Completion Notes

Folded the legal operating model into legal/AGENTS.md so the managed guidance is self-contained. Updated installed legal command examples to use python -B .praxis/harness/main.py, expanded command guidance to explain when each command group is relevant and what it roughly does, retained the state model, client and matter guidance, chronology/obligation/todo/memory distinctions, WIP rules, Typst compile rule, drafting guidance, and confidentiality/care rules, and removed the stale dependency on .agent_core/docs/legal_harness_function.md for core workflow guidance.
