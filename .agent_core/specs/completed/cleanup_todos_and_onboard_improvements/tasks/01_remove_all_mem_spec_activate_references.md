---
title: Remove all mem spec activate references
status: completed
created_at: '2026-01-26T09:29:20.825698'
updated_at: '2026-01-26T10:01:43.741297'
completed_at: '2026-01-26T10:01:43.741287'
---
Search entire codebase for 'activate' and 'assign' references to the legacy command. Key files to check: src/commands/init.py, src/commands/onboard.py, src/templates/. Remove or update all occurrences.

## Completion Notes

Updated src/commands/init.py, main.py, and README.md to replace all 'mem spec activate/deactivate' references with 'mem spec assign'. Historical references in .mem/logs/ and .mem/specs/completed/ were intentionally left unchanged as they document the codebase evolution.