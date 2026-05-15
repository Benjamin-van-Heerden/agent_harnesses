---
title: Build project-local path and config foundation
status: completed
created_at: '2026-05-12T16:25:29.962429'
updated_at: '2026-05-13T09:12:53.748897'
completed_at: '2026-05-13T09:12:53.748890'
---
Replace env_settings.py with a neutral project-local path/config layer. State root must be .agent_core, harness root must be .agent_core/harness, config must be .agent_core/config.toml, and user mappings must be .agent_core/user_mappings.toml. Remove import-time GITHUB_TOKEN assertion and validate GitHub credentials only inside commands that need GitHub. Remove global ~/.config/mem access from the foundation. Use typed models for path/config data and neutral names such as ProjectConfig, AgentCoreConfig, project_root, state_root, and harness_root instead of mem_dir/caller_dir/mem_working_dir. Verify existing path consumers are migrated to the new API.

## Completion Notes

Created the repository-side harness template under harnesses/mem/ with install payload at harnesses/mem/.agent_core/harness/. Added a neutral project-local path/config foundation inside the harness, including ProjectPaths for project_root, state_root, harness_root, config, user mappings, specs, todos, memories, logs, and docs. Added typed config models and TOML load/validation/default generation. Added frontmatter and markdown helpers plus state-backed command consumers for specs, tasks, todos, memories, and logs so the new PROJECT_PATHS API is exercised by actual harness commands. Verified the harness through focused Ruff checks, vanilla local entrypoint smoke tests, temp install smoke tests, no .mem state creation, no .agent_core/tmp setup creation, and no standalone product-word usage in migrated harness code or setup script.