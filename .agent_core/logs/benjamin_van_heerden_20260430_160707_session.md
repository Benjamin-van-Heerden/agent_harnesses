---
created_at: '2026-04-30T16:07:07.342928'
username: benjamin_van_heerden
---
# Work Log - Praxis tightening: drop over-strict primitives, add first-run setup flow

## Overarching Goals

After publishing the first praxis cut to mem-lite earlier in the day, the
focus in this leg was on **cutting out scaffolding that wasn't pulling its
weight** and **adding a first-run experience** that gives the lawyer
something tangible (a compiled, working default template) on day one.

The user's framing throughout: praxis should not be a system of strict
primitives that try to anticipate every action. Most of what the lawyer
asks for is dynamic enough that the agent should *infer* the right move
from context, with conventions documented in AGENTS.md, not playbooks for
every routine file operation. Trim, then make day one feel valuable.

## What Was Accomplished

### Killed `agent_rules/tmp/`

Same diagnosis as `docs/research/` last leg: created via `mkdir -p` in
`bash_setup.sh:create_directories()`, mentioned in the AGENTS.md directory
layout, and never referenced by any script or command. Removed the
directory, the `create_directories()` entry, and the AGENTS.md
directory-layout line. The `mktemp`/`tmp` references in
`_lib.sh:frontmatter_set` are local shell variables (system tmp), not
related — left alone.

### Dropped `c_new_document`, `c_new_template`, `c_new_function`

Three commands plus their backing scripts (`new_document.sh`,
`new_template.sh`, `new_function.sh`) deleted. The user's argument: these
are routine file operations dressed up as primitives. The agent doesn't
need a playbook to copy a template into a matter, write a focused snippet
to `functions/`, or sanitise-then-save a template — it needs a
*convention* it can apply.

Replaced the three commands with a single AGENTS.md section,
`## Drafting, functions, and templates`, which absorbs what used to be
`## Working with typst` and codifies the conventions:

