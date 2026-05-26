<AGENT_CORE>
# Working With Agent Core

This project uses a project-local harness for context management and version control in AI-assisted development.

## First Action

The first action in every session is typically to get up to date with the project context:

```bash
python -B .agent_core/harness/main.py onboard
```

Be on the lookout for trigger phrases like "Let's get to work", "Let's go" or "Get onboarded". If you see one, run the onboard command to get started.

Use this local Python invocation for harness commands. Do not assume a global CLI is installed on `PATH`.

Onboard gives you everything you need: project info, coding guidelines, active specs, tasks, todos, memories, and recent work logs. The onboard output includes all available commands and project state.

**Note:** The onboard command (and indeed many of the harness commands) performs git/network operations such as fetch and rebase. It must be ran it in an elevated shell with outbound network access. Run all harness commands with such elevation.

## About Agent Core

Agent Core is a project-local CLI tool for managing project context in AI-assisted development. It uses a file-first, git-native architecture where all project state is stored as markdown files with YAML frontmatter in the `.agent_core/` directory.

### Project State

Project-owned state lives in `.agent_core/`:

- `.agent_core/config.toml`
- `.agent_core/user_mappings.toml`
- `.agent_core/specs/`
- `.agent_core/todos/`
- `.agent_core/memories/`
- `.agent_core/logs/`
- `.agent_core/docs/`

### Concepts and Commands

**Note**: For all of the agent core commands, the global python interpreter should ALWAYS be used.

**Specs (larger pieces of planned work):**
Specs are high-level feature or change specifications linked to GitHub issues. They are used when work needs planning, task breakdown, assignment, a worktree, and a PR lifecycle.

- `python -B .agent_core/harness/main.py spec new "title"` - Create a draft spec.
- `python -B .agent_core/harness/main.py spec sync <slug>` - Create or update the linked GitHub issue after the spec body and tasks are ready.
- `python -B .agent_core/harness/main.py spec assign <slug>` - Assign the spec and create its worktree. DO NOT ASSIGN SPECS WITHOUT EXPLICIT CONSENT.
- `python -B .agent_core/harness/main.py spec complete <slug> "detailed commit message"` - Create the PR and mark the spec merge-ready.

**Tasks (concrete work inside a spec):**
Tasks are actionable work items that belong to a spec. When run from a spec worktree, task commands infer the active spec. Use `--spec <slug>` only when managing a specific spec from outside its worktree (this will be the case most of the time, since planning and spec creation happens in non spec branches - where specs are not yet "active").

- `python -B .agent_core/harness/main.py task new "title" "detailed description with implementation notes if necessary" --spec <slug>` - Create a task in the active spec.
- `python -B .agent_core/harness/main.py task complete <task_slug> "detailed notes about what was done"` - Mark a task complete in the active spec (this command only really makes sense when within a spec branch/worktree).

**Todos (standalone matters that require attention):**
Todos are short notes on tasks that need to be completed or triaged. If the workload of a todo is large, create a spec for the implementation. Treat todos as a mechanism to draw attention to problems or changes, not full guidelines. As such, **when starting work on a todo, claim it immediately**.

- `python -B .agent_core/harness/main.py todo new "title" "description"` - Create a todo and linked GitHub issue.
- `python -B .agent_core/harness/main.py todo list` - List all open todos.
- `python -B .agent_core/harness/main.py todo claim <slug> <user>` - Claim a todo and close the linked GitHub issue.

**Work Logs (session records):**
Work logs capture what happened in a session, what changed, blockers, and next steps. They are end-of-session artifacts that help the next agent continue with accurate context.

- `python -B .agent_core/harness/main.py log new` - Create a work log for the session. This is an extremely important command that should be run towards the end of every session.

**Memories (atomic notes on patterns and conventions)**
Memories are short, atomic notes about patterns, conventions, or preferences in the codebase. They are shown during onboard so every session has access to accumulated project knowledge.

- **When the user asks you to remember something** - create a memory with `python -B .agent_core/harness/main.py memory new "title" "content"`.
- **When you notice a useful pattern** - suggest creating a memory, but only create it if the user agrees.
- Do not use external memory tools. Use the project-local harness memory command instead.
- `python -B .agent_core/harness/main.py memory list` - List all memories.
- `python -B .agent_core/harness/main.py memory show <slug>` - Show memory details.
- `python -B .agent_core/harness/main.py memory update <slug> "new content"` - Update a memory.
- `python -B .agent_core/harness/main.py memory delete <slug>` - Delete a memory.

