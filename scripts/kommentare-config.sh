#!/bin/bash
# Schreibt die Kommentar-Konfiguration für den Deploy. Auf den Server kommt nur
# der Hash des Admin-Passworts. Aufruf: COMMENT_ADMIN_PASSWORD=… kommentare-config.sh <zieldatei>
set -euo pipefail

export COMMENT_ADMIN_PASSWORD
hash=$(docker run --rm -e COMMENT_ADMIN_PASSWORD php:8.5-cli \
  php -r 'echo password_hash(getenv("COMMENT_ADMIN_PASSWORD"), PASSWORD_DEFAULT);')

if [[ $hash != \$2y\$* ]]; then
  echo "Fehler: Passwort-Hash konnte nicht erzeugt werden." >&2
  exit 1
fi

printf "<?php\nreturn ['admin_password_hash' => '%s'];\n" "$hash" > "$1"