- **Always work in a focused matter when drafting.** If `c_focus_matter`
  hasn't been run for this matter in this session, run it first. **And
  when the lawyer switches matters mid-session ("now let's look at
  Jones"), re-focus the new matter** — don't carry stale context across.
- **Drafting in a matter.** Pick a template (lawyer specifies, or you
  pick the closest from `templates/<category>/`); write to the matter
  root as `NN_<slug>.typ` (zero-padded next sequence number); use
  `functions/` and `templates/components/`; preview in plain language
  rather than dumping typst source. Explicit "do **not** auto-suggest
  `c_log_communication` after drafting" rule — drafting isn't a
  communication.
- **Extracting a function.** Identify snippet, pick slug, write
  `functions/<slug>.typ` with a one-line header comment, update callers
  to `#import` it.
- **Promoting a template.** Pick category, sanitise (remove
  matter-specific content), confirm the sanitised version, write to
  `templates/<category>/<slug>.typ`. Suggest `c_create_memory` if the
  template represents a "way of doing things worth remembering".

The AGENTS.md commands table lost three rows; the Common moves table
gained explicit drafting / extracting / promoting / generic-remember
rows that point at the new section instead of named commands.

### Added switching-matters trigger to `c_focus_matter.md`

Updated the "When to use" triggers to explicitly include the
mid-session switch case ("now let's look at Jones", "actually, on the
Smith one…") with the rule that the new matter's status, record, and
deadlines must be in the agent's working memory before any drafting,
deadline, or communication action on it.

Also fixed the "After the brief" line that referenced the now-deleted
`c_new_document`; it now points at the AGENTS.md *Drafting, functions,
and templates* section.

### `c_onboard.md` step 10 — ambient awareness of typst building blocks

New step: list filenames (not contents) of `functions/` and the
`templates/` subdirs via `find functions templates -maxdepth 2 -name
'*.typ' -type f`. The agent now knows what reusable templates and
functions exist when the lawyer asks for something drafted, without
having to re-survey the tree on demand. Read contents lazily.

### `c_initial_setup.md` — first-run flow

The big addition. A guided three-phase walk-through for a fresh praxis
install:

**Phase 1 — Lawyer profile.** Interview-style, not a form. Walk through
Identity → Specialty/venues → Working style. Replace the entire
placeholder file content (sentinel block included) with their answers.

**Phase 2 — Default document template.** Most info already gathered in
Phase 1. Two extras: ask for a logo (drop into
`templates/components/assets/`, agent never types the path; lawyer can
skip and go text-only), and page setup defaults (A4/Letter, margins,
font). Write `templates/components/style.typ` exposing a `firm` data
record, a letterhead block, a signature block, a page/text helper, and
a high-level `firm_letter(...)` helper.

Then **the agent compiles a test sample** — writes a tiny letter to a
fictional recipient as `/tmp/praxis_initial_setup_preview.typ`, runs
`typst compile`, owns the error loop until it compiles cleanly (lawyer
should not see compile errors), reads the rendered PDF to verify, hands
the path off to the lawyer for review:

> "Your default template is ready. I've compiled a sample at
> `/tmp/praxis_initial_setup_preview.pdf` — open it to have a look. Tell
> me what you want to change…"

Iterate until satisfied; clean up temp files at the end. The user's
framing: "the less time the lawyer spends in the terminal the better".

**Phase 3 — Legal context (optional).** Agent offers, doesn't insist.
"Want to spend another 10 minutes filling in the jurisdictional
reference? Or skip and we'll do it the first time it actually matters."
If accepted, walk through `legal_context.typ` section by section,
replacing `_TODO_` markers with real content and removing the
PLACEHOLDER sentinel block.

**Wrap-up.** Brief plain-language summary of what now exists and a
nudge toward the normal flow.

### `c_onboard.md` first-run dispatch

`c_onboard` step 11 detects the first-run condition (lawyer_profile
sentinel **and** `templates/components/style.typ` absent) and sets a
`first_run` flag.

Initial implementation put the welcome framing ("welcome — let's get
you set up", the 10–15 minutes pitch, the readiness check) inside
`c_onboard`. User correctly pointed out this content **belongs in
c_initial_setup**, not in the dispatcher. Fixed by collapsing
c_onboard's first-run section to a clean handoff:

> ## If `first_run` flag is set
>
> Stop the onboard flow here and run `c_initial_setup`. Do not print
> the normal briefing — there's nothing useful in it (no clients, no
> matters, no deadlines, no logs). c_initial_setup handles the
> welcome, the pitch, and the setup itself.

Moved the welcome message into `c_initial_setup.md`'s new "Welcome
(open with this)" section. c_onboard now does its job (detect,
dispatch, or brief) and nothing else.

### `bash_setup.sh` and AGENTS.md tie-up

- `bash_setup.sh:create_directories()` adds `templates/components/assets/`
  on init so the lawyer always has somewhere to drop logo files when
  c_initial_setup asks for one.
- AGENTS.md commands table gains a `c_initial_setup` row scoped to
  "first run only — when lawyer_profile is a placeholder AND
  templates/components/style.typ doesn't exist". Common moves table
  gains a row for "Let's set things up" / "Help me get started" /
  "Design my default template" → `c_initial_setup`.
- The Drafting section now explicitly names `templates/components/style.typ`
  as the base every document builds on, and tells the agent to run
  `c_initial_setup` rather than improvise drafts if it doesn't exist
  yet.

## Key Files Affected

All under `src/templates/mem_lite/praxis/`:

### New

- `agent_rules/commands/c_initial_setup.md` — three-phase first-run
  playbook with welcome framing, lawyer-profile interview,
  default-template build + test compile, optional legal_context.

### Deleted

- `agent_rules/commands/c_new_document.md`
- `agent_rules/commands/c_new_template.md`
- `agent_rules/commands/c_new_function.md`
- `agent_rules/scripts/new_document.sh`
- `agent_rules/scripts/new_template.sh`
- `agent_rules/scripts/new_function.sh`
- `agent_rules/tmp/` (empty directory)

### Modified

- `AGENTS.md` — directory-layout block (no `tmp/`); commands table
  (-3 rows for the deleted commands, +1 row for `c_initial_setup`);
  Common moves (rewrote 2 rows to point at the new Drafting section,
  +3 rows for first-run / extract / promote / general-remember);
  replaced "Working with typst" with "Drafting, functions, and
  templates" section that absorbs the typst notes and codifies
  conventions; Drafting section now names `style.typ` as the base
  template.
- `agent_rules/commands/c_onboard.md` — step 10 lists functions/ and
  templates/ filenames; step 11 detects first-run condition; briefing
  branches as a clean dispatcher (`if first_run, run c_initial_setup;
  else, normal briefing`).
- `agent_rules/commands/c_focus_matter.md` — added switching-matters
  trigger; fixed `c_new_document` reference in "After the brief".
- `bash_setup.sh:create_directories()` — added
  `templates/components/assets/`; removed `agent_rules/tmp/`.

## Errors and Barriers

### Welcome content placement (own goal)

First implementation of the first-run flow put the welcome message,
the "about 10–15 minutes" pitch, and the "ready?" readiness check
inside `c_onboard.md`. User flagged this directly: that content
belongs in `c_initial_setup`, not in the dispatcher. Fixed by
collapsing c_onboard's first-run section to a one-paragraph "stop,
run c_initial_setup" handoff and moving the welcome framing into
c_initial_setup's new "Welcome (open with this)" section.

The lesson: keep dispatch logic stupid; let the dispatched command
own its own framing and content. If you find yourself writing
narrative content in a place whose job is to *route to* a narrative,
the content is in the wrong file.

### Local typst packages — investigated, dropped

User asked whether to ship a `@local/praxis:0.1.0` typst package so
documents can `#import` from anywhere on disk without relative paths.
Investigated: typst local packages live at OS-specific paths
(`~/Library/Application Support/typst/packages/local/...` on macOS),
so the only ergonomic way is a symlink from the data directory to
the project's `local_package/` dir. Dropped because Windows symlinks
need Developer Mode or admin rights and silently fail otherwise —
not worth the platform fragility for one ergonomic win.

## What Comes Next

### Publish + real-world first-run test

Ready to commit and publish. Once `mem lite publish` runs, the
trimmed command set, the new c_initial_setup playbook, and the
templates/components/assets/ directory creation will be live in the
mem-lite repo. The lawyer install one-liner remains:

```
bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/mem-lite/main/praxis/bash_setup.sh)
```

The first-run flow has not been driven by an actual lawyer in a real
session yet. The natural next test:

1. Spin up a fresh praxis project (via the published install).
2. Open a Claude Code session in it, say "Let's get to work".
3. Confirm the agent (a) auto-onboards, (b) detects the first-run
   condition, (c) dispatches to c_initial_setup, (d) opens with the
   welcome message, (e) interviews through Phase 1, (f) builds and
   compiles the template through Phase 2 with a real PDF preview,
   (g) offers Phase 3 as optional. This is the validation that
   matters — playbooks read well in isolation but only show their
   seams under conversational pressure.

### Cosmetic gap (still)

`bash_setup.sh` "Next steps" message at end of init still references
`typst_reference.typ`; the source tree actually ships
`typst_basic_reference.typ` and `typst_legal_cookbook.typ`. One-line
fix when next touching the installer.

### Architectural notes worth preserving

- **Trim aggressively when a primitive isn't pulling its weight.**
  Two rounds this session — `docs/research/`, `agent_rules/tmp/`,
  the three `c_new_*` commands, `project_actions.md` — reinforced
  that empty placeholders or thinly-wrapped file operations are
  worse than nothing. They make the system look more capable than
  it is and require the agent to reason about scaffolding it'll
  never use.
- **Conventions in AGENTS.md beat command playbooks for dynamic
  work.** The Drafting / functions / templates section is the
  cleanest expression of this principle: rather than three commands
  the agent must dispatch into, three short sub-sections of prose
  the agent reads at onboard and applies as needed.
- **The first-run flow is the system's "wow" moment.** A compiled,
  working default template at the end of a 15-minute interview is
  the moment that earns the lawyer's trust on day one. The agent
  owns the compile loop so the lawyer never sees a typst error.
- **Dispatcher commands stay stupid.** c_onboard detects first-run
  and hands off; c_initial_setup owns the welcome framing, the
  pitch, the whole flow. Don't smuggle content into a dispatcher
  just because it's the entry point.
