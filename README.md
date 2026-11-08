# FdyFox.com

Persönliche Website von Ferdinand Berger — gebaut mit [Hugo](https://gohugo.io/) und dem Theme [PaperMod](https://github.com/adityatelange/hugo-PaperMod).

## Voraussetzungen

- [mise](https://mise.jdx.dev/) - installiert die in `mise.toml` festgelegte Hugo-Extended-Version (`mise install`)
- `lftp` für FTP-Deployment
- Docker (optional) - für die Kommentare in der lokalen Entwicklung (PHP-Container)

## Lokale Entwicklung

```bash
git submodule update --init --recursive   # einmalig: Theme herunterladen
make dev
```

Die Seite ist dann unter [http://localhost:1313](http://localhost:1313) erreichbar, Entwürfe und Beiträge mit Datum in der Zukunft werden mit angezeigt. In code-server läuft sie automatisch über `/absproxy/1313/`. Alle Befehle zeigt `make help`.

## Neuen Inhalt erstellen

```bash
make logbuch                  # Logbuch-Eintrag für heute (content/logbuch/JJJJ-MM-TT.md)
make logbuch mein-thema       # Logbuch-Eintrag mit eigenem Namen
make bastelstube mein-thema   # Bastelstube-Beitrag
make wiki homelab/proxmox     # Wiki-Seite (Kategorie/Name)
make page ueber-mich          # Einzelne Seite
```

Neue Inhalte starten als Entwurf. Zum Veröffentlichen `draft: false` setzen.

Die Hörbuch-Daten für Wiki und `/now` holt `make hoerbuecher` aus Audiobookshelf (Zugangsdaten in `.env`).

## Deployment

### Manuell

```bash
cp .env.example .env   # einmalig, Werte ausfüllen
make deploy            # baut die Seite und lädt sie per FTP hoch (deploy.sh)
```

### Automatisch

Bei jedem Push auf `main` wird die Seite automatisch via GitHub Actions gebaut und deployed.

FTP-Zugangsdaten müssen als GitHub Secrets hinterlegt sein:

| Secret | Beschreibung |
|---|---|
| `FTP_HOST` | FTP-Server |
| `FTP_USER` | Benutzername |
| `FTP_PASS` | Passwort |
| `FTP_PATH` | Zielpfad auf dem Server |
| `COMMENT_ADMIN_PASSWORD` | Passwort für die Kommentar-Verwaltung (siehe [Kommentare](#kommentare)) |

### Updates

Hugo-Version (`mise.toml`), Theme (Submodul) und GitHub Actions werden von [Renovate](https://docs.renovatebot.com/) überwacht. Neue Versionen kommen als Pull Request, werden dort testweise gebaut und bei grünem Build automatisch gemergt (und damit deployed).

## Kommentare

Unter Beiträgen im Logbuch und in der Bastelstube gibt es ein Kommentarformular. Das System ist selbst gebaut und läuft komplett auf dem eigenen Webspace: PHP, SQLite, keine Drittanbieter. Der Code liegt im eigenen Repo [hugo-php-comments](https://github.com/FdyFox/hugo-php-comments) und ist unter `themes/hugo-php-comments` als Submodul eingebunden.

### Ablauf

1. Besucher schicken das Formular ab (per AJAX, ohne Seitenwechsel). Name, E-Mail und Website sind optional.
2. Der Kommentar landet als „offen“ in der Datenbank, und es kommt eine Benachrichtigung an `ferdy@fdyfox.com` mit Links zum Freigeben und Löschen.
3. Freigegebene Kommentare lädt die Seite per `fetch` nach. Sie erscheinen sofort, ohne neuen Build.
4. In der Verwaltung kann ich als Autor antworten. Die Antwort erscheint eingerückt unter dem Kommentar, und ein noch offener Kommentar wird dabei freigegeben. Wird ein Kommentar verborgen oder gelöscht, gilt das auch für die Antworten darauf.

Verwaltung (freigeben, verbergen, beantworten, bearbeiten, löschen): **<https://fdyfox.com/kommentare/admin.php>**

### Dateien

| Datei | Zweck |
|---|---|
| `themes/hugo-php-comments/` | Das Kommentarsystem (Submodul, Updates bewusst ohne Automerge) |
| `layouts/partials/comments.html` | Bindet die Komponente an PaperMods Kommentar-Hook an |
| `hugo.toml` | `[module]` legt die Komponente unter `/kommentare/`, `[params]` setzt Endpunkt und Sprache |
| `assets/css/extended/custom.css` | Farben aus dem Theme für die Komponente |
| `scripts/kommentare-config.sh` | Erzeugt `kommentare/config.php` beim Deploy, inklusive der Einstellungen dieser Seite |

Aktiviert werden die Kommentare pro Sektion im `_index.md` mit `cascade.params.comments: true`. Erlaubte Sektionen stehen zusätzlich in `allowed_sections` in `scripts/kommentare-config.sh`.

### Auf dem Server

- `kommentare/config.php` wird beim Deploy von `scripts/kommentare-config.sh` aus `COMMENT_ADMIN_PASSWORD` erzeugt (GitHub-Secret bzw. `.env` bei `./deploy.sh`) und enthält nur den Hash des Passworts. Dafür braucht der Deploy Docker. Ohne Passwort ist nur die Verwaltung gesperrt, kommentieren geht trotzdem.
- `kommentare/daten/` enthält die SQLite-Datenbank und das Salz für die IP-Hashes. Der Ordner wird beim ersten Kommentar angelegt und beim Deploy per `lftp --exclude` nicht angefasst. Neue Spalten ergänzt `lib.php` beim nächsten Zugriff selbst.
- **Kein Backup:** Die Kommentare liegen nur auf dem Webspace und nicht im Repo.

### Schutz

- Honeypot-Feld gegen Bots, höchstens 3 Kommentare pro 10 Minuten und IP. Die IP wird nur als gesalzener Hash gespeichert und nach Ablauf der 10 Minuten beim nächsten Abruf der Kommentare gelöscht.
- Admin-Login: Sperre nach 5 Fehlversuchen pro IP für 15 Minuten, Abmeldung nach 2 Stunden Inaktivität, CSRF-Token für alle Aktionen.
- Die Mail-Links öffnen erst eine Bestätigungsseite, damit Mail-Scanner beim Vorab-Aufruf nichts freigeben oder löschen.

### Lokal testen

`make dev` startet zusätzlich zum Hugo-Server einen PHP-8.5-Container auf Port 1314. Daten und Config liegen in `.kommentare-dev/` (nicht im Repo).

```bash
make dev               # Hugo + PHP-Container
make kommentare-seed   # Dummy-Kommentare anlegen bzw. zurücksetzen
```

Die Verwaltung ist dann unter `http://localhost:1314/kommentare/admin.php` erreichbar, in code-server unter `…/proxy/1314/kommentare/admin.php`. Das Passwort ist `admin`. Mails werden lokal nicht verschickt.

## Struktur

```
content/
├── logbuch/           # Logbuch-Einträge (Tagebuch, Gedanken)
├── bastelstube/       # Anleitungen und Basteleien
├── wiki/              # Wachsende Sammlungen (z. B. homelab/, bibliothek/)
├── about.md, now.md, uses.md, blogroll.md, kontakt.md   # Slash-Pages
├── search.md          # Suchseite
├── impressum.md
└── datenschutz.md
archetypes/            # Vorlagen für make logbuch / wiki / page
data/
├── blogroll.yaml      # Blogroll (auch als /blogroll.opml)
└── hoerbuecher.json   # von make hoerbuecher erzeugt
assets/
├── css/extended/custom.css   # Catppuccin-Farben & Anpassungen
└── hoerbuecher/covers/       # Cover von make hoerbuecher
layouts/
├── _default/kontakt.html     # Kontaktseite
├── partials/                 # Header, Footer, Kommentare, Favicons, …
├── shortcodes/               # amazon, blogroll, status, now-hoerbuecher
└── wiki/                     # Layouts für das Wiki
static/
├── contact.php               # Versand des Kontaktformulars
└── kommentare/               # Kommentar-Backend (PHP)
scripts/
├── abs-sync.py               # Audiobookshelf-Sync (make hoerbuecher)
└── kommentare-seed.php       # Dummy-Kommentare für die lokale Entwicklung
```
