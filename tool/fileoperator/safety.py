from pathlib import Path

from tool.fileoperator.config import ROOT, load_accessible_paths

CONFIG_SUFFIXES = {".yaml", ".yml", ".toml", ".ini", ".conf", ".properties"}
CONFIG_FILENAMES = {
    ".env",
    "application.properties",
    "application.yml",
    "application.yaml",
    "pom.xml",
    "vite.config.js",
    "package.json",
    "package-lock.json",
}


def get_allowed_roots() -> list[Path]:
    roots = [ROOT.resolve()]
    for path in load_accessible_paths():
        if path not in roots:
            roots.append(path)
    return roots


def resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _matching_root(path: Path) -> Path | None:
    for root in get_allowed_roots():
        if _is_under(path, root):
            return root
    return None


def is_blocked_path(path: Path) -> bool:
    parts_lower = [p.lower() for p in path.parts]
    if ".venv" in parts_lower:
        return True
    if "qweather_key" in parts_lower and "private" in path.name.lower():
        return True
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = None
    if rel is not None:
        rel_str = rel.as_posix().lower()
        if rel_str == "data/vault.json" or rel_str.startswith("data/vault.json"):
            return True
    return False


def is_config_file(path: Path) -> bool:
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return True
    if name in CONFIG_FILENAMES:
        return True
    if path.suffix.lower() in CONFIG_SUFFIXES:
        return True
    try:
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] == "config":
            return True
    except ValueError:
        pass
    return False


def is_allowed_root_path(path: Path) -> bool:
    path = path.resolve()
    for root in get_allowed_roots():
        if path == root:
            return True
    return False


def validate_path(raw_path: str, operation: str) -> Path:
    path = resolve_path(raw_path)
    root = _matching_root(path)
    if root is None:
        raise PermissionError(
            f"Path '{path}' is outside allowed workspace. "
            f"Use a path under {ROOT} or add AccessablePath=... to .env."
        )
    if is_blocked_path(path):
        raise PermissionError(f"Path '{path}' is blocked for file operations.")
    if operation == "delete" and is_allowed_root_path(path):
        raise PermissionError(f"Cannot delete allowed root directory '{path}'.")
    return path


def require_user_confirmed(user_confirmed: bool, reason: str) -> None:
    if not user_confirmed:
        raise PermissionError(f"{reason} Requires user_confirmed=true after user approval.")
