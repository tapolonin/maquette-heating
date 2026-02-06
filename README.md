```markdown
# Maquette Heating (Local MQTT + SQLite + Flask)

This project receives sensor data (MQTT), stores it (SQLite), displays it (Flask website), and can send control commands back (MQTT).

## Architecture
ESP32 (publisher/subscriber) → MQTT (Mosquitto on Raspberry Pi) → Collector (Python) → SQLite DB → Flask Web Dashboard  
Web UI → Flask API → MQTT commands → ESP32

---

# 0) Project structure
```

maquette/
app/
webapp.py
templates/           (if using the multi-page UI)
scripts/
init_db.py
collector.py
fake_publisher.py    (for testing without hardware)
check_db.py          (optional)
data/
maquette.db

````

---

# 1) Run on Windows laptop (development)

## 1.1 Requirements
- Python 3 installed
- Mosquitto installed (Windows) OR Mosquitto service running
- PowerShell

## 1.2 Create venv + install deps
From the project root:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install paho-mqtt flask
````

## 1.3 Start MQTT broker (Windows)

If Mosquitto installed as a service:

```powershell
Get-Service mosquitto
```

It should show `Running`.

If you need the CLI tools without PATH:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t test/topic
```

## 1.4 Initialize DB (once)

```powershell
python scripts\init_db.py
```

## 1.5 Run the system (3 terminals)

Terminal 1 (collector):

```powershell
.venv\Scripts\Activate.ps1
python scripts\collector.py
```

Terminal 2 (fake data):

```powershell
.venv\Scripts\Activate.ps1
python scripts\fake_publisher.py
```

Terminal 3 (web):

```powershell
.venv\Scripts\Activate.ps1
python app\webapp.py
```

Open in browser:

* [http://127.0.0.1:8000](http://127.0.0.1:8000)  (or the port configured in `app.run(...)`)

---

# 2) Run on Raspberry Pi (deployment)

## 2.1 Requirements

* Raspberry Pi OS
* Connected to Wi-Fi / phone hotspot
* Laptop on the same network to view the website

## 2.2 Install system packages on Pi

On the Raspberry Pi:

```bash
sudo apt update
sudo apt install -y python3-venv mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
sudo systemctl status mosquitto --no-pager
```

## 2.3 Copy project to Pi (from laptop)

On laptop PowerShell, in the folder that contains `maquette/`:

```powershell
scp -r maquette poly-etn@10.137.203.253:~
```

Replace:

* `poly-etn` with your Pi username
* `10.137.203.253` with your Pi IP (check `hostname -I` on Pi)

## 2.4 Setup Python env on Pi

On Pi:

```bash
cd ~/maquette
python3 -m venv .venv
source .venv/bin/activate
pip install paho-mqtt flask
```

## 2.5 Initialize DB on Pi (once)

```bash
python scripts/init_db.py
```

## 2.6 IMPORTANT: Make the website visible from laptop

On Raspberry Pi, edit `app/webapp.py` so Flask listens on all interfaces:

At the bottom use:

```python
app.run(host="0.0.0.0", port=8000, debug=True)
```

## 2.7 Run the system on Pi (3 terminals)

Terminal 1 (collector):

```bash
cd ~/maquette
source .venv/bin/activate
python scripts/collector.py
```

Terminal 2 (fake publisher for testing OR ESP32 real data later):

```bash
cd ~/maquette
source .venv/bin/activate
python scripts/fake_publisher.py
```

Terminal 3 (web app):

```bash
cd ~/maquette
source .venv/bin/activate
python app/webapp.py
```

---

# 3) View the Raspberry Pi website from laptop

1. Ensure laptop and Raspberry Pi are on the **same Wi-Fi / hotspot**
2. Find Pi IP:

   ```bash
   hostname -I
   ```
3. On laptop browser open:

   ```
   http://<PI_IP>:8000
   ```

Example:

```
http://10.137.203.253:8000
```

---

# 4) Transfer a NEW version to Raspberry Pi (update)

When you modify code on laptop and want to deploy the new version:

## 4.1 Copy updated folder to Pi

From laptop:

```powershell
scp -r maquette poly-etn@10.137.203.253:~
```

If you want to keep the old version on Pi, copy with another name:

```powershell
scp -r maquette poly-etn@10.137.203.253:~/maquette_new
```

## 4.2 Reinstall Python deps only if requirements changed

On Pi:

```bash
cd ~/maquette
source .venv/bin/activate
pip install -r requirements.txt
```

(Only if you created a `requirements.txt`)

## 4.3 Restart processes

Stop old scripts (Ctrl+C) and re-run:

* `python scripts/collector.py`
* `python app/webapp.py`

---

# 5) MQTT topics & message formats

## Measurements (ESP32 → Pi)

Topic:

* `maquette/mesures`

JSON fields:

```json
{
  "timestamp": "2026-02-06T11:07:55+01:00",
  "temp_in": 21.8,
  "hum_in": 45.0,
  "temp_out": 16.2,
  "hum_out": 55.0,
  "heater_state": 1,
  "status": "ok"
}
```

## Commands (Pi → ESP32)

Topic:

* `maquette/commandes`

JSON fields:

```json
{
  "timestamp": "2026-02-06T11:10:00+01:00",
  "mode": "auto",
  "setpoint": 21.0,
  "heater_manual": 0
}
```

---

# Troubleshooting

## Website works on Pi but not on laptop

* Ensure Flask uses `host="0.0.0.0"`
* Ensure laptop and Pi are on same network
* Check Pi IP with `hostname -I`
* Check port is listening on Pi:

  ```bash
  ss -ltnp | grep 8000
  ```

## “Module not found” on Windows

* Activate venv first:

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

## Don’t copy `.venv` between laptop and Pi

Virtual environments are OS-specific (Windows vs Linux). Always recreate `.venv` on the target machine.

```

If you want, I can also generate a tiny `requirements.txt` for you and add a “one-command run” script for Pi (so it starts collector + web automatically).
```
