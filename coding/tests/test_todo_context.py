from types import ModuleType

import pytest
import typer

from helpers import HARNESS_ROOT


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _patch_non_dev_context(monkeypatch: pytest.MonkeyPatch, module: ModuleType) -> None:
    config_models = _load_module(monkeypatch, "src.config.models")
    monkeypatch.setattr(
        module,
        "get_branch_names",
        lambda: config_models.BranchNames(dev="dev", test="test", main="main"),
    )
    monkeypatch.setattr(module.worktrees, "is_worktree", lambda: False)
    monkeypatch.setattr(module.git, "current_branch", lambda: "main")


def test_todo_context_requires_dev_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    _patch_non_dev_context(monkeypatch, context)

    with pytest.raises(typer.Exit) as error:
        context.require_dev_main_repo("claim todos")

    assert error.value.exit_code == 1


def test_todo_new_stops_before_github_outside_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _load_module(monkeypatch, "src.commands.todo.utils.context")
    new = _load_module(monkeypatch, "src.commands.todo.new")
    _patch_non_dev_context(monkeypatch, context)
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
    _patch_non_dev_context(monkeypatch, context)
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
    _patch_non_dev_context(monkeypatch, context)
    monkeypatch.setattr(
        delete,
        "resolve_or_exit",
        lambda _identifier: pytest.fail("todo delete should stop before resolving todos"),
    )

    with pytest.raises(typer.Exit) as error:
        delete.run("example")

    assert error.value.exit_code == 1
