<?php
/*
 * Öffentlicher Kommentar-Endpunkt.
 *
 *   GET  ?section=…&page=…                freigegebene Kommentare als JSON
 *   POST section, page, path, name, …     neuen Kommentar einreichen (landet in der Moderation)
 *   GET  ?action=approve|delete&id&token  Bestätigungsseite für Links aus der Benachrichtigungs-Mail
 *   POST action, id, token                Aktion aus der Mail ausführen
 *
 * Die Mail-Links öffnen bewusst nur eine Bestätigungsseite, damit Mail-Scanner,
 * die Links vorab aufrufen, nichts freigeben oder löschen.
 */
declare(strict_types=1);
require __DIR__ . '/lib.php';

const RATE_LIMIT = 3;  // Kommentare pro RATE_WINDOW und IP

if (config()['cors']) {
    header('Access-Control-Allow-Origin: *');
}

$method = $_SERVER['REQUEST_METHOD'];
$action = $_REQUEST['action'] ?? '';

if ($action === 'approve' || $action === 'delete') {
    moderate_via_mail_link($method, $action);
} elseif ($method === 'GET' && isset($_GET['section'], $_GET['page'])) {
    list_comments((string) $_GET['section'], (string) $_GET['page']);
} elseif ($method === 'POST') {
    submit_comment();
} else {
    header('Location: /');
}
exit;

