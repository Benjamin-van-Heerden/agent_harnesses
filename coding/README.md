# Agent Core Coding Harness

Agent Core is a project-local coordination harness for AI-assisted coding work. It gives coding agents a consistent repository-native workflow for getting context, planning larger changes, isolating implementation work, syncing durable state with GitHub, and leaving handoff notes for the next session.

The harness is installed into a project under `.agent_core/`. It is intentionally file-first and git-native: project state lives in readable files, important lifecycle events are reflected in git history, and command output tells the agent what it must do next.

This `README.md` is copied into `.agent_core/README.md` during install and update so humans can understand the installed harness without reading the agent-facing `AGENTS.md` contract or runtime source code.

## What Gets Installed

A coding harness installation has three main surfaces:

- Managed runtime files, mainly `.agent_core/harness/`. These implement the local CLI and may be replaced by setup and update commands.
- Project-owned state, such as `.agent_core/config.toml`, `.agent_core/specs/`, `.agent_core/todos/`, `.agent_core/memories/`, `.agent_core/logs/`, `.agent_core/docs/`, `.agent_core/patches.toml`, and `.agent_core/user_mappings.toml`. These are preserved across updates.
- Root agent instructions in `AGENTS.md`. The harness owns the `<AGENT_CORE>...</AGENT_CORE>` block, while project-specific notes outside that block are preserved.

Managed runtime files are disposable. Project-owned state is the durable record of what agents and humans have planned, claimed, completed, documented, or learned about the project.

## The Command Surface

Harness commands are run with the project-local Python entry point:

```bash
python -B .agent_core/harness/main.py <command>
```

The main command groups are:

- `onboard`: build the current agent context and enforce session preflight checks.
- `spec`: create, sync, assign, show, abandon, and complete larger planned work.
- `task`: create, list, show, rename, amend, and complete tasks inside specs.
- `todo`: create, list, show, claim, and delete standalone follow-up items.
- `memory`: create, list, show, update, and delete durable project notes.
- `log`: create, list, and show session work logs.
- `promotion`: prepare documented, remote-only promotions from `dev` to `test` and from `test` to `main`.
- `pr`: discover, review, respond to, and merge pull requests through the standardized workflow.
- `sync`: reconcile local spec and todo state with linked GitHub issues.
- `worktree` and `cleanup`: manage implementation worktrees and local branch/worktree hygiene.
- `introspect`: scaffold durable project reference documents for agents to complete.
- `config`: inspect or print default project configuration.
- `paths`: print resolved harness paths for debugging.

Not every command is meant to be used directly in every session. The agent-facing `AGENTS.md` block and command output define the required sequencing.

## The Onboard Loop

Every agent session normally starts with:

```bash
python -B .agent_core/harness/main.py onboard
```

Onboard is the context-building command. It checks whether local git state is safe, fetches remote state, runs the normal issue sync flow when possible, performs due harness updates, creates assigned spec worktrees for the authenticated user, and generates the context the agent must read before doing work.

The generated context can include project docs, important configured files, configured directory trees, configured runnable command output, active specs, tasks, todos, memories, recent work logs, branch state, and workflow instructions for the current checkout.

Onboard is deliberately strict. If local state or a remote check makes the context unsafe, it stops and explains what must be resolved. The command output is part of the workflow contract, not just status text.

## Mission Control On Dev

The configured development branch, usually `dev`, is mission control. Work done directly there should be small, focused, and appropriate for the shared coordination branch.

Mission control is where agents can:

- make small ad hoc edits;
- inspect project state;
- create and sync specs;
- assign specs after explicit approval;
- claim todos;
- merge completed pull requests;
- clean up completed worktrees and branches;
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

4. Assign the spec only after explicit approval.

   Bare assignment assigns the spec to the authenticated GitHub user, creates a dedicated local worktree, pushes the spec branch, and updates the GitHub issue:

   ```bash
   python -B .agent_core/harness/main.py spec assign <slug>
   ```

   Remote assignment assigns another mapped GitHub user, records and pushes the branch state, updates the GitHub issue, and does not create a local worktree for the current user:

   ```bash
   python -B .agent_core/harness/main.py spec assign <slug> --assignee <github_username>
   ```

   The assignee receives the local worktree automatically the next time they run onboard from mission control.

   Local spec worktrees are created outside the main checkout under a sibling `<project_name>-worktrees/` directory, with a separate directory for the assigned spec.

5. Implementation happens inside that spec worktree directory, on the spec branch. Tasks are completed one by one:

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

## Promotions And Pull Request Reviews

Protected branches remain on one shared linear history: `main` is behind `test`, and `test` is behind `dev`. A promotion advances a protected branch to an already existing point on that history. Direct `dev` to `test` and `test` to `main` branch updates are not part of the normal workflow.

Promotion creation is deliberately two-step:

```bash
python -B .agent_core/harness/main.py promotion create test
python -B .agent_core/harness/main.py promotion create test --execute
```

The first command fetches, checks out, and synchronizes the promotion source branch: `dev` for a test promotion or `test` for a production promotion. It then creates an ignored temporary promotion-description draft under `.agent_core/tmp/`. It does not push anything or create a branch or pull request. The agent remains on the source branch and treats its tracked code as read-only while investigating, testing, and documenting the promotion. The execution command validates the completed description, creates a remote-only snapshot branch from that inspected source checkout, opens the promotion PR with the description as its body, removes the temporary draft, and returns to `dev`.

