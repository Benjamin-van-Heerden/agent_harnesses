---
created_at: '2026-05-02T18:45:28.497889'
username: benjamin_van_heerden
---
# Work Log - Praxis: bash → Python script migration; AGENTS.md trim + show_commands.py dump

## Overarching Goals

Two related changes to praxis (`src/templates/mem_lite/praxis/`):

1. **Migrate runtime scripts from bash to Python.** The lawyer's coding agent
   on Windows can't reliably invoke bash. Distribution (`bash_setup.sh`)
   stays bash because the lawyer has git bash for installs/updates — only
   the per-action scripts the agent runs at conversation time needed to
   move. Python 3.12, stdlib only, like-for-like translation (no behaviour
   changes).

2. **Fix the trigger-discovery problem in command playbooks.** Each
   `c_*.md` had a "When to suggest" section with the canonical triggers,
   but the agent only reads a `c_*.md` *after* deciding to use it —
   chicken-and-egg. AGENTS.md was duplicating the trigger info via a
   *Common moves* table. Resolved by making AGENTS.md the principles index
   only and dumping every command playbook into context at onboard via a
   single `show_commands.py` invocation.

## What Was Accomplished

### Bash → Python script migration

- Translated all 19 bash scripts under
  `agent_rules/scripts/` to Python 3.12 stdlib-only:
  - `_lib.py` — shared helpers: `praxis_root`, `today`/`now_time`/`now_stamp`,
    `validate_slug`, `frontmatter_get`/`frontmatter_set` (line-oriented top-level
    scalar parser, no PyYAML), `render_skeleton` (literal `$KEY` substitution),
    `resolve_client`, `resolve_matter` (substring search at depth 4 below
    `clients/`, dies on multi-match), `ensure_file_from_skeleton`,
    `append_record`.
  - 18 action/read scripts mirroring the bash versions name-for-name with
    identical argument shape, stdout, stderr `praxis: ...` prefixes and
    exit codes.
- The Python scripts use `from _lib import ...` — Python automatically adds
  the script's directory to `sys.path` when run as `python agent_rules/scripts/foo.py`,
  so no package, no `__init__.py`, no path manipulation needed.
- Two parity issues caught during translation:
  - `list_clients`, `list_open_matters`, `upcoming_deadlines` in bash always
    print the header even when empty, with the `(no ...)` line *appended*.
    First Python pass had the empty-case skip the header — fixed to match
    bash exactly.
  - `frontmatter_set` on a missing key dies in bash; preserved that
    semantics rather than silently appending.
