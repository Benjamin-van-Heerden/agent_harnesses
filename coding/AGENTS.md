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

### Note

The onboard command performs git/network operations such as fetch and rebase. It must be ran it in an elevated shell with outbound network access. 

## About Agent Core

Agent Core is a project-local CLI tool for managing project context in AI-assisted development. It uses a file-first, git-native architecture where all project state is stored as markdown files with YAML frontmatter in the `.agent_core/` directory.

**Core concepts:**
- **Specs**: High-level feature specifications linked to GitHub issues.
- **Tasks**: Concrete work items within a spec.
- **Todos**: Standalone work items not tied to a spec, synced with GitHub issues.
- **Memories**: Short, atomic notes about patterns, conventions, or preferences in the codebase.
- **Work Logs**: Session records of what was done and what's next.

**Key commands:**
- `python -B .agent_core/harness/main.py spec new "title"` - Create a new spec.
- `python -B .agent_core/harness/main.py sync issues` - Sync the project context with the remote repository. This is a very important command. It ensures the remote knows about local specs and todos before assignment or GitHub-linked work.
- `python -B .agent_core/harness/main.py spec assign <slug>` - Assign spec to and create worktree. DO NOT ASSIGN SPECS WITHOUT EXPLICIT CONSENT.
- `python -B .agent_core/harness/main.py task new <spec_slug> "title" "detailed description with implementation notes if necessary"` - Create a task under a specific spec.
- `python -B .agent_core/harness/main.py task complete <spec_slug> <task_slug> "detailed notes about what was done"` - Mark task done.
- `python -B .agent_core/harness/main.py spec complete <slug> "detailed commit message"` - Create PR and mark spec merge-ready.
- `python -B .agent_core/harness/main.py log new` - Create work log for the session. This is an extremely important command that should be run towards the end of every session. If you feel at any point your context window is becoming too large, suggest creating a log and continuing in a new session.

**Todos (standalone work items):**
- `python -B .agent_core/harness/main.py todo new "title" "description"` - Create a todo and linked GitHub issue.
- `python -B .agent_core/harness/main.py todo list` - List all open todos.
- `python -B .agent_core/harness/main.py todo claim <slug> <user>` - Claim a todo and close the linked GitHub issue.

**Memories (project-specific notes):**
- `python -B .agent_core/harness/main.py memory new "title" "content"` - Create a memory, a short note about a pattern, convention, or preference.
- `python -B .agent_core/harness/main.py memory list` - List all memories.
- `python -B .agent_core/harness/main.py memory show <slug>` - Show memory details.
- `python -B .agent_core/harness/main.py memory update <slug> "new content"` - Update a memory.
- `python -B .agent_core/harness/main.py memory delete <slug>` - Delete a memory.

**Documents:**
- Durable project context that should appear during onboard belongs in `.agent_core/docs/`.
- Onboard reads markdown documents from `.agent_core/docs/` directly.
- Optional repo-local docs can be managed from the harness template with `setup.sh docs list`, `setup.sh docs add <slug> [slug ...]`, and `setup.sh docs update [slug ...]`.

## Project State

Project-owned state lives in `.agent_core/`:

- `.agent_core/config.toml`
- `.agent_core/user_mappings.toml`
- `.agent_core/specs/`
- `.agent_core/todos/`
- `.agent_core/memories/`
- `.agent_core/logs/`
- `.agent_core/docs/`

The managed runtime lives in `.agent_core/harness/` and may be overwritten by
`setup.sh --update`.

## Memories

Memories are short, atomic notes about patterns, conventions, or preferences in the codebase. They are shown during onboard so every session has access to accumulated project knowledge.

- **When the user asks you to remember something** - create a memory with `python -B .agent_core/harness/main.py memory new "title" "content"`.
- **When you notice a useful pattern** - suggest creating a memory, but only create it if the user agrees.
- Do not use external memory tools. Use the project-local harness memory command instead.

## Notes

- Do not `cd` into the project directory unless necessary; your shell is typically already at the project root.
- Do not enter plan mode - the harness handles planning through specs and tasks.
- Do not use external task management tools - use harness tasks and todos instead.
- Do not create specs unless prompted - often times work happens out of spec.
- When running any harness command that talks to GitHub, **ALWAYS** allow for at least 60 seconds of execution time because the GitHub API can hang.
- `python -B .agent_core/harness/main.py log new` is not an interactive command. When prompted to "Create a log" or "Let's log", run the log command and follow the instructions.
- Do not create logs arbitrarily, logs are meant to be end of session artifacts that inform the next session. If it is your estimation that a session is becoming long or if your interaction with the user would indicate that some form of context corruption has occurred (constant pushback, frustration etc.), you may suggest creating a log and changing over to a fresh session.
- When working in the context of a spec inside a worktree directory, you are ABSOLUTELY NEVER allowed to perform mutating action on the main repo directory in any way shape or form. No git operations. If any merge or rebase fails inside a spec, you must resolve the issues inside that spec.
- Do not add your name or the fact that you co-authored something to any commit messages. Commit messages should be clean and descriptive, with no extra information.
- Do not run onboard arbitrarily - its output can be very large and typically within the scope of a session it will not provide additional information. The purpose of the onboard command is to sync/build initial context. No other time is it necessary unless the user asks.
- The outputs produced by harness commands are to be strictly adhered to. Especially in cases where the harness instructs you to stop and give feedback. This is important to keep a human in the loop.
- When working within a spec, DO NOT CREATE TASKS unless explicitly prompted to do so.
- Preserve project-owned state during harness updates.
- Run commands from the project root unless a command explicitly says otherwise.
- When you encounter a file or changes that you did not make, you must stop and ask about them. Removing such files or changes is NOT ACCEPTABLE unless explicit consent is given.
- When you are interrupted by the user with "Stop" or "No" or similar, you must **IMMEDIATELY** stop what you are doing, give a brief explanation of what you were busy with, and wait for further instructions. DO NOT continue working.

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria like "make it work" require constant clarification.
</AGENT_CORE>
