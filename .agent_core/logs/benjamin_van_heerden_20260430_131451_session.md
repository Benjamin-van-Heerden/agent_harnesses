---
created_at: '2026-04-30T13:14:51.318490'
username: benjamin_van_heerden
---
# Work Log - Praxis migration: info/ layout, record.md chronology, mem-lite distribution piggyback, placeholder warnings

## Overarching Goals

Continue the Praxis (typst-first agent system for solo SA lawyers) work
started in the prior session. The plan logged at the end of the previous
session was to apply schema changes (rename `project_description.md` →
`lawyer_profile.md`, lighten `project_actions.md`, migrate per-matter files
into `<matter>/info/`), then design and add `record.md` as the canonical
chronology. Beyond that plan, the user also pulled in: piggybacking praxis
distribution on the existing `mem-lite` repo, replacing `project_actions.md`
entirely with sentinel-warning placeholders, and surfacing matter-scoped
todos in the onboard flow.

This was implementation-heavy. We deliberately stayed close to the prior
session's design intent and pushed deeper on the suggestion-driven UX —
the agent now drives mini-onboards on a matter, auto-appends to a single
chronology file, warns prominently when configuration placeholders are
unfilled, and is reachable via a one-line install that piggybacks on the
existing mem-lite repo distribution.

## What Was Accomplished

### Schema cleanup (carry-over from prior session)

- Renamed `agent_rules/project_description.md` → `lawyer_profile.md`.
  Updated all references in `bash_setup.sh`, `AGENTS.md` directory layout,
  and `c_onboard.md` step 1.
- Migrated all per-matter housekeeping files into a dedicated
  `<matter>/info/` subdirectory so the matter root contains only
  deliverables (typst + PDFs) and structural folders. Updated:
  - `_lib.sh`: `resolve_matter` now checks `info/status.md`;
    `ensure_file_from_skeleton` now `mkdir -p`s the parent.
  - `new_matter.sh`: writes `info/status.md`; creates `info/` at
    matter creation time.
  - `resolve_matter.sh`, `add_deadline.sh`, `log_communication.sh`:
    all now write under `info/`.
  - `list_open_matters.sh`, `upcoming_deadlines.sh`, `lint.sh`:
    `find` mindepth/maxdepth bumped from 5 to 6, path filter changed
    to `*/matters/open/*/info/status.md` (or `info/deadlines.md`),
    extra `dirname` calls to walk up to client.
  - `AGENTS.md` directory layout block; "Updating a matter" and
    "Reading files in a matter" sections updated to point at
    `info/...`.
  - Command files: `c_new_matter`, `c_log_communication`,
    `c_add_deadline`, `c_resolve_matter`, `c_ingest_raw`,
    `c_new_document`, `c_onboard` — all updated to reference
    `info/...` paths.

### record.md as the canonical matter chronology

Folded `communications.md` into a single `record.md` file per matter under
`info/`. record.md is append-only and structured with one entry per event:

```
## YYYY-MM-DD — <kind> — <one-line summary>

<body, optional>
```

- New skeleton `agent_rules/skeletons/record.md` (replaces the deleted
  `communications.md` skeleton).
- New `append_record` helper in `_lib.sh`:
  ```bash
  append_record() {
      local matter_dir="$1" date="$2" kind="$3" summary="$4" body="${5:-}"
      local file="$matter_dir/info/record.md"
      ensure_file_from_skeleton "$file" record
      {
          printf '\n## %s — %s — %s\n' "$date" "$kind" "$summary"
          if [[ -n "$body" ]]; then
              printf '\n%s\n' "$body"
          fi
      } >> "$file"
  }
  ```
- Auto-append wired into:
  - `new_matter.sh` → `matter:opened — <type> — <slug> (priority X, billing Y)`
  - `add_deadline.sh` → `deadline:added — <date> — <type> — <description>`
  - `log_communication.sh` → `comm:<dir>:<medium> — <counterparty> — <subject>` (with `_TODO: body_` placeholder for the agent to fill in afterwards)
  - `resolve_matter.sh` → `matter:resolved — Matter closed.`
- New `record.sh` script + `c_record.md` command for free-text notes.
  Lawyer says "for the record" or makes a strategic observation; the
  agent appends a `note` entry. First line of the text is the summary;
  remaining lines (if any) are the body.

### c_focus_matter — mini-onboard on a matter

