import shutil

from tool.fileoperator.safety import is_config_file, require_user_confirmed, validate_path


def delete_file(path: str, user_confirmed: bool = False) -> dict:
    resolved = validate_path(path, "delete")
    require_user_confirmed(user_confirmed, "Deleting files or directories requires user approval.")

    if is_config_file(resolved):
        require_user_confirmed(
            user_confirmed,
            "Deleting config file requires user approval.",
        )

    if not resolved.exists():
        raise FileNotFoundError(f"Path not found: {resolved}")

    if resolved.is_dir():
        shutil.rmtree(resolved)
        kind = "directory"
    else:
        resolved.unlink()
        kind = "file"

    return {
        "path": str(resolved),
        "kind": kind,
        "deleted": True,
    }
