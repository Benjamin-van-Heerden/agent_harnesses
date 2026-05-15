# Create todo

Use for follow-up items that aren't currently in scope but shouldn't be
forgotten.

## When to suggest

When the lawyer says things like:

- "Remind me to call the registrar next week."
- "We'll need to review that clause before signing."
- "I should check the new amendments to the Act when I have time."
- "Don't forget to invoice for this."
- "Later we should...", "When I have time..."

Suggest:

> "Want me to add that as a todo?"

## You handle

- **Slug.** Short, lowercase, descriptive: `call_registrar`, `review_clause_5`, `invoice_smith_corp`.
- **Title.** One line.
- **Priority.** From urgency cues: "ASAP" → `high`; "when I have time" → `low`; default `normal`.
- **Matter ref** (optional but preferred when applicable). If the todo is
  clearly about a specific matter, scope it — pass the matter ref so it
  shows up under that matter on onboard and in `c_focus_matter`. Only leave
  unscoped for genuinely cross-cutting tasks ("invoice everyone in May",
  "update CPD log").
- **Description.** Concrete: what needs to be done, why, any context.

## Action

```
python agent_rules/scripts/new_todo.py <slug> "<title>" [priority] [matter_ref]
```

## Then fill in

- Replace `_TODO_` in the body with a concrete description.

## After

- Confirm in plain language. The todo will surface on the next onboard.