Promoted what used to be a passing section in AGENTS.md to a proper
command playbook. When the lawyer says "let's work on X", the agent
runs `c_focus_matter`:

1. `find_matter` to resolve (handle multi-match).
2. Read `info/status.md` in full.
3. Read `info/record.md` in full (the timeline).
4. Read `info/deadlines.md` in full.
5. Survey deliverables at matter root + raw/reference, flag
   anything unparsed.
6. List matter-scoped open todos.
7. Brief in plain language: where it stands, last activity, pending,
   imminent/overdue, what's next. End with an open invitation grounded
   in the matter's "What's next".

AGENTS.md `## Focusing on a matter` section trimmed to a one-line
pointer at the command. `## Common moves` table got a row pointing
"Let's work on X" / "Pull up the X case" / "The breach matter" →
`c_focus_matter`.

### Matter-scoped todos in onboard

The todo skeleton already had a `matter:` frontmatter field. Surfaced it:

- `list_open_matters.sh` gained an `open_todos` column that counts
  open todos whose `matter:` matches the current matter ref. Bash 3.2
  compatible (macOS) — uses a temp index file rather than associative
  arrays. There was a bug where `grep -cFx` outputs "0" *and* exits
  non-zero on no match, so my first `|| echo 0` fallback produced
  `0\n0` and broke the TSV row. Fixed by capturing with `|| true`
  and falling back to `0` only when the result is empty.
- New `list_matter_todos.sh` script that lists open todos for a given
  matter. Used by `c_focus_matter`.
- `c_onboard.md` briefing now includes a "Matters with open todos"
  line per matter and counts total open todos in the headline.
- `c_create_todo.md` updated to nudge scoping to a matter when the
  context implies one.

### Email-paste cue

`AGENTS.md` `## Common moves` got a new row: when the lawyer pastes an
email body, the agent should suggest `c_log_communication` and derive
direction (in/out from sender/recipient), counterparty, and subject from
the email itself. `c_log_communication.md` extended with the same cue
under "When to suggest".

### Distribution: piggyback on mem-lite repo

Restructured `src/templates/` so it mirrors the published mem-lite repo
1:1. Specifically, moved `src/templates/praxis/` →
`src/templates/mem_lite/praxis/`. Now the template tree on disk looks
like the published repo:

```
src/templates/mem_lite/
├── AGENTS.md           (mem_lite at root)
├── README.md
├── agent_rules/
├── bash_setup.sh
└── praxis/             (praxis nested)
    ├── AGENTS.md
    ├── agent_rules/
    ├── bash_setup.sh
    ├── functions/
    └── templates/
```

This made `lite.py:publish()` very simple — a single copy from
`src/templates/mem_lite/` to the cloned repo root, and praxis comes
along for free as a subdir. Reverted my earlier (more complex)
`PRAXIS_TEMPLATES_DIR` + extra-copy-step approach in favour of the
simpler structure-mirroring approach.

praxis's own `bash_setup.sh` updated to match:

- `REPO_URL` → `https://github.com/Benjamin-van-Heerden/mem-lite.git`
- New `TEMPLATE_SUBPATH="praxis"` variable; `TEMPLATE_ROOT="$CLONE_DIR/$TEMPLATE_SUBPATH"`.
- All template reads (in `copy_tree`, `setup_agents_md`, the
  placeholder copies) now go through `$TEMPLATE_ROOT/...` instead of
  `$CLONE_DIR/...`.
- `--update` mode now also runs a non-overwrite copy of skeletons
  (`copy_tree "agent_rules/skeletons" "agent_rules/skeletons" false`).
  This means new skeletons added in template versions get pulled in,
  but lawyer-edited existing skeletons are preserved. Without this,
  the new `record.md` skeleton wouldn't reach existing installs and
  `append_record` would fail at runtime.

Lawyer's install one-liner becomes:
`bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/mem-lite/main/praxis/bash_setup.sh)`

### Placeholder warnings (configurability discipline)

Replaced the previous "soft TODO" approach in `lawyer_profile.md` and
introduced `agent_rules/docs/core/legal_context.typ` as a structured
jurisdiction reference. Both files contain the literal sentinel:

```
PLACEHOLDER — NOT YET FILLED IN
```

