---
created_at: '2026-03-03T12:37:54.063032'
username: benjamin_van_heerden
---
# Work Log - Fix sync bugs and add ADR command

## Overarching Goals

Address three open todos: fix merge-ready specs being reset to todo during sync (#91), fix user_mappings.toml not updating during sync (#93), and add an ADR (Architecture Decision Record) command (#92).

## What Was Accomplished

### Fixed merge-ready specs reset to todo during sync (#91)

Root cause: when returning to dev after completing a spec, `build_sync_plan()` in sync.py reads the spec file from the dev branch (which still has `status: todo`). It then pushes that stale status to GitHub, overwriting the correct `merge_ready` label set by `mem spec complete` on the feature branch.

Fix: added a check in the status sync logic — when GitHub has `merge_ready` and local has `todo`, the sync direction is now inbound (trust GitHub) instead of outbound. The local spec file on dev gets updated to `merge_ready` rather than overwriting GitHub's correct label.

### Fixed user_mappings.toml not updating during sync (#93)

Previously, `user_mappings.toml` was only populated during `mem init`. New collaborators who skipped init and went straight to `mem sync` would not be added.

Fix: added a step at the very end of the sync function (after all other operations) that checks if the current git user exists in `user_mappings.toml`. If not, it adds them using the authenticated GitHub username and git config name/email, then commits and pushes with a descriptive message. Runs last so it doesn't dirty the repo during main sync operations. Errors are silently caught since this is a nice-to-have.

### Added ADR command (#92)

Full implementation of `mem adr` command group for managing Architecture Decision Records. ADRs document decisions that overrule or modify active SOWs or agreements, with enforced referential integrity to source documents.

Key design decisions:
- Agreement documents must live in `.mem/docs/agreements/` as markdown files
- ADRs must reference at least one agreement document — validated at creation time
- References are `{document, section}` pairs where `document` must resolve to a real file and `section` is a free-text note describing which part
- CLI uses `--ref "document:section note"` format (repeatable)
- Correspondence records tracked separately via `mem adr link`

Subcommands: `new`, `list`, `show`, `update`, `link`, `delete`, `documents`

### Claimed all three todos

Claimed and closed GitHub issues #91, #92, #93.

## Key Files Affected

- `src/commands/sync.py` — Status sync logic fix (merge_ready precedence), user_mappings.toml check at end of sync, added imports for `get_authenticated_user` and `get_git_user_info`
- `src/models.py` — Added `ADRDocumentReference`, `ADRFrontmatter`, `ADRStatus`, `create_adr_frontmatter()`
- `src/utils/adrs.py` — New file: CRUD operations, document validation, correspondence linking, slug resolution
- `src/commands/adr.py` — New file: Typer command group with all subcommands
- `src/templates/adr.md` — New file: ADR body template
- `env_settings.py` — Added `adrs_dir` property
- `main.py` — Registered adr_app

## What Comes Next

- Changes need to be committed and pushed to dev
- The ADR feature should be tested on a real project with actual agreement documents
- Consider adding ADR listing to the onboard output so agents see existing ADRs
- The codebase reference doc should be updated to reflect the new ADR command
