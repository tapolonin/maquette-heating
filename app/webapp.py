import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
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

@app.get("/api/recent")
def api_recent():
    n = int(request.args.get("n", "120"))  # last 120 points
    rows = db_all("SELECT * FROM measurements ORDER BY id DESC LIMIT ?;", (n,))
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
    # export last N rows (default 1000)
    n = int(request.args.get("n", "1000"))

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT timestamp, temp_in, hum_in, temp_out, hum_out, heater_state, status
        FROM measurements
        ORDER BY id DESC
        LIMIT ?
    """, (n,))
    rows = cur.fetchall()
    con.close()

    rows.reverse()

    header = "timestamp,temp_in,hum_in,temp_out,hum_out,heater_state,status\n"
    lines = [header]
    for r in rows:
        # safe CSV formatting
        line = ",".join("" if v is None else str(v) for v in r) + "\n"
        lines.append(line)

    csv_data = "".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=measurements.csv"}
    )


@app.get("/api/analysis")
def api_analysis():
    # number of recent points
    n = int(request.args.get("n", "300"))

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT temp_in, temp_out, heater_state
        FROM measurements
        ORDER BY id DESC
        LIMIT ?
    """, (n,))
    rows = cur.fetchall()
    con.close()

    if not rows:
        return jsonify({})

    rows = list(reversed(rows))

    tin = [r[0] for r in rows if r[0] is not None]
    tout = [r[1] for r in rows if r[1] is not None]
    heater = [r[2] for r in rows if r[2] is not None]

    avg_tin = sum(tin) / len(tin) if tin else 0
    avg_tout = sum(tout) / len(tout) if tout else 0
    delta_t = avg_tin - avg_tout

    heater_on_ratio = sum(heater) / len(heater) if heater else 0

    # assume heater power = 25 W (adjust later if needed)
    heater_power = 25.0

    # assume 5s between samples (same as fake publisher)
    sample_period_s = 5
    total_time_h = (len(heater) * sample_period_s) / 3600.0

    energy_wh = heater_power * total_time_h * heater_on_ratio

    return jsonify({
        "avg_temp_in": round(avg_tin, 2),
        "avg_temp_out": round(avg_tout, 2),
        "delta_t": round(delta_t, 2),
        "heater_on_percent": round(heater_on_ratio * 100, 1),
        "estimated_energy_Wh": round(energy_wh, 2),
        "samples_used": len(rows)
    })

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