`c_onboard.md` step 1 (lawyer profile) and step 2 (core docs) now
explicitly check for this sentinel during the read. The briefing's
first section is now a "Placeholder warnings" block that lists exactly
which files are unfilled. If both are filled, the section is skipped.
The closing invitation nudges toward "let's fill those in first" when
placeholders remain.

`lawyer_profile.md` content folded in what would have been a separate
`firm_style.md` (tone, formality, citation density, structural
preferences, drafting habits, letterhead/signature) — one file for
everything that shapes how the agent writes for this lawyer.

`legal_context.typ` covers: jurisdiction, court hierarchy, citation
conventions, date and currency formatting, court days vs calendar days,
common rule-based deadlines, document-format conventions, privilege and
ethics. Genericised — no SA assumptions in the structure itself; the
lawyer fills in their jurisdiction.

Removed `project_actions.md` entirely. It was originally an "onboard
side-effects" file (typst version check, fonts) but for a solo lawyer
there's nothing to verify. Removed:

- The file itself.
- The placeholder-creation block in `bash_setup.sh`.
- Step 2 of `c_onboard.md` (subsequent steps renumbered).
- The directory-layout entry in `AGENTS.md`.

`AGENTS.md` "Working with typst" section also had hardcoded SA defaults
(ZAR formatting, dd Month yyyy date format, "SA citation conventions").
Genericised to defer to `legal_context.typ` for currency, citation
style, and jurisdictional formatting. ISO dates kept as the internal
default for frontmatter and records.

### Removed dead directory

`agent_rules/docs/research/` was created speculatively early on but
never wired to anything. Removed:

- The directory.
- Its entry in `bash_setup.sh:create_directories()`.
- Its line in the `AGENTS.md` directory layout.

### Local typst packages — investigated, dropped

User asked whether to ship a `@local/praxis:0.1.0` typst package so
documents can `#import "@local/praxis:0.1.0": ...` from anywhere on
disk without relative paths. Investigated: typst local packages live
at OS-specific paths (`~/Library/Application Support/typst/packages/local/...`
on macOS), so the only ergonomic way is a symlink from the data
directory to the project's `local_package/` dir. Dropped because
Windows symlinks need Developer Mode or admin rights and silently fail
otherwise — not worth the platform fragility for one ergonomic win.

## Key Files Affected

All under `src/templates/mem_lite/praxis/` after the move:

### New files

- `agent_rules/skeletons/record.md`
- `agent_rules/scripts/record.sh`
- `agent_rules/scripts/list_matter_todos.sh`
- `agent_rules/commands/c_record.md`
- `agent_rules/commands/c_focus_matter.md`
- `agent_rules/docs/core/legal_context.typ`

### Deleted files

- `agent_rules/skeletons/communications.md`
- `agent_rules/project_actions.md`
- `agent_rules/project_description.md` (renamed)
- Empty directory `agent_rules/docs/research/`

### Significantly modified

- `agent_rules/scripts/_lib.sh` — added `append_record` helper, `mkdir -p` in `ensure_file_from_skeleton`, `info/status.md` checks in `resolve_matter`.
- `agent_rules/scripts/new_matter.sh` — writes to `info/`, auto-appends to record.
- `agent_rules/scripts/log_communication.sh` — single record-append, no separate communications.md.
- `agent_rules/scripts/add_deadline.sh` — `info/` paths, auto-appends to record.
- `agent_rules/scripts/resolve_matter.sh` — `info/status.md` path, auto-appends to record.
- `agent_rules/scripts/list_open_matters.sh` — `open_todos` column, depth-6 find, bash 3.2 compatible counting.
- `agent_rules/scripts/upcoming_deadlines.sh` — depth-6 find, info/ path filter.
- `agent_rules/scripts/lint.sh` — depth-6 find, info/ path filter.
- `agent_rules/lawyer_profile.md` — sentinel + working-style content.
- `agent_rules/commands/c_onboard.md` — sentinel detection, briefing warning section, info/ paths, focus_matter pointer.
- `agent_rules/commands/c_log_communication.md` — record.md flow, email-paste cue.
- `agent_rules/commands/c_add_deadline.md`, `c_resolve_matter.md`, `c_new_matter.md`, `c_ingest_raw.md`, `c_new_document.md` — info/ paths, record.md mention where relevant.
- `agent_rules/commands/c_create_memory.md`, `c_create_todo.md` — minor reference updates.
- `AGENTS.md` — directory layout (info/, no project_actions, no research, lawyer_profile rename), focus-matter row in Common moves, email-paste row, c_record row, info/ paths in Reading and Updating sections, focus section trimmed, typst conventions defer to legal_context.typ.
- `bash_setup.sh` — REPO_URL → mem-lite, TEMPLATE_SUBPATH wiring, placeholder copies use TEMPLATE_ROOT, --update copies new skeletons (non-overwrite), no project_actions, no docs/research.

