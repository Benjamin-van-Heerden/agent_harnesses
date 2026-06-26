from dataclasses import dataclass
from types import ModuleType

import pytest
import typer

from helpers import HARNESS_ROOT


@dataclass(frozen=True)
class _SpecRecord:
    branch: str
    status: str


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _patch_context(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    branch: str,
    is_worktree: bool = False,
    specs: list[_SpecRecord] | None = None,
) -> None:
    config_models = _load_module(monkeypatch, "src.config.models")
    monkeypatch.setattr(
        module,
        "get_branch_names",
        lambda: config_models.BranchNames(dev="dev", test="test", main="main"),
    )
    monkeypatch.setattr(module.worktrees, "is_worktree", lambda: is_worktree)
    monkeypatch.setattr(module.git, "current_branch", lambda: branch)
    monkeypatch.setattr(module.specs, "list_all", lambda: specs or [])


def test_todo_context_allows_dev_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    _patch_context(monkeypatch, context, "dev")

    branch = context.require_todo_management_branch("claim todos")

    assert branch == "dev"


def test_todo_context_allows_active_spec_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    _patch_context(
        monkeypatch,
        context,
        "dev-octo-example",
        is_worktree=True,
        specs=[_SpecRecord(branch="dev-octo-example", status="todo")],
    )

    branch = context.require_todo_management_branch("claim todos")

    assert branch == "dev-octo-example"


def test_todo_context_blocks_test_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    _patch_context(monkeypatch, context, "test")

    with pytest.raises(typer.Exit) as error:
        context.require_todo_management_branch("claim todos")

    assert error.value.exit_code == 1


def test_todo_context_blocks_untracked_worktree_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    _patch_context(monkeypatch, context, "feature/example", is_worktree=True)

    with pytest.raises(typer.Exit) as error:
        context.require_todo_management_branch("claim todos")

    assert error.value.exit_code == 1


def test_todo_new_stops_before_github_outside_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    new = _load_module(monkeypatch, "src.commands.todo.new")
    _patch_context(monkeypatch, context, "main")
    monkeypatch.setattr(
        new,
        "repository",
        lambda: pytest.fail("todo new should stop before GitHub access"),
    )

    with pytest.raises(typer.Exit) as error:
        new.run("Example todo", "body")

    assert error.value.exit_code == 1


def test_todo_claim_stops_before_resolve_outside_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    claim = _load_module(monkeypatch, "src.commands.todo.claim")
    _patch_context(monkeypatch, context, "main")
    monkeypatch.setattr(
        claim,
        "resolve_or_exit",
        lambda _identifier: pytest.fail("todo claim should stop before resolving todos"),
    )

    with pytest.raises(typer.Exit) as error:
        claim.run("example", "octo")

    assert error.value.exit_code == 1


def test_todo_delete_stops_before_resolve_outside_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    delete = _load_module(monkeypatch, "src.commands.todo.delete")
    _patch_context(monkeypatch, context, "main")
    monkeypatch.setattr(
        delete,
        "resolve_or_exit",
        lambda _identifier: pytest.fail("todo delete should stop before resolving todos"),
    )

    with pytest.raises(typer.Exit) as error:
        delete.run("example")

    assert error.value.exit_code == 1
