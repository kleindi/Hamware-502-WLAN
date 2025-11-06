# ==============================================================
# Hamware AT-502 Server – Telnet-Debug auf Port 23 (CRLF & RSSI)
# Autor: DG8EK
# --------------------------------------------------------------
# - Port 1234: Kommunikation mit Client
# - Port 23:   Debug-Ausgabe (Telnet-kompatibel, CRLF)
# - GPIO 0–22: Ausgänge, folgen Client-Bitstring
# - LED GP28:  AN = Client verbunden / blinkt = kein Client
# ==============================================================

import network, socket, time
from machine import Pin
from secrets import ssid, password

# --------------------------------------------------------------
# Hardware
# --------------------------------------------------------------
led = Pin(28, Pin.OUT)
def led_on(): led.value(1)
def led_off(): led.value(0)
def led_toggle(): led.toggle()
led_off()

# 23 Ausgänge (GPIO 0–22), initial auf LOW
outputs = [Pin(i, Pin.OUT, value=0) for i in range(23)]

print("⏳ Starte Server in 2 Sekunden …")
for _ in range(4):
    led_toggle()
    time.sleep(0.5)
led_off()

# --------------------------------------------------------------
# WLAN
# --------------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("🔌 WLAN verbinden …")
        wlan.connect(ssid, password)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                print("⚠️ WLAN-Timeout – neuer Versuch …")
                wlan.disconnect()
                time.sleep(1)
                wlan.connect(ssid, password)
                start = time.ticks_ms()
            time.sleep(0.25)
    print("✅ WLAN verbunden, IP:", wlan.ifconfig()[0])
    return wlan

def ensure_wifi(wlan):
    if not wlan.isconnected():
        print("⚠️ WLAN getrennt – versuche Neuverbindung …")
        wlan.disconnect()
        time.sleep(1)
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
    print(f"🪵 Debug-Server aktiv auf Port {DEBUG_PORT}")

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
# TCP Server Port 1234
# --------------------------------------------------------------
def setup_tcp():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 1234))
    s.listen(1)
    s.settimeout(0)
    debug("🖧 TCP-Server läuft auf Port 1234")
    return s

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
def run_server():
    global debug_client
    wlan = connect_wifi()
    setup_debug_socket()
    tcp  = setup_tcp()
    client = None
    last_blink = time.ticks_ms()

    debug("🌐 Hamware AT-502 Server aktiv – wartet auf Client …")

    while True:
        # Debug-Verbindung
        try:
            c, addr = debug_sock.accept()
            debug_client = c
            debug(f"🪵 Debug-Client verbunden: {addr}")
        except OSError:
            pass

        # WLAN prüfen
        wlan = ensure_wifi(wlan)

        # Clienthandling
        if not client:
            try:
                c, addr = tcp.accept()
                client = c
                client.settimeout(10)
                led_on()
                debug(f"✅ TCP-Client verbunden: {addr}")
            except OSError:
                if time.ticks_diff(time.ticks_ms(), last_blink) > 500:
                    led_toggle()
                    last_blink = time.ticks_ms()
        else:
            try:
                data = client.recv(512)
                if not data:
                    raise OSError("Client getrennt")

                s = data.decode().strip()
                p = parse_bitstring(s)
                if p:
                    trx, l, ant, b = p
                    antname = "ANT2" if b else "ANT1"
                    try:
                        rssi = wlan.status('rssi')
                    except:
                        rssi = "?"
                    msg = f"📥 TRX={trx} L={l} ANT={ant} {antname} RSSI={rssi}dBm"
                    debug(msg)

                    # ------------------------------------------------------
                    # Empfangenes Bitmuster auf Ausgänge legen (GPIO 0–22)
                    # ------------------------------------------------------
                    for i in range(min(len(s), len(outputs))):
                        outputs[i].value(int(s[i]))

                    ack = f"ACK: TRX={trx} L={l} ANT={ant} {antname} RSSI={rssi}dBm\r\n".encode()
                else:
                    msg = f"📥 Ungültige Daten empfangen: {s}"
                    debug(msg)
                    ack = b"ACK: ERROR invalid bitstring\r\n"
                client.send(ack)

            except OSError:
                debug("❌ Client getrennt.")
                try: client.close()
                except: pass
                client = None
                led_off()

        time.sleep(0.05)

# --------------------------------------------------------------
# Start
# --------------------------------------------------------------
try:
    run_server()
except Exception as e:
    debug(f"💥 Fehler im Hauptloop: {e}")
    time.sleep(2)
    run_server()
