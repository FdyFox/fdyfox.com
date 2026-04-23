#!/bin/bash
set -e

if [ ! -f .env ]; then
  echo "Fehler: .env nicht gefunden. Kopiere .env.example nach .env und fülle die Werte aus."
  exit 1
fi

source .env

echo "→ Seite wird gebaut..."
hugo --minify

echo "→ Upload via FTP..."
lftp -c "
  set ftp:ssl-allow no;
  open ftp://$FTP_USER:$FTP_PASS@$FTP_HOST;
  mirror --reverse --delete --verbose public/ $FTP_PATH
"

echo "✓ Deploy abgeschlossen."
