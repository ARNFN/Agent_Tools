from tool.database.connection import cursor
from tool.database.safety import validate_sql


def _rows_to_dicts(rows, db_type: str) -> list[dict]:
    if not rows:
        return []
    if db_type == "sqlite":
        return [dict(row) for row in rows]
    if isinstance(rows[0], dict):
        return list(rows)
    return [dict(row) for row in rows]


def execute_sql(sql: str, confirm: bool = False) -> dict:
    validate_sql(sql, confirm=confirm)

    statements = [s.strip() for s in sql.split(";") if s.strip()]
    results = []

    with cursor() as (cur, db_type):
        for stmt in statements:
            cur.execute(stmt)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                data = _rows_to_dicts(rows, db_type)
                results.append(
                    {
                        "db_type": db_type,
                        "columns": columns,
                        "rows": data,
                        "row_count": len(data),
                    }
                )
            else:
                results.append(
                    {"db_type": db_type, "affected_rows": cur.rowcount}
                )

    if len(results) == 1:
        return results[0]
    return {"db_type": db_type, "statements": results}
