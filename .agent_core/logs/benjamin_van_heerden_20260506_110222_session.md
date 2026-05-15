---
created_at: '2026-05-06T11:02:22.646709'
username: benjamin_van_heerden
---
# Work Log - Praxis Typst soft-type library and update-safe installer copying

## Overarching Goals

Add the new Praxis Typst soft-type system as an out-of-the-box capability.
The user had added a core document describing the desired `src/types/*.typ`
house rules and wanted the corresponding soft types and typed constants shipped by
`bash_setup.sh` for both fresh installs and existing users via `--update`.

The important installer constraint was that `legal_context.typ` must remain
lawyer-owned and must not be overwritten on update, while canonical
`typst_*.typ` reference files should be refreshed even when they live either
under `agent_rules/docs/core/` or directly under `agent_rules/docs/`.

## What Was Accomplished

### Added local git integration for Praxis projects

- `bash_setup.sh` now fails fast if `git` is not installed or not on PATH.
- Fresh setup runs `git init` in the Praxis target directory.
- `--update` also checks for a local `.git/` directory and initialises one if
  an existing Praxis install predates git support.
- Setup creates or extends `.gitignore` with a managed Praxis block that keeps
  generated office/binary documents out of local git history:
  `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, OpenDocument
  formats, RTF, iWork formats, Office lock files, and common OS noise.
- Existing `.gitignore` content is preserved. If the Praxis block is already
  present, setup leaves it alone.

### Added onboard git snapshot helper

- New script `agent_rules/scripts/git_snapshot.py`.
- It resolves the Praxis root, runs `git add -A`, and creates a local commit
  when there are staged changes.
- It does not push.
- It uses local one-shot git identity settings (`Praxis <praxis@local>`) for
  the commit command so the lawyer does not need global git identity configured
  just to get local snapshots.
- `c_onboard.md` now runs `python agent_rules/scripts/git_snapshot.py` before
  first-run dispatch, so normal and fresh-install onboarding both attempt a
  local snapshot.

### Added canonical Typst `src/` support library

Added `src/templates/mem_lite/praxis/src/` with only the pieces that belong to
the Praxis soft-type foundation:

- Type modules use capitalized filenames and CamelCase constructors:
  `Assert.typ`, `BankAccount.typ`, `Client.typ`, `Company.typ`, `Money.typ`,
  `ShareHolder.typ`, and `WorkEntry.typ`.
- Type validators are exported as `{Type}_assert`.
- Public callable functions remain snake_case, while variables and dictionary
  fields use kebab-case.
- Added generic placeholder constants instead of the original Yhat-specific
  company and bank-account defaults.
- Removed the earlier over-broad invoice rendering functions and templates
  because those belonged to the user's own business setup, not a legal
  practice starter kit.

### Updated `bash_setup.sh`

- `create_directories()` now creates the canonical `src/` tree.
- Fresh init copies `src/` into new Praxis installs.
- `--update` copies `src/` into existing Praxis installs as well.
- `copy_typst_docs()` copies only `agent_rules/docs/**/typst_*.typ` from the
  template, intentionally refreshing canonical Typst docs without touching
  `agent_rules/docs/core/legal_context.typ`.
- `copy_tree()` pruning is now limited to command/script trees. This preserves
  user-added files under `src/` while still allowing stale command/script files
  to be removed on update.
- The init "Next steps" message now tells the user to fill in
  `agent_rules/docs/core/legal_context.typ` instead of referencing the old
  non-existent `typst_reference.typ` path.

### Updated agent instructions

- `AGENTS.md` now documents the new `src/` directory layout and tells the
  agent to read
  `agent_rules/docs/core/typst_soft_typesystem_and_house_rules_updated.typ`
  before creating or editing `src/types/`.
- `c_onboard.md` now includes `src/**/*.typ` in the filename-only Typst
  building-block scan. It deliberately does not scan legacy top-level
  `functions/` or `templates/`; the first post-update job for an existing
  install is to migrate anything useful from those old locations into `src/`
  and adapt it to the current rules.
- `c_initial_setup.md` no longer references the old missing
  `typst_legal_cookbook.typ`; it points at `agent_rules/docs/typst_detailed_reference.typ`
  and now builds the default document template at
  `src/templates/components/style.typ`.
- The soft-type house-rules document's typed-constant example was made generic
  (`default-company`) rather than Yhat-specific.

## Key Files Affected

- `src/templates/mem_lite/praxis/bash_setup.sh` — installer copy/update policy
  for local git init, `.gitignore`, `src/`, and `typst_*.typ` docs;
  `legal_context.typ` preservation.
- `src/templates/mem_lite/praxis/AGENTS.md` — `src/` layout and editing rules.
- `src/templates/mem_lite/praxis/agent_rules/commands/c_onboard.md` — onboard
  scan includes only `src/**/*.typ`; local git snapshot step added.
- `src/templates/mem_lite/praxis/agent_rules/scripts/git_snapshot.py` — local
  git add/commit helper.
- `src/templates/mem_lite/praxis/agent_rules/commands/c_initial_setup.md` —
  corrected Typst reference paths and helper locations.
- `src/templates/mem_lite/praxis/agent_rules/docs/core/typst_soft_typesystem_and_house_rules_updated.typ`
  — generic constant example.
- `src/templates/mem_lite/praxis/src/**` — new canonical Typst support library.
- Existing modified files
  `agent_rules/docs/core/typst_basic_reference.typ` and
  `agent_rules/docs/typst_detailed_reference.typ` were already dirty at the
  start of the session; they were not part of the edits made here.

## Errors and Barriers

No unresolved implementation barriers.

One installer safety issue was caught during review: using `copy_tree "src" ...
true` would have reused the existing update-prune behavior and deleted
user-added files under `src/` if they were not present in the template. Fixed
by limiting pruning to `commands` and `scripts`.

The first pass also brought over too much from `~/Documents/work/src`: invoice
templates, invoice/payment/work-log rendering functions, a theme file, and a
Date soft type. These were removed after the user clarified that Praxis should
only ship the soft-type foundation referenced by the house-rules document and
that `src/types` filenames should remain capitalized.

## What Comes Next

- Decide whether `src/` should always be overwritten on update or only copied
  when missing. The current implementation overwrites canonical filenames but
  preserves user-added files.
- Run a real Praxis `--update` after publishing to confirm the existing user
  receives `src/` and refreshed `typst_*.typ` docs while their
  `legal_context.typ` remains untouched.
- If desired, compile a tiny Typst fixture that imports the new capitalized
  `src/types/*.typ` files once Typst verification is in scope.
