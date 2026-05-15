---
created_at: '2026-04-29T17:23:08.745767'
username: benjamin_van_heerden
---
# Work Log - Scaffold Praxis: a typst-first agent system for solo SA lawyers

## Overarching Goals

Design and scaffold a brand-new system, **Praxis**, parallel to mem lite but for a different user: a solo South African lawyer who works with a coding agent to draft, format, and manage all legal documents in typst. Replace Word/Acrobat workflows. The lawyer is technologically weak — does not know git, shell, slugs, or filesystem concepts. The agent is the entire user interface.

The work was design-first: we deliberately spent significant back-and-forth on primitives, file shapes, suggestion-driven UX, and what a lawyer's day actually looks like (intake, drafting, communications, deadlines, logging, closing) before writing any code. After alignment, we scaffolded the full system, smoke-tested it end-to-end, and revised it once based on user feedback (no git anywhere, mandatory onboard, relaxed validation, suggestion-driven UX).

## What Was Accomplished

### Design alignment (multi-turn discussion)

Settled the core primitives and structure through iterative discussion:

- **Clients are the top-level primitive**, with matters nested under them (`clients/<slug>/matters/{open,resolved}/<dir>/`). Reasoning: lawyers think client-first, conflict checks are client-level, billing rolls up.
- **`status.md` is the only mandatory per-matter file.** All others (chronology, parties register, communications.md, deadlines.md, time.md) are lazy-created on first use. KISS principle — don't pre-create empty files.
- **Skeletons** (canonical file shapes) live separately from typst templates. After bikeshedding, named the directory `agent_rules/skeletons/` to avoid collision with root `templates/` (which holds typst skeletons).
- **No CLI tool, no Python.** Pure markdown command playbooks + POSIX shell scripts + skeletons. The agent is the tool. Significantly cheaper to maintain and trivial for the lawyer to adopt (zero install once distributed).
- **No git workflow exposed to the lawyer at all.** `bash_setup.sh` uses `git clone` for distribution but the lawyer never sees it. No `.gitignore`, no commits, no branches.

### Scaffold: src/templates/praxis/

Created a sibling to `src/templates/mem_lite/` (intentionally not nested under it — Praxis is a parallel product, not a flavor of mem lite).

Tree:

```
src/templates/praxis/
├── AGENTS.md                        # core_instructions envelope, suggestion-driven UX
├── bash_setup.sh                    # init / --update / --reset-skeletons
├── agent_rules/
│   ├── commands/                    # 15 command playbooks
│   ├── scripts/                     # 19 POSIX shell helpers
│   ├── skeletons/                   # 7 canonical file shapes
│   ├── docs/core/                   # typst_reference.md (stub for user to fill), placeholders for sa_legal_context + firm_style
│   ├── docs/research/               # empty
│   ├── memories/, log/, todos/{,claimed/}, tmp/    # working dirs
│   ├── project_description.md       # lawyer profile placeholder
│   └── project_actions.md           # onboard side-effects placeholder (typst version check)
├── functions/                       # empty starter
├── templates/{components,letters,pleadings,opinions,contracts,memos}/    # empty starters
└── (clients/ created at install time)
```

### Skeletons (`agent_rules/skeletons/`)

7 canonical file shapes used by scripts via `render_skeleton`:

- `profile.md` — client profile with frontmatter (client_slug, display_name, client_type, opened, status)
- `status.md` — matter dashboard with frontmatter (matter_type, status, priority, opened, client, co_clients, opposing_parties, court, case_number, next_deadline, billing, tags) + Posture / Key facts / What's next / Open threads sections
- `communications.md` — append-only log header
- `deadlines.md` — single-line entries: `- [STATUS] YYYY-MM-DD — TYPE — DESCRIPTION`
- `log.md` — work session log with What was done / What's next / Notes
- `memory.md`, `todo.md` — atomic file frontmatter shells

Skeletons use `$PLACEHOLDER` markers; scripts substitute via bash native `${var//pattern/replacement}` (NOT awk gsub — see Errors below).

### Scripts (`agent_rules/scripts/`)

Shared library `_lib.sh` with: `praxis_root`, `die`, `today`, `now_time`, `now_stamp`, `validate_slug`, `frontmatter_get`, `frontmatter_set`, `render_skeleton`, `resolve_client`, `resolve_matter`, `ensure_file_from_skeleton`.

