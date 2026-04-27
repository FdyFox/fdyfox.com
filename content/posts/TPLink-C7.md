---
title: "TP-Link Archer C7 - Stock-Firmware via TFTP wiederherstellen"
date: 2026-04-24T14:08:33+02:00
tags: ["router", "openwrt", "tftp", "netzwerk", "linux"]
draft: false
---

Im Zuge der Vorbereitungen für den Umzug habe ich einen alten Router, mit dem ich OpenWrt ausprobiert hatte, wieder auf die Stock-Firmware geflasht. Dabei bin ich zum ersten Mal mit `tftp` in Berührung gekommen.

`TFTP` steht für "Trivial File Transfer Protocol", arbeitet standardmäßig auf Port 69 über UDP und wird vom Router im Recovery-Modus genutzt, um eine neue Firmware zu empfangen. Als TFTP-Server habe ich [uftpd](https://github.com/troglobit/uftpd) verwendet - lässt sich ohne Konfiguration direkt in der Konsole starten. Als Referenz habe ich die [OpenWrt-Dokumentation zum Archer C7](https://openwrt.org/toh/tp-link/archer_c7#installation_or_restore_with_tftp_on_linux) genutzt.

## Vorbereitung

1. Originale Firmware von der [TP-Link-Website](https://www.tp-link.com/de/support/download/archer-c7/) herunterladen
2. Datei in `ArcherC7v5_tp_recovery.bin` umbenennen - der Router sucht genau nach diesem Namen
3. Netzwerkadapter auf statisch setzen: IP `192.168.0.66`, Subnetz `255.255.255.0`, Gateway `192.168.0.1`

## TFTP-Server starten

```bash {title="I use Arch, btw"}
# uftpd installieren (AUR)
aur -S uftpd

# Port 69 freigeben
sudo ufw allow 69/udp

# TFTP-Server starten, FTP deaktivieren
sudo uftpd -n -o ftp=0,tftp=69 -l debug $HOME/Downloads/TPLink
```

## Router flashen

Den Router per LAN-Kabel an Port 1 anschließen und beim Einschalten den Reset-Knopf gedrückt halten, bis die WPS-LED leuchtet (die mit den zwei gegenläufigen Pfeilen ganz rechts). Im `uftpd`-Log sollten jetzt Einträge erscheinen. Nach ca. 2 Minuten startet der Router selbstständig neu und ist wieder auf der Stock-Firmware.

Eigentlich ganz einfach, wenn man weiß wie :)
