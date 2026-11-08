<?php
/*
 * Füllt die lokale Dev-Datenbank mit Dummy-Kommentaren (make kommentare-seed).
 * Löscht vorher alle vorhandenen Kommentare - nur für die Entwicklung gedacht!
 */
declare(strict_types=1);

if (!getenv('COMMENTS_CONFIG')) {
    fwrite(STDERR, "COMMENTS_CONFIG nicht gesetzt - bitte über 'make kommentare-seed' starten.\n");
    exit(1);
}
// Im Dev-Container liegt static/ unter /app (Arbeitsverzeichnis)
require getcwd() . '/kommentare/lib.php';

$dummies = [
    // section, page, name, email, website, comment, status, created_at
    ['logbuch', '2026-11-05', 'Sabine', 'sabine@example.org', 'https://example.org',
     "Danke für den Hinweis zur Brotli-Lücke! Das Ansible-Skript würde mich auch interessieren.\n\nMagst du das irgendwann mal in die Bastelstube packen?",
     'approved', '2026-11-05T22:10:00+01:00'],
    ['logbuch', '2026-11-05', '', '', '',
     'Bei uns war zum Glück nichts betroffen. Gut, dass du so schnell reagiert hast.',
     'approved', '2026-11-06T07:15:00+01:00'],
    ['logbuch', '2026-11-05', 'Spambot 3000', 'win@example.com', 'https://example.com/casino',
     'Super Beitrag!!! Besuchen Sie meine Seite für tolle Angebote.',
     'pending', '2026-11-06T10:02:00+01:00'],
    ['bastelstube', 'win11-und-fido2', 'Tobi', 'tobi@example.net', '',
     'Hat bei mir mit einem YubiKey 5 auf Anhieb funktioniert. Super Anleitung!',
     'approved', '2026-11-04T18:00:00+01:00'],
    ['logbuch', 'analog-vs-digital', 'Mara', '', 'https://mara.example',
     'Ich bin auch wieder zurück zum Papier-Notizbuch. Kann ich nur empfehlen.',
     'approved', '2026-11-02T12:00:00+01:00'],
    ['logbuch', '2026-11-06', 'Jens', 'jens@example.org', '',
     "Schöner Eintrag! Eine Frage: Welches Tool nutzt du für die Screenshots?",
     'pending', '2026-11-06T12:45:00+01:00'],
];

$db = db();
$db->exec('DELETE FROM comments');
$stmt = $db->prepare(
    'INSERT INTO comments (section, page, path, name, email, website, comment, status, token, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
);
foreach ($dummies as [$section, $page, $name, $email, $website, $comment, $status, $date]) {
    $stmt->execute([$section, $page, "/$section/$page/", $name, $email, $website, $comment, $status,
                    bin2hex(random_bytes(16)), $date]);
}
$parent = (int) $db->query("SELECT id FROM comments WHERE name = 'Sabine'")->fetchColumn();
$db->prepare(
    "INSERT INTO comments (section, page, path, name, comment, status, token, created_at, parent_id)
     VALUES ('logbuch', '2026-11-05', '/logbuch/2026-11-05/', 'Ferdy', ?, 'approved', ?, '2026-11-06T09:30:00+01:00', ?)"
)->execute(["Kommt! Ich räume das Skript noch etwas auf.\nTest mit <b>HTML</b>, das nicht interpretiert werden darf.",
            bin2hex(random_bytes(16)), $parent]);
echo count($dummies) . " Dummy-Kommentare und eine Antwort angelegt.\n";
