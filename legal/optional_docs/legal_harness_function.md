# Legal Harness Function

This document defines the legal harness operating model. It is for agent judgment: what to capture, when to capture it, and how to keep matter state useful without exposing implementation details to the lawyer.

## Product Contract

The lawyer speaks naturally. The agent translates natural legal work into harness actions and file edits, then reports back in plain language. Do not make the lawyer choose command names, slugs, TOML, paths, or directory layout unless they ask.

Keep the system small and predictable. Prefer the core primitive that matches the legal significance of the instruction:

- **Matter**: the legal file and working container.
- **Chronology**: what happened, in time order.
- **Obligation**: what must be done, watched, attended, filed, served, prepared, waived, extended, superseded, or closed.
- **Todo**: work management for the lawyer or agent.
- **Memory**: stable practice knowledge that should survive across sessions.
- **Source material**: raw inbound material and parsed references.
- **Draft/output**: Typst drafts and generated documents.

Deadlines are obligations. Records are chronology. Do not introduce separate deadline or record concepts in lawyer-facing explanations.

## Command Shape

Use the local harness entrypoint:

```bash
python -B .agent_core/harness/main.py <command>
```

Native command hierarchy:

- `onboard`
- `client new`, `client list`
- `matter new`, `matter list`, `matter find`, `matter focus`, `matter resolve`, `matter list-unparsed`
- `chronology add conversation`, `chronology add meeting`, `chronology add email`, `chronology add letter`, `chronology add filing`, `chronology add service`, `chronology add note`, `chronology list`
- `obligation add deadline`, `obligation add appearance`, `obligation add follow-up`, `obligation add preparation`, `obligation list`
- `todo new`, `todo list`, `todo claim`
- `memory new`
- `log new`
- `lint`

## State Shape

Global state:

```text
.agent_core/
  docs/
  memories/
  todos/
    open/
    claimed/
  practice/
    logs/
```

Matter state:

```text
clients/<client>/matters/open/YYYYMMDD-<type>-<slug>/
  info/
    status.md
    chronology/
      conversation/
      meeting/
      email/
      letter/
      filing/
      service/
      note/
    obligations/
      deadline/
      court_appearance/
      follow_up/
      preparation/
    todos/
      claimed/
  raw/
  reference/
  *.typ
  *.pdf
```

Folder hierarchy mirrors command hierarchy: `chronology add email` writes under `info/chronology/email/`; `obligation add deadline` writes under `info/obligations/deadline/`. Global todos live under `.agent_core/todos`; matter todos live under `info/todos` for the matter.

## Action Triggers

Run `onboard` at the start of a session. Use it to understand the practice-level picture: open matters, upcoming obligations, todos, memories, recent logs, and the current session log. Do not treat onboard as matter analysis; it should stay concise.

Run `matter focus` before advising, drafting, changing matter state, or answering a matter-specific question. Run it again if the lawyer switches matters or if important matter state has changed during the session.

Create chronology when something happened:

- the lawyer reports a call, meeting, email, letter, filing, service, or factual development;
- source material records an event that matters to the legal timeline;
- a draft was sent, filed, served, discussed, or otherwise became part of the matter history;
- the matter is opened or resolved.

Create or update an obligation when something must not be missed:

- a court or contract deadline exists;
- an appearance, filing, service step, preparation milestone, prescription issue, or follow-up is required;
- an obligation is extended, waived, completed, missed, superseded, or replaced.

Create a todo when work needs to be done but it is not itself the legal duty:

- draft or revise a document;
- summarize source material;
- check a rule or authority;
- prepare a bundle, index, chronology, or client update;
- call or email someone as a work task.

Use a global todo for practice-wide work. Use a matter todo when the work belongs to a specific legal file. A todo may support an obligation, but it is not the obligation.

Create a memory when the lawyer asks you to remember something or when a stable practice pattern is established. Memory-triggering language includes:

- "remember this";
- "keep this in mind";
- "for future matters";
- "we always do it this way";
- "use this wording/style going forward";
- "this is my preference";
- "note this convention";
- "next time, do X".

Do not create a memory for transient matter facts, tactical guesses, one-off instructions, or confidential facts that belong only in the matter file. Put those in chronology, obligations, todos, or matter notes as appropriate.

Create or update the work log as meaningful work happens. The log should let the next agent resume without reconstructing the session from chat.

Stop and ask when state looks legally ambiguous, destructive, contradictory, or speculative. Do not repair chronology, obligations, frontmatter, or matter state by guessing.

## Chronology

Chronology is the point-in-time matter history. It answers: what happened, when, who was involved, and why it matters.

Use chronology for conversations, meetings, emails, letters, filings, service, free-text notes, and lifecycle events. Keep entries factual and dated. Do not use chronology as a task list.

On general onboard, do not load full matter chronology. Chronology belongs to matter focus.

## Obligations

Obligations are future-facing legal or practical duties/consequences. They answer: what must not be missed?

Every open obligation has a due date and status. Deadlines, appearances, prescription risks, filing/service steps, follow-ups, preparation milestones, and client meetings are all obligations when missing them would matter.

When a todo supports an obligation, keep both concepts visible:

- Obligation: answering affidavit due on 2026-05-30.
- Todo: draft first version by 2026-05-24.
- Chronology: client sent source documents on 2026-05-22.

## Todos

Todos are work queue items, not legal duties. They should be actionable and scoped.

Global todos are for practice-wide work. Matter todos are for work tied to a matter. Matter focus surfaces matter-scoped todos for the focused matter; onboard surfaces all global and matter todos so the lawyer can be briefed on the live work queue.

Do not create vague todos such as "look into this" if the next action can be made concrete. Prefer "summarize the 2026-05-22 email chain" or "draft first version of answering affidavit".

## Memories

Memories are durable practice knowledge. They should be short, atomic, and reusable.

Good memories capture preferences, conventions, recurring drafting patterns, local workflow choices, and lawyer-specific style. Bad memories duplicate matter facts, store temporary strategy, or preserve information that should stay attached to a single client file.

When creating a memory, title it around the reusable rule and write the content as a direct instruction for future sessions.

## Drafting

Draft matter-specific documents at the matter root as `NN_<slug>.typ`. Use `src/` for reusable Typst types, constants, functions, templates, style, currency, dates, citations, letterhead, and signature blocks.

Use the Typst reference docs only when needed. The detailed Typst reference lives in `.agent_docs/` so it does not bloat routine onboard context.

Do not treat drafting as chronology unless the draft is sent, filed, served, discussed, or otherwise becomes an event.

## Confidentiality And Care

Every file under `clients/` is confidential.

Memories can contain confidential practice observations, but should not contain one-off matter facts.

If frontmatter, directories, chronology, obligations, or matter state look wrong, stop and ask. Do not repair speculative legal state.
