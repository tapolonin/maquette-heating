import json
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_MEAS = "maquette/mesures"

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    temp_in = 20.0
    temp_out = 15.0

    while True:
        temp_in += random.uniform(-0.2, 0.4)
        temp_out += random.uniform(-0.1, 0.1)

        heater_state = 1 if temp_in < 21.0 else 0

        payload = {
            "timestamp": now_iso(),
            "temp_in": round(temp_in, 2),
            "hum_in": round(random.uniform(35, 55), 1),
            "temp_out": round(temp_out, 2),
            "hum_out": round(random.uniform(45, 70), 1),
            "heater_state": heater_state,
        }

        client.publish(TOPIC_MEAS, json.dumps(payload))
        print("⬆️ Published:", payload)
        time.sleep(5)

if __name__ == "__main__":
    main()
