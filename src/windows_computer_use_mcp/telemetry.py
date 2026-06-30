"""Telemetry SQLite store — logs every action for stats and adaptive learning."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from windows_computer_use_mcp.cua_env import cua_getenv

logger = logging.getLogger(__name__)

_local = threading.local()


def _get_db_path() -> Path:
    base = cua_getenv(
        "WINDOWS_COMPUTER_USE_MCP_TELEMETRY_DIR",
        default=None,
    )
    if base:
        path = Path(base)
    else:
        path = Path.home() / ".windows-computer-use-mcp"
    path.mkdir(parents=True, exist_ok=True)
    return path / "telemetry.db"


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(_get_db_path()))
        _local.conn.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                tool TEXT NOT NULL,
                operation TEXT NOT NULL,
                target TEXT,
                strategy_used TEXT,
                success INTEGER NOT NULL,
                duration_ms REAL,
                error TEXT,
                selector TEXT,
                app TEXT,
                session_id TEXT
            )
        """)
        _local.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_ts ON actions(ts)
        """)
        _local.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_tool ON actions(tool, operation)
        """)
        _local.conn.commit()
    return _local.conn


def log_action(
    tool: str,
    operation: str,
    *,
    target: str | None = None,
    strategy_used: str | None = None,
    success: bool = True,
    duration_ms: float | None = None,
    error: str | None = None,
    selector: dict | None = None,
    app: str | None = None,
    session_id: str | None = None,
) -> None:
    """Record a non-trivial action in the telemetry store."""
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO actions (ts, tool, operation, target, strategy_used, success, duration_ms, error, selector, app, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(),
                tool,
                operation,
                target,
                strategy_used,
                1 if success else 0,
                duration_ms,
                error,
                json.dumps(selector) if selector else None,
                app,
                session_id,
            ),
        )
        conn.commit()
    except Exception as e:
        logger.warning("telemetry log_action failed: %s", e)


def get_stats(days: int = 7) -> dict[str, Any]:
    """Return aggregate stats from the telemetry store."""
    try:
        conn = _get_conn()
        cutoff = time.time() - days * 86400

        total = conn.execute("SELECT COUNT(*) FROM actions WHERE ts > ?", (cutoff,)).fetchone()[0]

        by_tool = {}
        for row in conn.execute(
            "SELECT tool, operation, COUNT(*), SUM(success), AVG(duration_ms) FROM actions WHERE ts > ? GROUP BY tool, operation",
            (cutoff,),
        ).fetchall():
            key = f"{row[0]}/{row[1]}"
            by_tool[key] = {
                "total": row[2],
                "success": row[3],
                "fail": row[2] - row[3],
                "avg_duration_ms": round(row[4], 1) if row[4] else None,
            }

        top_fails = []
        for row in conn.execute(
            "SELECT tool, operation, error, COUNT(*) as cnt FROM actions WHERE ts > ? AND success = 0 AND error IS NOT NULL GROUP BY tool, operation, error ORDER BY cnt DESC LIMIT 10",
            (cutoff,),
        ).fetchall():
            top_fails.append(
                {
                    "tool": row[0],
                    "operation": row[1],
                    "error": row[2],
                    "count": row[3],
                }
            )

        by_strategy = {}
        for row in conn.execute(
            "SELECT strategy_used, COUNT(*), SUM(success) FROM actions WHERE ts > ? AND strategy_used IS NOT NULL GROUP BY strategy_used",
            (cutoff,),
        ).fetchall():
            by_strategy[row[0]] = {"total": row[1], "success": row[2], "fail": row[1] - row[2]}

        return {
            "total_actions": total,
            "days": days,
            "by_tool": by_tool,
            "top_fails": top_fails,
            "by_strategy": by_strategy,
        }
    except Exception as e:
        return {"error": str(e)}