function list_comments(string $section, string $page): never
{
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    try {
        purge_ip_hashes();
    } catch (PDOException $e) {
        error_log('comment: ' . $e->getMessage());  // Anzeigen soll trotzdem klappen
    }
    $stmt = db()->prepare(
        "SELECT id, parent_id, name, website, comment, created_at AS date FROM comments
         WHERE section = ? AND page = ? AND status = 'approved' ORDER BY created_at, id"
    );
    $stmt->execute([$section, $page]);
    $rows = $stmt->fetchAll();

    $public  = fn(array $c) => ['name' => display_name($c['name']), 'website' => $c['website'],
                                'comment' => $c['comment'], 'date' => $c['date']];
    $replies = [];
    foreach ($rows as $c) {
        if ($c['parent_id'] !== null) {
            $replies[$c['parent_id']][] = $public($c);
        }
    }
    // Antworten hängen am Kommentar: Ist er verborgen, erscheinen auch sie nicht
    $comments = [];
    foreach ($rows as $c) {
        if ($c['parent_id'] === null) {
            $comments[] = $public($c) + ['replies' => $replies[$c['id']] ?? []];
        }
    }
    echo json_encode(['comments' => $comments], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function submit_comment(): never
{
    $wantsJson = str_contains($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json');
    $path      = preg_match('#^/[A-Za-z0-9/_\-]*$#', $_POST['path'] ?? '') ? $_POST['path'] : '/';

    $respond = function (bool $ok, string $message, int $status = 200) use ($wantsJson, $path): never {
        if ($wantsJson) {
            http_response_code($status);
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(['success' => $ok, 'message' => $message], JSON_UNESCAPED_UNICODE);
        } else {
            // Ohne JavaScript: zurück zum Beitrag, Meldung per CSS :target
            header('Location: ' . $path . ($ok ? '#kommentar-danke' : '#kommentar-fehler'), true, 303);
        }
        exit;
    };

    // Honeypot: Bots füllen versteckte Felder aus, Menschen nicht
    if (!empty($_POST['fax'])) {
        $respond(true, 'Danke!');
    }

    $section = (string) ($_POST['section'] ?? '');
    $page    = (string) ($_POST['page'] ?? '');
    if (!in_array($section, ALLOWED_SECTIONS, true) || !preg_match('/^[A-Za-z0-9][A-Za-z0-9_\-]{0,99}$/', $page)) {
        $respond(false, 'Unbekannter Beitrag.', 400);
    }
    $fields = clean_fields($_POST);
    if (is_string($fields)) {
        $respond(false, $fields, 400);
    }

    try {
        $db     = db();
        $ipHash = ip_hash();
        $since  = date('c', time() - RATE_WINDOW);
        purge_ip_hashes();
        $stmt = $db->prepare('SELECT COUNT(*) FROM comments WHERE ip_hash = ? AND created_at > ?');
        $stmt->execute([$ipHash, $since]);
        if ((int) $stmt->fetchColumn() >= RATE_LIMIT) {
            $respond(false, 'Das waren gerade ziemlich viele Kommentare. Versuch es in ein paar Minuten nochmal.', 429);
        }

        $token = bin2hex(random_bytes(16));
        $db->prepare(
            'INSERT INTO comments (section, page, path, name, email, website, comment, token, ip_hash, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )->execute([$section, $page, $path, $fields['name'], $fields['email'], $fields['website'],
                    $fields['comment'], $token, $ipHash, date('c')]);
        $id = (int) $db->lastInsertId();
    } catch (PDOException $e) {
        error_log('comment: ' . $e->getMessage());
        $respond(false, 'Beim Speichern ist etwas schiefgelaufen. Versuch es später nochmal.', 500);
    }

    notify($id, $token, $path, $fields);
    $respond(true, 'Danke! Dein Kommentar ist angekommen und erscheint, sobald ich ihn freigeschaltet habe.');
}

function notify(int $id, string $token, string $path, array $f): void
{
    $base = config()['site_url'];
    $link = fn(string $action) => "$base/kommentare/api.php?action=$action&id=$id&token=$token";
    $body = 'Beitrag: ' . $base . $path . "\n"
          . 'Name:    ' . display_name($f['name']) . "\n"
          . ($f['email'] !== '' ? "E-Mail:  {$f['email']}\n" : '')
          . ($f['website'] !== '' ? "Website: {$f['website']}\n" : '')
          . "\n" . $f['comment'] . "\n\n"
          . 'Freigeben: ' . $link('approve') . "\n"
          . 'Löschen:   ' . $link('delete') . "\n"
          . "Verwalten: $base/kommentare/admin.php\n";
    send_mail('[fdyfox.com] Neuer Kommentar von ' . display_name($f['name']), $body);
}

function moderate_via_mail_link(string $method, string $action): never
{
    $id    = (int) ($_REQUEST['id'] ?? 0);
    $token = (string) ($_REQUEST['token'] ?? '');
    $stmt  = db()->prepare('SELECT * FROM comments WHERE id = ?');
    $stmt->execute([$id]);
    $c = $stmt->fetch();

    if (!$c || !hash_equals($c['token'], $token)) {
        page('Nicht gefunden', '<p>Diesen Kommentar gibt es nicht (mehr), oder der Link ist ungültig.</p>'
            . '<p><a href="admin.php">Alle Kommentare</a></p>');
    }

    $post = h(config()['site_url'] . $c['path']) . '#kommentare';

    if ($method === 'POST') {
        if ($action === 'approve') {
            db()->prepare("UPDATE comments SET status = 'approved' WHERE id = ?")->execute([$id]);
            page('Freigegeben', "<p>Der Kommentar ist jetzt online.</p><p><a href=\"$post\">Zum Beitrag</a> · <a href=\"admin.php\">Alle Kommentare</a></p>");
        }
        delete_comment($id);
        page('Gelöscht', '<p>Der Kommentar wurde gelöscht.</p><p><a href="admin.php">Alle Kommentare</a></p>');
    }

    $label = $action === 'approve' ? 'Freigeben' : 'Löschen';
    $note  = $c['status'] === 'approved' && $action === 'approve'
        ? '<p class="muted">Dieser Kommentar ist bereits freigegeben.</p>' : '';
    page("Kommentar " . strtolower($label) . "?", $note
        . '<div class="comment"><div class="meta"><strong>' . h(display_name($c['name'])) . '</strong> · '
        . h(date('d.m.Y, H:i', strtotime($c['created_at']))) . " · <a href=\"$post\">Beitrag</a></div>"
        . '<div>' . nl2br(h($c['comment'])) . '</div></div>'
        . '<form method="post"><input type="hidden" name="action" value="' . h($action) . '">'
        . '<input type="hidden" name="id" value="' . $id . '"><input type="hidden" name="token" value="' . h($token) . '">'
        . '<button class="' . ($action === 'delete' ? 'danger' : '') . '">' . $label . '</button></form>');
}

function page(string $title, string $html): never
{
    header('Content-Type: text/html; charset=utf-8');
    header('X-Robots-Tag: noindex');
    $title = h($title);
    echo <<<HTML
        <!DOCTYPE html>
        <html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="robots" content="noindex"><title>$title · fdyfox.com</title>
        <style>
          body { background:#1e1e2e; color:#cdd6f4; font:16px/1.6 system-ui, sans-serif; max-width:640px; margin:3rem auto; padding:0 1rem; }
          h1 { font-size:1.4rem; } a { color:#89b4fa; } .muted { color:#a6adc8; }
          .comment { background:#313244; border-left:3px solid #89b4fa; border-radius:8px; padding:.8rem 1rem; margin:1rem 0; }
          .meta { color:#a6adc8; font-size:.85rem; margin-bottom:.4rem; }
          button { background:#89b4fa; color:#1e1e2e; border:0; border-radius:8px; padding:.5rem 1.4rem; font-weight:bold; cursor:pointer; }
          button.danger { background:#f38ba8; }
        </style></head>
        <body><h1>$title</h1>$html</body></html>
        HTML;
    exit;
}