An explicit direct-promotion request can begin with `promotion create <test|main> --no-pr`. The first invocation only explains what review protections would be bypassed and requires separate confirmation. If confirmed, the follow-up command printed by the harness fast-forwards the destination directly without creating a description, snapshot branch, or pull request. Direct promotion still enforces ancestry and refuses to proceed while a promotion PR is open for the destination.

Promotion PRs are completed through a fast-forward rather than a GitHub squash, rebase, or merge commit:

```bash
python -B .agent_core/harness/main.py pr merge <pr_ref>
```

PRs targeting the configured `main` branch require `--force` after separate explicit user confirmation. Completed and closed promotion branches are deleted immediately when possible and reconciled during normal sync to prevent remote branch accumulation.

PR review can start without full onboarding:

```bash
python -B .agent_core/harness/main.py pr review
```

With no reference, the command queries GitHub, lists open PRs, explains the available actions, and instructs the agent to ask which PR the user means. Once identified, `pr review <pr_ref>` generates the context the agent must inspect. Review comments, approvals, change requests, and merges use explicit PR references so no hidden local selection state is required.

## Tasks, Todos, Memories, Docs, And Logs

Tasks belong to specs. They describe implementation steps and are completed from the relevant spec worktree.

Todos are standalone reminders or small pieces of follow-up work. When a todo becomes substantial, it should become a spec. When an agent starts on a todo, it claims it through the harness so the linked GitHub issue is closed and ownership is clear.

Memories are short, atomic notes about durable project patterns and preferences. They are shown during onboard. They are not a substitute for specs or docs.

Docs are durable project context under `.agent_core/docs/`. They are included in onboard output. The harness can scaffold some docs, but project-specific docs remain project-owned state.

Harness-provided optional docs are managed locally after installation:

```bash
python -B .agent_core/harness/main.py docs list
python -B .agent_core/harness/main.py docs add coding_python coding_uv
python -B .agent_core/harness/main.py docs update coding_python
python -B .agent_core/harness/main.py docs remove coding_uv
```

The optional-doc catalog is refreshed with the harness. Installed selections and source hashes are tracked in `.agent_core/optional_docs.toml`. Update and removal refuse to overwrite or delete locally modified managed docs unless `--force` is passed. Unknown or invalid slugs are rejected before any requested document is changed.

Work logs record what happened in a session, what changed, blockers, and useful next steps. They are end-of-session artifacts. The `log new` command creates a template and tells the agent what must be filled in before committing or completing a spec.

## Introspection

The `introspect` command scaffolds durable reference documents under `.agent_core/docs/`:

```bash
python -B .agent_core/harness/main.py introspect structure
python -B .agent_core/harness/main.py introspect what
```

`introspect structure` creates a factual codebase map for an agent to complete after reading the repository. `introspect what` creates a project-purpose document and instructs the agent to interview the user before filling it in.

These commands create starting points, not finished documentation. The generated files contain placeholders and agent-facing completion instructions.

## Configuration

The main configuration file is `.agent_core/config.toml`.

Important fields include:

- `[project]`: project name and human-readable description for onboard context.
- `[[files]]`: optional individual files to include in onboard output. Projects should opt in deliberately.
- `[[tree_dirs]]`: optional directory trees to include in onboard output.
- `[[runnables]]`: optional project-local commands whose output should be captured in onboard context.
- `[worktree].symlink_paths`: project-root relative paths that should be symlinked from the main checkout into spec worktrees. Each configured path is automatically added to `.gitignore`; only use paths that are intentionally untracked, such as local env files, local dependency directories, or other development-only artifacts.
- `[branches]`: logical branch mapping for `dev`, `test`, and `main`, plus optional no-switch branch mappings.
- `[harness]`: update settings, including `update_interval_days` and `last_updated_at`.

Setup and update preserve configured values. They may patch managed comments, add missing required keys, or run recorded migrations, but they should not overwrite project-specific choices.

## Updates And Patches

The harness can be updated manually or during onboard.

Manual project-local update:

```bash
python -B .agent_core/harness/update.py --force
```

The update command runs only from the main checkout, not from a spec worktree. It expects to run on the configured dev branch. It downloads the current setup script for the coding harness and executes it with `--update` in the target project.

Onboard also checks whether an update is due based on `[harness].update_interval_days` and `[harness].last_updated_at`. If an update is due, onboard runs the same setup update flow and restarts itself with the refreshed harness.

The setup update flow:

- refreshes `.agent_core/harness/`;
- refreshes the managed `AGENTS.md` core block;
- refreshes the installed optional-doc catalog without overwriting project docs;
- copies this human README to `.agent_core/README.md`;
- applies source-side harness patches that have not yet been recorded in `.agent_core/patches.toml`;
- updates managed config comments and missing required config keys without resetting project-specific values;
- records a new `last_updated_at` timestamp;
- preserves specs, tasks, todos, memories, logs, docs, config choices, patch records, and user mappings.

If setup or onboard creates changes during a harness update, the harness update helper commits and pushes those changes so the refreshed harness state is durable.
