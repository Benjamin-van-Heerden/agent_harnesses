import importlib.util
import subprocess
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonPackage:
    import_name: str
    package_name: str


@dataclass(frozen=True)
class ExternalCommand:
    name: str
    purpose: str
    install_guidance: tuple[str, ...]


REQUIRED_PACKAGES = [
    PythonPackage(import_name="pydantic", package_name="pydantic"),
    PythonPackage(import_name="typer", package_name="typer"),
    PythonPackage(import_name="yaml", package_name="PyYAML"),
]

REQUIRED_COMMANDS = [
    ExternalCommand(
        name="git",
        purpose="local practice-state checkpoints",
        install_guidance=(
            "Windows: winget install --id Git.Git",
            "macOS: xcode-select --install, or brew install git",
            "Linux: use your distribution package manager, for example sudo apt install git",
        ),
    ),
    ExternalCommand(
        name="typst",
        purpose="legal document compilation",
        install_guidance=(
            "Windows: winget install --id Typst.Typst",
            "macOS: brew install typst",
            "Linux: use your distribution package manager, or download Typst from https://github.com/typst/typst/releases",
        ),
    ),
]


def missing_python_packages() -> list[PythonPackage]:
    return [
        package
        for package in REQUIRED_PACKAGES
        if importlib.util.find_spec(package.import_name) is None
    ]


def command_version_available(command: str) -> bool:
    if shutil.which(command) is None:
        return False
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def missing_external_commands() -> list[ExternalCommand]:
    return [
        command
        for command in REQUIRED_COMMANDS
        if not command_version_available(command.name)
    ]


def require_dependencies() -> None:
    missing_packages = missing_python_packages()
    missing_commands = missing_external_commands()

    if not missing_packages and not missing_commands:
        return

    print("Missing required dependencies.", file=sys.stderr)

    if missing_packages:
        packages = " ".join(package.package_name for package in missing_packages)
        print("", file=sys.stderr)
        print("Install Python packages with:", file=sys.stderr)
        print(f"  python -m pip install {packages}", file=sys.stderr)

    if missing_commands:
        print("", file=sys.stderr)
        print("Install external commands:", file=sys.stderr)
        for command in missing_commands:
            print(f"  - {command.name}: required for {command.purpose}", file=sys.stderr)
            for guidance in command.install_guidance:
                print(f"    {guidance}", file=sys.stderr)

    raise SystemExit(1)
