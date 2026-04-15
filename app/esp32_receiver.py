import socket
import time
import json
import re
from datetime import datetime
import paho.mqtt.publish as publish


MQTT_TOPIC = "maquette/mesures"

MQTT_HOST = "localhost"
MQTT_PORT = 1883

# ESP32_IP = "127.0.0.1" #fake esp
# ESP32_IP = "172.20.10.7" #esp (mirass wifi)
ESP32_IP = "192.168.4.3" #esp (maquette wifi)

SEND_PORT = 5005
RECEIVE_PORT = 5006

def extract_float(pattern: str, text: str):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_message(text: str):
    """
    Extract values from ESP32 message.
    Even if the message is incomplete, return the fields that were found.
    """
    try:
        parsed = {
            "timestamp": datetime.now().isoformat(),
            "raw_message": text,
        }

        # Extract values independently

        temp_out = extract_float(r"OUTDOOR\s+([\d.]+)", text)
        temp_in = extract_float(r"INDOOR\s+([\d.]+)", text)
        hum_matches = re.findall(r"(?:INDOOR|OUTDOOR)\s+([\d.]+)%", text, re.IGNORECASE)
        hum_in = None
        hum_out = None
        if len(hum_matches) >= 1:
            hum_in = float(hum_matches[0])
        if len(hum_matches) >= 2:
            hum_out = float(hum_matches[1])

        mosfet = extract_float(r"MOSFET\s+STATE\s+([\d.]+)", text)

        # Save only fields that exist
        if temp_in is not None:
            parsed["temp_in"] = temp_in
        if temp_out is not None:
            parsed["temp_out"] = temp_out
        if hum_in is not None:
            parsed["hum_in"] = hum_in
        if hum_out is not None:
            parsed["hum_out"] = hum_out
        if mosfet is not None:
            parsed["mosfet_percent"] = mosfet
            parsed["heater_state"] = 1 if mosfet > 0 else 0

        # Track completeness
        expected_fields = ["temp_in", "temp_out", "hum_in", "hum_out", "mosfet_percent"]
        missing_fields = [field for field in expected_fields if field not in parsed]

        parsed["is_complete"] = len(missing_fields) == 0
        parsed["missing_fields"] = missing_fields

        # If nothing useful was parsed, return None
        useful_fields = [k for k in parsed.keys() if k not in ("timestamp", "raw_message", "is_complete", "missing_fields")]
        if not useful_fields:
            return None

        return parsed

    except Exception as e:
        print("Parse error:", e)
        return None


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", RECEIVE_PORT))
    sock.settimeout(1.0)

    print("UDP Receiver started")

    while True:
        # send ping
        # sock.sendto("HELLO BEEES".encode(), (ESP32_IP, SEND_PORT))

        try:
            data, addr = sock.recvfrom(1024)
            text = data.decode(errors="replace")

            print("RAW:\n", text)

            parsed = parse_message(text)

            if parsed:
                if parsed["is_complete"]:
                    print("PARSED COMPLETE:", parsed)
                else:
                    print("PARSED PARTIAL:", parsed)

                publish.single(
                    MQTT_TOPIC,
                    json.dumps(parsed),
                    hostname=MQTT_HOST,
                    port=MQTT_PORT,
                )

                print("Published to MQTT:", parsed)
            else:
                print("Could not parse any useful data")

        except socket.timeout:
            print("No reply")
        except Exception as e:
            print("Receiver error:", e)

        time.sleep(5)


if __name__ == "__main__":
    main()