from datetime import datetime, timedelta
from pathlib import Path

from src.config.paths import PROJECT_PATHS


def write_output(content: str) -> Path:
    temp_dir = PROJECT_PATHS.state_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(hours=1)
    for path in temp_dir.glob("onboard_*.md"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                path.unlink()
        except OSError:
            pass

    output_path = temp_dir / f"onboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path.write_text(content)
    return output_path
