import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify, request, Response

import paho.mqtt.client as mqtt

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_CMD = "maquette/commandes"

def db_one(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None

def db_all(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]

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

    # log command in DB
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO commands (timestamp, mode, setpoint, heater_manual)
        VALUES (?, ?, ?, ?)
    """, (payload["timestamp"], payload["mode"], payload["setpoint"], payload["heater_manual"]))
    con.commit()
    con.close()

    # publish to MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.publish(TOPIC_CMD, json.dumps(payload))
    client.disconnect()

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
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Maquette - Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1000px; margin: 20px auto; }
    pre { background: #f3f3f3; padding: 12px; border-radius: 8px; }
    .row { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; min-width: 280px; flex: 1; }
    input, select, button { padding: 6px; margin: 6px 0; }
    canvas { background: #fff; }
    .links a { margin-right: 12px; }
  </style>
</head>
<body>
  <h1>Maquette Dashboard (Local)</h1>

  <div class="links">
    <a href="/api/export.csv?n=1000">Download CSV (last 1000)</a>
  </div>

<div class="card" style="margin-top: 20px;">
  <h2>Analysis (recent data)</h2>
  <pre id="analysis">Loading...</pre>
</div>

  <div class="row">
    <div class="card">
      <h2>Latest measurement</h2>
      <pre id="latest">Loading...</pre>
    </div>

    <div class="card">
      <h2>Control</h2>
      <label>Mode</label><br/>
      <select id="mode">
        <option value="auto">auto</option>
        <option value="manual">manual</option>
      </select><br/>

      <label>Setpoint (°C)</label><br/>
      <input id="setpoint" type="number" step="0.1" value="21.0"/><br/>

      <label>Manual heater</label><br/>
      <select id="heater_manual">
        <option value="0">OFF</option>
        <option value="1">ON</option>
      </select><br/>

      <button onclick="sendCommand()">Send command</button>
      <pre id="cmdresp"></pre>
    </div>
  </div>

  <div class="card" style="margin-top: 20px;">
    <h2>Temperature (last points)</h2>
    <label>Number of points:
      <input id="npoints" type="number" value="120" min="10" max="5000"/>
    </label>
    <button onclick="reloadChart()">Reload</button>
    <canvas id="tempChart" height="120"></canvas>
  </div>

<script>
let chart;

async function refreshLatest() {
  const r = await fetch('/api/latest');
  const data = await r.json();
  document.getElementById('latest').innerText = JSON.stringify(data, null, 2);
}
setInterval(refreshLatest, 2000);
refreshLatest();

async function sendCommand() {
  const payload = {
    mode: document.getElementById('mode').value,
    setpoint: parseFloat(document.getElementById('setpoint').value),
    heater_manual: parseInt(document.getElementById('heater_manual').value)
  };

  const r = await fetch('/api/command', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });

  const data = await r.json();
  document.getElementById('cmdresp').innerText = JSON.stringify(data, null, 2);
}

async function loadRecent(n=120) {
  const r = await fetch('/api/recent?n=' + n);
  return await r.json();
}

async function reloadChart() {
  const n = parseInt(document.getElementById('npoints').value);
  const rows = await loadRecent(n);

  const labels = rows.map(r => r.timestamp);
  const tin = rows.map(r => r.temp_in);
  const tout = rows.map(r => r.temp_out);

  const ctx = document.getElementById('tempChart');

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: 'Temp In (°C)', data: tin, tension: 0.2 },
        { label: 'Temp Out (°C)', data: tout, tension: 0.2 }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } }
      }
    }
  });
async function refreshAnalysis() {
  const r = await fetch('/api/analysis?n=300');
  const data = await r.json();
  document.getElementById('analysis').innerText =
    JSON.stringify(data, null, 2);
}

setInterval(refreshAnalysis, 5000);
refreshAnalysis();

}

reloadChart();
setInterval(reloadChart, 15000); // refresh chart every 15s
</script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
