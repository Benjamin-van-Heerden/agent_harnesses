# Initial setup — first run

A guided walk-through for a fresh praxis install. Three phases:

1. **Lawyer profile** — interview the lawyer, populate `lawyer_profile.md`.
2. **Default document template** — design and build `src/templates/components/style.typ`,
   then compile a sample document so the lawyer can see what their drafts will
   look like.
3. **Legal context** (optional) — offer to populate `agent_rules/docs/core/legal_context.typ`.
   Skip gracefully if they decline.

The goal of the first run is concrete: by the end, the lawyer has a working
template they can use immediately, and you (the agent) have enough context
to draft in their voice.

## When to use

Run this when **all** of these are true:

- `agent_rules/lawyer_profile.md` still contains the literal string
  `PLACEHOLDER — NOT YET FILLED IN`.
- `src/templates/components/style.typ` does not exist.

c_onboard detects this combination and hands control to this command.
You may also be invoked directly if the lawyer says something like
"let's set things up" or "design my default template" mid-session.

## Tone

Conversational, not a form. Ask one or two questions at a time, listen,
write things down as you go. The lawyer is reading your output, not filling
in a survey. Keep it human.

## Welcome (open with this)

Open the flow with a brief framing so the lawyer knows what's coming.
Something like:

> **Welcome — let's get you set up.**
>
> This is a fresh praxis install. Before you can use it properly, two
> things need to exist:
>
> 1. Your profile — who you are, how you write, what conventions to follow.
> 2. A default document template — the base every letter, opinion, and
>    pleading we draft will be built from.
>
> I'll walk you through both. About 10–15 minutes. By the end, you'll have
> a working template I'll have compiled and tested — open it, tell me what
> to change, and we iterate until you like it. We can also fill in
> jurisdictional details after that if you want.
>
> Ready?

If the lawyer wants to defer ("not now", "later"), don't push — they can
trigger this command any time with "let's set things up". The c_onboard
placeholder warning will keep prompting them on future sessions until
the setup is done.

If they're ready, proceed.

---

## Phase 1 — Lawyer profile

Goal: a populated `agent_rules/lawyer_profile.md` with the placeholder block
removed.

Open the file, see the structure (Identity / Specialty and venues / Working
style), and walk the lawyer through it. Keep blocks of questions short —
**Identity first, then Specialty, then Working style** — confirm each block
back to them before moving on.

Don't read the questions verbatim — paraphrase. Examples:

- Identity: name, year admitted and where, sole practitioner / advocate /
  attorney, firm name (if any).
- Specialty and venues: primary practice areas, primary courts, secondary
  venues.
- Working style: tone (formal / plain / conversational), formality
  conventions ("Yours faithfully" vs "Kind regards"; salutations), citation
  density (heavy footnoting / sparse / in-text), structural preferences
  (numbered paragraphs in pleadings? affidavit quirks?), drafting habits
  (recurring formulations, words to avoid), letterhead and signature
  details.

When you have all three blocks, write the file in one pass: replace the
**entire file** with their answers. The placeholder block goes away — no
leftover sentinel. Use the existing structure (`## Identity`, `## Specialty
and venues`, `## Working style — how the agent should write for this lawyer`)
so future onboards parse it the same way.

Read it back briefly — one or two lines — and ask if anything's wrong.

---

## Phase 2 — Default document template

Goal: `src/templates/components/style.typ` exists and produces a good-looking
sample document.

Most of what's needed for the template you already learned in Phase 1
(letterhead content, signature block). Two extras to ask about now:

- **Logo.** "Do you have a firm logo as an image file? If so, save it as
  `logo.png` (or `.svg`/`.jpg`) and put it in
  `src/templates/components/assets/` — let me know when it's there. Or skip and
  we'll go text-only for now." If the lawyer drops a logo, accept whatever
  they give you and reference it by the path they used. If they have no
  logo, build the letterhead from text alone.
- **Page setup.** A4 vs Letter. Margins (default 2.5cm each side is fine).
  Default font (have a sensible suggestion ready — EB Garamond or similar
  serif for a traditional look; ask).

### Build `src/templates/components/style.typ`