**Documents (durable project context):**
Documents are durable project context files that appear during onboard. They belong in `.agent_core/docs/`. Their creation and management is done manually by the user. DO NOT create or update files in `.agent_core/docs` without explicit consent.

**Repair Commands (manual reconciliation):**
Repair commands are for explicit recovery or reconciliation. Do not run them as part of normal onboarding; `onboard` already syncs version control and issue state before building context. Any repair command should be a last resort.

- `python -B .agent_core/harness/main.py sync issues` - Reconcile local specs and todos with linked GitHub issues when issue metadata has drifted or a previous sync failed.

## Notes

- Do not `cd` into the project directory unless necessary; your shell is typically already at the project root.
- Do not enter plan mode - the harness handles planning through specs and tasks.
- Do not use external task management tools - use harness tasks and todos instead.
- Do not create specs unless prompted - often times work happens out of spec.
- When running any harness command that talks to GitHub, **ALWAYS** allow for at least 60 seconds of execution time because the GitHub API can hang.
- `python -B .agent_core/harness/main.py log new` is not an interactive command. When prompted to "Create a log" or "Let's log", run the log command and follow the instructions.
- Do not create logs arbitrarily, logs are meant to be end of session artifacts that inform the next session. If it is your estimation that a session is becoming long or if your interaction with the user would indicate that some form of context corruption has occurred (constant pushback, frustration etc.), you may suggest creating a log and changing over to a fresh session.
- When working in the context of a spec inside a worktree directory, you are ABSOLUTELY NEVER allowed to perform mutating action on the main repo directory in any way shape or form. If any merge or rebase fails inside a spec, you must resolve the issues inside that spec.
- Do not add your name or the fact that you co-authored something to any commit messages. Commit messages should be clean and descriptive, with no extra information.
- Do not run the onboard command arbitrarily - its output can be very large and typically within the scope of a session it will not provide additional information. The purpose of the onboard command is to sync version control and build initial context. No other time is it necessary unless the user asks.
- The outputs produced by harness commands are to be strictly adhered to. Especially in cases where the harness instructs you to stop and give feedback. This is important to keep a human in the loop.
- When working within a spec, DO NOT CREATE TASKS unless explicitly prompted to do so.
- Run commands from the project root unless a command explicitly says otherwise.
- When you encounter a file or changes that you did not make, you must stop and ask about them. Removing such files or changes is NOT ACCEPTABLE unless explicit consent is given.
- When you are interrupted by the user with "Stop" or "No" or similar, you must **IMMEDIATELY** stop what you are doing, give a brief explanation of what you were busy with, and wait for further instructions. DO NOT continue working.
- Refrain from performing actions without user consent unless the action is trivial or has very low risk. Always explain choices and invite user feedback.
- Strive for a workflow loop where:
    > - The *user* gives an instruction.
    > (loop)
    >   - *You* do research, establish and understand the problem.
    >   - *You* provide context and diagnostics. to the user and ask clarifying questions
    >   - The *user* gives feedback.
    > (end loop if feedback intends for implementation to proceed)
    > - *You* implement the changes/updates as discussed with the *user*.
    > - *You* provide a clear and informative summary of what you did and what changed. 
  This kind of workflow is not always possible nor practical, but especially when larger changes need to happen, this should be adhered to. "Quick and dirty" changes prompted via direct instruction can be implemented at your discretion. 

---------------------------------------------------------------

### Source Formatting

- Do not hard-wrap lines just to satisfy an arbitrary line length. This project assumes modern editors with line wrapping.
- Keep user-facing strings, command strings, markdown output fragments, and simple expressions on one line when that is clearer.
- Only split a line when it improves structure or readability, such as a genuinely complex expression, a long data literal, or nested call arguments. When applicable use multiline strings for this.
- Do not reflow existing prose or strings unless the requested change requires it.
</AGENT_CORE>

<core_instructions>
# Working With Agent Core

This project uses a project-local harness for context management and version control in AI-assisted development.

## First Action

The first action in every session is typically to get up to date with the project context:

```bash
python -B .agent_core/harness/main.py onboard
```

