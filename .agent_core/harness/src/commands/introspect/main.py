import os
from pathlib import Path
from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS


app = typer.Typer(help="Scaffold durable project reference documents", no_args_is_help=True)

MAX_TREE_LINES = 300
EXCLUDED_DIR_NAMES = {
    ".agent_core",
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "deps",
    "dist",
    "node_modules",
    "target",
    "venv",
}
EXCLUDED_FILE_SUFFIXES = {
    ".7z",
    ".avif",
    ".bin",
    ".bmp",
    ".cache",
    ".class",
    ".dll",
    ".dmg",
    ".eot",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".lock",
    ".mp3",
    ".mp4",
    ".o",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".svg",
    ".tar",
    ".ttf",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}
EXCLUDED_FILE_NAMES = {".DS_Store"}

STRUCTURE_DOC_SLUG = "codebase_and_structure"
WHAT_DOC_SLUG = "what"

STRUCTURE_TEMPLATE = """# Codebase and Structure

## Overview
{One concise factual summary of the repository as found. Describe the main artifact or application type only when confirmed by repo files. Do not infer goals or intent.}

## Tech Stack
{Bullet list: languages, frameworks, key libraries, databases, and infrastructure that matter for day-to-day development.}

## Directory Layout
{Annotated tree of top-level and important nested directories. Describe what lives in each important directory and which directories are source, tests, generated output, configuration, or durable project state. Do not list every file.}

## Key Modules
{For each significant module or component, describe what it does, key files, and what it depends on or what depends on it.}

## Data Flow
{Describe the primary data paths through the system. Cover the main flows, not every edge case.}

## Entry Points
{Describe how the application, service, package, or tool is started. Include development and production entry points when they differ.}

## Commands and Workflows
{Document repo-defined commands, scripts, CLIs, task runners, setup/update flows, and developer workflows that are visible in repo files.}

## External Interfaces
{Describe APIs exposed, external services consumed, databases, message queues, filesystem dependencies, or other codebase boundaries. Omit this section if none apply.}

## Tests and Verification
{Describe the test layout, meaningful test categories, and the focused commands used to verify changes. Include only commands confirmed from repo files or existing harness docs.}

## Conventions and Patterns
{Describe patterns that would help an agent or developer make fitting changes in this codebase. Only include patterns confirmed from the code.}
"""

WHAT_TEMPLATE = """# What Is This Project?

## Purpose
{What problem this project solves, why it exists, and what would be harder or impossible without it.}

## Goals
{The concrete short-term and long-term goals the project is trying to achieve.}

## Target Users / Consumers
{Who uses or consumes this project, including people, teams, AI agents, automated systems, or other software.}

## Core Value Proposition
{The single most important thing this project provides.}

## Current State
{Where the project is now: what works, what is still emerging, and what remains to be built.}

## Non-Goals
{What this project deliberately avoids or excludes by design.}
"""

STRUCTURE_AGENT_INSTRUCTIONS = """======================================================================
INTROSPECT STRUCTURE: You must complete the generated document
======================================================================

The file has been created at: .agent_core/docs/codebase_and_structure.md

It contains placeholders. You must research the codebase and replace every placeholder with accurate, specific content. This document is a factual repository map, not a product vision or goals document.

Phase 1: Gather raw information

1. Use the file tree above to orient yourself.
2. Read the root configuration and manifest files that exist, such as package.json, pyproject.toml, Cargo.toml, go.mod, Makefile, docker-compose.yml, README files, task runner files, or env examples.
3. Identify and read the primary entry points.

Phase 2: Explore the architecture

Work through the codebase methodically. Prioritize entry points, routers or controllers, core business logic, data models and schemas, storage access, configuration, and shared utilities that appear frequently in imports.

Do not read every file. Follow imports, function calls, and data flow strategically. Focus on architecture and project-specific conventions, not implementation trivia.

Stay factual. Describe what is in the repository, where it lives, and how the pieces connect. Do not infer goals, strategy, target users, or future direction unless those are explicitly present in durable repository docs.

Phase 3: Write the reference document

Replace every placeholder in .agent_core/docs/codebase_and_structure.md.

Rules:
- Be specific. Use actual file paths, module names, command names, and function names.
- Be concise. This is a reference document, not a tutorial.
- Be accurate. Only write facts confirmed by reading the code or durable project docs.
- Do not document Agent Core itself unless this repository's product is an Agent Core harness.
- Do not include project goals, motivation, target users, or non-goals. Those belong in .agent_core/docs/what.md.
- Omit sections that do not apply.
- Keep the document well under 5000 words.

When done, show the user what you wrote and ask whether it is accurate before doing any commit or follow-up workflow.
"""

