from tool.fileoperator.config import get_read_limits
from tool.fileoperator.safety import validate_path


def read_file(path: str, offset: int | None = None, limit: int | None = None) -> dict:
    resolved = validate_path(path, "read")
    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved}")

    max_return_bytes, max_lines = get_read_limits()
    start = max((offset or 1) - 1, 0)
    effective_limit = limit if limit is not None else max_lines

    selected: list[str] = []
    return_bytes = 0
    line_no = 0

    try:
        with open(resolved, encoding="utf-8") as f:
            for line in f:
                line_no += 1
                if line_no <= start:
                    continue
                if len(selected) < effective_limit:
                    line_bytes = len(line.encode("utf-8"))
                    if return_bytes + line_bytes > max_return_bytes:
                        raise ValueError(
                            f"Return content exceeds {max_return_bytes} bytes. "
                            f"Reduce limit (currently {effective_limit} lines requested)."
                        )
                    selected.append(line)
                    return_bytes += line_bytes
    except UnicodeDecodeError as exc:
        raise ValueError(f"File is not valid UTF-8 text: {resolved}") from exc

    total_lines = line_no
    content = "".join(selected)

    return {
        "path": str(resolved),
        "content": content,
        "total_lines": total_lines,
        "offset": start + 1,
        "limit": len(selected),
    }
