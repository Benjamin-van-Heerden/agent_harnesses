# Legal Harness Migration Research

This note maps the current `legal/` harness into a native Agent Core shape and records the design decisions that should guide implementation.

This file is the primary handoff reference for the next implementation session. Read it before editing `legal/`, especially before building `legal/setup.py` or the native legal runtime. The decisions below supersede the neutral options in the original spec text where they differ.

## Executive Direction

The migration is not just a mechanical move from Bash/scripts/markdown playbooks to Typer modules. The legal harness should become a native Agent Core harness with legal-domain primitives that match how a lawyer works.

The lawyer-facing product remains:

- the lawyer speaks naturally;
- the agent translates natural-language instructions into harness actions;
- the lawyer should not need to know slugs, paths, command names, console output, or code;
- the agent reports completed actions in plain human language;
- harness stdout is for agent control and must be direct, informative, and unambiguous.

The implementation target is:

- fresh installs use `.agent_core/`, not `agent_rules/`;
- updates from legacy installs detect `agent_rules/` and migrate durable state into `.agent_core/`;
- client and matter work product remains top-level under `clients/`;
- native runtime code lives under `legal/.agent_core/harness/`;
- command behavior moves from markdown playbooks and standalone scripts into typed Python modules;
- legal concepts are modeled as matters, chronology events, obligations, matter-local todos, memories, logs, and source material;
- the Python harness stays local-first and deliberately avoids remote sync, auth, database, or firm-wide infrastructure.

## Current Legacy Surfaces

| Surface | Current role | Migration decision |
|---|---|---|
| `legal/AGENTS.md` | Lawyer-facing contract plus legacy command routing to markdown playbooks and scripts. | Keep as first-class agent entrypoint, but rewrite around `python -B .agent_core/harness/main.py ...` and remove playbooks/scripts as the command source of truth. |
| `legal/bash_setup.sh` | Bash installer/updater that fetches from `mem-lite`, copies `agent_rules`, manages `.gitignore`, `AGENTS.md`, `CLAUDE.md`, Typst source, and skeletons. | Replace with stdlib-only `legal/setup.py` modeled on `coding/setup.py`. Keep only as deprecated compatibility during migration if needed. |
| `legal/agent_rules/commands/*.md` | Command playbooks containing trigger rules, agent judgment, and old script invocations. | Migrate behavioral content into native command stdout, AGENTS guidance, and possibly durable workflow docs. Final path must not require reading these files. |
| `legal/agent_rules/scripts/*.py` | File mutation and listing helpers. | Port into typed runtime modules under `legal/.agent_core/harness/src/{commands,state,utils}`. |
| `legal/agent_rules/skeletons/*.md` | Canonical file templates for profiles, status, records, deadlines, todos, memories, logs. | Move into `.agent_core/` managed template/runtime structure. Preserve lawyer-edited installed skeletons during legacy migration unless reset is explicit. |
| `legal/agent_rules/docs/core/*.typ` | Always-loaded legal/Typst reference, including lawyer-owned `legal_context.typ`. | Move durable legal context into `.agent_core/`. Split managed reference docs from lawyer-owned jurisdiction context. |
| `legal/agent_rules/lawyer_profile.md` | Lawyer profile and drafting style. | Move into `.agent_core/` as lawyer-owned durable state during `setup.py --update`. Preserve on update. |
| `legal/src/**/*.typ` | Managed reusable Typst support library. | Managed support source refreshed on update, while lawyer-created additions under `src/functions` and `src/templates` need explicit preservation rules. |
| `clients/<client>/...` | Confidential client and matter state. | Lawyer-owned durable state; never clobber on update. |
| `functions/`, `templates/` | Legacy lawyer-owned reusable Typst locations. | Preserve on update. Native guidance should discourage new files here and support migration into `src/`. |

## Current Domain Model

The present harness revolves around:

