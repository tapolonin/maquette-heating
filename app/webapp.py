import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from db import db_one, db_all, db_exec

from flask import Flask, jsonify, request, Response, render_template

from mqtt_client import publish_command

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_CMD = "maquette/commandes"

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

@app.get("/api/latest")
def api_latest():
    row = db_one("SELECT * FROM measurements ORDER BY id DESC LIMIT 1;")
    return jsonify(row or {})

@app.get("/api/days")
def api_days():
    rows = db_all("""
        SELECT DISTINCT substr(timestamp, 1, 10) AS day
        FROM measurements
        WHERE timestamp IS NOT NULL
        ORDER BY day DESC
    """)
    return jsonify(rows)


@app.get("/api/day")
def api_day():
    day = request.args.get("day")
    limit = int(request.args.get("limit", "2000"))

    if not day:
        return jsonify({"error": "Missing day parameter, expected YYYY-MM-DD"}), 400

    rows = db_all("""
        SELECT
            id,
            timestamp,
            temp_in,
            hum_in,
            temp_out,
            hum_out,
            heater_state,
            mosfet_percent,
            is_complete,
            raw_message,
            missing_fields
        FROM measurements
        WHERE substr(timestamp, 1, 10) = ?
        ORDER BY timestamp ASC
        LIMIT ?
    """, (day, limit))

    return jsonify(rows)


@app.get("/api/range")
def api_range():
    start = request.args.get("start")
    end = request.args.get("end")
    limit = int(request.args.get("limit", "3000"))

    if not start or not end:
        return jsonify({"error": "Missing start or end parameter"}), 400

    rows = db_all("""
        SELECT
            id,
            timestamp,
            temp_in,
            hum_in,
            temp_out,
            hum_out,
            heater_state,
            mosfet_percent,
            is_complete,
            raw_message,
            missing_fields
        FROM measurements
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
        LIMIT ?
    """, (start, end, limit))

    return jsonify(rows)


@app.get("/api/recent")
def api_recent():
    # Keep temporarily for compatibility, but prefer /api/day or /api/range in the frontend
    n = int(request.args.get("n", "120"))
    rows = db_all("""
        SELECT
            id,
            timestamp,
            temp_in,
            hum_in,
            temp_out,
            hum_out,
            heater_state,
            mosfet_percent,
            is_complete,
            raw_message,
            missing_fields
        FROM measurements
        ORDER BY id DESC
        LIMIT ?;
    """, (n,))
    rows.reverse()
    return jsonify(rows)

@app.post("/api/command")
def api_command():
    data = request.get_json(force=True)

    payload = {
        "timestamp": now_iso(),
        "mode": data.get("mode", "auto"),
        "setpoint": float(data.get("setpoint", 21.0)),
        "heater_manual": int(data.get("heater_manual", 0)),
    }

    db_exec(
        "INSERT INTO commands(timestamp, mode, setpoint, heater_manual) VALUES(?,?,?,?)",
        (
            payload["timestamp"],
            payload["mode"],
            payload["setpoint"],
            payload["heater_manual"],
        ),
    )

    publish_command(payload)

    return jsonify({"ok": True, "published": payload})

@app.get("/api/export.csv")
def export_csv():
    start = request.args.get("start")
    end = request.args.get("end")
    n = int(request.args.get("n", "20000"))

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    if start and end:
        cur.execute("""
            SELECT
                timestamp,
                temp_in,
                hum_in,
                temp_out,
                hum_out,
                heater_state,
                mosfet_percent,
                is_complete,
                raw_message,
                missing_fields
            FROM measurements
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (start, end, n))
    else:
        cur.execute("""
            SELECT
                timestamp,
                temp_in,
                hum_in,
                temp_out,
                hum_out,
                heater_state,
                mosfet_percent,
                is_complete,
                raw_message,
                missing_fields
            FROM measurements
            ORDER BY id DESC
            LIMIT ?
        """, (n,))
    rows = cur.fetchall()
    con.close()

    if not (start and end):
        rows.reverse()

    header = (
        "timestamp,temp_in,hum_in,temp_out,hum_out,"
        "heater_state,mosfet_percent,is_complete,raw_message,missing_fields\n"
    )
    lines = [header]
    for r in rows:
        line = ",".join("" if v is None else str(v).replace("\n", " ").replace(",", ";") for v in r) + "\n"
        lines.append(line)

    csv_data = "".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=measurements.csv"}
    )


@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
