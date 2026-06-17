from tool.fileoperator.safety import validate_path


def create_file(
    path: str,
    is_directory: bool = False,
    content: str | None = None,
) -> dict:
    resolved = validate_path(path, "create")
    if resolved.exists():
        raise FileExistsError(f"Path already exists: {resolved}")

    if is_directory:
        resolved.mkdir(parents=True, exist_ok=False)
        kind = "directory"
    else:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content or "", encoding="utf-8")
        kind = "file"

    return {
        "path": str(resolved),
        "kind": kind,
    }
