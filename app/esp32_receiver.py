import socket
import time
import json
import re
from datetime import datetime
import paho.mqtt.publish as publish


MQTT_TOPIC = "maquette/mesures"

MQTT_HOST = "localhost"
MQTT_PORT = 1883

ESP32_IP = "192.168.4.3"
SEND_PORT = 5005
RECEIVE_PORT = 5006


def parse_message(text: str):
    """
    Extract values from ESP32 message
    """
    try:
        # temperatures
        temp_match = re.search(r"INDOOR ([\d.]+).*OUTDOOR ([\d.]+)", text)
        hum_match = re.search(r"INDOOR ([\d.]+)%.*OUTDOOR ([\d.]+)%", text)
        mosfet_match = re.search(r"MOSFET STATE ([\d.]+)", text)

        if not (temp_match and hum_match and mosfet_match):
            return None

        temp_in = float(temp_match.group(1))
        temp_out = float(temp_match.group(2))

        hum_in = float(hum_match.group(1))
        hum_out = float(hum_match.group(2))

        mosfet = float(mosfet_match.group(1))

        # convert % → 0/1
        heater_state = 1 if mosfet > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "temp_in": temp_in,
            "temp_out": temp_out,
            "hum_in": hum_in,
            "hum_out": hum_out,
            "mosfet_percent": mosfet,
            "heater_state": heater_state,
        }

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
        sock.sendto("HELLO BEEES".encode(), (ESP32_IP, SEND_PORT))

        try:
            data, addr = sock.recvfrom(1024)
            text = data.decode()

            print("RAW:\n", text)

            parsed = parse_message(text)

            if parsed:
                print("PARSED:", parsed)

                publish.single(
                    MQTT_TOPIC,
                    json.dumps(parsed),
                    hostname=MQTT_HOST,
                    port=MQTT_PORT,
                )
                
                print("Published to MQTT:", parsed)
            else:
                print("Could not parse message")

        except socket.timeout:
            print("No reply")

        time.sleep(5)


if __name__ == "__main__":
    main()