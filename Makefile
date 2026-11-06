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

.DEFAULT_GOAL := help

.PHONY: help dev drafts build clean deploy logbuch bastelstube page wiki hoerbuecher open

help:
	@echo "Verfügbare Befehle:"
	@echo "  make dev            Dev-Server starten"
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
	$(HUGO) server -D -F -p $(PORT) $(DEV_FLAGS)

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
