import json
import sqlite3
from pathlib import Path
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_MEAS = "maquette/mesures"

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "maquette.db"
REQUIRED_KEYS = {"timestamp", "temp_in", "hum_in", "temp_out", "hum_out", "heater_state"}

def insert_measurement(payload: dict):
    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise ValueError(f"Missing keys: {missing}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO measurements (timestamp, temp_in, hum_in, temp_out, hum_out, heater_state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        payload["timestamp"],
        float(payload["temp_in"]),
        float(payload["hum_in"]),
        float(payload["temp_out"]),
        float(payload["hum_out"]),
        int(payload["heater_state"]),
    ))
    con.commit()
    con.close()

def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Connected to MQTT broker. rc =", rc)
    client.subscribe(TOPIC_MEAS)
    print("📡 Subscribed to:", TOPIC_MEAS)

def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8")
        payload = json.loads(raw)
        insert_measurement(payload)
        print("⬇️  Saved:", payload)
    except Exception as e:
        print("❌ Error:", e)

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH} (run scripts/init_db.py)")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