- lawyer profile and jurisdiction context;
- clients;
- matters grouped as `open` or `resolved`;
- matter dashboard: `info/status.md`;
- matter chronology: `info/record.md`;
- matter obligations: currently `info/deadlines.md`, target native obligation records;
- matter source material: `raw/` and `reference/`;
- produced matter documents at the matter root;
- cross-cutting todos, memories, and work logs;
- reusable Typst types, constants, functions, and templates.

From a lawyer's perspective, the strongest primitives are not scripts. They are:

- **Matter**: the live file the lawyer is thinking about.
- **Chronology event**: what happened, who said what, what was filed, what changed.
- **Obligation**: a deadline, court date, follow-up date, prescription risk, filing/service obligation, or preparation milestone with a state and category.
- **Task**: work that must be done before an obligation or next session.
- **Source material**: inbound originals and parsed references.
- **Draft/output**: Typst/PDF work product tied to a matter.
- **Practice memory**: stable preferences, jurisdictional rules, and reusable approaches.
- **Session log**: continuity between days.

The native command API should expose these legal primitives directly rather than mirror every old script name.

## Managed vs Lawyer-Owned Boundary

Managed by the harness template:

- `AGENTS.md` managed core block;
- `CLAUDE.md` compatibility file;
- `.agent_core/harness/**`;
- `.agent_core/README.md` if provided;
- managed legal/Typst reference docs;
- command/runtime Python modules;
- default skeleton/template assets;
- baseline Typst type and constant modules.

Lawyer-owned durable state:

- lawyer profile;
- legal jurisdiction/context file;
- clients and matters;
- matter `raw/`, `reference/`, `info`, drafts, and PDFs;
- todos, memories, and work logs;
- lawyer-created Typst functions/templates/assets;
- legacy `functions/` and `templates/`;
- any content outside the managed AGENTS core block.

Boundary decisions:

- The installed durable legal state should move under `.agent_core/` so the legal harness takes on the same primary shape as the coding harness.
- `legal/setup.py --update` must detect legacy `agent_rules/` installs and migrate their state into `.agent_core/` as best it can.
- Fresh initialization should create only the native `.agent_core/` structure, not `agent_rules/`.
- Client and matter state should remain top-level `clients/` durable lawyer-owned content because it is the practice's work product, not harness internals.

Concrete legacy migration targets:

| Legacy installed path | Native target | Notes |
|---|---|---|
| `agent_rules/lawyer_profile.md` | `.agent_core/practice/lawyer_profile.md` | Lawyer-owned. Preserve exactly where possible. |
| `agent_rules/docs/core/legal_context.typ` | `.agent_core/docs/legal_context.typ` | Lawyer/firm-owned jurisdiction context. Preserve exactly. |
| `agent_rules/docs/core/typst_basic_reference.typ` | `.agent_core/docs/typst_basic_reference.typ` | Managed reference doc. Refresh from template on update. |
| `agent_rules/docs/core/typst_soft_typesystem_and_house_rules_updated.typ` | `.agent_core/docs/typst_soft_typesystem_and_house_rules_updated.typ` | Managed reference doc. Refresh from template on update. |
| `agent_rules/docs/typst_detailed_reference.typ` | `.agent_core/docs/typst_detailed_reference.typ` | Managed reference doc. Refresh from template on update if retained. |
| `agent_rules/memories/*.md` | `.agent_core/practice/memories/*.md` | Lawyer-owned durable memories. |
| `agent_rules/log/*.md` | `.agent_core/practice/logs/*.md` | Lawyer-owned session continuity logs. |
| `agent_rules/todos/*.md` with `matter: null` | `.agent_core/practice/todos/*.md` or `.agent_core/practice/todos/open/*.md` | Cross-cutting practice todo. Exact subshape can be chosen during implementation. |
| `agent_rules/todos/*.md` with matter scope | `<matter>/info/todos/<slug>.md` | Matter-local todo. The migration should resolve the matter path from frontmatter. |
| `agent_rules/todos/claimed/*.md` | corresponding claimed/done location | Preserve history. If matter-scoped, move into the matter's todo area with claimed status. |
| `agent_rules/skeletons/*.md` | `.agent_core/practice/templates/` or harness-managed template location | Existing lawyer-edited skeletons should not be clobbered. |
| `agent_rules/commands/*.md` | no native durable target | Legacy command source. Keep only during compatibility window, then retire. |
| `agent_rules/scripts/*.py` | no native durable target | Behavior moves into `legal/.agent_core/harness/src/`. |

