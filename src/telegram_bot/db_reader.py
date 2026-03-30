"""
Read-only access to the HedgeFundAI SQLite database for the Telegram bot.
Adds a `posted_to_telegram` column to ai_recommendations if missing.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent.parent.parent / "data" / "hedgefund.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    """Add posted_to_telegram column if it doesn't exist yet (idempotent)."""
    with _connect() as conn:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(ai_recommendations)")]
        if "posted_to_telegram" not in cols:
            conn.execute(
                "ALTER TABLE ai_recommendations ADD COLUMN posted_to_telegram INTEGER DEFAULT 0"
            )
            conn.commit()


def get_unposted_recommendations() -> List[Dict]:
    """
    Return ai_recommendations rows that have not been posted to Telegram yet,
    enriched with asset name from the assets table.
    Ordered by created_at ASC so older ones go first.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.ticker, r.recommendation, r.reasoning, r.score, r.created_at,
                   a.name AS asset_name
            FROM ai_recommendations r
            LEFT JOIN assets a ON a.ticker = r.ticker
            WHERE r.posted_to_telegram = 0
            ORDER BY r.created_at ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_recent_recommendations(limit: int = 10) -> List[Dict]:
    """Return the most recent recommendations regardless of posted status."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.ticker, r.recommendation, r.reasoning, r.score, r.created_at,
                   a.name AS asset_name
            FROM ai_recommendations r
            LEFT JOIN assets a ON a.ticker = r.ticker
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_as_posted(rec_id: int):
    """Mark a single recommendation as posted to Telegram."""
    with _connect() as conn:
        conn.execute(
            "UPDATE ai_recommendations SET posted_to_telegram = 1 WHERE id = ?",
            (rec_id,),
        )
        conn.commit()


def get_latest_scoring_summary() -> Optional[Dict]:
    """
    Return the most recent long_short_selection scoring result as a dict,
    or None if not available.
    """
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT data, created_at FROM scoring_results
            WHERE result_type = 'long_short_selection'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    data = json.loads(row["data"]) if row["data"] else {}
    data["_saved_at"] = row["created_at"]
    return data


def get_stats() -> Dict:
    """Return aggregate statistics from the database."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM ai_recommendations").fetchone()[0]
        by_rec = conn.execute(
            "SELECT recommendation, COUNT(*) as cnt FROM ai_recommendations GROUP BY recommendation"
        ).fetchall()
        posted = conn.execute(
            "SELECT COUNT(*) FROM ai_recommendations WHERE posted_to_telegram = 1"
        ).fetchone()[0]
        last_run = conn.execute(
            "SELECT MAX(created_at) FROM ai_recommendations"
        ).fetchone()[0]
        asset_count = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]

    breakdown = {row["recommendation"]: row["cnt"] for row in by_rec}
    return {
        "total": total,
        "posted": posted,
        "pending": total - posted,
        "breakdown": breakdown,
        "last_run": last_run,
        "asset_count": asset_count,
    }
