# app/db.py
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Keep the DB path logic in one place
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "maquette.db"


def _connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def db_one(sql: str, params: Sequence[Any] = (), db_path: Path = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def db_all(sql: str, params: Sequence[Any] = (), db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def db_exec(sql: str, params: Sequence[Any] = (), db_path: Path = DEFAULT_DB_PATH) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid when available, else 0."""
    with _connect(db_path) as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return int(cur.lastrowid or 0)