## Native Runtime Shape

A first native runtime can use:

```text
legal/.agent_core/harness/
  main.py
  deps.py
  requirements.txt
  src/
    commands/
      onboard/
      client/
      matter/
      deadline/
      obligation/
      record/
      todo/
      memory/
      log/
      lint/
    config/
    models/
    state/
    utils/
```

This matches Agent Core structure while keeping legal concepts separate from coding-harness specs/tasks/worktrees.

Potential higher-level command grouping:

- `onboard`
- `client new/list`
- `matter new/focus/list/find/resolve`
- `chronology add/list` or `record communication/note`
- `obligation add/close/list`
- `source list-unparsed/ingest`
- `todo new/claim/list`
- `memory new/list`
- `log new`
- `lint`

Implementation order recommendation:

1. Build the native runtime foundation first, even though the spec task order lists setup before runtime. `legal/setup.py` needs a real `legal/.agent_core/harness/` tree to install.
2. Add `legal/setup.py` once the runtime skeleton exists. Setup should create the native structure on init and migrate legacy `agent_rules/` state on `--update`.
3. Port state models and helpers before porting all command behavior. Command modules should be thin Typer-facing wrappers over typed state APIs.
4. Implement context/onboard and list/focus commands early because they prove the state layout and lawyer-facing stdout.
5. Port lifecycle and bookkeeping commands after the primitives are stable.

## Compatibility Strategy

Temporary compatibility is useful while migration is incomplete:

- keep legacy command playbooks until native commands cover their workflows;
- keep script wrappers only if they delegate to native commands or are clearly marked legacy;
- migrate installed legacy `agent_rules/` state paths into native `.agent_core/` state paths during update;
- migrate `bash_setup.sh` out of the supported path as soon as `legal/setup.py` exists;
- final `AGENTS.md` must document only the native command path.

## Lawyer-Centered Design Observations

The existing system has the right product instinct: the lawyer speaks naturally and the agent translates. The migration should protect that. It should not make the lawyer think in CLI verbs, slugs, or directories.

The largest functional gap is obligations. A lawyer cares about more than a simple deadline list:

- court deadlines;
- court appearances;
- prescription/limitation dates;
- follow-up diary dates;
- filing/service obligations;
- preparation milestones before a hard date;
- obligations that are done, waived, missed, extended, or superseded.

Treating all of these as `deadline` works mechanically, but a native design may benefit from an `obligation` primitive with `kind`, `due_date`, `status`, `source_event`, `matter`, and optional reminder/preparation fields.

Decision: native legal state should use **obligations** as the primary model. Deadlines are one obligation category, not the whole concept. For migration compatibility, old `info/deadlines.md` entries can be imported into obligation records with `category = "deadline"` or an inferred category where obvious.

Obligation categories should leave room for at least:

- `deadline`;
- `court_appearance`;
- `prescription`;
- `follow_up`;
- `filing`;
- `service`;
- `preparation`;
- `client_meeting`;
- `other`.

Obligation status should leave room for at least:

- `open`;
- `done`;
- `missed`;
- `waived`;
- `extended`;
- `superseded`.

The onboard flow should surface urgent obligations in human terms. It should not force the lawyer to distinguish technical categories. Example lawyer-facing summary: `Smith / Jones arbitration: answering affidavit due 15 May 2026; prepare draft by 8 May 2026.`

Matter-scoped todos should live inside the matter directory, not in a global todo folder with a `matter:` pointer. Onboard must still surface them concisely, for example: `Smith / Jones arbitration has 2 open todos: draft affidavit, call registrar.` The onboard output should not dump full todo bodies unless the agent is focusing that matter or the todo is cross-cutting.

