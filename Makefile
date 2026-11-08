HUGO    := $(shell which hugo || echo ~/.local/bin/hugo)
# code-server setzt BROWSER auf seinen Helper (öffnet URLs im Client-Browser);
# vor dem Überschreiben sichern.
ENV_BROWSER := $(BROWSER)
BROWSER := $(shell which powershell.exe 2>/dev/null || which xdg-open 2>/dev/null || echo echo)
PORT    := 1313

# Neue Beiträge mit deutscher Zeit (+01:00/+02:00) statt UTC anlegen.
export TZ := Europe/Berlin

# In code-server-Terminals ist VSCODE_PROXY_URI gesetzt (…/proxy/{{port}}/).
# Dann über /absproxy/ ausliefern, damit Hugo den Pfad-Präfix kennt.
ifdef VSCODE_PROXY_URI
DEV_URL   := $(subst {{port}},$(PORT),$(subst /proxy/,/absproxy/,$(VSCODE_PROXY_URI)))
DEV_FLAGS := --baseURL $(DEV_URL) --appendPort=false --liveReloadPort=443
DEV_OPEN  := $(ENV_BROWSER)
else
DEV_URL   := http://localhost:$(PORT)/
endif

# Kommentare: PHP-Dev-Container für das Submodul hugo-php-comments (Daten in .kommentare-dev/).
# Über /proxy/ statt /absproxy/, damit PHP die Skripte ohne Pfad-Präfix sieht.
KOMMENTARE_PORT := 1314
ifdef VSCODE_PROXY_URI
KOMMENTARE_URL := $(subst {{port}},$(KOMMENTARE_PORT),$(VSCODE_PROXY_URI))
else
KOMMENTARE_URL := http://localhost:$(KOMMENTARE_PORT)/
endif
KOMMENTARE_DOCKER := --user $$(id -u):$$(id -g) \
	-v $(CURDIR)/themes/hugo-php-comments/static/comments:/app/kommentare:ro -v $(CURDIR)/scripts:/scripts:ro -v $(CURDIR)/.kommentare-dev:/data \
	-e COMMENTS_CONFIG=/data/config.php -w /app php:8.5-cli

.DEFAULT_GOAL := help

.PHONY: help dev drafts build clean deploy logbuch bastelstube page wiki hoerbuecher open \
        kommentare-start kommentare-stop kommentare-seed

help:
	@echo "Verfügbare Befehle:"
	@echo "  make dev            Dev-Server starten (inkl. PHP-Container für Kommentare)"
	@echo "  make kommentare-seed Dummy-Kommentare in die Dev-Datenbank schreiben"
	@echo "  make build          Seite bauen (public/)"
	@echo "  make clean          public/ löschen"
	@echo "  make deploy         Bauen und per FTP deployen"
	@echo "  make logbuch [name]     Logbuch-Eintrag anlegen (ohne Name: heute)"
	@echo "  make bastelstube <name> Neuen Bastelstube-Beitrag anlegen"
	@echo "  make page <name>    Neue Seite anlegen"
	@echo "  make wiki <kat/name> Neue Wiki-Seite anlegen"
	@echo "  make hoerbuecher    Hörbuch-Daten aus Audiobookshelf holen"
	@echo "  make open           Lokale Seite im Browser öffnen"

dev:
	@echo "→ $(DEV_URL)"
ifneq ($(DEV_OPEN),)
	@( for i in $$(seq 40); do \
	     curl -s -o /dev/null localhost:$(PORT) && exec $(DEV_OPEN) $(DEV_URL); \
	     sleep 0.5; \
	   done ) >/dev/null 2>&1 &
endif
	@trap '$(MAKE) -s kommentare-stop' EXIT INT TERM; \
	  $(MAKE) -s kommentare-start; \
	  HUGO_PARAMS_COMMENTSENDPOINT=$(KOMMENTARE_URL)kommentare/api.php \
	  $(HUGO) server -D -F -p $(PORT) $(DEV_FLAGS)

# PHP-Container im Hintergrund (ohne Docker läuft make dev einfach ohne Kommentare).
kommentare-start: kommentare-stop .kommentare-dev/config.php
	@command -v docker >/dev/null || { echo "⚠ Docker fehlt, Kommentare lokal deaktiviert"; exit 0; }; \
	 docker run -d --rm --name fdyfox-kommentare -p 127.0.0.1:$(KOMMENTARE_PORT):8000 \
	   $(KOMMENTARE_DOCKER) php -S 0.0.0.0:8000 >/dev/null && \
	 echo "→ Kommentar-Verwaltung: $(KOMMENTARE_URL)kommentare/admin.php (Passwort: admin)"

kommentare-stop:
	@docker stop fdyfox-kommentare >/dev/null 2>&1 || true
	@while docker container inspect fdyfox-kommentare >/dev/null 2>&1; do sleep 0.2; done

kommentare-seed: .kommentare-dev/config.php
	docker run --rm $(KOMMENTARE_DOCKER) php /scripts/kommentare-seed.php

.kommentare-dev/config.php:
	@mkdir -p .kommentare-dev
	@printf '%s\n' "<?php" "return ['admin_password_hash' => password_hash('admin', PASSWORD_DEFAULT), 'data_dir' => '/data', 'db_file' => 'kommentare.sqlite', 'cors' => true, 'language' => 'de', 'author_name' => 'Ferdy', 'allowed_sections' => ['logbuch', 'bastelstube']];" > $@

build:
	$(HUGO) --minify

clean:
	rm -rf public/

deploy: build
	@bash deploy.sh

logbuch:
	$(eval NAME := $(or $(filter-out $@,$(MAKECMDGOALS)),$(shell date +%F)))
	@if [ -e content/$@/$(NAME).md ]; then \
	   echo "→ Eintrag existiert bereits: content/$@/$(NAME).md"; \
	 else \
	   $(HUGO) new content/$@/$(NAME).md && \
	   echo "→ Eintrag erstellt: content/$@/$(NAME).md"; \
	 fi

bastelstube:
	$(eval NAME := $(filter-out $@,$(MAKECMDGOALS)))
	@test -n "$(NAME)" || (echo "Fehler: Name fehlt. Beispiel: make $@ mein-beitrag" && exit 1)
	$(HUGO) new content/$@/$(NAME).md
	@echo "→ Beitrag erstellt: content/$@/$(NAME).md"

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
