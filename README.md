# Hamware AT-502 – MicroPython Netzwerk-Client/Server

Entwickelt von **DG8EK**  
Version: 2025-11  
Lizenz: MIT  

## 🔧 Projektbeschreibung
Der Hamware AT-502 ist ein auf **Raspberry Pi Pico W** basierendes 
Client-/Server-System für zuverlässige, latenzarme Datenübertragung 
über WLAN in MicroPython.

### Komponenten
- **Server** (`server_AT502_debugsocket_rssi_crlf_port23.py`)  
  Lauscht auf Port 1234, verarbeitet Bit-Strings, gibt Debug-Infos 
  über **Telnet (Port 23)** aus und zeigt Status über LED GP28.  
  Zeigt zudem WLAN-RSSI zur Kontrolle der Signalstärke.

- **Client** (`client_AT502_debugsocket_rssi_crlf_port23.py`)  
  Liest 23 Eingänge (GPIO 0-22, Pull-Ups, invertiert), sendet deren 
  Status regelmäßig an den Server und gibt Debug-Infos ebenfalls 
  über **Telnet (Port 23)** aus.

### Hardware-Belegung
| Funktion | Pin |
|-----------|-----|
| Eingänge (Client) | GPIO 0 – 22 |
| Status-LED | GPIO 28 |
| Versorgung | 3.3 V |
| GND | GND |

Empfohlener LED-Vorwiderstand: **470 Ω** zwischen GPIO 28 und GND.

---

## ⚙️ Einrichtung

### 1. MicroPython flashen
Installiere MicroPython ≥ v1.26 auf beiden Pico W-Boards.

### 2. Projektdateien kopieren
Kopiere auf **beide Geräte**:
- `secrets.py` (deine WLAN-Zugangsdaten)
- jeweilige Hauptdatei (`client_…` oder `server_…`)

### 3. Netzwerk-Konfiguration
Trage in `secrets.py`:
```python
ssid = "dein_WLAN"
password = "dein_Passwort"
server_ip = "192.168.11.54"   # IP des Servers
```

### 4. Start
Beim Einschalten:
- LED blinkt → keine Verbindung  
- LED dauerhaft an → Verbindung aktiv  
- Telnet auf Port 23 liefert Debug-Infos  

### 5. Telnet-Verbindung
Mit jedem Telnet-Client:
```bash
telnet 192.168.11.54        # Server
telnet 192.168.11.56        # Client
```

Beenden mit `Ctrl+]` und `quit`.

---

## 🧠 Systemverhalten

- Heartbeat-Intervall: 5 s  
- Reconnect bei WLAN-Ausfall  
- CRLF-Zeilenenden (kompatibel mit Windows Telnet)  
- LED blinkt 1 Hz bei Disconnect  

---

## 🛠️ Entwicklung
Quellcode basiert auf MicroPython-Standardbibliotheken  
(`network`, `socket`, `machine`, `time`).  

Entwicklungsumgebung: **Thonny**  
Programmierstil: *Robust, funktional, Sicherheit vor Schönheit.*

---

73 de **DG8EK**
