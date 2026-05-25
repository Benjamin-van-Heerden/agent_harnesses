import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.paths import PROJECT_PATHS, ProjectPaths, matter_workflow_progress_file
from src.state.matters import parse_matter_status, resolve_matter, touch_matter
from src.state.validation import validate_slug
from src.utils.markdown import MarkdownDocument, read_markdown, write_markdown


VALID_STEP_KINDS = ("task", "todo", "obligation", "draft", "review", "decision")
SLUG_TEXT_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    title: str
    kind: str
    requires: list[str]
    blocks: list[str]
    todo: str | None
    obligation: str | None


@dataclass(frozen=True)
class Workflow:
    slug: str
    name: str
    steps: list[WorkflowStep]
    path: Path


@dataclass(frozen=True)
class WorkflowProgress:
    completed_steps: list[str]
    blocked_steps: list[str]
    current_steps: list[str]


@dataclass(frozen=True)
class WorkflowFocus:
    workflow: Workflow | None
    progress: WorkflowProgress
    available_steps: list[WorkflowStep]
    blocked_steps: list[WorkflowStep]
    missing_prerequisites: dict[str, list[str]]
    next_action: str
    error: str | None = None


def slugify_workflow_name(name: str) -> str:
    slug = SLUG_TEXT_RE.sub("_", name.lower()).strip("_")
    if not slug:
        raise ValueError(f"cannot generate workflow slug from '{name}'")
    validate_slug(slug)
    return slug


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item)]


def workflow_template(name: str, slug: str) -> str:
    return "\n".join(
        [
            f"name = {_toml_string(name)}",
            f"slug = {_toml_string(slug)}",
            "",
            "# Edit this generated workflow before using it on a matter.",
            "# Step kinds: task, todo, obligation, draft, review, decision.",
            "",
            "[[steps]]",
            'id = "intake"',
            'title = "Confirm instructions and source material"',
            'kind = "task"',
            "requires = []",
            'blocks = ["draft"]',
            'todo = "Confirm instructions, parties, dates, and available source material."',
            "",
            "[[steps]]",
            'id = "draft"',
            'title = "Prepare first draft"',
            'kind = "draft"',
            'requires = ["intake"]',
            "blocks = []",
            'todo = "Prepare the first working draft or note why drafting is blocked."',
            "",
        ]
    )


