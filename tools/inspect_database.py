import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("SELECT COUNT(*) FROM measurements;")
print("Rows:", cur.fetchone()[0])

cur.execute("SELECT timestamp, temp_in, temp_out, heater_state FROM measurements ORDER BY id DESC LIMIT 5;")
for row in cur.fetchall():
    print(row)

con.close()