Chronology should become typed wherever possible. The current append-only `record.md` is readable but hard to validate. A native matter can use a structured file such as `info/chronology.toml` or per-event typed records under `info/chronology/`. Command stdout and onboard can render a human chronology from typed records. If a markdown chronology is kept, it should be generated or compatibility-only rather than the source of truth.

Chronology events should cover at least:

- matter opened;
- communication in/out;
- note;
- filing;
- deadline/obligation added;
- obligation status changed;
- document drafted;
- matter resolved.

Chronology should be called `chronology`, not `record`, in native state. The old `record.md` can be treated as legacy input or optional generated/readable output during migration.

Raw ingestion should stay lightweight for now. The native harness should keep `raw/` and `reference/` conventions and list unparsed materials, but specialized parsing scripts can come later.

Typst support under `src/` remains partly managed and partly evolved through use. Setup/update must refresh managed baseline files without clobbering lawyer-developed functions, templates, assets, or firm-specific customizations.

This means `src/` cannot be treated as a disposable managed runtime in the same way as `.agent_core/harness/`. It is a living legal drafting library. Setup/update needs an explicit policy for managed baseline files versus lawyer-authored additions. A conservative first policy is:

- refresh known managed baseline files that ship with the template;
- create missing managed files;
- preserve unknown files under `src/functions/`, `src/templates/`, and assets directories;
- do not delete lawyer-created Typst files during update;
- keep legacy `functions/` and `templates/` folders preserved, while steering new work into `src/`.

The core workflow should still optimize for a single lawyer's day-to-day practice. The state model should leave room for multi-lawyer or firm use from the beginning: firm rules, firm templates, shared legal context, multiple lawyer profiles, and matter responsibility/assignment fields should be possible without a future disruptive migration.

Firm/global sync is intentionally out of scope for this Python harness migration. The legal harness should remain local-first and solo-lawyer oriented for now. A later product rewrite can handle firm-wide state, database-backed sync, authentication, and remote APIs. The current design should avoid blocking that future, but should not build it prematurely.

The long-term direction discussed was: prove the workflow with real users first, then a later Rust rewrite can ship a binary and handle database-backed multi-lawyer state, authentication, and remote API sync. The Python harness should not anticipate that by adding half-built network sync.

The second gap is parties/contacts. `client` plus free-text opposing parties is enough for a solo first pass, but real matters often involve:

- multiple clients;
- opposing parties;
- attorneys;
- counsel;
- courts/registrars;
- witnesses;
- experts.

This can stay as frontmatter/body text initially, but command and model names should leave room for a future contact/party layer.

## Native State Proposal

Target fresh install shape:

```text
.agent_core/
  config.toml
  harness/
  docs/
    legal_context.typ          # lawyer/firm-owned
    typst_basic_reference.typ  # managed
    typst_soft_typesystem_and_house_rules_updated.typ  # managed
  practice/
    lawyer_profile.md          # default active lawyer profile
    firm_profile.md            # optional shared firm identity/rules
    memories/
    logs/
    templates/                 # managed skeletons and support templates
clients/
  <client_slug>/
    profile.md
    matters/
      open/
        YYYYMMDD-<type>-<slug>/
          info/
            status.md
            chronology/
              <event_slug>.toml
            obligations/
              <obligation_slug>.toml
            todos/
              <todo_slug>.md
          raw/
          reference/
          *.typ
          *.pdf
      resolved/
src/
  types/
  constants/
  functions/
  templates/
```

Open design details before implementation:

1. Use one typed file per chronology event under `info/chronology/`.
2. Use one typed file per obligation under `info/obligations/`.
3. Use `.agent_core/practice/` for lawyer-owned global practice state.

Recommended typed state record shapes:

```text
info/chronology/<YYYYMMDD-HHMMSS-kind-slug>.toml
```

Likely fields:

- `id`;
- `date`;
- `time` when useful;
- `kind`;
- `summary`;
- `body`;
- `actor` or `participants` when useful;
- `source` when imported from legacy state or linked to raw/reference material;
- `created_at`;
- `created_by` when multi-lawyer support eventually exists.

