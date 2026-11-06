<?php
/*
 * Gemeinsamer Code für api.php (öffentliche API) und admin.php.
 *
 * Kommentare liegen in einer SQLite-Datei in daten/ neben den Skripten.
 * Der Ordner wird beim Deploy per lftp --exclude in Ruhe gelassen und ist per
 * .htaccess gesperrt.
 *
 * Konfiguration: config.php (beim Deploy erzeugt, enthält das
 * Admin-Passwort). Lokal zeigt COMMENT_CONFIG auf eine Dev-Konfiguration.
 */
declare(strict_types=1);

if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    http_response_code(404);
    exit;
}

// Einheitliche Zeitzone, damit created_at (ISO 8601) als Text sortier- und vergleichbar bleibt
date_default_timezone_set('Europe/Berlin');

const ALLOWED_SECTIONS = ['logbuch', 'bastelstube'];
const MAX_NAME    = 80;
const MAX_EMAIL   = 200;
const MAX_WEBSITE = 200;
const MAX_COMMENT = 5000;

function config(): array
{
    static $config = null;
    if ($config === null) {
        $file   = getenv('COMMENT_CONFIG') ?: __DIR__ . '/config.php';
        $config = (is_file($file) ? require $file : []) + [
            'admin_password' => '',
            'data_dir'       => __DIR__ . '/daten',
            'mail_to'        => 'ferdy@fdyfox.com',
            'mail_from'      => 'noreply@fdyfox.com',
            'site_url'       => 'https://fdyfox.com',
            'cors'           => false,   // nur lokal: Hugo-Dev-Server läuft auf anderem Port
        ];
    }
    return $config;
}

function db(): PDO
{
    static $db = null;
    if ($db !== null) {
        return $db;
    }
    $dir = config()['data_dir'];
    if (!is_dir($dir)) {
        mkdir($dir, 0700, true);
    }
    if (!is_file("$dir/.htaccess")) {
        file_put_contents("$dir/.htaccess", "Require all denied\n");
    }
    $db = new PDO('sqlite:' . $dir . '/kommentare.sqlite', null, null, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $db->exec('PRAGMA busy_timeout = 5000');
    // Gelöschte Kommentare wirklich überschreiben statt nur als frei markieren
    $db->exec('PRAGMA secure_delete = ON');
    $db->exec(<<<'SQL'
        CREATE TABLE IF NOT EXISTS comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            section    TEXT NOT NULL,
            page       TEXT NOT NULL,
            path       TEXT NOT NULL,
            name       TEXT NOT NULL DEFAULT '',
            email      TEXT NOT NULL DEFAULT '',
            website    TEXT NOT NULL DEFAULT '',
            comment    TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'pending',  -- pending | approved
            token      TEXT NOT NULL,                     -- für Freigabe-Links in der Mail
            ip_hash    TEXT NOT NULL DEFAULT '',          -- nur fürs Rate-Limit
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS comments_page ON comments (section, page, status);
        CREATE TABLE IF NOT EXISTS login_failures (
            ip_hash    TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        SQL);
    return $db;
}

/**
 * Hash der Besucher-IP fürs Rate-Limit (die IP selbst wird nie gespeichert).
 * Mit eingerechnet wird ein geheimer Zufallswert (daten/salt), der nur auf dem
 * Server liegt. Wer nur die Datenbank hat, kann deshalb nicht alle möglichen IPs
 * durchprobieren, um die IP hinter einem Hash herauszufinden.
 */
function ip_hash(): string
{
    $file = config()['data_dir'] . '/salt';
    if (!is_file($file)) {
        db();  // legt das Datenverzeichnis samt .htaccess an
        file_put_contents($file, bin2hex(random_bytes(32)), LOCK_EX);
        chmod($file, 0600);
    }
    return hash_hmac('sha256', $_SERVER['REMOTE_ADDR'] ?? '', trim(file_get_contents($file)));
}

function h(?string $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function display_name(string $name): string
{
    return $name !== '' ? $name : 'Anonym';
}

function is_https(): bool
{
    return ($_SERVER['HTTPS'] ?? '') === 'on' || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
}

/**
 * Prüft und normalisiert Name, E-Mail, Website und Kommentar.
 * Gibt die bereinigten Felder zurück oder einen Fehlertext.
 */
function clean_fields(array $in): array|string
{
    $name    = preg_replace('/\s+/u', ' ', trim((string) ($in['name'] ?? '')));
    $email   = trim((string) ($in['email'] ?? ''));
    $website = trim((string) ($in['website'] ?? ''));
    $comment = trim(str_replace("\r\n", "\n", (string) ($in['comment'] ?? '')));

    if ($comment === '') {
        return 'Der Kommentar ist leer.';
    }
    if (mb_strlen($comment) > MAX_COMMENT) {
        return 'Der Kommentar ist zu lang (maximal ' . MAX_COMMENT . ' Zeichen).';
    }
    if (mb_strlen($name) > MAX_NAME) {
        return 'Der Name ist zu lang.';
    }
    if ($email !== '' && (mb_strlen($email) > MAX_EMAIL || !filter_var($email, FILTER_VALIDATE_EMAIL))) {
        return 'Die E-Mail-Adresse sieht nicht gültig aus.';
    }
    if ($website !== '') {
        if (!preg_match('#^https?://#i', $website)) {
            $website = 'https://' . $website;
        }
        if (mb_strlen($website) > MAX_WEBSITE || !filter_var($website, FILTER_VALIDATE_URL)) {
            return 'Die Website-Adresse sieht nicht gültig aus.';
        }
    }
    return compact('name', 'email', 'website', 'comment');
}

function send_mail(string $subject, string $body): bool
{
    $c       = config();
    $headers = implode("\r\n", [
        'From: ' . $c['mail_from'],
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
    ]);
    $ok = @mail($c['mail_to'], '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $headers);
    if (!$ok) {
        error_log('comment: Mailversand fehlgeschlagen: ' . $subject);
    }
    return $ok;
}
