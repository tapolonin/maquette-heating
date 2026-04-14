import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"


def reset_commands_table():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    try:
        cur.execute("DROP TABLE IF EXISTS commands")

        cur.execute("""
            CREATE TABLE commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL CHECK (mode IN ('auto', 'manual', 'off')),
                value REAL NOT NULL
            )
        """)

        con.commit()
        print("✅ commands table recreated successfully.")

        cur.execute("PRAGMA table_info(commands)")
        columns = cur.fetchall()

        print("\nNew commands table schema:")
        for col in columns:
            print(col)

    except Exception as e:
        con.rollback()
        print("❌ Error while resetting commands table:", e)
        raise

    finally:
        con.close()


if __name__ == "__main__":
    reset_commands_table()