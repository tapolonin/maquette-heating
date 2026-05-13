import socket
import random
import time

RECEIVER_IP = "127.0.0.1"
RECEIVER_PORT = 5006
COMMAND_PORT = 5005

temp_in = 22.0
temp_out = 16.0
hum_in = 50.0
hum_out = 65.0
mosfet = 0.0


def clamp(x, low, high):
    return max(low, min(high, x))


def update_values():
    global temp_in, temp_out, hum_in, hum_out, mosfet

    temp_in = clamp(temp_in + random.uniform(-0.4, 0.4), 18.0, 28.0)
    temp_out = clamp(temp_out + random.uniform(-0.5, 0.5), 5.0, 30.0)
    hum_in = clamp(hum_in + random.uniform(-2.0, 2.0), 20.0, 80.0)
    hum_out = clamp(hum_out + random.uniform(-2.5, 2.5), 20.0, 95.0)
    mosfet = random.choice([0, 0, 0, 25, 50, 75, 100])


def make_complete():
    return (
        f"INDOOR {temp_in:.1f} °C| OUTDOOR {temp_out:.1f}°C\n"
        f"INDOOR {hum_in:.1f}% | OUTDOOR {hum_out:.1f}%\n"
        f"MOSFET STATE {mosfet:.0f}\n"
    )


def make_partial():
    kind = random.choice([
        "no_humidity",
        "no_mosfet",
        "temp_only",
        "nan_values",
        "missing_percent",
        "outdoor_missing",
    ])

    if kind == "no_humidity":
        return (
            f"INDOOR {temp_in:.1f} °C| OUTDOOR {temp_out:.1f}°C\n"
            f"MOSFET STATE {mosfet:.0f}\n"
        )

    if kind == "no_mosfet":
        return (
            f"INDOOR {temp_in:.1f} °C| OUTDOOR {temp_out:.1f}°C\n"
            f"INDOOR {hum_in:.1f}% | OUTDOOR {hum_out:.1f}%\n"
        )

    if kind == "temp_only":
        return f"INDOOR {temp_in:.1f} °C| OUTDOOR {temp_out:.1f}°C\n"

    if kind == "nan_values":
        return (
            f"INDOOR nan °C| OUTDOOR {temp_out:.1f}°C\n"
            f"INDOOR {hum_in:.1f}% | OUTDOOR nan%\n"
            "MOSFET STATE nan\n"
        )

    if kind == "missing_percent":
        return (
            f"INDOOR {temp_in:.1f} °C| OUTDOOR {temp_out:.1f}°C\n"
            f"INDOOR {hum_in:.1f} | OUTDOOR {hum_out:.1f}\n"
            f"MOSFET STATE {mosfet:.0f}\n"
        )

    return (
        f"INDOOR {temp_in:.1f} °C| OUTDOOR \n"
        f"INDOOR {hum_in:.1f}% | OUTDOOR \n"
        f"MOSFET STATE {mosfet:.0f}\n"
    )


def choose_reply():
    if random.random() < 0.65:
        return "complete", make_complete()
    return "partial", make_partial()


def main():
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(("0.0.0.0", COMMAND_PORT))
    recv_sock.setblocking(False)

    print(f"Fake ESP32 sending to {RECEIVER_IP}:{RECEIVER_PORT}")
    print(f"Fake ESP32 listening for commands on UDP {COMMAND_PORT}")

    while True:
        update_values()
        label, reply = choose_reply()

        send_sock.sendto(reply.encode(), (RECEIVER_IP, RECEIVER_PORT))
        print(f"📤 Sent {label}:\n{reply}")

        start = time.time()
        while time.time() - start < 5:
            try:
                data, addr = recv_sock.recvfrom(1024)
                cmd = data.decode(errors="replace").strip()
                print(f"📥 Received command from {addr}: {cmd}")
            except BlockingIOError:
                pass

            time.sleep(0.1)


if __name__ == "__main__":
    main()