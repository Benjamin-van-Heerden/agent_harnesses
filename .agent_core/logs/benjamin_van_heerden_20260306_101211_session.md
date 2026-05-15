---
created_at: '2026-03-06T10:12:11.027638'
username: benjamin_van_heerden
---
# Work Log - Fix sync idempotency bug for unlinked specs

## Overarching Goals

Fix a bug where `mem sync` repeatedly tries to create a spec that already exists locally, producing a warning every run without resolving the underlying issue.

## What Was Accomplished

### Fixed sync linkage loop

Root cause: `build_sync_plan` matches local specs to GitHub issues via `specs_by_issue_id` (keyed by `issue_id` from frontmatter). If a local spec exists by slug but has no `issue_id`, it's invisible to this lookup. The planner sees an unmatched GitHub issue and plans an INBOUND CREATE. `execute_inbound_create` finds the spec already exists by slug, prints a warning, and returns without ever setting the `issue_id`. Next sync repeats the cycle.

Two-layer fix:

1. **Planning (`build_sync_plan`)**: When no match by `issue_id`, added a slug-based fallback lookup via `slugify(issue_title)`. If a local spec exists by slug without an `issue_id`, it's tracked in `slugs_pending_link` and planned as a link action rather than a fresh create. The `slugs_pending_link` set also prevents the outbound creates loop from trying to create a duplicate GitHub issue for the same spec.

2. **Execution (`execute_inbound_create`)**: When the spec already exists without `issue_id`, it now links it (sets `issue_id`, `issue_url`, content hashes) instead of just skipping. Subsequent syncs then find the spec via `specs_by_issue_id` normally.

## Key Files Affected

- `src/commands/sync.py` — `build_sync_plan()`: added slug fallback lookup and `slugs_pending_link` tracking; `execute_inbound_create()`: link existing unlinked specs instead of skipping

## What Comes Next

- Commit and push changes to dev