WHAT_AGENT_INSTRUCTIONS = """======================================================================
INTROSPECT WHAT: You must interview the user before completing the document
======================================================================

The file has been created at: .agent_core/docs/what.md

It contains placeholders. You must understand the project's purpose and goals, then replace every placeholder with accurate, specific content.

Phase 1: Interview the user

Ask the user these questions conversationally and do not proceed until they have answered:

1. What does this project do, in your own words?
2. Why does it exist? What problem motivated it?
3. Who is it for? Include people, other systems, AI agents, or automated consumers.
4. What are the goals now and later?
5. What is explicitly not a goal?
6. Where is the project now? What works, what is missing, and what is still uncertain?

Ask follow-up questions when an answer is ambiguous. The goal is to capture the user's intent, not impose a generic product frame.

Phase 2: Ground the answer in the codebase

Use the file tree above to orient yourself. Read README files, manifest/configuration files, entry points, and core business logic to confirm the user's description and fill in gaps.

This is not the structure document. Do not drift into technical architecture except where it clarifies purpose, users, current state, or boundaries.

Phase 3: Write the reference document

Replace every placeholder in .agent_core/docs/what.md.

Rules:
- Write from the project owner's perspective.
- Be specific to this project.
- Be honest about current state.
- Do not oversell incomplete behavior.
- Do not include architecture detail that belongs in codebase_and_structure.md.
- Keep the document well under 2000 words.

When done, show the user what you wrote and ask whether it accurately captures their vision before doing any commit or follow-up workflow.
"""


def _is_excluded_file(path: Path) -> bool:
    return path.name in EXCLUDED_FILE_NAMES or path.suffix.lower() in EXCLUDED_FILE_SUFFIXES


def _relative_file_tree(project_root: Path) -> str:
    files: list[str] = []
    for root, dir_names, file_names in os.walk(project_root):
        current = Path(root)
        dir_names[:] = sorted(name for name in dir_names if name not in EXCLUDED_DIR_NAMES)
        for file_name in sorted(file_names):
            path = current / file_name
            if _is_excluded_file(path):
                continue
            relative_path = path.relative_to(project_root).as_posix()
            files.append(f"./{relative_path}")

    files.sort()
    total = len(files)
    if total > MAX_TREE_LINES:
        files = files[:MAX_TREE_LINES]
        files.append(f"... ({total} total files, truncated to {MAX_TREE_LINES})")
    return "\n".join(files)


def _doc_path(doc_slug: str) -> Path:
    return PROJECT_PATHS.docs_dir / f"{doc_slug}.md"


def _write_template(doc_path: Path, template: str, force: bool) -> None:
    if doc_path.exists() and not force:
        typer.confirm(f"{doc_path.relative_to(PROJECT_PATHS.project_root)} already exists. Overwrite?", abort=True)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(template.lstrip())


def _scaffold_and_instruct(doc_slug: str, template: str, agent_instructions: str, force: bool) -> None:
    doc_path = _doc_path(doc_slug)
    _write_template(doc_path, template, force)
    relative_doc_path = doc_path.relative_to(PROJECT_PATHS.project_root).as_posix()
    file_tree = _relative_file_tree(PROJECT_PATHS.project_root)

    typer.echo(f"Created introspection document: {relative_doc_path}")
    typer.echo("")
    if file_tree:
        typer.echo("FILE TREE")
        typer.echo("=" * 70)
        typer.echo(file_tree)
        typer.echo("=" * 70)
        typer.echo("")
    typer.echo(agent_instructions)


@app.command()
def structure(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite an existing structure document without prompting."),
    ] = False,
) -> None:
    """Scaffold a codebase structure reference document."""
    _scaffold_and_instruct(STRUCTURE_DOC_SLUG, STRUCTURE_TEMPLATE, STRUCTURE_AGENT_INSTRUCTIONS, force)


@app.command()
def what(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite an existing purpose document without prompting."),
    ] = False,
) -> None:
    """Scaffold a project purpose and goals reference document."""
    _scaffold_and_instruct(WHAT_DOC_SLUG, WHAT_TEMPLATE, WHAT_AGENT_INSTRUCTIONS, force)
