# Focus on a matter

A "mini-onboard" for a single matter. Run this whenever the lawyer points to
a specific matter and you're about to work on it. Do this **before** you
start whatever they actually asked for — being briefed beats guessing.

## When to use

The lawyer signals they want to work on a particular matter. Triggers:

- "Let's work on the Smith case."
- "Pull up the Jones matter."
- "The breach matter — where are we?"
- "Open up [matter]."
- They mention an event ("Jones called this morning") and you need to ground
  yourself in the matter before suggesting `c_log_communication`.
- **The lawyer switches matters mid-session** ("now let's look at Jones",
  "actually, on the Smith one…"). Re-focus the new matter — don't carry
  stale context. The new matter's status, record, and deadlines must be in
  your working memory before any drafting, deadline, or communication
  action on it.

If the wording is ambiguous (a name shared by multiple matters), resolve
first — don't guess.

## You handle

- **Resolve the matter.** Run `python agent_rules/scripts/find_matter.py <pattern>`.
  If multiple match, briefly list candidates by client and ask which one.
- **Read everything in `info/`.** Specifically:
  1. `info/status.md` — full file (frontmatter + Posture + Key facts + What's
     next + Open threads).
  2. `info/record.md` — full file. The chronology is the spine; read it.
  3. `info/deadlines.md` — full file. Note open vs closed entries.
- **Survey the matter root.** List `*.typ` and `*.pdf` files; identify the
  most recent. List `raw/` and `reference/`; flag anything in `raw/` that
  has no counterpart in `reference/` (would warrant `c_ingest_raw`).
- **List matter-scoped open todos.** Run
  `python agent_rules/scripts/list_matter_todos.py <matter_ref>`.

## Brief

Then brief the lawyer in plain language. Aim for ~10–15 lines. Cover:

- **Where it stands.** One or two sentences from Posture + most recent
  record entry.
- **Last activity.** The most recent `record.md` entry, plain language.
- **Pending.** Open deadlines (date + plain-language description), open
  todos (title + priority).
- **Imminent / overdue.** Anything within 14 days or already past — flag it
  separately.
- **What's next.** The matter's `## What's next` section, summarised.
- **Outstanding parses.** Note any `raw/` files without a `reference/`
  counterpart and offer `c_ingest_raw`.

End with an open invitation grounded in the matter:

> "Where do you want to pick up — [What's next item 1], [What's next item 2],
> or something else?"

## After the brief

Listen for direction. From here, the usual flow applies — translate natural
language into the right action (drafting in the matter per AGENTS.md
*Drafting, functions, and templates*; `c_log_communication`; `c_add_deadline`;
edit `info/status.md`; etc.). The matter is now "loaded" in your working
memory; subsequent moves should be informed by what you just read.