```text
info/obligations/<YYYYMMDD-category-slug>.toml
```

Likely fields:

- `id`;
- `category`;
- `status`;
- `due_date`;
- `description`;
- `source_event`;
- `preparation_date` or linked preparation todo when useful;
- `supersedes` / `superseded_by` when useful;
- `created_at`;
- `closed_at` when not open.

```text
info/todos/<todo_slug>.md
```

Likely frontmatter:

- `slug`;
- `created`;
- `status`;
- `priority`;
- `obligation` when linked to an obligation;
- `created_at`;
- `claimed_at` or `completed_at` when done.

The todo body can remain markdown because todos need human context more than strict structure. Matter-local placement supplies the matter scope.

Cross-cutting practice todos, if retained, should live under `.agent_core/practice/todos/` and be surfaced separately from matter-local todos.

## Local Git Snapshot Model

The legal harness should not copy the coding harness's remote-first git workflow. Legal installs are local practice folders, not GitHub-backed development repositories.

The native runtime can wrap Typer command execution with a local post-command snapshot:

```python
if __name__ == "__main__":
    try:
        app()
    finally:
        post_sync()
```

`post_sync()` should:

- no-op when the project is not a git repository or git is unavailable, unless the command explicitly requires snapshotting;
- run `git status --porcelain`;
- if there are changes, run `git add -A`;
- create a local commit with a timestamp message such as `2026-05-21 10:30:00`;
- never pull, rebase, or push.

There is no remote sync in this migration. No merge/rebase behavior is needed because the expected legal harness workflow is local-only.

This differs intentionally from the coding harness. The legal harness should not require protected branches, GitHub issues, PRs, worktrees, fetch, rebase, or push. Local git exists as a simple safety net and audit trail for a lawyer's folder.

Setup may initialize a local git repository if missing, as the legacy setup did, but it should not require a remote. Runtime snapshot failures should be reported clearly to the agent without exposing technical noise to the lawyer unless the lawyer asks.

## Stdout And Lawyer-Facing Language

Harness stdout is agent guidance. It should be written as instructions that leave no ambiguity about what the agent must read, edit, or say next.

Good command stdout examples:

- `Created matter: Smith Corp / Jones breach. You must read clients/smith_corp/matters/open/.../info/status.md before drafting. Tell the lawyer the matter is open and ask what first step they want to take.`
- `Added obligation: answering affidavit due 2026-05-15. You must mention the due date to the lawyer and suggest creating a preparation todo if none exists.`
- `Focused matter: Smith Corp / Jones breach. You must brief the lawyer in plain language using the summary below. Do not mention file paths unless asked.`

The lawyer-facing response should be plain language, for example:

- `I've opened the Smith Corp matter and captured the basic posture. What should we tackle first: the answering affidavit, the chronology, or the client update?`
- `I've diarised the answering affidavit for 15 May 2026. There is no preparation todo yet; I suggest we add one for the first draft.`

Avoid exposing implementation details to the lawyer:

- do not mention Typer, TOML, file paths, slugs, git commits, or command names unless asked;
- do not ask the lawyer to run commands;
- do not make the lawyer choose technical identifiers;
- derive slugs and paths internally.

## Next Implementation Session

The next agent should start by reading this file in full. The immediate coding path should be:

1. Create the native `legal/.agent_core/harness/` foundation.
2. Add config/path helpers for `.agent_core/practice/`, `.agent_core/docs/`, `clients/`, matter `info/chronology/`, `info/obligations/`, and `info/todos/`.
3. Add local git post-command snapshot support with no pull/rebase/push behavior.
4. Build `legal/setup.py` around the native runtime and implement legacy `agent_rules/` migration.
5. Port typed state models for lawyer profile, client profile, matter status, chronology events, obligations, todos, memories, and logs.
6. Implement onboard/focus/list commands before lifecycle/bookkeeping commands so the state shape is exercised early.

Do not begin by copying coding harness GitHub/spec/worktree concepts into legal. The reusable pattern is the native harness shape, dependency check, command composition, typed state, setup/update boundary, and assertive stdout.