This file is the base every document will import from. It should expose:

- A small `firm` data record (firm name, address, contact, registration).
- A letterhead block (logo + firm name + address + contact, laid out
  appropriately).
- A signature block (signatory name, capacity, contact).
- A page/text setup helper (`firm_doc` or similar) — paper, margins, font.
- A high-level letter helper that takes recipient, salutation, body and
  produces a complete formatted letter using the above.

Don't be overly prescriptive in *how* you structure these — the goal is a
working, edit-friendly template the lawyer can grow into. Reference the
patterns in `agent_rules/docs/core/typst_basic_reference.typ` and
`agent_rules/docs/typst_detailed_reference.typ` if you need a refresher on
how to express any of this in typst.

Two important conventions:

- **Currency, citation, date format.** If `legal_context.typ` is filled in,
  honour what it says. If not, default to ISO dates and ask the lawyer for
  any preferences before writing format-sensitive helpers.
- **Don't hardcode jurisdictional assumptions** into the template. Defer to
  lawyer-specific snippets in `src/functions/` for things like currency
  formatting and citation rendering.

### Test-compile a sample

After writing `style.typ`, you compile a small sample to make sure it
works and to give the lawyer something to look at.

Write a short test letter to a fictional recipient (e.g. "Mr T Test, 1
Test Road, Testville, 1234") that uses the new template. Save it to
`/tmp/praxis_initial_setup_preview.typ`.

Compile it:

```
typst compile /tmp/praxis_initial_setup_preview.typ /tmp/praxis_initial_setup_preview.pdf
```

If the compile fails, read the error, fix the template, and try again.
**The lawyer should not see compile errors** — own the loop until it
compiles cleanly. If you hit something you genuinely can't resolve after
two or three attempts, surface it: "I'm hitting a typst issue I can't
work around — here's what I tried…" and ask for help.

When it compiles, read the PDF (you can read PDFs directly) to verify it
looks right — letterhead in the right place, signature block at the
bottom, no obvious layout glitches. Then tell the lawyer in plain
language:

> "Your default template is ready. I've compiled a sample at
> `/tmp/praxis_initial_setup_preview.pdf` — open it to have a look. Tell
> me what you want to change: the logo placement, fonts, spacing, the
> firm name styling, anything."

Iterate until they're happy. Each iteration: edit `style.typ`, recompile,
ask. Don't pretend an iteration finished by re-rendering only in your
head — actually run the compile each time.

When they're satisfied, delete the temp preview files:

```
rm -f /tmp/praxis_initial_setup_preview.typ /tmp/praxis_initial_setup_preview.pdf
```

---

## Phase 3 — Legal context (optional)

Once Phases 1 and 2 are done, offer Phase 3 — but only as an option:

> "While we're here — want to spend another 10 minutes filling in the
> jurisdictional reference? It means I won't guess at citations or
> deadlines later. Or skip and we'll do it the first time it actually
> matters."

If the lawyer declines, that's fine — the placeholder warning will keep
prompting them on future onboards.

If they accept, walk them through `agent_rules/docs/core/legal_context.typ`
section by section: Jurisdiction → Court hierarchy → Citation conventions
→ Date and currency → Court days vs calendar days → Common rule-based
deadlines → Document-format conventions → Privilege / ethics / regulator →
Anything else.

Take their answers and write them into the file under each heading,
replacing the `_TODO_` markers. Remove the entire placeholder comment
block at the top of the file once everything is filled — keep the comment
about replacing per-section if helpful, but the sentinel must go.

---

## Wrap-up

When the setup is complete (Phase 1 always; Phase 2 always; Phase 3 if
they did it), confirm in plain language:

> "You're set up. `lawyer_profile.md` is filled in. Your default template
> lives at `src/templates/components/style.typ` — every document we draft from
> now on will use it. [If Phase 3:] `legal_context.typ` is filled in too.
>
> From here, the normal flow applies: tell me about a new client and I'll
> open the matter, or just say what you want drafted. Try me."

Don't run `c_log_work` automatically — this is setup, not a billable
session. If the lawyer wants a log of the setup itself, they'll ask.
