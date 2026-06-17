import shutil


def resolve_command(name: str) -> str:
    """Resolve an executable on PATH (required on Windows for .cmd/.bat shims like npm.cmd)."""
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"'{name}' not found on PATH. Install Node.js and ensure it is available in PATH."
        )
    return path
