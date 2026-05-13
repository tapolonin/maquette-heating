import json
import socket
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_CMD = "maquette/commandes"


# ESP32_IP = "127.0.0.1" #fake esp
# ESP32_IP = "172.20.10.7" #esp (mirass wifi)
ESP32_IP = "192.168.4.3" #esp (maquette wifi)
ESP32_PORT = 5005

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def to_udp_command(payload: dict):
    mode = payload.get("mode")
    value = payload.get("value", 0)

    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0

    if mode == "auto":
        return f"1 {value}"
    elif mode == "manual":
        return f"0 {value}"
    elif mode == "off":
        return "0 0"
    return None


def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Connected to MQTT broker. rc =", rc)
    client.subscribe(TOPIC_CMD)
    print("📡 Subscribed to:", TOPIC_CMD)


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8")
        payload = json.loads(raw)

        udp_command = to_udp_command(payload)
        if udp_command is None:
            print("❌ Invalid command payload:", payload)
            return

        udp_sock.sendto(udp_command.encode("utf-8"), (ESP32_IP, ESP32_PORT))
        print("📤 Sent UDP command:", udp_command)

    except Exception as e:
        print("❌ Bridge error:", e)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print("🚀 Command bridge starting...")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()