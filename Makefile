HUGO    := $(shell which hugo || echo ~/.local/bin/hugo)
BROWSER := $(shell which powershell.exe 2>/dev/null || which xdg-open 2>/dev/null || echo echo)

.DEFAULT_GOAL := help

.PHONY: help dev drafts build clean deploy post page open

help:
	@echo "Verfügbare Befehle:"
	@echo "  make dev            Dev-Server starten"
	@echo "  make build          Seite bauen (public/)"
	@echo "  make clean          public/ löschen"
	@echo "  make deploy         Bauen und per FTP deployen"
	@echo "  make post <name>    Neuen Beitrag anlegen"
	@echo "  make page <name>    Neue Seite anlegen"
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

%:
	@:

open:
	$(BROWSER) -c "start http://localhost:1313"
