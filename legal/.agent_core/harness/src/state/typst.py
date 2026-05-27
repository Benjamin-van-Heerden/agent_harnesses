import subprocess
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths


def resolve_typst_source(source: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    candidate = (paths.project_root / source).resolve()
    if not candidate.is_file():
        raise FileNotFoundError(f"Typst source not found: {source}")
    if candidate.suffix != ".typ":
        raise ValueError(f"Typst source must end with .typ: {source}")
    try:
        candidate.relative_to(paths.project_root)
    except ValueError as error:
        raise ValueError("Typst source must be inside the practice workspace") from error
    return candidate


def generated_pdf_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}.p.pdf")


def compile_typst(source: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    source_path = resolve_typst_source(source, paths)
    output_path = generated_pdf_path(source_path)
    result = subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(paths.project_root),
            str(source_path),
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "typst compile failed"
        raise RuntimeError(message)
    return output_path
