---
created_at: '2026-03-07T17:42:14.487407'
username: benjamin_van_heerden
---
# Work Log - Fix sync detecting archived specs by slug

## Overarching Goals

Fix a persistent sync bug where `mem sync` repeatedly tried to create a local spec that already existed as a completed/archived spec, caused by a duplicate GitHub issue with a different issue number.

## What Was Accomplished

### Diagnosed root cause

The studii project had two GitHub issues for the same spec "UI housekeeping and polish": #60 (open, with template body) and #61 (closed, linked to the archived spec). The archived spec lookup only matched by `issue_id` (61), so issue #60 slipped through and was planned as an inbound create every sync.

### Closed the duplicate issue

Closed issue #60 on the studii repo as a duplicate of #61.

### Added slug-based matching for archived specs

Extended `build_sync_plan` to also build an `archived_slugs` set from completed/abandoned specs. The stale issue check now matches on both `issue_id` and `slugify(issue_title)`, so duplicate or reused-title issues for archived specs are caught and queued for closing.

## Key Files Affected

- `src/commands/sync.py` — Added `archived_slugs` set alongside `archived_issue_ids`, extended the stale issue check condition to include slug matching.

## What Comes Next

- Commit and push changes to dev
