# Create memory

Use when something is worth remembering across sessions: a pattern,
preference, jurisdictional quirk, judge's preference, recurring phrasing,
reusable insight.

## When to suggest

Ambient cues that warrant a suggestion:

- "Save this", "Remember this approach", "Make a note of this for next time."
- The lawyer says "we always do it this way".
- A jurisdiction-specific rule comes up that isn't in `agent_rules/docs/core/legal_context.typ`.
- A particular judge or registrar's preference becomes apparent.
- A solution to a tricky problem is found that may recur.
- The lawyer corrects you in a way that should stick.

If the thing to save is specifically a reusable typst snippet or document
template, prefer extracting a function or promoting a template (see AGENTS.md
*Drafting, functions, and templates*) over creating a memory.

When you notice one, ask:

> "Worth remembering this for next time?"

Only proceed if the lawyer agrees.

## You handle

- **Slug.** Short, lowercase, descriptive: `judge_khumalo_preferences`, `prescription_calculation`, `firm_letter_signoff`.
- **Title.** One line summarising the memory.
- **Content.** The body — drawn from the conversation.

## Action

```
python agent_rules/scripts/new_memory.py <slug> "<title>"
```

Creates `agent_rules/memories/<slug>.md` with `_TODO_` for the body.

## Then fill in

- Replace `_TODO_` with the actual content. Keep it short and atomic — one
  idea per file. Two paragraphs maximum.
- Add tags in the frontmatter if relevant.

## After

- Confirm: "Saved. I'll remember that next time."
