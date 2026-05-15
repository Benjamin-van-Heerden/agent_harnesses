---
title: Remove ADR vector docs global config and unused dependencies
status: completed
created_at: '2026-05-12T16:26:44.055137'
updated_at: '2026-05-13T10:29:48.974490'
completed_at: '2026-05-13T10:29:48.974484'
---
Delete the ADR command surface, ADR utilities, ADR templates, and ADR models. Delete docs index/search/summarization/vector-store command functionality and supporting utilities. Remove global ~/.config/mem template support. Remove dependencies that only existed for deleted functionality, including vector/AI/textual/doc-index dependencies unless a retained command still needs them. Update README, AGENTS template, config models, and tests to reflect .agent_core, local harness invocation, and full-read docs. Keep the changes scoped to functionality explicitly removed by this spec.

## Completion Notes

Added focused harness template regression tests covering setup/update state preservation, config default upsert, stale harness overwrite, no eager tmp creation, and simplified docs onboarding without index/vector data. Verified removed ADR/vector/global-config surfaces are absent from the harness template, standalone product-word scan remains clean for migrated/refactored harness code, Ruff passes, and no bytecode/cache artifacts exist under the template.