---
title: "Kommentare selbst gebaut"
date: 2026-11-07T11:35:00+01:00
tags: ["meta", "php", "sicherheit"]
draft: false
---

Seit heute kann man unter den Beiträgen im Logbuch und hier in der Bastelstube kommentieren. Klingt nach einer Kleinigkeit, hat mich aber eine ganze Weile beschäftigt - nicht das Bauen, sondern die Frage, *was* ich eigentlich will.

## Was ich wollte

Etwas ganz Einfaches. Kein Konto, kein Login mit GitHub oder Google, kein Drittanbieter, der beim Seitenaufruf mitliest. Name, vielleicht eine Website, ein Textfeld, absenden. Und ich will jeden Kommentar sehen, bevor er online geht.

Als Vorbild hatte ich [grumpyoldman.de](https://grumpyoldman.de/) im Kopf: Unter jedem Beitrag steht ein schlichtes Formular, nach dem Absenden kommt der Hinweis, dass der Kommentar geprüft wird. Mehr nicht. Genau so.

Die üblichen Verdächtigen haben alle einen Haken:

- **Giscus** und **Utterances** speichern Kommentare in GitHub-Discussions bzw. -Issues. Wer kommentieren will, braucht ein GitHub-Konto - für ein Technik-Publikum vielleicht okay, für alle anderen eine Hürde.
- **Isso**, **Remark42** und **Comentario** sind ausgereift, wollen aber einen eigenen, dauerhaft laufenden Server. Für ein paar Kommentare im Monat ist mir das zu viel Betrieb.
- **Cusdis** und Co. als gehosteter Dienst - dann liegen die Daten wieder woanders.

Diese Seite ist statisch (Hugo) und liegt bei einem ganz normalen Webhoster, der PHP kann. Das Kontaktformular läuft schon über ein kleines PHP-Skript. Warum also nicht auch die Kommentare?

## Umweg über Pull Requests

Mein erster Ansatz war allerdings ein anderer: Das PHP-Skript legt jeden Kommentar als YAML-Datei per Pull Request im Repo der Seite an. Mergen heißt freischalten, Schließen heißt verwerfen, Hugo baut die Kommentare beim Deploy fest in die Seite ein. Versioniert, ohne Datenbank, eigentlich elegant.

Zwei Dinge haben mich dann aber gestört: Das Repo ist öffentlich, jeder Kommentar wäre also schon *vor* der Freigabe auf GitHub zu lesen gewesen - inklusive Spam. Eine E-Mail-Adresse hätte ich so gar nicht abfragen können. Und das Skript hätte einen GitHub-Token gebraucht, den man jährlich erneuern muss.

Also alles wieder raus.

## Wie es jetzt funktioniert

Alles läuft auf dem Webspace, aus drei PHP-Dateien und einer SQLite-Datenbank:

1. Du schickst das Formular ab. Das passiert per `fetch`, die Seite bleibt also stehen, das Formular wird an Ort und Stelle durch ein „Danke“ ersetzt. Ohne JavaScript geht es auch, dann mit einem normalen Seitenwechsel.
2. Der Kommentar landet als „offen“ in der Datenbank, und ich bekomme eine Mail mit dem Text und zwei Links: **Freigeben** und **Löschen**.
3. Freigegebene Kommentare lädt die Seite beim Aufruf nach. Sie sind also sofort sichtbar, ohne dass die Seite neu gebaut werden muss.

Die Links in der Mail öffnen übrigens erst eine Bestätigungsseite. Manche Mailprogramme und Virenscanner rufen Links vorab auf, um sie zu prüfen - ohne diesen Zwischenschritt würde der Scanner munter Kommentare freischalten.

Zusätzlich gibt es eine kleine Verwaltungsseite mit Passwort, auf der ich alle Kommentare sehe und sie freigeben, wieder verbergen, bearbeiten oder löschen kann.

Ein- und ausschalten lassen sich die Kommentare pro Bereich über das `_index.md`:

```yaml {title="content/bastelstube/_index.md"}
cascade:
  params:
    comments: true
```

PaperMod bindet dann automatisch das Partial `comments.html` ein, in dem Liste, Formular und das bisschen JavaScript stecken.

## Der Deploy darf nichts kaputt machen

Die Seite wird per `lftp mirror --delete` hochgeladen. Das spiegelt den gebauten Stand auf den Server und löscht alles, was dort zusätzlich liegt - also auch eine Datenbank, die erst auf dem Server entstanden ist. Ein `--exclude` sorgt dafür, dass der Datenordner in Ruhe gelassen wird:

```bash {title=".github/workflows/deploy.yml"}
mirror --reverse --delete --exclude ^kommentare/daten/ --parallel=8 public/ $FTP_PATH
```

Das Admin-Passwort steht natürlich nicht im Repo. Der Deploy-Workflow schreibt es aus einem GitHub-Secret in eine kleine Konfigurationsdatei, bevor er hochlädt.

## Aber der Code liegt doch öffentlich?

Die Frage habe ich mir auch gestellt. Das Repo dieser Seite ist öffentlich, die [Kommentar-Skripte](https://github.com/FdyFox/fdyfox.com/tree/main/static/kommentare) kann also jeder lesen.

Das ist aber kein Problem, solange die Sicherheit nicht davon abhängt, dass niemand weiß, wie es funktioniert. Wer den Code kennt, weiß, *wie* das Admin-Login funktioniert - aber nicht das Passwort. Er weiß, *wo* die Datenbank liegt - aber der Server liefert sie nicht aus. Alles Geheime (Passwort, Datenbank, Freigabe-Tokens) existiert nur auf dem Server.

Ein paar Dinge, die sonst noch drin stecken:

- Die E-Mail-Adresse ist optional und wird nirgends angezeigt. Die öffentliche Schnittstelle gibt sie schlicht nicht heraus.
- Alle Ausgaben werden escaped, im Browser wird nur mit `textContent` gearbeitet. HTML in einem Kommentar bleibt also Text.
- Gegen Bots gibt es ein unsichtbares Honeypot-Feld und ein Limit von drei Kommentaren pro zehn Minuten.
- Für dieses Limit muss das Skript wiedererkennen, ob dieselbe IP gerade schon kommentiert hat. Gespeichert wird aber nur ein Hash der IP, mit einem geheimen Zufallswert verrechnet, und nach zehn Minuten wieder gelöscht. Ohne den Zufallswert könnte man den Hash einfach zurückrechnen - es gibt nur etwa vier Milliarden IPv4-Adressen, die probiert ein normaler PC in Minuten durch.
- Das Admin-Login sperrt nach fünf Fehlversuchen für eine Viertelstunde.

## Lokal testen

Hugos Dev-Server kann kein PHP. Damit ich trotzdem lokal alles sehe, startet `make dev` jetzt nebenbei einen PHP-Container, und `make kommentare-seed` füllt ihn mit ein paar Dummy-Kommentaren - inklusive eines Spambots zum Löschen :)

## Was fehlt

Ein Backup. Die Kommentare liegen nur auf dem Webspace und nicht im Repo. Das kommt als Nächstes.

Und natürlich: Kommentare. Das Formular ist direkt hier unten - probier es gerne aus.
