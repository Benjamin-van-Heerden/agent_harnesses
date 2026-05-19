---
created_at: '2026-05-19T16:59:18.371641'
username: benjamin_van_heerden
spec_slug: global_mem_to_project_harness_migration_research
---
# Work Log - Onboard Output Formatting Iteration

## Overarching Goals

Improve the coding harness onboard output for the spec workflow without doing the original migration research yet. The session focused on presentation clarity, separation between codebase conventions and operational state, active-spec guidance, and making the onboard command implementation easier to maintain.

## What Was Accomplished

- Split the coding harness onboard command from one large `onboard.py` file into an `onboard/` command package with separate content, formatting, preflight, output, and main modules.
- Reworked onboard output sections so `CODEBASE AND CONVENTIONS` is distinct from `ONBOARD OUTPUT`, with `=`/`-`/`#` separators for top-level sections, subsections, and file boundaries.
- Omitted empty important-file/doc entries from onboard output and moved project memories under codebase conventions.
- Updated project memory rendering, work-log empty-state copy, AGENT INSTRUCTION conditionals, and suggested next-step wording.
- Moved active-spec `git diff origin/<dev> --stat` output into the Git State section and preserved git stat alignment.
- Tightened active-spec task rendering: pending task titles use blockquote styling and completed tasks remain compact.
- Allowed `coding/setup.py --update` to run from configured dev-prefixed spec branches such as `dev-*`, not only the exact dev branch.
- Added source-formatting guidance to the coding harness `AGENTS.md` template to avoid arbitrary hard wrapping of clear single-line strings and expressions.

## Key Files Affected

- `coding/.agent_core/harness/main.py`
- `coding/.agent_core/harness/src/commands/onboard/`
- `coding/.agent_core/harness/src/commands/onboard.py`
- `coding/setup.py`
- `coding/AGENTS.md`
- Installed `.agent_core/harness/` runtime files were also refreshed by the user via `coding/setup.py --update`; those were generated propagation artifacts, not the primary source edits.

## What Comes Next

- Commit and push the current harness-template changes if the output now looks acceptable.
- Continue iterating on onboard presentation if the next generated onboard output exposes more formatting or workflow issues.
- The original migration research spec tasks remain open and should be handled later once the spec workflow smoke test is satisfactory.
