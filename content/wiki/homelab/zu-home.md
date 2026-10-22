---
title: "Zu Hause"
description: "Was bei mir zu Hause so läuft."
date: 2026-10-22T09:00:00+02:00
draft: false
---

Das Homelab besteht im Moment aus folgender Hardware:

<!-- TODO: Modelle, CPU, RAM, Platten ergänzen -->
- **Evoli** – Proxmox-Node
- **Hardbase** – Synology-NAS
- **Pikachu** – Proxmox-Node
- **UniFi Dream Router (UDR)** als Router, Firewall und VLAN-Zentrale
- **vServer** im Internet als öffentlicher Eingang

Auf den beiden Proxmox-Nodes läuft fast alles in eigenen LXC-Containern. Angelegt und konfiguriert werden die komplett per Ansible – das Setup liegt in meinem [HomeLab-Repo](https://github.com/FdyFox/HomeLab). Was dort nicht drinsteht, gibt es nicht. Zumindest nicht lange.

## Docker-Container

Zwei LXC-Container dienen als Docker-Hosts, verwaltet mit [Komodo](https://komo.do/).

### [Komodo](https://komo.do/)

Verwaltet die Docker-Hosts und deployt die Stacks. Container, Logs und Updates habe ich damit an einer Stelle im Blick.

{{< status "fest" >}}

### [meshcore-mux](https://github.com/FdyFox/meshcore-mux)

Verteilt die eine TCP-Verbindung zu meinem MeshCore-Node auf mehrere Clients. Mehr dazu im [Beitrag zum MeshCore TCP-Node](/posts/meshcore-tcp-node/).

{{< status "selbst" >}}

### Minecraft

Ein Minecraft-Server. Braucht man eben.

{{< status "fest" >}}

### [Paperless-ngx](https://docs.paperless-ngx.com/)

Jeder Brief wird gescannt und landet hier – durchsuchbar, verschlagwortet und das Papier kann weg.

{{< status "fest" >}}

## Infrastruktur

### [AdGuard Home](https://adguard.com/de/adguard-home/overview.html)

DNS mit Werbe- und Trackingfilter, doppelt ausgelegt. Abgelöst durch den Adblocker des UniFi Dream Routers.

{{< status "alt" >}}

### [Authentik](https://goauthentik.io/)

Single Sign-On für die Dienste, die selbst keine vernünftige Anmeldung mitbringen.

{{< status "fest" >}}

### [Caddy](https://caddyserver.com/)

Reverse Proxy vor allem, was eine Weboberfläche hat. TLS kommt automatisch, die Vhosts generiert Ansible direkt aus den Host-Variablen der einzelnen Container.

{{< status "fest" >}}

### [Forgejo](https://forgejo.org/)

Eigener Git-Server inklusive Actions-Runner, unter anderem für die Runner-Images, in denen Ansible läuft.

{{< status "fest" >}}

### [Pangolin](https://github.com/fosrl/pangolin)

Läuft auf einem vServer im Internet und gibt ausgewählte Anwendungen öffentlich frei. Die Verbindung nach Hause baut ein Tunnel von innen nach außen auf, zu Hause bleibt also weiterhin kein Port offen.

{{< status "fest" >}}

## Medien

### [Audiobookshelf](https://www.audiobookshelf.org/)

Hörbücher und Podcasts. Dazu [Libation](https://github.com/rmcrackan/Libation), das meine Audible-Bibliothek automatisch herunterlädt.

{{< status "fest" >}}

### [Jellyfin](https://jellyfin.org/)

Der Medienserver, in einem eigenen Container und eigenem VLAN.

{{< status "fest" >}}

## Monitoring & Benachrichtigungen

### [ntfy](https://ntfy.sh/)

Push-Benachrichtigungen aufs Handy – von Uptime Kuma, Watchtower-Updates und allem anderen, was etwas zu sagen hat.

{{< status "fest" >}}

### [Uptime Kuma](https://uptime.kuma.pet/)

Schaut regelmäßig, ob alles noch antwortet.

{{< status "fest" >}}

## Smart Home

### [Home Assistant](https://www.home-assistant.io/)

Die Zentrale für alles, was im Haus blinkt und misst, samt MQTT-Broker. Läuft in einem eigenen VLAN.

{{< status "fest" >}}

<!-- Vorlage für weitere Dienste:

### [Name](https://link-zum-projekt)

Ein, zwei Sätze, was der Dienst macht und warum er da ist.

{{< status "test" >}}

Status: "fest" (fest integriert), "test" (evaluierend), "selbst" (selbstgemacht), "alt" (deprecated)
-->
