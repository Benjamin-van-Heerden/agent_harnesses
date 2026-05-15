# Onboard

The first thing to do at the start of every session, before responding to
anything else. Builds context: who the lawyer is, what's open, what's due,
what's in flight, what's been said before.

You run this on the **first message of every session**, regardless of what the
lawyer asked for, unless they explicitly say "skip onboard".

## Actions

Read these in order. Be efficient — don't dump every file's contents to the
lawyer; just internalise the context.

1. **Lawyer profile.** Read `agent_rules/lawyer_profile.md`. As you read,
   check whether the literal string `PLACEHOLDER — NOT YET FILLED IN` appears.
   If it does, set a flag: this file is unfilled. You will warn the lawyer
   prominently in the briefing.
2. **Core docs.** Read every file in `agent_rules/docs/core/`. These are
   always-on reference (typst syntax, jurisdictional legal context). You will
   pull from these throughout the session. As you read each file, check for
   the literal string `PLACEHOLDER — NOT YET FILLED IN`. Track which core
   docs are unfilled — you will warn about those in the briefing.
3. **Command playbooks.** Run `python agent_rules/scripts/show_commands.py`.
   This dumps every command file (except this one) in a single output. Read
   it in full and hold it in working memory — the *When to suggest* / *When
   to use* sections are how you recognise which command applies to a given
   lawyer cue, and the *Action* sections give the exact script invocation.
   This is the single source of truth for command behaviour; do not assume
   from past sessions.
4. **Clients.** Run `python agent_rules/scripts/list_clients.py`. This is who
   exists. A client may have zero open matters and still need to be on your
   radar.
5. **Open matters.** Run `python agent_rules/scripts/list_open_matters.py`. The
   output includes the `open_todos` count per matter — note matters with
   non-zero scoped todos.
6. **Upcoming deadlines (14 days).** Run `python agent_rules/scripts/upcoming_deadlines.py 14`.
7. **High-priority matters.** For any matter from step 5 with `priority: high`
   or `urgent`, read `info/status.md` (`## Posture` + `## What's next`) and
   the last ~5 entries of `info/record.md`. Don't run the full
   `c_focus_matter` flow yet — just enough to brief.
8. **Recent work logs.** Read the 3 most recent files in `agent_rules/log/`.
9. **Memories.** Read every file in `agent_rules/memories/`.
10. **Open todos.** Read every file in `agent_rules/todos/` (excluding
    `claimed/`).
11. **Available typst building blocks.** List filenames only (do not read
    contents) of `src/` and its subdirs. Use your Glob tool with pattern
    `src/**/*.typ`.

    This is for ambient awareness — when the lawyer later asks for something
    drafted, you should know what reusable types, constants, templates, and
    functions already exist without having to re-survey the tree. Read the
    contents on demand when actually drafting.

12. **Local git snapshot.** Run `python agent_rules/scripts/git_snapshot.py`.
    This stages all non-ignored files and creates a local commit if anything
    changed. It does not push.

13. **First-run detection.** This is a fresh praxis install when **both** of
    these are true:

    - The `lawyer_profile.md` placeholder flag from step 1 is set.
    - `src/templates/components/style.typ` does **not** exist.

    If both are true, set a `first_run` flag and skip the normal briefing
    (see *If `first_run` flag is set* below).

## If `first_run` flag is set

Stop the onboard flow here and run `c_initial_setup`. Do not print the
normal briefing — there's nothing useful in it (no clients, no matters,
no deadlines, no logs). c_initial_setup handles the welcome, the pitch,
and the setup itself.

## Briefing (normal case)

Print a compact briefing to the lawyer in plain language. Aim for under
30 lines. Structure:

- **Placeholder warnings (if any).** If `lawyer_profile.md` or any core
  doc was flagged as unfilled in steps 1–2, lead with a strong, prominent
  warning block before anything else. Be direct, not apologetic. For
  example:

  > ⚠ **Setup incomplete.** `agent_rules/lawyer_profile.md` and
  > `agent_rules/docs/core/legal_context.typ` are still placeholders.
  > Until you fill these in, my drafting will be guesswork — wrong tone,
  > wrong citation style, possibly wrong jurisdictional rules. Please
  > fill them in before we draft anything substantive.

  List exactly which files are unfilled. Don't soften — the lawyer needs
  to know. If everything is filled, skip this section entirely.

- **Profile line.** One line: who they are / what they practice (drawn
  from `lawyer_profile.md`). Skip if `lawyer_profile.md` is still a
  placeholder (the warning above already covers it).
- **Where things stand.** Number of clients, number of open matters, count
  of upcoming deadlines, total open todos.
- **Imminent.** Any deadlines in the next 14 days, sorted by date. State
  each in plain language: "_15 May 2026 (16 days) — answering affidavit on
  the Smith / Jones arbitration_".
- **High-priority attention.** For each high or urgent matter, one sentence
  drawn from Posture + What's next, plus the most recent record entry if
  useful.
- **Matters with open todos.** One line per matter that has scoped todos:
  "_Smith / Jones arbitration — 2 open todos_". Skip if none.
- **Recent activity.** Two or three lines summarising the last sessions
  from the recent logs — what was done, what was left for next time.
- **Open todos.** One line each (or "(none)"). Note which matter each is
  scoped to, if any.

End with a single open invitation, e.g. _"Where do you want to start?"_ If
placeholders are unfilled, the natural next move is "let's fill those in
first" — say so explicitly.

## After the briefing

The lawyer will respond. Listen for direction:

- **They name a matter** ("let's work on Smith", "the breach case") → run `c_focus_matter`. Do that **before** continuing with any specific request they tacked on.
- **They mention something that happened** ("Jones called this morning", "we got served yesterday") → suggest the appropriate record (`c_log_communication`, `c_add_deadline`, edit `info/status.md`).
- **They want something drafted** → make sure the matter is focused first (run `c_focus_matter` if not), then draft per AGENTS.md *Drafting, functions, and templates*. If they didn't name a matter, ask.
- **They want to start something new** ("I have a new client", "open a matter") → run the corresponding `c_new_client` / `c_new_matter` command.
- **They ask a question** → answer from the loaded context, draw on memories.
- **They go quiet or say "let's begin"** → wait for direction; don't start work uninvited.

Throughout, follow the *How to talk to the lawyer* section of `AGENTS.md` and
the *When to suggest* sections of the command playbooks loaded in step 3.