Be on the lookout for trigger phrases like "Let's get to work", "Let's go" or "Get onboarded". If you see one, run the onboard command to get started.

Use this local Python invocation for harness commands. Do not assume a global CLI is installed on `PATH`.

Onboard gives you everything you need: project info, coding guidelines, active specs, tasks, todos, memories, and recent work logs. The onboard output includes all available commands and project state.

**Note:** The onboard command (and indeed many of the harness commands) performs git/network operations such as fetch and rebase. It must be ran it in an elevated shell with outbound network access. Run all harness commands with such elevation.

## About Agent Core

Agent Core is a project-local CLI tool for managing project context in AI-assisted development. It uses a file-first, git-native architecture where all project state is stored as markdown files with YAML frontmatter in the `.agent_core/` directory.

### Project State

Project-owned state lives in `.agent_core/`:

- `.agent_core/config.toml`
- `.agent_core/user_mappings.toml`
- `.agent_core/specs/`
- `.agent_core/todos/`
- `.agent_core/memories/`
- `.agent_core/logs/`
- `.agent_core/docs/`

### Concepts and Commands

**Note**: For all of the agent core commands, the global python interpreter should ALWAYS be used.

**Specs (larger pieces of planned work):**
Specs are high-level feature or change specifications linked to GitHub issues. They are used when work needs planning, task breakdown, assignment, a worktree, and a PR lifecycle.

- `python -B .agent_core/harness/main.py spec new "title"` - Create a draft spec.
- `python -B .agent_core/harness/main.py spec sync <slug>` - Create or update the linked GitHub issue after the spec body and tasks are ready.
- `python -B .agent_core/harness/main.py spec assign <slug>` - Assign the spec and create its worktree. DO NOT ASSIGN SPECS WITHOUT EXPLICIT CONSENT.
- `python -B .agent_core/harness/main.py spec complete <slug> "detailed commit message"` - Create the PR and mark the spec merge-ready.

**Tasks (concrete work inside a spec):**
Tasks are actionable work items that belong to a spec. When run from a spec worktree, task commands infer the active spec. Use `--spec <slug>` only when managing a specific spec from outside its worktree (this will be the case most of the time, since planning and spec creation happens in non spec branches - where specs are not yet "active").

- `python -B .agent_core/harness/main.py task new "title" "detailed description with implementation notes if necessary" --spec <slug>` - Create a task in the active spec.
- `python -B .agent_core/harness/main.py task complete <task_slug> "detailed notes about what was done"` - Mark a task complete in the active spec (this command only really makes sense when within a spec branch/worktree).

**Todos (standalone matters that require attention):**
Todos are short notes on tasks that need to be completed or triaged. If the workload of a todo is large, create a spec for the implementation. Treat todos as a mechanism to draw attention to problems or changes, not full guidelines. As such, **when starting work on a todo, claim it immediately**.

- `python -B .agent_core/harness/main.py todo new "title" "description"` - Create a todo and linked GitHub issue.
- `python -B .agent_core/harness/main.py todo list` - List all open todos.
- `python -B .agent_core/harness/main.py todo claim <slug> <user>` - Claim a todo and close the linked GitHub issue.

**Work Logs (session records):**
Work logs capture what happened in a session, what changed, blockers, and next steps. They are end-of-session artifacts that help the next agent continue with accurate context.

- `python -B .agent_core/harness/main.py log new` - Create a work log for the session. This is an extremely important command that should be run towards the end of every session. DO NOT create work logs without user permission. If you find you are at a logical point where a work log could/should be created, YOU MUST first inform your intent to the user and ask permission.

**Memories (atomic notes on patterns and conventions)**
Memories are short, atomic notes about patterns, conventions, or preferences in the codebase. They are shown during onboard so every session has access to accumulated project knowledge.

- **When the user asks you to remember something** - create a memory with `python -B .agent_core/harness/main.py memory new "title" "content"`.
- **When you notice a useful pattern** - suggest creating a memory, but only create it if the user agrees.
- Do not use external memory tools. Use the project-local harness memory command instead.
- `python -B .agent_core/harness/main.py memory list` - List all memories.
- `python -B .agent_core/harness/main.py memory show <slug>` - Show memory details.
- `python -B .agent_core/harness/main.py memory update <slug> "new content"` - Update a memory.
- `python -B .agent_core/harness/main.py memory delete <slug>` - Delete a memory.

