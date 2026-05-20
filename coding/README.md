# Agent Core Coding Harness

Agent Core is a project-local development harness for AI-assisted coding work. It gives coding agents a consistent way to gather context, plan larger changes, isolate implementation work, and leave durable handoff notes without relying on global state outside the repository.

The harness is installed into a project under `.agent_core/`. It is intentionally file-first and git-native: project state is stored as readable files, the important lifecycle steps are reflected in git history, and the command output tells the agent what it must do next.

## What Gets Installed

A coding harness installation has two different kinds of files:

- Managed runtime files, mainly `.agent_core/harness/`. These are replaced by setup and update commands.
- Project-owned state, such as `.agent_core/config.toml`, `.agent_core/specs/`, `.agent_core/todos/`, `.agent_core/memories/`, `.agent_core/logs/`, `.agent_core/docs/`, and `.agent_core/user_mappings.toml`. These are preserved across updates.

The root `AGENTS.md` file is also managed in a careful way. The harness owns the `<AGENT_CORE>...</AGENT_CORE>` block, but project-specific notes outside that block are preserved.

This `README.md` is copied into `.agent_core/README.md` during install and update so humans can understand the harness without reading the agent-facing instructions or source code.

## The Onboard Loop

Every agent session normally starts with:

```bash
python -B .agent_core/harness/main.py onboard
```

Onboard is the context-building command. It fetches remote state, checks whether local git state is safe, runs the normal sync flow when possible, performs due harness updates, creates assigned spec worktrees for the authenticated user, and then generates the context the agent must read before doing work.

The generated context includes project docs, important configured files, active specs, tasks, todos, memories, recent work logs, branch state, and workflow instructions for the current location.

Onboard is deliberately strict. If the working tree is dirty before sync, it stops and explains what must be resolved. If a required remote check fails, it stops before producing potentially stale context. The command output is part of the workflow contract, not just status text.

## Mission Control On Dev

The configured development branch, usually `dev`, is mission control. Work done directly there should be small, focused, and appropriate for the shared coordination branch.

Mission control is where agents can:

- make small ad hoc edits;
- inspect project state;
- create and sync specs;
- assign specs;
- claim todos;
- manage completed worktrees and merged work;
- update the harness.

Open specs shown during onboard are context, not automatically the current workspace. If a spec has its own worktree, implementation work belongs in that worktree, not in the main repo checkout on `dev`.

## Specs And Worktrees

Specs are for larger pieces of planned work. A spec is a durable record under `.agent_core/specs/<slug>/` with a spec body, task files, assignment metadata, GitHub issue linkage, and later pull request metadata.

The normal spec lifecycle is:

1. Create the draft spec from mission control:

   ```bash
   python -B .agent_core/harness/main.py spec new "title"
   ```

2. Fill in the spec body and create concrete tasks:

   ```bash
   python -B .agent_core/harness/main.py task new "title" "detailed description" --spec <slug>
   ```

3. Sync the spec to GitHub after the body and tasks are ready:

   ```bash
   python -B .agent_core/harness/main.py spec sync <slug>
   ```

4. Assign the spec only after explicit user approval.

   Bare assignment assigns the spec to the authenticated GitHub user, creates a dedicated local worktree, pushes the spec branch, and updates the GitHub issue:

   ```bash
   python -B .agent_core/harness/main.py spec assign <slug>
   ```

   Remote assignment assigns another mapped GitHub user, records and pushes the branch state, updates the GitHub issue, and does not create a local worktree for the current user:

   ```bash
   python -B .agent_core/harness/main.py spec assign <slug> --assignee <github_username>
   ```

   The assignee receives the local worktree automatically the next time they run onboard from mission control.

5. Implementation happens inside the spec worktree, on the spec branch. Tasks are completed one by one after user approval:

   ```bash
   python -B .agent_core/harness/main.py task complete <task_slug> "notes"
   ```

6. When all tasks are complete, the worktree agent creates a work log and completes the spec:

   ```bash
   python -B .agent_core/harness/main.py log new
   python -B .agent_core/harness/main.py spec complete <slug> "detailed commit message"
   ```

   Spec completion commits and pushes work, rebases onto `origin/dev`, creates the pull request, records the PR in spec state, updates GitHub issue labels, and tells the user how to merge from mission control.

The key distinction is isolation. Mission control coordinates. Spec worktrees implement. This prevents a shared dev checkout from accumulating feature-branch state and makes it clear which agent session owns which branch.

## Tasks, Todos, Memories, Docs, And Logs

Tasks belong to specs. They describe implementation steps and are completed from the relevant spec worktree.

Todos are standalone reminders or small pieces of follow-up work. When a todo becomes substantial, it should become a spec. When an agent starts on a todo, it should claim it through the harness so the linked GitHub issue is closed and ownership is clear.

Memories are short, atomic notes about durable project patterns and preferences. They are shown during onboard. They are not a substitute for specs or docs.

Docs are durable project context under `.agent_core/docs/`. They are included in onboard output. The harness does not create or edit project docs unless explicitly instructed.

Work logs record what happened in a session, what changed, blockers, and useful next steps. They are end-of-session artifacts. The `log new` command creates a template and requires the agent to fill it in before committing or completing a spec.

## Configuration

The main configuration file is `.agent_core/config.toml`.

Important fields include:

- `[project]`: project name and human-readable description for onboard context.
- `[[files]]`: optional individual files to include in onboard output. The default README example is commented out; projects should opt in deliberately.
- `[[tree_dirs]]`: optional directory trees to include in onboard output.
- `[worktree].symlink_paths`: project-root relative paths that should be symlinked from the main checkout into spec worktrees. Each configured path is automatically added to `.gitignore`; only use paths that are intentionally untracked, such as local env files, local dependency directories, or other development-only artifacts.
- `[branches]`: logical branch mapping for `dev`, `test`, and `main`, plus optional no-switch branch mappings.
- `[harness]`: update settings, including `update_interval_days` and `last_updated_at`.

Setup and update preserve configured values. They may patch managed comments or add missing required keys, but they should not overwrite project-specific choices.

## Update Mechanism

The harness can be updated manually or during onboard.

Manual project-local update:

```bash
python -B .agent_core/harness/update.py --force
```

The update command runs only from the main checkout, not from a spec worktree. It expects to run on the configured dev branch. It downloads the current `coding/setup.py` from the harness repository and executes it with `--update` in the target project.

Onboard also checks whether an update is due based on `[harness].update_interval_days` and `[harness].last_updated_at`. If an update is due, onboard runs the same setup update flow and then restarts itself with the refreshed harness.

The setup update flow:

- refreshes `.agent_core/harness/`;
- refreshes the managed `AGENTS.md` core block;
- refreshes installed optional docs that still match harness-provided docs;
- copies this human README to `.agent_core/README.md`;
- updates managed config comments and missing required config keys without resetting project-specific values;
- records a new `last_updated_at` timestamp;
- preserves specs, tasks, todos, memories, logs, docs, config choices, and user mappings.

If setup or onboard creates changes during a harness update, the harness update helper commits and pushes those changes so the refreshed harness state is durable.

## Development Boundary

When developing the coding harness itself, source changes belong under `coding/`. The installed `.agent_core/harness/` directory in this repository is generated runtime and should not be manually edited as the source of truth.

The normal local propagation loop while developing the coding harness is:

```bash
python -B coding/setup.py --update
```

For installed projects outside this repository, updates flow through `.agent_core/harness/update.py` or onboard's automatic update check after the harness changes have been pushed to the repository branch used by the remote setup URL.