- `bash_setup.sh` kept structurally identical (still bash + git for
  install/update on the lawyer's git-bash). Only changes:
  - Header docstring `*.sh` → `*.py`.
  - Added Python 3.12 runtime requirement note.
  - Removed `set_executable()` and its calls (no `chmod +x` needed for
    `python script.py` invocation; on Windows it's moot anyway).
- `bash -n` syntax check on the modified `bash_setup.sh` passes.
- All 14 command playbooks updated: every
  `agent_rules/scripts/<name>.sh args` → `python agent_rules/scripts/<name>.py args`.
- `AGENTS.md`: "Shell helpers" → "Python helpers"; one quote example
  ("Running new_client.sh") updated to `.py`.
- `c_onboard.md` step 10 (the only command file that *itself* shelled out
  via `find functions templates -maxdepth 2 -name '*.typ'`) — replaced with
  "Use your Glob tool with patterns `functions/**/*.typ` and
  `templates/**/*.typ`". Cross-platform via the agent's built-in tool.
- All 19 old `*.sh` files deleted from the source tree.
- Smoke-tested in `/tmp` sandbox: full Day 1 → Day 2 scenario
  (new_client → new_matter → add_deadline → log_communication → new_todo
  → record (multi-line) → new_log → list_clients → list_open_matters →
  upcoming_deadlines → list_matter_todos → claim_todo → resolve_matter →
  lint) plus edge cases (missing args, bad slug, invalid date, unknown
  matter, frontmatter_set on absent key, running outside a praxis project).
  All matches bash behaviour.

### AGENTS.md trim + show_commands.py dump

- Audit pass: walked AGENTS.md *Common moves* row by row against each
  corresponding `c_*.md` "When to suggest" section. Where the lawyer-voice
  phrasings in *Common moves* weren't in the playbook, added them so each
  playbook is self-contained for trigger recognition. Touched files:
  - `c_new_client.md`, `c_new_matter.md` — added explicit lawyer-voice
    "Ambient cues" sections (had only descriptive prose before).
  - `c_resolve_matter.md` — added a *When to suggest* section it lacked
    entirely.
  - `c_create_memory.md` — added "Save this", "Remember this approach"
    plus a one-line sibling-discrimination rule (prefer extracting a
    function or promoting a template if it's typst-shaped).
  - `c_create_todo.md`, `c_claim_todo.md`, `c_add_deadline.md` — minor
    additions to make sure the *Common moves* phrasings are reflected.
- Trimmed AGENTS.md from 272 → 237 lines:
  - Removed the entire `## Common moves` table.
  - Removed `## Focusing on a matter` paragraph (was a duplicate of
    `c_focus_matter.md`).
  - Replaced the `## Commands` table (had a "Use it when" column that
    duplicated triggers) with a flat grouped index — name + one-line
    purpose only.
  - Updated the "Be alert to ambient cues" bullet in *How to talk to the
    lawyer* — now points at the playbooks loaded via `show_commands.py`
    instead of *Common moves*.
- New script `agent_rules/scripts/show_commands.py`. Stdlib-only, dumps
  every `c_*.md` (sorted) with a `=`-line separator and `FILE:` header
  per file. Excludes `c_onboard.md` (the agent is in that flow already)
  and `c_initial_setup.md` (one-shot, dispatched explicitly when first-run
  is detected; no value in routine sessions). Output: 13 files, ~742 lines.
- `c_onboard.md`: added new step 3 right after core docs:
  > "Run `python agent_rules/scripts/show_commands.py` … hold it in
  > working memory — the *When to suggest* / *When to use* sections are
  > how you recognise which command applies to a given lawyer cue, and
  > the *Action* sections give the exact script invocation. This is the
  > single source of truth for command behaviour; do not assume from
  > past sessions."
- Subsequent steps renumbered (3→4 onward); the cross-reference in step 7
  ("from step 4" → "from step 5") fixed.
- Other tightening in `c_onboard.md`:
  - Step 11 (typst building blocks) — softened "e.g. Glob with pattern …"
    to a direct "Use your Glob tool with patterns …".
  - Step 12 (first-run detection) — removed the redundant re-check of the
    `lawyer_profile.md` placeholder (now references the flag already set
    in step 1) and clarified the dispatch-to-`c_initial_setup` wording.
  - The closing reference to *Common moves* updated to point at the
    playbooks loaded in step 3.
- One reverted change: I had also flipped step 2 (core docs) from "read
  every file" to "scan for placeholder only" on the grounds that those
  files are reference materials read on demand. User pushed back: core
  docs are designed to be read in full on every onboard — that's the
  designed system behaviour. Reverted to the original "Read every file"
  wording.

## Key Files Affected

All under `src/templates/mem_lite/praxis/`:

### New

- `agent_rules/scripts/_lib.py` (174 lines)
- `agent_rules/scripts/{add_deadline,claim_todo,find_matter,lint,
  list_clients,list_matter_todos,list_open_matters,list_unparsed,
  log_communication,matter_path,new_client,new_log,new_matter,
  new_memory,new_todo,record,resolve_matter,upcoming_deadlines}.py` —
  18 action/read scripts.
- `agent_rules/scripts/show_commands.py` — playbook dumper.

### Deleted

- `agent_rules/scripts/_lib.sh` and the 18 corresponding `*.sh` action
  scripts.

### Modified

- `bash_setup.sh` — header doc, Python runtime note, removed
  `set_executable`.
- `AGENTS.md` — trimmed *Common moves*, *Focusing on a matter*, and the
  "Use it when" column from the Commands table; tightened the ambient-cues
  bullet.
- `agent_rules/commands/c_onboard.md` — added show_commands step,
  renumbered, tightened steps 11–12, replaced the inline `find` with
  Glob-tool guidance.
- `agent_rules/commands/c_*.md` — all 14 invocations updated from
  `agent_rules/scripts/foo.sh` → `python agent_rules/scripts/foo.py`;
  trigger-section additions in `c_new_client`, `c_new_matter`,
  `c_resolve_matter`, `c_create_memory`, `c_create_todo`, `c_claim_todo`,
  `c_add_deadline`.

## Errors and Barriers

### Bash list-script header semantics not initially preserved

First Python pass on `list_clients.py`, `list_open_matters.py`, and
`upcoming_deadlines.py` skipped the header line in the empty-result case.
The bash originals print the header *always*, then append a `(no ...)`
line if no rows matched — so a downstream consumer always sees the same
TSV shape on the first line. Fixed by reordering: header → rows → empty
sentinel. Reminder for future translations: when matching bash output
exactly, match the *order* of side-effects, not just the set of lines.

### `python` vs `python3` on Mac

The `python3 -m` test path on macOS Homebrew has no `python` binary,
only `python3`. The lawyer's Windows PC will have `python` (python.org
installer puts it on PATH). Standardised on `python` in command playbooks
and `python3` for local sandbox testing only. Worth confirming the
lawyer's PATH has `python` (not just `py`) when his Python is installed.

## What Comes Next

### Distribution

- After this commit lands, run `mem lite publish` to push the changes
  through to the published mem-lite repo. Lawyer install/update
  one-liner stays unchanged:
  `bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/mem-lite/main/praxis/bash_setup.sh)`.
- The `--update` mode in `bash_setup.sh` will auto-remove the old `*.sh`
  files from existing installs (the `copy_tree` overwrite branch already
  prunes files that aren't in the template).

### Real-world test

The Python migration is sandbox-tested but has not been exercised in a
real lawyer session yet. Worth running through Day-1-on-Windows on the
lawyer's actual machine once the next release is out: confirm `python`
is on PATH, confirm the agent invokes scripts cleanly, confirm
`show_commands.py` dump renders well in the agent's context window.

### Cosmetic gap (still)

`bash_setup.sh` "Next steps" message at end of init still references
`typst_reference.typ`; the source tree actually ships
`typst_basic_reference.typ` and `typst_legal_cookbook.typ` (and
`typst_detailed_reference.typ`). One-line fix when next touching the
installer — left it alone in this leg per the no-behaviour-changes
discipline.

### Architectural notes worth preserving

- **Trigger info lives in the playbook, not in AGENTS.md.** The split
  is principles + structural reference (AGENTS.md) vs trigger conditions
  + execution detail (`c_*.md`). `show_commands.py` is the bridge: dumps
  every playbook in a single read at onboard so the agent has all
  triggers in working memory before the first lawyer message.
- **`c_initial_setup` is excluded from the dump.** It's a one-shot
  first-run flow dispatched explicitly from `c_onboard` when both
  conditions hold (placeholder profile + missing `style.typ`); loading
  it on every routine session is dead weight.
- **Stdlib-only Python is the right floor for portability.** PyYAML
  would be cleaner for frontmatter but adds a `pip install` step for the
  lawyer; the line-oriented "top-level scalar key" parser inherited
  from bash is sufficient for the schema in use.
- **`from _lib import ...` works without `__init__.py`** because Python
  adds the script's directory to `sys.path` when invoked as
  `python path/to/script.py`. Keeps the file layout flat and matches
  the bash `_lib.sh` convention.
