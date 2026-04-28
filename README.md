# ferdyverse.de

Persönliche Website von Ferdinand Berger — gebaut mit [Hugo](https://gohugo.io/) und dem Theme [PaperMod](https://github.com/adityatelange/hugo-PaperMod).

## Voraussetzungen

- [Hugo Extended](https://gohugo.io/installation/) ≥ 0.160.1
- `lftp` für FTP-Deployment

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

## Struktur

```
content/
├── posts/          # Logbuch-Beiträge
├── pilot.md        # Über-mich-Seite
├── search.md       # Suchseite
├── impressum.md
└── datenschutz.md
assets/css/extended/
└── custom.css      # Catppuccin-Farben & Anpassungen
layouts/partials/
└── extend_head.html # Favicons
```
