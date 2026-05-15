---
title: Update mem spec new to remind about todos
status: completed
created_at: '2026-01-23T15:35:55.332470'
updated_at: '2026-01-24T19:14:47.724195'
completed_at: '2026-01-24T19:14:47.724189'
---
Update src/commands/spec.py new() command to add a reminder about checking existing todos:

After the existing 'Next steps' output, add:
```
💡 Check if any existing todos relate to this spec:
   Run 'mem todo list' to see open todos  
   Use 'mem todo claim "title"' to mark them as addressed
```

## Amendments

Change the reminder text to be more direct:

```
💡 If this spec addresses any open todos, claim them:
   mem todo claim "title"
```

No need to tell them to run 'mem todo list' since todos are already visible in onboard output.

## Completion Notes

Per the amendment, simplified the reminder to: '💡 If this spec addresses any open todos, claim them:' followed by 'mem todo claim "title"'. Removed the instruction to run 'mem todo list' since todos are already visible in onboard. Also updated format_spec_detail() in onboard.py to show full task details for uncompleted tasks - completed tasks shown as simple list, pending tasks shown with full body content including amendments.