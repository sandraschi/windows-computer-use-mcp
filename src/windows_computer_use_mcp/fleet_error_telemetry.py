"""Fleet error telemetry helper - fleet_error/v1 ring buffer.

Copy-paste module implementing patterns/FLEET_ERROR_TELEMETRY.md.
Stdlib only. Drop into a repo as `fleet_error_telemetry.py` (or vendor into
`src/<pkg>/telemetry.py`) and call from tool error boundaries.

Usage:
    from fleet_error_telemetry import (
        error_response, query_fleet_errors, record_fleet_error,
    )

    try:
        return do_work()
    except Exception as e:
        return error_response(
            server="my-mcp", tool="my_tool", operation=operation,
            error_type="general", error=str(e), params=params,
            recovery=["retry with timeout=30"],
        )
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import UTC, datetime

__all__ = [
    "SCHEMA",
    "error_response",
    "query_fleet_errors",
    "record_fleet_error",
]

SCHEMA = "fleet_error/v1"
RING_SIZE = 500
DEFAULT_DB = os.environ.get("FLEET_ERROR_DB") or "data/fleet_errors.sqlite3"

logger = logging.getLogger(__name__)
_lock = threading.Lock()

_DDL = """
CREATE TABLE IF NOT EXISTS fleet_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema TEXT NOT NULL,
    ts TEXT NOT NULL,
    server TEXT NOT NULL,
    tool TEXT NOT NULL,
    operation TEXT,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    params TEXT,
    failure_state TEXT,
    recovery TEXT
);
CREATE INDEX IF NOT EXISTS idx_fleet_errors_ts ON fleet_errors(ts);
CREATE INDEX IF NOT EXISTS idx_fleet_errors_tool ON fleet_errors(tool, error_type);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_DDL)
    return conn


def record_fleet_error(
    *,
    server: str,
    tool: str,
    error_type: str,
    message: str,
    operation: str | None = None,
    params: dict | None = None,
    failure_state: dict | None = None,
    recovery: list | None = None,
    db_path: str | None = None,
) -> None:
    """Persist one fleet_error/v1 record into the local ring buffer.

    Thread-safe. Ring-bounded: records beyond RING_SIZE are evicted per insert.
    Never raises - telemetry must not break the caller's error path.
    """
    record = {
        "schema": SCHEMA,
        "ts": datetime.now(UTC).isoformat(),
        "server": server,
        "tool": tool,
        "operation": operation,
        "error_type": error_type,
        "message": message,
        "params": params,
        "failure_state": failure_state,
        "recovery": recovery,
    }
    target = db_path or DEFAULT_DB
    try:
        with _lock, _connect(target) as conn:
            conn.execute(
                "INSERT INTO fleet_errors (schema, ts, server, tool, operation, "
                "error_type, message, params, failure_state, recovery) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["schema"],
                    record["ts"],
                    record["server"],
                    record["tool"],
                    record["operation"],
                    record["error_type"],
                    record["message"],
                    json.dumps(record["params"]) if record["params"] is not None else None,
                    json.dumps(record["failure_state"]) if record["failure_state"] is not None else None,
                    json.dumps(record["recovery"]) if record["recovery"] is not None else None,
                ),
            )
            conn.execute(
                "DELETE FROM fleet_errors WHERE id NOT IN (SELECT id FROM fleet_errors ORDER BY id DESC LIMIT ?)",
                (RING_SIZE,),
            )
    except Exception:
        logger.warning("fleet error telemetry write failed", exc_info=True)


def query_fleet_errors(
    tool: str | None = None,
    error_type: str | None = None,
    server: str | None = None,
    last_n: int = 10,
    db_path: str | None = None,
) -> list[dict]:
    """Read recent fleet_error/v1 records, newest first.

    Returns a list of dicts; empty list when the buffer has no matching rows.
    """
    target = db_path or DEFAULT_DB
    clauses, values = [], []
    if tool:
        clauses.append("tool = ?")
        values.append(tool)
    if error_type:
        clauses.append("error_type = ?")
        values.append(error_type)
    if server:
        clauses.append("server = ?")
        values.append(server)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    values.append(int(last_n))
    try:
        with _lock, _connect(target) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM fleet_errors" + where + " ORDER BY id DESC LIMIT ?",  # noqa: S608 - whitelisted columns, bound params
                values,
            ).fetchall()
    except Exception:
        logger.warning("fleet error telemetry read failed", exc_info=True)
        return []
    out = []
    for row in rows:
        record = {
            "schema": row["schema"],
            "ts": row["ts"],
            "server": row["server"],
            "tool": row["tool"],
            "operation": row["operation"],
            "error_type": row["error_type"],
            "message": row["message"],
            "params": json.loads(row["params"]) if row["params"] else None,
            "failure_state": json.loads(row["failure_state"]) if row["failure_state"] else None,
            "recovery": json.loads(row["recovery"]) if row["recovery"] else None,
        }
        out.append(record)
    return out


def error_response(
    *,
    server: str,
    tool: str,
    error_type: str,
    error: str,
    operation: str | None = None,
    params: dict | None = None,
    failure_state: dict | None = None,
    recovery: list | None = None,
    **extra,
) -> dict:
    """Standardized failure dict that logs AND records fleet_error/v1 in one call.

    Mirrors the TOOL_DESIGN_STANDARDS.md _error_response pattern: logging.exception
    happens inside the except block (caller keeps that), while this helper adds the
    structured telemetry record. `extra` keys are merged into the returned dict.
    """
    record_fleet_error(
        server=server,
        tool=tool,
        operation=operation,
        error_type=error_type,
        message=error,
        params=params,
        failure_state=failure_state,
        recovery=recovery,
    )
    response = {"success": False, "error": error, "error_type": error_type}
    if recovery:
        response["recovery_options"] = recovery
    response.update(extra)
    return response
