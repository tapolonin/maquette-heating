import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        temp_in REAL,
        hum_in REAL,
        temp_out REAL,
        hum_out REAL,
        heater_state INTEGER,
        mosfet_percent REAL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        mode TEXT,
        setpoint REAL,
        heater_manual INTEGER
    );
    """)

    con.commit()
    con.close()
    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    main()
