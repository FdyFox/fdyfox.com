#!/bin/bash
# Schreibt die Kommentar-Konfiguration für den Deploy. Auf den Server kommt nur
# der Hash des Admin-Passworts. Aufruf: COMMENT_ADMIN_PASSWORD=… kommentare-config.sh <zieldatei>
#
# data_dir_protected: daten/ liegt im Webroot, ist hier aber per .htaccess gesperrt (von außen 403).
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
hash=$(COMMENTS_ADMIN_PASSWORD="$COMMENT_ADMIN_PASSWORD" "$root/themes/hugo-php-comments/scripts/hash-password.sh")

cat > "$1" <<EOF
<?php
return [
    'admin_password_hash' => '$hash',
    'author_name'         => 'Ferdy',
    'site_url'            => 'https://fdyfox.com',
    'mail_to'             => 'ferdy@fdyfox.com',
    'mail_from'           => 'noreply@fdyfox.com',
    'allowed_sections'    => ['logbuch', 'bastelstube'],
    'language'            => 'de',
    'timezone'            => 'Europe/Berlin',
    'date_format'         => 'd.m.Y, H:i',
    'data_dir'            => __DIR__ . '/daten',
    'db_file'             => 'kommentare.sqlite',
    'data_dir_protected'  => true,
    'admin_css'           => ':root { --bg:#1e1e2e; --entry:#313244; --text:#cdd6f4; --muted:#a6adc8; --border:#45475a; --accent:#89b4fa; --accent2:#cba6f7; --on-accent:#1e1e2e; --green:#a6e3a1; --red:#f38ba8; --yellow:#f9e2af; }',
];
EOF
