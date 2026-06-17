import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
ACCESSIBLE_PATH_KEY = "AccessablePath"

DEFAULT_MAX_RETURN_BYTES = 512 * 1024
DEFAULT_MAX_LINES = 1000


def get_read_limits() -> tuple[int, int]:
    max_bytes = int(os.getenv("FILE_READ_MAX_RETURN_BYTES", str(DEFAULT_MAX_RETURN_BYTES)))
    max_lines = int(os.getenv("FILE_READ_MAX_LINES", str(DEFAULT_MAX_LINES)))
    return max_bytes, max_lines

def load_accessible_paths() -> list[Path]:
    """Parse .env for all AccessablePath= lines (dotenv only keeps the last duplicate key)."""
    if not ENV_PATH.exists():
        return []

    paths: list[Path] = []
    pattern = re.compile(rf"^{re.escape(ACCESSIBLE_PATH_KEY)}\s*=\s*(.+?)\s*$", re.IGNORECASE)

    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = pattern.match(stripped)
            if not match:
                continue
            raw = match.group(1).strip().strip('"').strip("'")
            if raw:
                paths.append(Path(raw).expanduser().resolve())

    return paths