def get_failure_patterns(tool: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Return recent failures, optionally filtered by tool."""
    try:
        conn = _get_conn()
        cutoff = time.time() - 30 * 86400
        query = "SELECT ts, tool, operation, target, error, strategy_used FROM actions WHERE ts > ? AND success = 0"
        params: list[Any] = [cutoff]
        if tool:
            query += " AND tool = ?"
            params.append(tool)
        query += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        return [
            {
                "ts": row[0],
                "tool": row[1],
                "operation": row[2],
                "target": row[3],
                "error": row[4],
                "strategy_used": row[5],
            }
            for row in conn.execute(query, params).fetchall()
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_best_strategy(tool: str, operation: str) -> str | None:
    """Return the strategy with the highest success rate for a given tool+operation."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            """SELECT strategy_used, SUM(success) as wins, COUNT(*) as total
               FROM actions WHERE tool = ? AND operation = ? AND strategy_used IS NOT NULL
               GROUP BY strategy_used ORDER BY (wins * 1.0 / total) DESC LIMIT 1""",
            (tool, operation),
        ).fetchall()
        if rows:
            return rows[0][0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Self-improving telemetry — failure analysis, issue drafts, weekly reports
# ---------------------------------------------------------------------------


def analyze_failures(days: int = 7) -> dict[str, Any]:
    """Cluster failures by (tool, operation, error) and suggest improvements.

    Returns:
        Dict with clusters (common error patterns), suggestions (config changes),
        and top_apps (apps with most failures).
    """
    try:
        conn = _get_conn()
        cutoff = time.time() - days * 86400

        rows = conn.execute(
            """SELECT tool, operation, error, strategy_used, COUNT(*) as cnt
               FROM actions WHERE ts > ? AND success = 0 AND error IS NOT NULL
               GROUP BY tool, operation, error
               ORDER BY cnt DESC LIMIT 30""",
            (cutoff,),
        ).fetchall()

        clusters = []
        for tool, op, err, strategy, cnt in rows:
            suggestion = _suggest_improvement(tool, op, err, strategy)
            clusters.append(
                {
                    "tool": tool,
                    "operation": op,
                    "error": err[:200] if err else "",
                    "count": cnt,
                    "strategy_used": strategy,
                    "suggestion": suggestion,
                }
            )

        # App-level failure stats
        app_fails = conn.execute(
            """SELECT app, COUNT(*) as cnt FROM actions
               WHERE ts > ? AND success = 0 AND app IS NOT NULL
               GROUP BY app ORDER BY cnt DESC LIMIT 10""",
            (cutoff,),
        ).fetchall()

        return {
            "days": days,
            "cluster_count": len(clusters),
            "clusters": clusters,
            "top_apps": [{"app": r[0], "fail_count": r[1]} for r in app_fails],
            "analysis_ts": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def _suggest_improvement(tool: str, operation: str, error: str, strategy: str | None) -> str | None:
    """Generate a human-readable improvement suggestion from a failure pattern."""
    error_lower = (error or "").lower()

    if "elementnotfound" in error_lower or "windownotfound" in error_lower:
        return "Consider using automation_visual(describe_region) to verify the UI state first, or increase timeout."
    if "timeout" in error_lower:
        return "Increase timeout or call automation_windows(wait_window) before this operation."
    if "access is denied" in error_lower or "permission" in error_lower:
        return "Run the MCP server as Administrator, or use a different input dispatch mode."
    if "coordinate" in error_lower or "out of range" in error_lower:
        return "Check multi-monitor layout with automation_mouse(position) — set monitor_index if using a secondary display."
    if "focus" in error_lower or "foreground" in error_lower:
        return "Call automation_windows(focus, handle=...) before the operation, or set WINDOWS_COMPUTER_USE_MCP_DISPATCH=foreground."

    if strategy == "ocr" and "found" in error_lower:
        return "OCR region may be wrong — try a larger region or switch OCR provider with WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER env."

    if tool == "automation_elements" and operation in ("click", "set_text"):
        return "Try automation_smart(click) or automation_smart(set_text) which uses intent-based fallback."
    if tool == "automation_mission":
        return "Break the mission into smaller steps or verify preconditions with automation_assert first."
    return None


def generate_issue_draft(days: int = 7, max_clusters: int = 5) -> dict[str, str | list[dict]]:
    """Generate a GitHub issue draft from top failure clusters.

    Returns:
        Dict with title (str), body (str), and clusters used.
    """
    result = analyze_failures(days=days)
    clusters = result.get("clusters", [])[:max_clusters]

    if not clusters:
        return {"title": "", "body": "", "clusters": []}

    title = f"Telemetry: {clusters[0]['tool'].replace('automation_', '')}/{clusters[0]['operation']} failing ({clusters[0]['count']}x in {days}d)"
    body_lines = [
        "## Automated Failure Report",
        f"\nGenerated from {days}-day telemetry window.",
        f"\n### Summary\n- {result['cluster_count']} distinct failure clusters",
        f"- Top apps: {', '.join(a['app'] for a in result.get('top_apps', [])[:3])}",
        "\n### Top Failure Clusters\n",
    ]
    for c in clusters:
        body_lines.append(f"#### `{c['tool']}/{c['operation']}` — {c['count']}x")
        body_lines.append(f"- Error: `{c['error'][:150]}`")
        body_lines.append(f"- Strategy: {c['strategy_used'] or 'default'}")
        if c.get("suggestion"):
            body_lines.append(f"- Suggestion: {c['suggestion']}")
        body_lines.append("")

    return {"title": title, "body": "\n".join(body_lines), "clusters": clusters}


def weekly_report() -> dict[str, Any]:
    """Generate a weekly improvement report.

    Returns:
        Dict with period, summary stats, top improvements, and suggestions.
    """
    days = 7
    stats = get_stats(days=days)
    failures = analyze_failures(days=days)
    issue = generate_issue_draft(days=days)

    total = stats.get("total_actions", 0)
    total_fails = sum(c["count"] for c in failures.get("clusters", []))
    fail_rate = round(total_fails / max(total, 1) * 100, 1)

    by_tool = stats.get("by_tool", {})
    worst_tools = sorted(
        [{"tool": k, "fail": v["fail"], "total": v["total"]} for k, v in by_tool.items()],
        key=lambda x: x["fail"],
        reverse=True,
    )[:5]

    return {
        "period": f"Last {days} days",
        "report_ts": datetime.now().isoformat(),
        "total_actions": total,
        "total_failures": total_fails,
        "fail_rate_pct": fail_rate,
        "worst_performers": worst_tools,
        "failure_clusters": failures.get("clusters", [])[:10],
        "issue_draft": issue,
        "suggestions": list(set(c["suggestion"] for c in failures.get("clusters", []) if c.get("suggestion"))),
    }