def workflow_path(slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_slug(slug)
    return paths.workflows_root / f"{slug}.toml"


def create_workflow(name: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    slug = slugify_workflow_name(name)
    path = workflow_path(slug, paths)
    if path.exists():
        raise FileExistsError(f"workflow already exists: {slug}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(workflow_template(name, slug))
    return path


def _step_from_data(data: dict[str, Any], index: int) -> WorkflowStep:
    step_id = str(data.get("id", ""))
    title = str(data.get("title", ""))
    kind = str(data.get("kind", ""))
    if not step_id:
        raise ValueError(f"workflow step {index} is missing id")
    validate_slug(step_id)
    if not title:
        raise ValueError(f"workflow step {step_id} is missing title")
    if kind not in VALID_STEP_KINDS:
        raise ValueError(f"workflow step {step_id} has invalid kind '{kind}'")
    return WorkflowStep(
        id=step_id,
        title=title,
        kind=kind,
        requires=_string_list(data.get("requires")),
        blocks=_string_list(data.get("blocks")),
        todo=str(data["todo"]) if data.get("todo") else None,
        obligation=str(data["obligation"]) if data.get("obligation") else None,
    )


def parse_workflow(path: Path) -> Workflow:
    if not path.is_file():
        raise FileNotFoundError(f"workflow not found: {path.stem}")
    data = tomllib.loads(path.read_text())
    name = str(data.get("name", ""))
    slug = str(data.get("slug", path.stem))
    if not name:
        raise ValueError(f"workflow {path.stem} is missing name")
    validate_slug(slug)
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError(f"workflow {slug} must define at least one [[steps]] entry")
    steps: list[WorkflowStep] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            raise ValueError(f"workflow step {index} must be a TOML table")
        step_data: dict[str, Any] = {str(key): value for key, value in raw_step.items()}
        steps.append(_step_from_data(step_data, index))
    step_ids = {step.id for step in steps}
    for step in steps:
        missing_requires = [required for required in step.requires if required not in step_ids]
        missing_blocks = [blocked for blocked in step.blocks if blocked not in step_ids]
        if missing_requires:
            raise ValueError(f"workflow step {step.id} requires unknown step(s): {', '.join(missing_requires)}")
        if missing_blocks:
            raise ValueError(f"workflow step {step.id} blocks unknown step(s): {', '.join(missing_blocks)}")
    return Workflow(slug=slug, name=name, steps=steps, path=path)


def list_workflows(paths: ProjectPaths = PROJECT_PATHS) -> list[Workflow]:
    if not paths.workflows_root.is_dir():
        return []
    return [parse_workflow(path) for path in sorted(paths.workflows_root.glob("*.toml"))]


def resolve_workflow(slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Workflow:
    return parse_workflow(workflow_path(slug, paths))


def read_workflow_progress(matter_dir: Path) -> WorkflowProgress:
    path = matter_workflow_progress_file(matter_dir)
    if not path.is_file():
        return WorkflowProgress(completed_steps=[], blocked_steps=[], current_steps=[])
    data = tomllib.loads(path.read_text())
    return WorkflowProgress(
        completed_steps=_string_list(data.get("completed_steps")),
        blocked_steps=_string_list(data.get("blocked_steps")),
        current_steps=_string_list(data.get("current_steps")),
    )


def workflow_focus(matter_dir: Path, paths: ProjectPaths = PROJECT_PATHS) -> WorkflowFocus | None:
    status = parse_matter_status(matter_dir / "info" / "status.md")
    if status.workflow is None:
        return None
    progress = read_workflow_progress(matter_dir)
    try:
        workflow = resolve_workflow(status.workflow, paths)
    except (FileNotFoundError, ValueError) as error:
        return WorkflowFocus(
            workflow=None,
            progress=progress,
            available_steps=[],
            blocked_steps=[],
            missing_prerequisites={},
            next_action="Resolve the workflow configuration before relying on workflow guidance.",
            error=str(error),
        )
    completed = set(progress.completed_steps)
    blocked_ids = set(progress.blocked_steps)
    missing: dict[str, list[str]] = {}
    available: list[WorkflowStep] = []
    blocked: list[WorkflowStep] = []
    for step in workflow.steps:
        if step.id in completed:
            continue
        missing_requires = [required for required in step.requires if required not in completed]
        if missing_requires:
            missing[step.id] = missing_requires
        if step.id in blocked_ids or missing_requires:
            blocked.append(step)
        else:
            available.append(step)
    current_ids = set(progress.current_steps)
    if current_ids:
        available = [step for step in available if step.id in current_ids] or available
    next_action = available[0].title if available else "Ask the lawyer how to unblock the workflow."
    return WorkflowFocus(
        workflow=workflow,
        progress=progress,
        available_steps=available,
        blocked_steps=blocked,
        missing_prerequisites=missing,
        next_action=next_action,
    )


def link_matter_workflow(matter_ref: str, workflow_slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    workflow = resolve_workflow(workflow_slug, paths)
    matter_dir = resolve_matter(matter_ref, paths)
    status_file = matter_dir / "info" / "status.md"
    status_doc = read_markdown(status_file)
    status_metadata = dict(status_doc.frontmatter)
    status_metadata["workflow"] = workflow.slug
    write_markdown(status_file, MarkdownDocument(frontmatter=status_metadata, body=status_doc.body))
    progress_file = matter_workflow_progress_file(matter_dir)
    if not progress_file.exists():
        progress_file.write_text("completed_steps = []\nblocked_steps = []\ncurrent_steps = []\n")
    touch_matter(matter_dir)
    return progress_file
