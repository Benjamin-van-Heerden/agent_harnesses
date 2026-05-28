# Legal Agent Core Harness

This template installs a local-first legal practice harness for an agent-assisted, Typst-first legal workflow.

Fresh install from a target practice directory:

```bash
python -B /path/to/agent_harnesses/legal/setup.py
```

Update an existing install:

```bash
python -B /path/to/agent_harnesses/legal/setup.py --update
```

Manage optional/default docs:

```bash
python -B /path/to/agent_harnesses/legal/setup.py docs list
python -B /path/to/agent_harnesses/legal/setup.py docs add legal_harness_typst_basic_reference
python -B /path/to/agent_harnesses/legal/setup.py docs update
```

The installed project gets a native `.praxis/harness/` runtime and a managed `AGENTS.md` block. Setup/update refreshes managed runtime and reference files while preserving lawyer-owned state such as clients, matters, unbound matters, profile/context files, memories, logs, todos, custom Typst source, WIP drafting space, assets, drafts, PDFs, raw material, and references.

The agent-facing entrypoint in an installed practice is:

```bash
python -B .praxis/harness/main.py onboard
```

Primary native primitives are clients, matters, unbound matters, matter focus, chronology, obligations, todos, memories, global session work logs, and Typst drafting assets under `src/` plus reusable static assets under `assets/`. Deadlines are obligations, not a separate top-level primitive.

New practice installs use `ZZ_CLIENTS/` for client and matter state and `UNBOUND/open/` for legal work that is not yet tied to a known client. They also create `WIP/drafts/` and `WIP/experiments/` for non-matter drafting, template/style experiments, and workflow iteration. Matter-specific drafts belong in the matter folder, not in WIP.

Core legal context is installed under `.praxis/core_docs/`. Detailed and optional Typst references are installed under `.praxis/docs/` so routine onboard context can stay focused.
