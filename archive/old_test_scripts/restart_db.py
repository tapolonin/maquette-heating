import sqlite3

conn = sqlite3.connect("data/maquette.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS measurements")

cur.execute("""
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    temp_in REAL,
    hum_in REAL,
    temp_out REAL,
    hum_out REAL,
    heater_state INTEGER,
    mosfet_percent REAL,
    is_complete INTEGER,
    raw_message TEXT,
    missing_fields TEXT
)
""")

conn.commit()
conn.close()

print("✅ Fresh measurements table created")