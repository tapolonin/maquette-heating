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


def make_complete_payload(temp_in, temp_out):
    heater_state = 1 if temp_in < 21.0 else 0
    mosfet_percent = random.choice([0, 25, 50, 75, 100]) if heater_state else 0

    return {
        "timestamp": now_iso(),
        "temp_in": round(temp_in, 2),
        "hum_in": round(random.uniform(35, 55), 1),
        "temp_out": round(temp_out, 2),
        "hum_out": round(random.uniform(45, 70), 1),
        "heater_state": heater_state,
        "mosfet_percent": mosfet_percent,
        "is_complete": True,
        "raw_message": None,
        "missing_fields": [],
    }


def make_incomplete_payload(base_payload):
    payload = dict(base_payload)

    scenario = random.choice([
        "missing_hum_in",
        "missing_hum_out",
        "missing_temp_out",
        "missing_mosfet",
        "missing_heater_state",
        "two_missing",
        "null_value",
        "wrong_type",
        "only_timestamp_and_one_value",
    ])

    if scenario == "missing_hum_in":
        payload.pop("hum_in", None)

    elif scenario == "missing_hum_out":
        payload.pop("hum_out", None)

    elif scenario == "missing_temp_out":
        payload.pop("temp_out", None)

    elif scenario == "missing_mosfet":
        payload.pop("mosfet_percent", None)

    elif scenario == "missing_heater_state":
        payload.pop("heater_state", None)

    elif scenario == "two_missing":
        for key in random.sample(
            ["temp_in", "hum_in", "temp_out", "hum_out", "heater_state", "mosfet_percent"], 2
        ):
            payload.pop(key, None)

    elif scenario == "null_value":
        key = random.choice(["temp_in", "hum_in", "temp_out", "hum_out"])
        payload[key] = None

    elif scenario == "wrong_type":
        key = random.choice(["temp_in", "hum_in", "temp_out", "hum_out", "mosfet_percent"])
        payload[key] = "ERROR"

    elif scenario == "only_timestamp_and_one_value":
        keep_key = random.choice(["temp_in", "hum_in", "temp_out", "hum_out"])
        payload = {
            "timestamp": payload["timestamp"],
            keep_key: payload[keep_key],
        }

    expected = {"timestamp", "temp_in", "hum_in", "temp_out", "hum_out", "heater_state", "mosfet_percent"}
    present = set(payload.keys())
    missing = sorted(list(expected - present))

    payload["is_complete"] = False
    payload["missing_fields"] = missing
    payload["raw_message"] = f"FAKE_PARTIAL::{scenario}"

    return scenario, payload


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    temp_in = 20.0
    temp_out = 15.0

    while True:
        temp_in += random.uniform(-0.2, 0.4)
        temp_out += random.uniform(-0.1, 0.1)

        base_payload = make_complete_payload(temp_in, temp_out)

        r = random.random()

        if r < 0.70:
            payload = base_payload
            label = "complete"
        else:
            label, payload = make_incomplete_payload(base_payload)

        client.publish(TOPIC_MEAS, json.dumps(payload))
        print(f"⬆️ Published ({label}): {payload}")

        time.sleep(5)


if __name__ == "__main__":
    main()