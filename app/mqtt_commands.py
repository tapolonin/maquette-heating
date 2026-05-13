import json
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_COMMAND = "maquette/commandes"


def publish_command(payload: dict) -> None:
    """Publish a command payload to the MQTT broker."""
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC_COMMAND, json.dumps(payload))
    client.disconnect()