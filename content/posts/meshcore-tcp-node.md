---
title: "Ein MeshCore TCP-Node für LAN und VPN"
date: 2026-10-01T18:00:00+02:00
tags: ["funk", "netzwerk", "homelab"]
draft: false
---

[MeshCore](https://meshcore.co.uk/) ist ein schlankes Mesh-Routing-Protokoll für LoRa-Funkgeräte - ähnlich wie Meshtastic, nur mit eigenem Routing-Ansatz. Es läuft auf ESP32-Boards mit LoRa-Funkmodul, bei mir ein Heltec LoRa32.

Ich wollte einen stationären Node haben, der nicht nur per BLE oder USB erreichbar ist, sondern den ich aus dem lokalen Netz **und** von unterwegs per VPN ansprechen kann - und das mit mehreren Apps gleichzeitig. Dafür braucht es drei Bausteine: eine Firmware, die sich ins WLAN einbucht, einen Multiplexer, der die eine TCP-Verbindung zum Node auf mehrere Clients verteilt, und einen VPN-Zugang ins Heimnetz.

## WLAN-Zugangsdaten in die Firmware patchen

> [!NOTE]
> Seit Companion-Firmware v1.18.0 lassen sich die WLAN-Zugangsdaten bei vielen Boards direkt per CLI oder App setzen - siehe [Update](#update-seit-firmware-v1180-kein-patcher-mehr-nötig) am Ende des Beitrags.

MeshCore-Companion-Firmware kann grundsätzlich auch per WiFi/TCP statt nur über BLE oder USB angesprochen werden - praktisch für einen stationären Gateway-Node. Laut [offizieller MeshCore-Doku](https://docs.meshcore.io/faq/) muss man dafür aber selbst kompilieren: SSID und Passwort trägt man als `WIFI_SSID`/`WIFI_PWD` fest in der `platformio.ini` der jeweiligen Board-Variante ein, bevor man baut und flasht - mit eigener Toolchain und für jedes WLAN ein eigener Build.

Genau das nimmt einem der [ESP32 SSID Patcher](https://www.weyhmueller.org/webtools/esp32_ssid_patcher.html) von O. Weyhmüller ab. Im zugehörigen Firmware-Archiv liegen für dieses Tool vorbereitete WiFi-Companion-Builds, bei denen statt echter Zugangsdaten nur Platzhalter (`myssid_patchable` / `mypwd_patchable`) im Binary stehen. Firmware auswählen, SSID und Passwort eintragen - fertig. Der Patch läuft komplett lokal im Browser, es wird nichts an einen Server geschickt. Das Tool ersetzt die Platzhalter im Binary und passt anschließend Checksumme und SHA256 an, damit der ESP32 das Image beim Boot als gültig akzeptiert - kein eigener Build nötig.

Den ESP32 per USB angeschlossen, flasht der Patcher die gepatchte Firmware direkt aus dem Browser übers Web-Serial-API - kein `esptool.py` oder sonstige Toolchain nötig. Nach dem Flashen bucht sich der Node beim Boot automatisch ins WLAN ein und lauscht dort als Companion über TCP.

## Ein Companion, mehrere Clients

Das MeshCore-Companion-Protokoll über TCP erlaubt nur eine aktive Verbindung. Sobald die Handy-App verbunden ist, kommt kein Web-Client und keine Automatisierung mehr an den Node ran.

Die Lösung ist ein Multiplexer: Er hält eine einzige Verbindung zum Companion offen und stellt mehrere Ports bereit, an denen sich beliebig viele Clients anmelden können - einen Multi-Client-Port für kurze Sitzungen, dazu dedizierte Ports für langlebige Apps, die jeweils ihr eigenes Postfach behalten, auch wenn sie gerade nicht verbunden sind. Ein simpler TCP-Proxy reicht dafür nicht: Das Protokoll kennt keine Request-IDs, Antworten müssen also dem richtigen Client zugeordnet werden, und eingehende Nachrichten muss der Mux selbst aus dem Postfach des Nodes abholen und an alle Clients verteilen.

Angefangen habe ich mit [meshcore-tcp-mux](https://github.com/compumike/meshcore-tcp-mux) von Michael F. Robbins, das genau das sauber umsetzt. Im Betrieb haben mich dann aber ein paar Dinge gestört, und so habe ich das Projekt als [meshcore-mux](https://github.com/FdyFox/meshcore-mux) nach Go portiert und erweitert. Protokollverhalten, Limits und Kommandozeilen-Flags sind identisch zum Original, ein Umstieg funktioniert also ohne Anpassung. Den eigenen Namen trägt es nur, damit es nicht mit dem Original verwechselt wird.

### Warum ein eigener Mux

- **Persistenz:** Beim Original liegen die Postfächer der dedizierten Ports nur im RAM. Startet der Container neu - Update, Host-Reboot, Absturz - sind alle Nachrichten weg, die eine gerade nicht verbundene App noch nicht abgeholt hat. Dauerhafte Speicherung steht dort auf der Roadmap als „not planned“. meshcore-mux kann die Postfächer und die Deduplizierungs-Historie optional in einer State-Datei sichern, sodass sie Neustarts überleben.
- **Nachvollziehbares Logging:** Probleme wie abgelehnte Kommandos, zwangsweise getrennte Clients oder Timeouts zum Companion tauchten im Original oft nur auf `DEBUG`-Level auf - wenn etwas nicht ging, stand im Log schlicht nichts. meshcore-mux meldet solche Fälle als `WARN` bzw. `ERROR`, immer mit Ursache, etwa welches Limit gerissen ist oder warum ein Kommando abgelehnt wurde.
- **Konfigurationsdatei:** Statt einer langen Flag-Liste im `command:`-Block gibt es eine kommentierbare YAML-Datei. Flags funktionieren weiterhin und überschreiben bei Bedarf die Werte aus der Datei.
- **Gehärtetes Image:** Das Container-Image basiert auf `scratch` statt Alpine und läuft mit `read_only`, ohne Capabilities und mit `no-new-privileges`. Es gibt Images für `amd64` und `arm64`, also auch für den Raspberry Pi.

### Setup

Die Konfiguration:

```yaml {title="config.yaml"}
upstream:
  host: 192.168.1.50
  port: 5000

listen:
  multi_client_port: 5001
  dedicated_client_ports: [5002, 5003]

deduplicate_received_messages: true

persistence:
  enabled: true
```

`upstream.host` zeigt auf den Heltec-Node im WLAN. Die Handy-App und ein Web-Terminal bekommen je einen dedizierten Port, damit ihnen keine Nachricht entgeht, während sie offline sind. Der Multi-Client-Port bleibt für spontane Sitzungen, etwa mit `meshcore-cli`.

Dazu die Compose-Datei:

```yaml {title="docker-compose.yml"}
services:
  meshcore-mux:
    image: ghcr.io/fdyfox/meshcore-mux:latest
    restart: unless-stopped
    command: ["--config", "/etc/meshcore-mux/config.yaml"]
    volumes:
      - ./config.yaml:/etc/meshcore-mux/config.yaml:ro
      - meshcore-mux-state:/var/lib/meshcore-mux
    ports:
      - "5001-5003:5001-5003"
    environment:
      LOG_LEVEL: "INFO"
    read_only: true
    cap_drop: ["ALL"]
    security_opt: ["no-new-privileges:true"]

volumes:
  meshcore-mux-state:
```

Im Volume `meshcore-mux-state` liegt die State-Datei mit den gepufferten Nachrichten. Ein Hinweis dazu: Sie enthält den Klartext empfangener Nachrichten.

## Zugriff aus dem LAN und per VPN

Im lokalen Netz spreche ich den Mux einfach über die Server-IP und den jeweiligen Port an. Für unterwegs nutze ich mein bestehendes WireGuard-VPN ins Heimnetz. Damit sind dieselben Ports auch von draußen erreichbar, ohne dass ich irgendwas am Router öffentlich freigeben muss.

> [!CAUTION]
> Die Mux-Ports sollten nicht direkt ins Internet durchgereicht werden - das MeshCore-Companion-Protokoll bringt keine eigene Authentifizierung mit. Zugriff von außen nur über VPN, nie per Portforwarding.

## Fazit

Am Ende steht ein stationärer MeshCore-Node, auf den ich mit mehreren Geräten und Apps gleichzeitig zugreifen kann - egal ob ich im selben Netz sitze oder über WireGuard von unterwegs. Ohne eigenen Firmware-Build dank SSID Patcher, und dank meshcore-mux gehen auch bei Neustarts keine Nachrichten verloren.

## Update: Seit Firmware v1.18.0 kein Patcher mehr nötig

Mit der [Companion-Firmware v1.18.0](https://blog.meshcore.io/2026/10/15/release-1-18-0) vom 15. Oktober 2026 hat sich das Thema WLAN-Zugangsdaten erledigt: Für eine Reihe von ESP32-Boards - darunter Heltec v3, Heltec v4, Heltec Wireless Paper, RAK3112 und Xiao S3 - enthalten die offiziellen **BLE**-Builds jetzt zusätzlich das WiFi-Interface. SSID und Passwort lassen sich zur Laufzeit per CLI setzen und landen dauerhaft in den Node-Einstellungen:

```text
set wifi.ssid MeinWLAN
set wifi.pwd geheim
```

Nach einem Neustart bucht sich der Node ins WLAN ein und ist wie gehabt per TCP erreichbar. Alternativ geht das seit MeshCore-App v1.50.0 auch bequem über den neuen Bereich „WiFi Settings“: per BLE verbinden, Zugangsdaten eintragen, Node neu starten.

> [!WARNING]
> Das gilt nur für die **BLE**-Variante der Firmware. Die USB-Builds bekommen kein WiFi - laut Release Notes wird die USB-Schnittstelle in den BLE+WiFi-Builds für Serial-Logging gebraucht. Für einen WLAN-Node ist also das `companion_radio_ble`-Image des jeweiligen Boards die richtige Wahl.
