# FdyFox.com

Persönliche Website von Ferdinand Berger — gebaut mit [Hugo](https://gohugo.io/) und dem Theme [PaperMod](https://github.com/adityatelange/hugo-PaperMod).

## Voraussetzungen

- [mise](https://mise.jdx.dev/) - installiert die in `mise.toml` festgelegte Hugo-Extended-Version (`mise install`)
- `lftp` für FTP-Deployment
- Docker (optional) - für die Kommentare in der lokalen Entwicklung (PHP-Container)

## Lokale Entwicklung

```bash
hugo server
```

Die Seite ist dann unter [http://localhost:1313](http://localhost:1313) erreichbar.

Herunterladen der Submodules: `git submodule update --init --recursive`

## Neuen Beitrag erstellen

```bash
hugo new content posts/mein-beitrag/index.md
```

Danach die Datei bearbeiten und `draft: false` setzen.

## Deployment

### Manuell

```bash
cp .env.example .env   # einmalig, Werte ausfüllen
./deploy.sh
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

Unter Beiträgen im Logbuch und in der Bastelstube gibt es ein Kommentarformular. Das System ist selbst gebaut und läuft komplett auf dem eigenen Webspace: PHP, SQLite, keine Drittanbieter.

### Ablauf

1. Besucher schicken das Formular ab (per AJAX, ohne Seitenwechsel). Name, E-Mail und Website sind optional.
2. Der Kommentar landet als „offen“ in der Datenbank, und es kommt eine Benachrichtigung an `ferdy@fdyfox.com` mit Links zum Freigeben und Löschen.
3. Freigegebene Kommentare lädt die Seite per `fetch` nach. Sie erscheinen sofort, ohne neuen Build.

Verwaltung (freigeben, verbergen, bearbeiten, löschen): **<https://fdyfox.com/kommentare/admin.php>**

### Dateien

| Datei | Zweck |
|---|---|
| `layouts/partials/comments.html` | Kommentarliste und Formular (wird von PaperMod eingebunden) |
| `static/kommentare/api.php` | Öffentlicher Endpunkt: Kommentare auflisten und einreichen, Mail-Links |
| `static/kommentare/admin.php` | Verwaltung mit Passwort-Login |
| `static/kommentare/lib.php` | Gemeinsamer Code (Datenbank, Prüfung der Eingaben, Mailversand) |
| `static/kommentare/.htaccess` | Sperrt `lib.php`, `config.php` und `daten/` |

Aktiviert werden die Kommentare pro Sektion im `_index.md` mit `cascade.params.comments: true`. Erlaubte Sektionen stehen zusätzlich in `ALLOWED_SECTIONS` in `lib.php`.

### Auf dem Server

- `kommentare/config.php` wird beim Deploy aus `COMMENT_ADMIN_PASSWORD` erzeugt (GitHub-Secret bzw. `.env` bei `./deploy.sh`). Ohne Passwort ist nur die Verwaltung gesperrt, kommentieren geht trotzdem.
- `kommentare/daten/` enthält die SQLite-Datenbank und das Salz für die IP-Hashes. Der Ordner wird beim ersten Kommentar angelegt und beim Deploy per `lftp --exclude` nicht angefasst.
- **Kein Backup:** Die Kommentare liegen nur auf dem Webspace und nicht im Repo.

### Schutz

- Honeypot-Feld gegen Bots, höchstens 3 Kommentare pro 10 Minuten und IP. Die IP wird nur als gesalzener Hash gespeichert und nach 10 Minuten verworfen.
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
├── posts/          # Logbuch-Beiträge
├── about.md        # Über-mich-Seite
├── search.md       # Suchseite
├── impressum.md
└── datenschutz.md
assets/css/extended/
└── custom.css      # Catppuccin-Farben & Anpassungen
layouts/partials/
├── extend_head.html # Favicons
└── comments.html    # Kommentarliste & Formular
static/kommentare/   # Kommentar-Backend (PHP)
scripts/
└── kommentare-seed.php # Dummy-Kommentare für die lokale Entwicklung
```
