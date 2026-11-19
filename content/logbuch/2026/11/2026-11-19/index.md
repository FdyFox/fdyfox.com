---
title: "19.11.2026"
date: 2026-11-19T22:00:00+01:00
tags: ["familie", "meta", "sicherheit", "gaming"]
draft: false
---

Heute ging es zum Zahnarzt, es gibt Neues auf der Seite, auf der Arbeit ist viel los und es gibt ein kurzes Update zu meinem Magier.

## Nachkontrolle beim Zahnarzt

Am Nachmittag war ich mit meiner Tochter beim Zahnarzt zur Nachkontrolle. Sie hatte sich vor drei Wochen am Schneidezahn verletzt, dabei ist ein Stück davon abgebrochen. Jetzt sollte kontrolliert werden, ob mit dem Zahn noch alles in Ordnung ist.

Aktuell sieht es noch durchwachsen aus - es kann sein, dass wir mit ihr nach Berlin müssen, zu einem Arzt, der sich auf solche Zahnverletzungen bei Kindern spezialisiert hat.

## Neues auf der Seite: Filme im Wiki

Wie schon [angekündigt](/logbuch/2026-11-15/#neues-auf-der-seite-brettspiele-im-wiki), habe ich jetzt auch noch [Filme](/wiki/filme/) hier auf der Seite eingebaut. Die Daten zu den Filmen kommen von [TMDB](https://www.themoviedb.org/).

## Arbeit: PHP, nginx und Java

Auf der Arbeit geht aktuell alles drunter und drüber, weil es in den letzten Tagen gleich mehrere neue Schwachstellen gab - in PHP, nginx und Java.

Bei PHP wurden mit den heutigen Versionen 8.5.13, 8.4.28, 8.3.37 und 8.2.36 gleich 18 CVEs geschlossen (siehe [ChangeLog](https://www.php.net/ChangeLog-8.php)). Sieben davon sind mit CVSS 9.2 als kritisch eingestuft:

- [CVE-2026-129289](https://github.com/php/php-src/security/advisories/GHSA-qc49-hpvq-g2w6) - Request Smuggling in PHP-FPM
- [CVE-2026-129481](https://github.com/php/php-src/security/advisories/GHSA-g3vh-838c-65v7) - Use-after-free nach abgebrochenem Session-Shutdown
- [CVE-2026-129474](https://github.com/php/php-src/security/advisories/GHSA-8mjj-2r7p-4hg2) - Use-after-free in Backtraces von Magic Methods
- [CVE-2026-129182](https://github.com/php/php-src/security/advisories/GHSA-2fjv-p558-g82m) - Use-after-free nach dem Shutdown
- [CVE-2026-115560](https://github.com/php/php-src/security/advisories/GHSA-658j-r8rw-q6mx) - Session-Serializer-Mismatch kann zu Remote Code Execution führen
- [CVE-2026-126714](https://github.com/php/php-src/security/advisories/GHSA-fm2m-fjf5-v3cp) - teilweise überschriebene Session-Dateien können zu Remote Code Execution führen
- [CVE-2026-129496](https://github.com/php/php-src/security/advisories/GHSA-gr4f-wgx5-jpfv) - Use-after-free im Zeitzonen-Cache kann zu Remote Code Execution führen

Bei nginx kam gestern "nginx2root": mehrere Lücken, über die ein Angreifer ohne Anmeldung nginx abstürzen lassen und eventuell sogar Code ausführen kann. Behoben sind sie in nginx 1.30.7 und 1.31.9 (siehe [Security Advisories](https://nginx.org/en/security_advisories.html)). Mit CVSS 9.2 bewertet sind diese beiden:

- [CVE-2026-123007](https://www.cve.org/CVERecord?id=CVE-2026-123007) - Speicherfehler bei HTTP/2, steckt schon seit Version 1.9.5 von 2015 im Code. Dafür gibt es schon öffentlichen Exploit-Code.
- [CVE-2026-123633](https://www.cve.org/CVERecord?id=CVE-2026-123633) - Use-after-free bei HTTP/2

Und bei Java gab es vorgestern "Java4Shell" ([CVE-2026-114938](https://www.cisa.gov/news-events/alerts/2026/11/17/critical-java-vulnerability-requires-immediate-patching), CVSS 9.2): ein Pufferüberlauf im Base64-Decoder von OpenJDK, der ohne Anmeldung Code ausführen kann - zum Beispiel in Jira, Confluence oder Keycloak. Betroffen sind Java 17, 21, 25 und 27, allerdings nur auf Prozessoren mit AVX-512.

## WoW: Läuft beim Magier

Mit meinem [Magier](/wiki/spiele/wow-forever/merlin-fox/) komme ich bisher gefühlt viel einfacher und schneller voran. Aber wir sind ja auch noch im Bereich unter Level 20 - da ist das, denke ich, normal?!
