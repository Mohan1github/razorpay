from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv('DATABASE_PATH', str(ROOT_DIR / 'data' / 'razor_risk.db')))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                customer_name TEXT,
                merchant TEXT,
                amount REAL,
                risk_score INTEGER,
                decision TEXT,
                reasons TEXT,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_transaction(payload: dict[str, Any]) -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                transaction_id,
                customer_name,
                merchant,
                amount,
                risk_score,
                decision,
                reasons,
                explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get('transaction_id', 'UNKNOWN'),
                payload.get('customer_name', 'Unknown'),
                payload.get('merchant', 'Unknown'),
                float(payload.get('amount', 0)),
                int(payload.get('risk_score', 0)),
                payload.get('decision', 'APPROVE'),
                json.dumps(payload.get('reasons', [])),
                payload.get('explanation', ''),
            ),
        )
        conn.commit()


def fetch_recent_transactions(limit: int = 20) -> list[dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM transactions
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item['reasons'] = json.loads(item.get('reasons') or '[]')
        results.append(item)
    return results


def count_transactions() -> int:
    with _get_connection() as conn:
        row = conn.execute('SELECT COUNT(*) AS total FROM transactions').fetchone()
    return int(row['total']) if row else 0
