from tool.fileoperator.safety import is_config_file, require_user_confirmed, validate_path


def write_file(
    path: str,
    content: str | None = None,
    old_string: str | None = None,
    new_string: str | None = None,
    user_confirmed: bool = False,
) -> dict:
    resolved = validate_path(path, "write")
    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved}")

    has_content = content is not None
    has_patch = old_string is not None or new_string is not None
    if has_content and has_patch:
        raise ValueError("Provide either content or old_string/new_string, not both.")
    if not has_content and not has_patch:
        raise ValueError("Provide content for overwrite or old_string/new_string for patch.")

    if is_config_file(resolved):
        require_user_confirmed(
            user_confirmed,
            "Writing config file requires user approval.",
        )

    if has_content:
        resolved.write_text(content, encoding="utf-8")
        mode = "overwrite"
    else:
        if old_string is None or new_string is None:
            raise ValueError("Both old_string and new_string are required for patch mode.")
        text = resolved.read_text(encoding="utf-8")
        count = text.count(old_string)
        if count == 0:
            raise ValueError("old_string not found in file.")
        if count > 1:
            raise ValueError(f"old_string appears {count} times; must be unique.")
        resolved.write_text(text.replace(old_string, new_string, 1), encoding="utf-8")
        mode = "patch"

    return {
        "path": str(resolved),
        "mode": mode,
    }
