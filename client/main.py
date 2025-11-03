# ==============================================================
# Hamware AT-502 Client – mit Telnet-Debug auf Port 23 (CRLF & RSSI)
# Autor: DG8EK
# --------------------------------------------------------------
# - Port 1234: Kommunikation mit Server
# - Port 23:   Debug-Ausgabe (Telnet-kompatibel)
# - GPIO0–22 Eingänge mit Pull-Ups (invertiert)
# - LED GP28: AN = Verbindung aktiv / BLINK = keine Verbindung
# ==============================================================

import network, socket, time
from machine import Pin
from secrets import ssid, password, server_ip

# --------------------------------------------------------------
# Hardware
# --------------------------------------------------------------
inputs = [Pin(i, Pin.IN, Pin.PULL_UP) for i in range(23)]
led = Pin(28, Pin.OUT)
def led_on(): led.value(1)
def led_off(): led.value(0)
def led_toggle(): led.toggle()
led_off()

# --------------------------------------------------------------
# WLAN
# --------------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("🔌 WLAN verbinden …\r\n")
        wlan.connect(ssid, password)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                print("⚠️ WLAN-Timeout – Neustart WLAN-Interface\r\n")
                wlan.disconnect()
                wlan.active(False)
                time.sleep(0.5)
                wlan.active(True)
                wlan.connect(ssid, password)
                start = time.ticks_ms()
            time.sleep(0.05)
    print(f"✅ WLAN IP: {wlan.ifconfig()[0]}\r\n")
    return wlan

def ensure_wifi(wlan):
    if not wlan.isconnected():
        print("⚠️ WLAN getrennt – Reconnect …\r\n")
        wlan.disconnect()
        time.sleep(0.5)
        wlan.active(False)
        time.sleep(0.5)
        return connect_wifi()
    return wlan

# --------------------------------------------------------------
# Debug-Server (Telnet-Port 23)
# --------------------------------------------------------------
DEBUG_PORT = 23
debug_sock = None
debug_client = None

def setup_debug_socket():
    global debug_sock
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', DEBUG_PORT))
    s.listen(1)
    s.settimeout(0)
    debug_sock = s
    print(f"🪵 Debug-Server aktiv auf Port {DEBUG_PORT}\r\n")

def debug_send(msg):
    global debug_client
    try:
        if debug_client:
            debug_client.send((msg + "\r\n").encode())
    except:
        debug_client = None

def debug(msg):
    print(msg)
    debug_send(msg)

# --------------------------------------------------------------
# Kommunikation mit dem Server
# --------------------------------------------------------------
PORT = 1234
ADDR = (server_ip, PORT)

def try_connect_socket():
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(ADDR)
        s.settimeout(10)
        debug(f"✅ Verbunden mit Server {ADDR}")
        led_on()
        return s
    except:
        try: s.close()
        except: pass
        return None

# --------------------------------------------------------------
# Eingänge lesen / Bitstring parsen
# --------------------------------------------------------------
def read_inputs():
    return ''.join(str(1 - pin.value()) for pin in inputs)

def parse_bitstring(s):
    if len(s) != 23:
        return None
    try:
        ant = int(s[0:8], 2)
        b   = int(s[8], 2)
        l   = int(s[9:15], 2)
        trx = int(s[15:23], 2)
        return trx, l, ant, b
    except:
        return None

# --------------------------------------------------------------
# Hauptloop
# --------------------------------------------------------------
HEARTBEAT = 5
last_send = 0
last_state = ""
sock = None
blink_ts = time.ticks_ms()
connected = False

wlan = connect_wifi()
setup_debug_socket()

debug("🌐 Hamware AT-502 Client gestartet …")

while True:
    # Neue Debug-Verbindung annehmen
    try:
        c, addr = debug_sock.accept()
        debug_client = c
        debug(f"🪵 Debug-Client verbunden: {addr}")
    except OSError:
        pass

    # LED-Blinkverhalten
    if connected:
        led_on()
    else:
        if time.ticks_diff(time.ticks_ms(), blink_ts) > 500:
            led_toggle()
            blink_ts = time.ticks_ms()

    # WLAN prüfen
    wlan = ensure_wifi(wlan)

    # Verbindung zum Server
    if sock is None:
        sock = try_connect_socket()
        connected = sock is not None
        time.sleep(0.05)
        continue

    try:
        state = read_inputs()
        now = time.time()

        if state != last_state or (now - last_send) >= HEARTBEAT:
            sock.send(state.encode())
            last_state = state
            last_send = now

            resp = sock.recv(128)
            if not resp:
                raise OSError("Server getrennt")

            msg = resp.decode().strip()
            msg = msg.replace("ACK:", "").strip()
            debug(f"Empfangen <- {msg}")

            try:
                rssi = wlan.status('rssi')
            except:
                rssi = "?"

            parsed = parse_bitstring(state)
            if parsed:
                trx, l, ant, b = parsed
                antname = "ANT2" if b else "ANT1"
                debug(f"Gesendet -> TRX={trx} L={l} ANT={ant} {antname} RSSI={rssi}dBm")
            else:
                debug(f"⚠️ Ungültiger Bitstring: {state}")

        time.sleep(0.05)

    except (OSError, Exception) as e:
        debug(f"⚠️ Verbindung verloren: {e}")
        connected = False
        try: sock.close()
        except: pass
        sock = None
        time.sleep(0.05)
