#!/bin/bash
set -e

if [ ! -f .env ]; then
  echo "Fehler: .env nicht gefunden. Kopiere .env.example nach .env und fülle die Werte aus."
  exit 1
fi

source .env

echo "→ Seite wird gebaut..."
hugo --minify

if [ -n "$COMMENT_ADMIN_PASSWORD" ]; then
  printf "<?php\nreturn ['admin_password' => base64_decode('%s')];\n" \
    "$(printf '%s' "$COMMENT_ADMIN_PASSWORD" | base64 -w0)" > public/kommentare/config.php
else
  echo "⚠ COMMENT_ADMIN_PASSWORD fehlt in .env, die Kommentar-Verwaltung wird deaktiviert"
fi

echo "→ Upload via FTP..."
lftp -c "
  set ftp:ssl-force true; set ftp:ssl-protect-data true; set ssl:verify-certificate yes;
  open ftp://$FTP_USER:$FTP_PASS@$FTP_HOST;
  mirror --reverse --delete --exclude ^kommentare/daten/ --parallel=8 --verbose public/ $FTP_PATH
"

echo "✓ Deploy abgeschlossen."