### Repo-level (mem itself)

- `src/commands/lite.py` — `publish()` docstring updated to mention nested praxis distribution; copy step unchanged (single copy from `src/templates/mem_lite/`).

## Errors and Barriers

### Bash 3.2 on macOS — no associative arrays

First implementation of the `open_todos` count in
`list_open_matters.sh` used `declare -A TODO_COUNT` for a one-pass
aggregation. Bash 3.2 (macOS default) failed with "declare: -A:
invalid option". Replaced with a flat temp file (one matter ref per
line per open todo) and per-matter `grep -cFx`. Acceptable since the
dataset is tiny.

### `grep -c` outputs "0" AND exits non-zero on no match

Following the bash 3.2 fix, my first `|| echo 0` fallback produced
`0\n0` (one from grep itself, one from the fallback), which broke
the TSV row alignment in the output. Switched to `|| true` and an
explicit `[[ -z "$todos" ]] && todos=0` guard. The deeper lesson:
`grep -c` already prints a count even when nothing matched, so any
fallback that also prints just creates duplicates.

### Mid-task confusion on lite.py publish() shape

The first attempt to wire publish() up for praxis added a separate
`PRAXIS_TEMPLATES_DIR` constant and a second copy block. User pointed
out (rightly) that the cleaner mental model is to make
`src/templates/mem_lite/` mirror the published repo 1:1, including
the nested `praxis/` subdirectory. Reverted the
PRAXIS_TEMPLATES_DIR addition; moved `src/templates/praxis/` →
`src/templates/mem_lite/praxis/`; publish() became a single straight
copy again. This was the right call — less code, more legible
intent.

## What Comes Next

### Distribution

- The mem-lite repo will receive its first praxis subdirectory via
  the `mem lite publish` run that follows this commit. Once pushed,
  the lawyer install one-liner is live:
  `bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/mem-lite/main/praxis/bash_setup.sh)`

### Cosmetic gap to address

- `bash_setup.sh` "Next steps" message at the end of init still says
  "Drop the typst reference into agent_rules/docs/core/typst_reference.typ"
  but the source tree actually ships `typst_basic_reference.typ` and
  `typst_legal_cookbook.typ`. One-line fix when next touching the
  installer.

### Still deferred (carry-over from before)

- **Starter typst content** under `functions/` and
  `templates/`. Directories are created empty by
  `bash_setup.sh:create_directories()`. Wanted starters:
  - `functions/currency.typ`, `functions/dates.typ`,
    `functions/citations.typ`, `functions/tables.typ`
  - `templates/components/letterhead.typ`, `signature.typ`,
    `style.typ`
  - At least one example template per category — `templates/letters/demand.typ`
    is the natural first one to ship.
- **Real-world session test.** Spin up a fresh praxis directory
  (now via the published mem-lite repo install), fill in
  `lawyer_profile.md` and `legal_context.typ` with realistic
  content, and drive the system through a multi-day simulated
  session — does the agent auto-onboard, derive sensible slugs,
  warn appropriately when placeholders are unfilled, suggest the
  right command at the right ambient cue, follow the
  `c_focus_matter` flow, propose follow-on records?

### Architectural notes worth preserving

- record.md is the *canonical* timeline; communications and deadline
  events are auto-appended there. Deadlines also still live in
  `info/deadlines.md` for queryability (next_deadline frontmatter,
  upcoming_deadlines.sh window scanning). This is intentional
  duplication: record.md is human-readable narrative, deadlines.md is
  structured forward-looking state.
- The placeholder-sentinel pattern (`PLACEHOLDER — NOT YET FILLED IN`)
  is a simple, robust signal that doesn't require frontmatter parsing
  or schema extension. Worth reusing if more "must-be-configured"
  files are added.
- The directory mirror between `src/templates/mem_lite/` and the
  published mem-lite repo is the load-bearing simplification for
  distribution. Resist the temptation to flatten or split it — the
  1:1 mapping is what makes `publish()` trivial.
