HUGO    := $(shell which hugo || echo ~/.local/bin/hugo)
BROWSER := $(shell which powershell.exe 2>/dev/null || which xdg-open 2>/dev/null || echo echo)

.DEFAULT_GOAL := help

.PHONY: help dev drafts build clean deploy post page wiki hoerbuecher open

help:
	@echo "Verfügbare Befehle:"
	@echo "  make dev            Dev-Server starten"
	@echo "  make build          Seite bauen (public/)"
	@echo "  make clean          public/ löschen"
	@echo "  make deploy         Bauen und per FTP deployen"
	@echo "  make post <name>    Neuen Beitrag anlegen"
	@echo "  make page <name>    Neue Seite anlegen"
	@echo "  make wiki <kat/name> Neue Wiki-Seite anlegen"
	@echo "  make hoerbuecher    Hörbuch-Daten aus Audiobookshelf holen"
	@echo "  make open           Lokale Seite im Browser öffnen"

dev:
	$(HUGO) server -D

build:
	$(HUGO) --minify

clean:
	rm -rf public/

deploy: build
	@bash deploy.sh

post:
	$(eval NAME := $(filter-out $@,$(MAKECMDGOALS)))
	@test -n "$(NAME)" || (echo "Fehler: Name fehlt. Beispiel: make post mein-beitrag" && exit 1)
	$(HUGO) new content/posts/$(NAME).md
	@echo "→ Beitrag erstellt: content/posts/$(NAME).md"

page:
	$(eval NAME := $(filter-out $@,$(MAKECMDGOALS)))
	@test -n "$(NAME)" || (echo "Fehler: Name fehlt. Beispiel: make page ueber-mich" && exit 1)
	$(HUGO) new content/$(NAME).md
	@echo "→ Seite erstellt: content/$(NAME).md"

wiki:
	$(eval NAME := $(filter-out $@,$(MAKECMDGOALS)))
	@test -n "$(NAME)" || (echo "Fehler: Name fehlt. Beispiel: make wiki homelab/proxmox" && exit 1)
	$(HUGO) new --kind wiki content/wiki/$(NAME).md
	@echo "→ Wiki-Seite erstellt: content/wiki/$(NAME).md"

hoerbuecher:
	python3 scripts/abs-sync.py

%:
	@:

open:
	$(BROWSER) -c "start http://localhost:1313"
