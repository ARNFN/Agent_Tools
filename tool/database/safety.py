import re

DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bDROP\s+(DATABASE|TABLE|SCHEMA|INDEX)\b", re.I),
    re.compile(r"\bTRUNCATE\s+TABLE\b", re.I),
    re.compile(r"\bDELETE\s+FROM\b", re.I),
    re.compile(r"\bALTER\s+TABLE\b.*\bDROP\b", re.I),
    re.compile(r"\bALTER\s+TABLE\b.*\b(MODIFY|CHANGE)\b", re.I),
    re.compile(r"\bUPDATE\b", re.I),
]


def is_destructive(sql: str) -> bool:
    stripped = sql.strip().rstrip(";")
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(stripped):
            return True
    return False


def validate_sql(sql: str, confirm: bool = False) -> None:
    if is_destructive(sql) and not confirm:
        raise PermissionError(
            "Destructive SQL detected. Set confirm=true after user approval."
        )
