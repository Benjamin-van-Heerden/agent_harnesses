from src.config.main import load_project_config
from src.config.models import BranchNames
from src.config.paths import PROJECT_PATHS


def get_branch_names() -> BranchNames:
    result = load_project_config(PROJECT_PATHS.config_file)
    if result.config is None:
        raise ValueError(f"Missing or invalid {PROJECT_PATHS.config_file_display}")
    return BranchNames(
        dev=result.config.branches.dev,
        test=result.config.branches.test,
        main=result.config.branches.main,
        noswitch_branches=result.config.branches.noswitch_branches,
    )