**Documents (durable project context):**
Documents are durable project context files that appear during onboard. They belong in `.agent_core/docs/`. Their creation and management is done manually by the user. DO NOT create or update files in `.agent_core/docs` without explicit consent.

**Repair Commands (manual reconciliation):**
Repair commands are for explicit recovery or reconciliation. Do not run them as part of normal onboarding; `onboard` already syncs version control and issue state before building context. Any repair command should be a last resort.

- `python -B .agent_core/harness/main.py sync issues` - Reconcile local specs and todos with linked GitHub issues when issue metadata has drifted or a previous sync failed.

## Notes

- Do not `cd` into the project directory unless necessary; your shell is typically already at the project root.
- Do not enter plan mode - the harness handles planning through specs and tasks.
- Do not use external task management tools - use harness tasks and todos instead.
- Do not create specs unless prompted - often times work happens out of spec.
- When running any harness command that talks to GitHub, **ALWAYS** allow for at least 60 seconds of execution time because the GitHub API can hang.
- `python -B .agent_core/harness/main.py log new` is not an interactive command. When prompted to "Create a log" or "Let's log", run the log command and follow the instructions.
- Do not create logs arbitrarily, logs are meant to be end of session artifacts that inform the next session. If it is your estimation that a session is becoming long or if your interaction with the user would indicate that some form of context corruption has occurred (constant pushback, frustration etc.), you may suggest creating a log and changing over to a fresh session.
- When working in the context of a spec inside a worktree directory, you are ABSOLUTELY NEVER allowed to perform mutating action on the main repo directory in any way shape or form. If any merge or rebase fails inside a spec, you must resolve the issues inside that spec.
- Do not add your name or the fact that you co-authored something to any commit messages. Commit messages should be clean and descriptive, with no extra information.
- Do not run the onboard command arbitrarily - its output can be very large and typically within the scope of a session it will not provide additional information. The purpose of the onboard command is to sync version control and build initial context. No other time is it necessary unless the user asks.
- The outputs produced by harness commands are to be strictly adhered to. Especially in cases where the harness instructs you to stop and give feedback. This is important to keep a human in the loop.
- When working within a spec, DO NOT CREATE TASKS unless explicitly prompted to do so.
- Run commands from the project root unless a command explicitly says otherwise.
- When you encounter a file or changes that you did not make, you must stop and ask about them. Removing such files or changes is NOT ACCEPTABLE unless explicit consent is given.
- When you are interrupted by the user with "Stop" or "No" or similar, you must **IMMEDIATELY** stop what you are doing, give a brief explanation of what you were busy with, and wait for further instructions. DO NOT continue working.
- Refrain from performing actions without user consent unless the action is trivial or has very low risk. Always explain choices and invite user feedback.
- Strive for a workflow loop where:
    > - The *user* gives an instruction.
    > (loop)
    >   - *You* do research, establish and understand the problem.
    >   - *You* provide context and diagnostics. to the user and ask clarifying questions
    >   - The *user* gives feedback.
    > (end loop if feedback intends for implementation to proceed)
    > - *You* implement the changes/updates as discussed with the *user*.
    > - *You* provide a clear and informative summary of what you did and what changed. 
  This kind of workflow is not always possible nor practical, but especially when larger changes need to happen, this should be adhered to. "Quick and dirty" changes prompted via direct instruction can be implemented at your discretion. 

---------------------------------------------------------------

### Source Formatting

- Do not hard-wrap lines just to satisfy an arbitrary line length. This project assumes modern editors with line wrapping.
- Keep user-facing strings, command strings, markdown output fragments, and simple expressions on one line when that is clearer.
- Only split a line when it improves structure or readability, such as a genuinely complex expression, a long data literal, or nested call arguments. When applicable use multiline strings for this.
- Do not reflow existing prose or strings unless the requested change requires it.
</core_instructions>

# Very Important Scoping Context

This project deals with agentic harness development. Critically, the agentic harness for coding *is itself used to develop the other harnesses*. As a result, mutating python scripts in .agent_core/src *will not have the intended effect of updating the harness itself*. Work and changes to the coding harness should be made under coding/.

Should the local .agent_core/ need updating, the loop *must* be: 
> make changes to coding/ -> git push -> run `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/coding/setup.py').read())" -- --update`
