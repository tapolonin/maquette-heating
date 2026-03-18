

## Maquette Heating – Quick Start

Local system:
- MQTT broker (Mosquitto)
- Python collector (stores data in SQLite)
- Flask web dashboard
- Control commands via MQTT

Works on:
- Laptop (development)
- Raspberry Pi (final deployment)



## 1. Run on Laptop (development)

## 1. Go to project folder
```powershell
cd path\to\maquette
````

## 2. Create virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install paho-mqtt flask
```

## 3. Initialize database (once)

```powershell
python scripts\init_db.py
```

## 4. Start the system (3 terminals)

### Terminal 1 – collector

```powershell
.venv\Scripts\Activate.ps1
python scripts\collector.py
```

### Terminal 2 – fake data (for testing)

```powershell
.venv\Scripts\Activate.ps1
python scripts\fake_publisher.py
```

### Terminal 3 – website

```powershell
.venv\Scripts\Activate.ps1
python app\webapp.py
```

Open browser:

```
http://127.0.0.1:8000
```

(or 8050 if port changed)



# 2. Deploy to Raspberry Pi

## 1. Install dependencies on Pi

On Raspberry Pi terminal:

```bash
sudo apt update
sudo apt install -y python3-venv mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```



## 2. Copy project from laptop to Pi

On laptop PowerShell:

```powershell
scp -r maquette USER@PI_IP:~
```

Example:

```powershell
scp -r maquette poly-etn@10.137.203.253:~
```



## 3. Set up Python on Pi

On Raspberry Pi:

```bash
cd ~/maquette
python3 -m venv .venv
source .venv/bin/activate
pip install paho-mqtt flask
python scripts/init_db.py
```



## 4. Allow website access from laptop

Edit `app/webapp.py` on the Pi:

At the bottom:

```python
app.run(host="0.0.0.0", port=8000, debug=True)
```



## 5. Run system on Pi (3 terminals)

Terminal 1:

```bash
cd ~/maquette
source .venv/bin/activate
python scripts/collector.py
```

Terminal 2:

```bash
cd ~/maquette
source .venv/bin/activate
python app/esp32_receiver.py
```

Terminal 3:

```bash
cd ~/maquette
source .venv/bin/activate
python app/webapp.py
```



## 6. View Pi dashboard from laptop

1. Make sure laptop and Pi are on same Wi-Fi/hotspot.
2. On Pi:

```bash
hostname -I
```

3. On laptop browser:

```
http://PI_IP:8000
```

Example:

```
http://10.137.203.253:8000
```



# 3. Update code on Raspberry Pi

From laptop:

```powershell
scp -r maquette USER@PI_IP:~
```

Then on Pi:

```bash
cd ~/maquette
source .venv/bin/activate
python app/webapp.py
```



# Important notes

* Never copy `.venv` between laptop and Pi.
* Always recreate `.venv` on the target machine.
* Laptop uses `127.0.0.1`.
* Raspberry Pi must use `0.0.0.0`.

