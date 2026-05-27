---
created_at: '2026-05-27T17:09:39.896126'
username: benjamin_van_heerden
---
Work Log - PRAXIS_OUT restructuring and legal harness follow-ups

## Overarching Goals

Reorganize the imported `0.1____PRAXIS` legal workspace into `PRAXIS_OUT` so it can be handed back in a cleaner, safer state, while identifying changes needed in the source `legal/` harness so future generated work defaults to reusable Typst modules, soft domain types, and predictable workspace structure.

## What Was Accomplished

### PRAXIS_OUT workspace reconstruction

- Initialized `PRAXIS_OUT` from the current legal harness scaffold and migrated client/matter work from `0.1____PRAXIS`.
- Organized client directories under `ZZ_CLIENTS/` using uppercase directory names.
- Added an `UNBOUND/` workspace for legal work that is not clearly tied to one client, then created a project todo to add first-class UNBOUND support to the legal harness.
- Migrated valuation work into `UNBOUND/VALUATIONS/`.
- Removed same-stem generated `.pdf` outputs where corresponding `.typ` sources existed and rebuilt through the harness compile command so outputs use `.p.pdf`.
- Cleaned generated CATO preview/check image folders after confirming the Typst sources compile.

### Legal harness changes

- Updated legal matter creation behavior so client directories are uppercase by default going forward.
- Verified generated legal workspace structure against the completed legal layout spec after setup was rerun from current `main`.

### Typst modularization

- Built out reusable Typst modules in `PRAXIS_OUT/src`:
  - soft types for money, parties, companies, bank accounts, and valuation assets;
  - shared constants/theme modules;
  - shared components and document shells;
  - shared valuation, agreement, lease, trust deed, form, and letter templates.
- Converted repeated valuation schedules into typed `ValuationAsset(...)` arrays rendered through shared valuation table helpers.
- Standardized money values through the `Money(...)` soft type and `Money_display`/`valuation-money` helpers.
- Extracted shared lease/settlement document wrappers into a reusable lease template module.
- Extracted J401 form primitives and trust deed helpers into shared Typst modules.
- Ran a full compile sweep over Typst files under `ZZ_CLIENTS`, `UNBOUND`, and `WIP`; the sweep passed.
- Ran `python -B .praxis/harness/main.py lint`; lint reported `all frontmatter valid`.

### Project todos created

- Created todo `strengthen_legal_harness_reusable_typst_architecture` / GitHub issue #24 to make `legal/` strongly prefer reusable Typst modules, components, constants, and soft types.
- Created todo `add_legal_repair_command_for_post_repair_refactor_audits` / GitHub issue #25 for a repair command that audits changes since the last repair checkpoint using git history/status and performs aggressive cleanup/refactoring.
- Created todo `remove_legal_src_functions_layout_and_standardize_componentsassets_structure` / GitHub issue #26 to remove the `src/functions/` concept from future legal scaffolds and align `legal/` setup/instructions with the new PRAXIS_OUT layout.

## Key Files Affected

- `PRAXIS_OUT/src/types/ValuationAsset.typ`: added a soft type for valuation schedule rows.
- `PRAXIS_OUT/src/types/Money.typ`: used as the canonical money representation for valuation amounts.
- `PRAXIS_OUT/src/templates/valuations.typ`: expanded shared valuation renderers for money, asset tables, value panels, note boxes, cover panels, and related valuation components.
- `PRAXIS_OUT/src/templates/leases.typ`: added shared residential lease/settlement document shell, title block, fill-line helper, and numbered paragraph helper.
- `PRAXIS_OUT/src/templates/forms/j401.typ`: added reusable J401 form primitives.
- `PRAXIS_OUT/src/templates/trusts.typ`: added trust deed shell, cover, signature, people-list, and clause helpers.
- `PRAXIS_OUT/src/components/style.typ` and `PRAXIS_OUT/src/components/primitives.typ`: current intended component location after the user moved components out of `src/templates/components/`.
- `PRAXIS_OUT/assets/`: current intended root location for reusable static assets.
- `legal/.agent_core/harness/src/commands/matter/main.py` and related legal harness state modules: updated earlier so newly created client directories use uppercase names.
- `.agent_core/todos/strengthen_legal_harness_reusable_typst_architecture.md`: created.
- `.agent_core/todos/add_legal_repair_command_for_post_repair_refactor_audits.md`: created.
- `.agent_core/todos/remove_legal_src_functions_layout_and_standardize_componentsassets_structure.md`: created.

## Errors and Barriers

- A mechanical rewrite command using shell word splitting failed on the path `Kruger I/...`; the rewrite was rerun safely using null-delimited paths.
- The assistant accidentally edited `PRAXIS_OUT/AGENTS.md`, which is harness-controlled and should not be manually modified in `PRAXIS_OUT`. The user clarified that harness-controlled instruction files must be changed at the source harness level under `legal/`, not directly in `PRAXIS_OUT`. This edit should be reverted or regenerated from the corrected legal harness source.
- An attempted edit to `PRAXIS_OUT/CLAUDE.md` failed and did not apply.
- The final PRAXIS_OUT layout inspection/fix work was interrupted before a complete source-harness change under `legal/` could be made for the new `src/components` and root `assets` structure.

## What Comes Next

- Revert or regenerate the accidental manual edit to `PRAXIS_OUT/AGENTS.md`; make the wording/layout change in `legal/` instead.
- Update `legal/` setup/instructions/templates so future work uses the user-approved PRAXIS_OUT layout: root `assets/`, `src/components/`, `src/templates/`, `src/types/`, and `src/constants/`, with no `src/functions/` layer for document UI.
- Implement the legal repair command described in issue #25.
- Continue reducing remaining legacy local aliases in older valuation files, but preserve source evidence and stop for legal/content ambiguity.
