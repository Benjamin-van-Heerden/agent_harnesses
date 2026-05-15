# Claim todo

Use when a todo is done.

## When to suggest

When the lawyer says they've handled something that's on the todo list:

- "I called the registrar."
- "Reviewed clause 5, looks fine."
- "Sent the invoice."
- "Did the X thing", "Handled that one", "That's done."

If you can match it to an open todo, suggest:

> "Want me to mark that todo done?"

## You handle

- **Slug.** Match against existing todos.

## Action

```
python agent_rules/scripts/claim_todo.py <slug>
```

Sets `status: claimed` and moves the file to `agent_rules/todos/claimed/`.

## After

- Confirm briefly.
- If the work was substantive, suggest `c_log_work` if the session is winding
  down.