Action scripts:
- `new_client.sh <slug> <display_name> <client_type>` — client_type is free-form
- `new_matter.sh <client> <type> <slug> [priority] [billing]` — type and billing are free-form; priority validated (drives sort)
- `resolve_matter.sh <ref>` — sets status: resolved, moves dir to `resolved/`
- `log_communication.sh <ref> <date> <direction> <medium> <counterparty> <subject>` — direction validated (in/out), medium free-form
- `add_deadline.sh <ref> <date> <type> <desc>` — appends `[open]` entry, recomputes `next_deadline` via grep/sort/head
- `new_log.sh [matter_ref]`, `new_memory.sh <slug> <title>`, `new_todo.sh <slug> <title> [priority] [matter_ref]`, `claim_todo.sh <slug>`

Read scripts:
- `list_clients.sh` — TSV table; counts open/resolved matters per client
- `list_open_matters.sh` — TSV table of open matters across all clients
- `upcoming_deadlines.sh [days]` — sorted upcoming open deadlines (default 14d window)
- `find_matter.sh <pattern>`, `matter_path.sh <ref>` — substring matter resolution
- `list_unparsed.sh <ref>` — files in `raw/` without a counterpart in `reference/`
- `new_document.sh <ref> <template> <slug>` — copies template into matter as `NN_<slug>.typ`
- `new_template.sh <src> <category> <slug>`, `new_function.sh <slug>` — promote/scaffold typst
- `lint.sh` — validates required keys present + status/priority enums (only enums that drive logic)

### Commands (`agent_rules/commands/`)

15 markdown playbooks. Each follows the pattern: When to suggest → You handle (what the agent derives from natural input) → Confirm lightly → Action (the script) → After (proactive follow-up suggestions).

Commands: `c_onboard`, `c_new_client`, `c_new_matter`, `c_resolve_matter`, `c_new_document`, `c_new_template`, `c_new_function`, `c_ingest_raw`, `c_log_communication`, `c_add_deadline`, `c_log_work`, `c_create_memory`, `c_create_todo`, `c_claim_todo`, `c_lint`.

`c_onboard.md` is mandatory on first message of every session.

### AGENTS.md

Final form structures around the principle "the agent is the user interface". Sections:

