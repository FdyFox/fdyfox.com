---
title: "Uses"
layout: "page"
url: "/uses/"
summary: "Womit ich arbeite"
ShowReadingTime: false
hideAuthor: true
---

*Stand: November 2026*

Eine [/uses-Seite](https://uses.tech/): Hardware, Software und Werkzeuge, mit denen ich arbeite.

## Hardware

- **PC:** AMD Ryzen 5 5600X, NVIDIA GeForce RTX 3060 Ti, 32 GB RAM
- **Tastatur:** [Keychron](https://www.keychron.com/) K3 Max – flach, mechanisch, kabellos
- **Maus:** [Razer Naga Trinity](https://www.razer.com/gaming-mice/razer-naga-trinity) – mit austauschbaren Seitenplatten
- **Handy:** [Google Pixel 10 Pro](https://store.google.com/product/pixel_10_pro)
- **Homelab:** Zwei Lenovo ThinkCentre M900 Tiny (Core i5-6600T, 32 GB RAM) mit Proxmox, ein Synology-NAS, ein UniFi Dream Router und ein vServer bei Hetzner. Details unter [Zu Hause](/wiki/homelab/zu-home/).
- **Funk:** Ein [MeshCore](https://meshcore.co.uk/)-Node, angebunden per TCP.

## Editor & Terminal

- **[code-server](https://github.com/coder/code-server):** VS Code im Browser, läuft als LXC-Container im Homelab. Damit ist die Entwicklungsumgebung von überall gleich.
- **[Neovim](https://neovim.io/)** mit [LazyVim](https://www.lazyvim.org/), wenn es schnell gehen muss.
- **[WezTerm](https://wezterm.org/)** als Terminal.
- **Schrift:** MonaspiceRn Nerd Font – [Monaspace](https://monaspace.githubnext.com/) mit Nerd-Font-Icons.
- **Farben:** [Catppuccin](https://catppuccin.com/), zumindest hier auf der Seite.

## Shell

- **zsh** mit Oh My Zsh und den Plugins `git`, `zsh-autosuggestions`, `z`, `sudo` und `direnv`.
- **[Starship](https://starship.rs/)** als Prompt. Der Header dieser Seite ist davon inspiriert.
- **[mise](https://mise.jdx.dev/)** für Tool-Versionen: Python, Go, uv, ruff, Hugo, shellcheck, shfmt …
- **Dotfiles** liegen in einem Git-Repo und werden per Bootstrap-Skript ausgerollt – für Desktop, Server und Arbeit jeweils passend.

## Entwicklung

- **Sprachen:** Python und Bash
- **Frameworks:** FastAPI, Django
- **Python-Tooling:** [uv](https://docs.astral.sh/uv/) und [ruff](https://docs.astral.sh/ruff/)
- **[Claude Code](https://claude.com/claude-code)** als Pair-Programmer – mit Hooks, die mich [selbst erziehen](/posts/selbsterziehung-durch-hooks/).
- **[Forgejo](https://forgejo.org/)** als eigener Git-Server, dazu GitHub für Öffentliches.

## Homelab-Software

- **[Proxmox VE](https://www.proxmox.com/)** mit LXC-Containern für fast alles
- **[Ansible](https://www.ansible.com/)** – was nicht im [HomeLab-Repo](https://github.com/FdyFox/HomeLab) steht, gibt es nicht
- **[Caddy](https://caddyserver.com/)** als Reverse Proxy, **[Authentik](https://goauthentik.io/)** für Single Sign-On
- **[Komodo](https://komo.do/)** für die Docker-Hosts
- **[Glance](https://github.com/glanceapp/glance)** als Dashboard, **[Uptime Kuma](https://uptime.kuma.pet/)** fürs Monitoring
- **[Pangolin](https://github.com/fosrl/pangolin)** auf dem vServer als öffentlicher Eingang
- **[Paperless-ngx](https://docs.paperless-ngx.com/)** für jeden Brief, **[Audiobookshelf](https://www.audiobookshelf.org/)** für Hörbücher, **[Jellyfin](https://jellyfin.org/)** für Filme und Serien

## Passwörter & Sicherheit

- **[1Password](https://1password.com/)** inklusive CLI – auch Ansible holt seine Secrets von dort.
- **FIDO2-Hardware-Key** für die Anmeldung, wo es geht.

## Diese Seite

[Hugo](https://gohugo.io/) mit dem Theme [PaperMod](https://github.com/adityatelange/hugo-PaperMod), gehostet bei [all-inkl.com](https://all-inkl.com/), deployt per FTP. Mehr dazu auf der [About-Seite](/about/).