- **Always onboard first** — non-negotiable on first message, no exceptions unless lawyer says skip.
- **How to talk to the lawyer** — suggest don't ask, translate don't quote, derive slugs yourself, confirm briefly in plain language.
- **Directory layout** — agent's reference, not the lawyer's.
- **Commands table** — when to use each.
- **Common moves** — natural-language → command mapping (the agent's translation table). Examples: "Tom called" → c_log_communication; "Filing due Friday" → c_add_deadline; "Settled" → c_resolve_matter.
- **Focusing on a matter** — full read protocol when lawyer points to a matter (find_matter, full status.md read, list docs/raw/reference, read deadlines/communications, brief in plain language, ask where to pick up).
- **Updating a matter as facts emerge** — direct status.md edits + ambient suggestions.
- **Reading files in a matter** — order to look (status → deadlines → communications → recent typst → reference).
- **Working with typst** — watch mode, ZAR formatting, ISO dates internally / "29 April 2026" in body, SA citation conventions.
- **Stop conditions** — explicit interruption handling.

### bash_setup.sh

Modes: init (default), `--update`, `--reset-skeletons`. Clones template repo to `/tmp`, creates the full directory tree, copies files with appropriate overwrite policy:

- **Always refreshed** on update: `commands/`, `scripts/`, AGENTS.md core block (preserves user content after `</core_instructions>`).
- **Preserved** on update (lawyer-owned): `skeletons/`, `docs/core/`, `project_description.md`, `project_actions.md`, `functions/`, `templates/`.
- `--reset-skeletons` flag for explicit overwrite if needed.

REPO_URL placeholder: `https://github.com/Benjamin-van-Heerden/praxis.git` (does not exist yet).

### End-to-end smoke test

Verified with a Day 1 → Day 2 simulated lawyer session:

```
Day 1:
  new_client smith_corp "Smith Corp Pty Ltd" company
  new_matter smith_corp arbitration jones_breach high      # arbitration accepted (free-form)
  add_deadline jones_breach 2026-05-15 court_hearing "First arbitration hearing"
  log_communication jones_breach 2026-04-29 in call "Jones's attorneys" "Settlement overture"
  new_todo consider_settlement "Think about settlement position" high jones_breach
  new_log jones_breach

Day 2 onboard simulation:
  list_clients         → smith_corp / 1 open / 0 resolved
  list_open_matters    → arbitration high, next_deadline 2026-05-15
  upcoming_deadlines 30 → shows the 15 May hearing
  lint                 → ✓ all frontmatter valid
```

## Key Files Affected

All under `src/templates/praxis/`:

- `AGENTS.md` (1 file, ~140 lines, completely written then completely rewritten after feedback)
- `bash_setup.sh` (~250 lines)
- `agent_rules/skeletons/*.md` (7 files)
- `agent_rules/scripts/*.sh` (19 files including `_lib.sh`)
- `agent_rules/commands/c_*.md` (15 files, written then revised for slug-derivation + jargon removal)
- `agent_rules/project_description.md`, `agent_rules/project_actions.md`, `agent_rules/docs/core/typst_reference.md` (placeholders)

## Errors and Barriers

### Bash placeholder substitution via awk gsub silently no-ops

First implementation of `render_skeleton` in `_lib.sh` piped skeleton content through `awk -v k="\$$key" -v v="$value" '{ gsub(k, v); print }'`. This silently failed to substitute anything. Reason: awk's `gsub` treats its first arg as ERE regex, where `$` is an end-of-line anchor — so `\$KEY` matches "end of line followed by KEY", which never matches in practice.

Fix: switched to bash native parameter expansion `${content//\$$key/$value}` which is literal substitution. Simpler and correct. Lesson for future shell helpers: avoid awk regex when you only need literal substring replacement.

### `set -e` + `[[ ... ]] && cmd && exit 0` pattern can fail spuriously

`upcoming_deadlines.sh`, `list_open_matters.sh`, `list_unparsed.sh` originally ended with `[[ "$found" -eq 0 ]] && echo "..." && exit 0`. When `$found=1`, the test fails, short-circuit prevents the echo and exit, but the script falls through with a non-zero last exit code, which under `set -e` aborts. Replaced with explicit `if [[ ... ]]; then ... fi`.

### Initial validation was too restrictive — caught by user review

First version hardcoded enums for `client_type`, `matter_type`, `billing`, `medium`. User correctly pointed out this would reject perfectly valid SA entity types (`close_corporation`, `voluntary_association`) and matter types (`arbitration`, `appeal`, `tax`, `labour`). Relaxed: only enforced enums that drive logic (`status`, `priority`, `direction`). Everything else free-form text. Lint validates required-keys-present + the two enums that matter. Lesson: domain-specific enums are a smell — let the agent + lint catch typos, don't gate creation on closed sets.

### First AGENTS.md / commands had wrong UX direction

Initial commands said things like "Confirm with the lawyer: slug, display_name, type." This puts the lawyer in the position of typing slugs and answering technical questions — wrong for the target user. User flagged: "the lawyer has no clue what bash is" and the system should be such that the agent constantly suggests the next move, not asks open questions. Rewrote AGENTS.md around three principles:

1. **The agent is the UI.** No script names, slugs, or paths surface to the lawyer.
2. **Suggest, don't ask.** "Want me to log that?" not "What should we do next?"
3. **Mandatory onboard on first message of every session** — without it the agent has no continuity from previous sessions.

Revised every command file to match: agent derives slugs from natural input, confirms lightly, runs the script invisibly, follows up proactively.

## What Comes Next

### Schema/structure changes to apply at the start of next session

These were agreed in conversation after the smoke test was already passing.
They were **not** applied — start of next session does these first as a focused
migration before any other work.

1. **Rename `agent_rules/project_description.md` → `agent_rules/lawyer_profile.md`.**
   The original name was a leftover from the mem-lite analogy; "lawyer_profile"
   names the actual content. Update references in:
   - `bash_setup.sh` (the placeholder-creation block in the init mode)
   - `AGENTS.md` (directory layout listing)
   - `agent_rules/commands/c_onboard.md` (step 1 of the onboard sequence)

2. **`agent_rules/project_actions.md` stays, but acknowledge stopgap nature.**
   In practice this file is unlikely to see use — for a solo lawyer there is
   little to verify on each onboard. Lighten the placeholder content to a
   one-liner saying it's optional, and update `c_onboard.md` step 2 to skip
   gracefully if the file is empty or only contains a comment.

3. **Move per-matter housekeeping files into `<matter>/info/`.** Today
   `status.md`, `communications.md`, `deadlines.md` live flat at the matter
   root, mixed with produced typst documents and PDFs. Move them into a
   dedicated `info/` subdirectory so the matter root contains only deliverables
   (typst + PDFs) and folders. New per-matter shape:

   ```
   <matter>/
   ├── info/
   │   ├── status.md           # always present after new_matter
   │   ├── communications.md   # lazy
   │   ├── deadlines.md        # lazy
   │   └── record.md           # NEW — see below
   ├── raw/                    # unchanged
   ├── reference/              # unchanged
   └── *.typ / *.pdf           # produced documents at matter root
   ```

   Files to update for the path migration:

   - **`agent_rules/scripts/_lib.sh`** — `resolve_matter` existence-check uses
     `<input>/status.md`; change to `<input>/info/status.md`.
     `ensure_file_from_skeleton` should also `mkdir -p "$(dirname "$file")"`
     before copying so info/ gets created on first use.
   - **`new_matter.sh`** — write `info/status.md`, also `mkdir -p info`.
   - **`resolve_matter.sh`** — read/write `info/status.md`.
   - **`add_deadline.sh`** — write `info/deadlines.md`, frontmatter_set on
     `info/status.md`.
   - **`log_communication.sh`** — write `info/communications.md`.
   - **`list_open_matters.sh`** — `find` depth changes from 5 to 6, path
     filter from `*/matters/open/*/status.md` to
     `*/matters/open/*/info/status.md`. Also the chained `dirname` to
     reach `client` needs one more `dirname` call (info → matter → open →
     matters → client).
   - **`upcoming_deadlines.sh`** — same depth/path migration. `matter_dir`
     derivation is one extra `dirname` deeper.
   - **`lint.sh`** — same depth/path migration for the matter-status
     enumeration.
   - **`bash_setup.sh`** — `create_directories` does not need to know
     about `info/` (it's per-matter and created at matter creation time).
     But verify nothing in the install flow assumes the old layout.
   - **`AGENTS.md`** — update directory layout block; update "Focusing on a
     matter" and "Reading files in a matter" sections to show the new
     paths.
   - **Command files mentioning the paths**: `c_new_matter.md`,
     `c_resolve_matter.md`, `c_add_deadline.md`, `c_log_communication.md`,
     `c_ingest_raw.md`. The "Focusing on a matter" guidance also lives in
     AGENTS.md — make sure it points to `info/`.

4. **Add `record.md` — append-only event log per matter.** This is genuinely
   new and worth thinking about properly before implementing. Distinct from
   the existing files:
   - **`record.md`** = chronological narrative of *everything* that has
     happened on the matter (events, in lawyer/agent voice). One entry per
     event, append-only, never edited.
   - **`status.md`** = the dashboard / snapshot, edited freely as posture
     changes.
   - **`communications.md`** = subset of record — only inbound/outbound
     contact events.
   - **`deadlines.md`** = forward-looking only.

   Open design questions to settle next session:
   - Format of an entry. Probably markdown with a short YAML-like header
     (date, kind, optional reference) and a free-text body. Single-line
     entries should also work for one-liners ("client confirmed
     instructions, telephonically").
   - Whether `c_log_communication`, `c_add_deadline`, etc. should
     **automatically** append to record.md (so the record is a derived
     superset), or whether record.md is **only** for things that don't fit
     the other commands. My instinct: auto-append from the structured
     commands so record.md is the canonical timeline; bare `c_record` (or
     similar) is for events that don't have a dedicated command — strategic
     decisions, observations, internal notes, things the lawyer just wants
     to capture.
   - New command `c_record` (or `c_add_event`) and matching script.
   - Skeleton for `record.md` (header + entry format) under
     `agent_rules/skeletons/`.
   - Whether `c_onboard` "Focusing on a matter" should default-read
     record.md or only on demand. Probably show the last N entries in the
     focus brief.

   This needs a discussion before implementation — the auto-append vs
   only-explicit choice has knock-on effects.

### Migration approach for next session

A clean path:

1. Apply changes 1–3 (renames + `info/` migration). These are mechanical.
2. Smoke-test the same Day 1 → Day 2 scenario from this session — it
   should pass identically with the new paths. Include a `lint` run.
3. Discuss `record.md` design (question 4 above) before writing any code.
4. Once design is settled, add the skeleton, script, command file, and
   wire auto-append into the structured commands as decided.

### Mid-migration revert note

During this session I started applying the `info/` migration and the rename
before the user clarified that the request was to log the plan for next
session, not implement now. The partial migration was reverted manually
(no git history for it, since the entire `src/templates/praxis/` tree was
untracked at the time). The state at commit time should be the
pre-migration state — the old flat layout. If anything looks half-migrated
on next session's first read, that's a revert miss; check the files listed
under change 3 above against the old paths.

### Not yet done (deferred)

These are explicitly known gaps. Nothing was promised on them — they remain TODO for next session:

1. **`agent_rules/docs/core/sa_legal_context.md`** — content not written. Should cover SA court hierarchy (ConCourt, SCA, High Court divisions, Magistrate's Court), SA citation conventions (e.g. *Smith v Jones* 2020 (3) SA 123 (SCA), neutral citations like ZACC/ZASCA/ZAGPPHC), date format conventions, ZAR currency formatting, court days vs calendar days rules, common rule-based deadlines (NOID 10 court days, plea 20 court days, replication 15 court days, discovery). The user is South African and this is core domain context.

2. **`agent_rules/docs/core/firm_style.md`** — content not written. The lawyer will need to fill this with firm-specific tone/formality/citation density preferences.

3. **`agent_rules/docs/core/typst_reference.md`** — currently a stub with TODO header. The user said they will provide the comprehensive typst reference document.

4. **Starter typst content under `functions/` and `templates/`** — directories created empty. User feedback removed the typst_compile.sh idea. Still need:
   - `functions/currency.typ` (ZAR formatting: `R 1 000,00`)
   - `functions/dates.typ` (long-form: "29 April 2026")
   - `functions/citations.typ` (SA case citations)
   - `functions/tables.typ` (table style helper)
   - `templates/components/letterhead.typ`, `signature.typ`, `style.typ`
   - At least one example template per category — `templates/letters/demand.typ` is the natural first one to ship as a worked example

### Testing recommendations for next session

The system has been smoke-tested via direct script invocation but has **not** been tested through:

- A full `bash_setup.sh` install run (init mode end-to-end). Would need a separate empty test directory and the praxis repo must exist (currently doesn't — REPO_URL is a placeholder). Could test locally by pointing REPO_URL at the source dir or by testing copy_tree logic in isolation.
- An actual agent session driving the system through natural-language input (e.g. running Claude Code in a fresh praxis project and saying "Let's get to work" → "I have a new client..."). This is the most important test: does the agent correctly:
  - auto-onboard on first message?
  - derive sensible slugs from natural input?
  - suggest the right command at the right ambient cue?
  - follow the "Focusing on a matter" flow when the lawyer points to a matter?
  - update status.md narrative as facts emerge?
  - propose follow-on records (deadline → todo, communication → posture update)?

This is "more involved testing" territory — design choices about suggestion timing, briefing density, and slug derivation can only be evaluated against real conversational pressure. Suggested approach: spin up a fresh praxis directory by manually copying the scaffolded files, fill in `project_description.md` with a synthetic SA lawyer profile, write a minimal `sa_legal_context.md`, and then run a simulated multi-day session with realistic events (new client, summons received, communications, drafting, settlement, resolution).

### Distribution

When the system is ready for real use:

1. Create a `praxis` repo on GitHub.
2. Copy the `src/templates/praxis/` contents to that repo.
3. The one-liner becomes: `bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/praxis/main/bash_setup.sh)`
4. Until then, lawyers (only the user) can install by running the `bash_setup.sh` from a local copy of the source tree (REPO_URL needs to be tweaked or replaced with a local path).

### Architectural notes worth preserving

- The split between `agent_rules/skeletons/` (canonical structural shapes for markdown files) and root `templates/` (typst document skeletons) is deliberate — they serve different consumers (scripts vs lawyer-via-agent) and naming overlap was considered but the path distinction is sufficient.
- The choice to keep mem and Praxis fully isolated (separate template trees, separate distribution, separate AGENTS.md vocabularies) was deliberate. Resist the temptation to share scaffolding logic between mem-lite's `bash_setup.sh` and praxis's — the workflows diverge enough that abstracting them creates more friction than it saves.
- The choice to ship POSIX shell scripts rather than a Python CLI was deliberate based on user constraint (zero install for the lawyer). If aggregation pain emerges later, the right escalation is more shell scripts (with `awk` for YAML extraction) — not introducing a Python tool.
