<?php
/*
 * Kommentar-Verwaltung: Login mit dem Passwort aus config.php,
 * dann freigeben, verbergen, bearbeiten und löschen.
 */
declare(strict_types=1);
require __DIR__ . '/lib.php';

header('X-Robots-Tag: noindex');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');

const LOGIN_MAX_FAILURES = 5;     // Fehlversuche ...
const LOGIN_WINDOW       = 900;   // ... pro 15 Minuten und IP
const SESSION_IDLE       = 7200;  // nach 2 Stunden Inaktivität abmelden

session_name('fdyfox_admin');
session_set_cookie_params(['httponly' => true, 'samesite' => 'Strict', 'secure' => is_https()]);
session_start();

if (!empty($_SESSION['admin']) && time() - ($_SESSION['seen'] ?? 0) > SESSION_IDLE) {
    $_SESSION = [];
}
$_SESSION['seen'] = time();

$password = (string) config()['admin_password'];
$self     = 'admin.php';
$flash    = $_SESSION['flash'] ?? '';
unset($_SESSION['flash']);

function redirect(string $to, string $flash = ''): never
{
    if ($flash !== '') {
        $_SESSION['flash'] = $flash;
    }
    header('Location: ' . $to, true, 303);
    exit;
}

// --- Login / Logout -------------------------------------------------------

if ($password === '') {
    render('Kommentare', '<p class="muted">Kein Admin-Passwort konfiguriert (<code>COMMENT_ADMIN_PASSWORD</code>).</p>');
}

if (($_POST['do'] ?? '') === 'login') {
    // Sperre nach zu vielen Fehlversuchen pro IP (gilt auch für parallele Anfragen)
    $db    = db();
    $ip    = ip_hash();
    $since = date('c', time() - LOGIN_WINDOW);
    $db->prepare('DELETE FROM login_failures WHERE created_at <= ?')->execute([$since]);
    $stmt = $db->prepare('SELECT COUNT(*) FROM login_failures WHERE ip_hash = ?');
    $stmt->execute([$ip]);

    if ((int) $stmt->fetchColumn() >= LOGIN_MAX_FAILURES) {
        $flash = 'Zu viele Fehlversuche. Bitte in ' . (LOGIN_WINDOW / 60) . ' Minuten nochmal.';
    } elseif (hash_equals($password, (string) ($_POST['password'] ?? ''))) {
        session_regenerate_id(true);
        $_SESSION['admin'] = true;
        $_SESSION['csrf']  = bin2hex(random_bytes(16));
        redirect($self);
    } else {
        $db->prepare('INSERT INTO login_failures (ip_hash, created_at) VALUES (?, ?)')->execute([$ip, date('c')]);
        sleep(1);
        $flash = 'Falsches Passwort.';
    }
}

if (empty($_SESSION['admin'])) {
    render('Anmelden', '<form method="post" class="login">'
        . '<input type="hidden" name="do" value="login">'
        . '<input type="password" name="password" placeholder="Passwort" autofocus required autocomplete="current-password">'
        . '<button>Anmelden</button></form>', $flash);
}

// --- Aktionen ---------------------------------------------------------------

$view = in_array($_GET['status'] ?? '', ['pending', 'approved', 'all'], true) ? $_GET['status'] : 'pending';
$back = "$self?status=$view";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!hash_equals($_SESSION['csrf'] ?? '', (string) ($_POST['csrf'] ?? ''))) {
        redirect($back, 'Sitzung abgelaufen, bitte nochmal.');
    }
    $do = (string) ($_POST['do'] ?? '');
    $id = (int) ($_POST['id'] ?? 0);
    $db = db();

    switch ($do) {
        case 'logout':
            $_SESSION = [];
            session_destroy();
            redirect($self);
        case 'approve':
            $db->prepare("UPDATE comments SET status = 'approved' WHERE id = ?")->execute([$id]);
            redirect($back, 'Kommentar freigegeben.');
        case 'unapprove':
            $db->prepare("UPDATE comments SET status = 'pending' WHERE id = ?")->execute([$id]);
            redirect($back, 'Kommentar verborgen.');
        case 'delete':
            $db->prepare('DELETE FROM comments WHERE id = ?')->execute([$id]);
            redirect($back, 'Kommentar gelöscht.');
        case 'save':
            $fields = clean_fields($_POST);
            if (is_string($fields)) {
                redirect($back, $fields);
            }
            $db->prepare('UPDATE comments SET name = ?, email = ?, website = ?, comment = ? WHERE id = ?')
               ->execute([$fields['name'], $fields['email'], $fields['website'], $fields['comment'], $id]);
            redirect($back . "#c$id", 'Kommentar gespeichert.');
    }
    redirect($back);
}

// --- Liste ------------------------------------------------------------------

$db     = db();
$counts = $db->query("SELECT status, COUNT(*) AS n FROM comments GROUP BY status")->fetchAll(PDO::FETCH_KEY_PAIR);
$counts += ['pending' => 0, 'approved' => 0];
$counts['all'] = $counts['pending'] + $counts['approved'];

$sql = 'SELECT * FROM comments' . ($view === 'all' ? '' : ' WHERE status = :status') . ' ORDER BY created_at DESC, id DESC';
$stmt = $db->prepare($sql);
$stmt->execute($view === 'all' ? [] : ['status' => $view]);
$comments = $stmt->fetchAll();

$csrf = h($_SESSION['csrf']);
$tabs = '';
foreach (['pending' => 'Offen', 'approved' => 'Freigegeben', 'all' => 'Alle'] as $key => $label) {
    $tabs .= '<a href="' . "$self?status=$key" . '"' . ($key === $view ? ' class="active"' : '') . ">$label <span>{$counts[$key]}</span></a>";
}

$button = fn(string $do, int $id, string $label, string $class = '', string $confirm = '') =>
    '<form method="post"' . ($confirm ? ' onsubmit="return confirm(\'' . $confirm . '\')"' : '') . '>'
    . "<input type=\"hidden\" name=\"csrf\" value=\"$csrf\"><input type=\"hidden\" name=\"do\" value=\"$do\">"
    . "<input type=\"hidden\" name=\"id\" value=\"$id\"><button class=\"$class\">$label</button></form>";

$list = '';
foreach ($comments as $c) {
    $id      = (int) $c['id'];
    $pending = $c['status'] === 'pending';
    $post    = h(config()['site_url'] . $c['path']) . '#kommentare';
    $who     = '<strong>' . h(display_name($c['name'])) . '</strong>'
             . ($c['email'] !== '' ? ' · <a href="mailto:' . h($c['email']) . '">' . h($c['email']) . '</a>' : '')
             . ($c['website'] !== '' ? ' · <a href="' . h($c['website']) . '" rel="noopener noreferrer" target="_blank">' . h(preg_replace('#^https?://#', '', $c['website'])) . '</a>' : '');

    $list .= "<article id=\"c$id\" class=\"comment" . ($pending ? ' pending' : '') . '">'
        . '<div class="meta">' . $who . '</div>'
        . '<div class="meta muted">' . h(date('d.m.Y, H:i', strtotime($c['created_at'])))
        . " · <a href=\"$post\" target=\"_blank\">" . h($c['section'] . '/' . $c['page']) . '</a>'
        . ($pending ? ' · <span class="badge">offen</span>' : '') . '</div>'
        . '<div class="text">' . nl2br(h($c['comment'])) . '</div>'
        . '<div class="actions">'
        . ($pending ? $button('approve', $id, 'Freigeben') : $button('unapprove', $id, 'Verbergen', 'secondary'))
        . $button('delete', $id, 'Löschen', 'danger', 'Kommentar wirklich löschen?')
        . '</div>'
        . '<details><summary>Bearbeiten</summary><form method="post" class="edit">'
        . "<input type=\"hidden\" name=\"csrf\" value=\"$csrf\"><input type=\"hidden\" name=\"do\" value=\"save\"><input type=\"hidden\" name=\"id\" value=\"$id\">"
        . '<div class="row"><input name="name" placeholder="Name" value="' . h($c['name']) . '">'
        . '<input name="email" placeholder="E-Mail" value="' . h($c['email']) . '">'
        . '<input name="website" placeholder="Website" value="' . h($c['website']) . '"></div>'
        . '<textarea name="comment" rows="5" required>' . h($c['comment']) . '</textarea>'
        . '<button>Speichern</button></form></details>'
        . '</article>';
}
if ($list === '') {
    $list = '<p class="muted">' . ($view === 'pending' ? 'Nichts zu moderieren. 🎉' : 'Keine Kommentare.') . '</p>';
}

$logout = "<form method=\"post\" class=\"logout\"><input type=\"hidden\" name=\"csrf\" value=\"$csrf\">"
        . '<input type="hidden" name="do" value="logout"><button class="link">Abmelden</button></form>';

render('Kommentare', "<nav class=\"tabs\">$tabs</nav>$list", $flash, $logout);

// --- Layout -----------------------------------------------------------------

function render(string $title, string $body, string $flash = '', string $header = ''): never
{
    header('Content-Type: text/html; charset=utf-8');
    $title = h($title);
    $flash = $flash !== '' ? '<div class="flash">' . h($flash) . '</div>' : '';
    echo <<<HTML
        <!DOCTYPE html>
        <html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="robots" content="noindex"><title>$title · fdyfox.com</title>
        <style>
          :root { --bg:#1e1e2e; --entry:#313244; --text:#cdd6f4; --muted:#a6adc8; --border:#45475a;
                  --accent:#89b4fa; --accent2:#cba6f7; --green:#a6e3a1; --red:#f38ba8; --yellow:#f9e2af; }
          * { box-sizing:border-box; }
          body { background:var(--bg); color:var(--text); font:15px/1.6 system-ui, sans-serif; max-width:820px; margin:2rem auto; padding:0 1rem; }
          a { color:var(--accent); } a:hover { color:var(--accent2); }
          header { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1rem; }
          h1 { font-size:1.4rem; margin:0; } h1 small { color:var(--muted); font-weight:normal; font-size:.9rem; }
          .muted { color:var(--muted); }
          .tabs { display:flex; gap:.4rem; margin-bottom:1.2rem; border-bottom:1px solid var(--border); }
          .tabs a { padding:.4rem .9rem; text-decoration:none; color:var(--muted); border-bottom:2px solid transparent; }
          .tabs a.active { color:var(--text); border-color:var(--accent); }
          .tabs span { background:var(--entry); border-radius:99px; padding:0 .5rem; font-size:.8rem; }
          .flash { background:color-mix(in srgb, var(--green) 15%, var(--entry)); border-left:4px solid var(--green); border-radius:8px; padding:.6rem 1rem; margin-bottom:1rem; }
          .comment { background:var(--entry); border-left:3px solid var(--accent); border-radius:8px; padding:.8rem 1rem; margin-bottom:1rem; }
          .comment.pending { border-color:var(--yellow); }
          .meta { font-size:.9rem; } .meta.muted { font-size:.8rem; margin-bottom:.5rem; }
          .badge { color:var(--bg); background:var(--yellow); border-radius:4px; padding:0 .4rem; font-size:.75rem; font-weight:bold; }
          .text { overflow-wrap:anywhere; }
          .actions { display:flex; gap:.5rem; margin-top:.7rem; }
          form { margin:0; }
          button { background:var(--accent); color:var(--bg); border:0; border-radius:8px; padding:.35rem 1rem; font:inherit; font-weight:bold; cursor:pointer; }
          button:hover { background:var(--accent2); }
          button.secondary { background:var(--border); color:var(--text); }
          button.danger { background:var(--red); }
          button.link { background:none; color:var(--accent); padding:0; font-weight:normal; }
          details { margin-top:.6rem; } summary { cursor:pointer; color:var(--muted); font-size:.85rem; }
          input, textarea { width:100%; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:8px; padding:.45rem .7rem; font:inherit; }
          input:focus, textarea:focus { outline:none; border-color:var(--accent); }
          .edit { display:flex; flex-direction:column; gap:.5rem; margin-top:.5rem; align-items:flex-start; }
          .edit .row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:.5rem; width:100%; }
          @media (max-width:640px) { .edit .row { grid-template-columns:1fr; } }
          .login { display:flex; gap:.5rem; max-width:360px; }
        </style></head>
        <body><header><h1>$title <small>fdyfox.com</small></h1>$header</header>$flash$body</body></html>
        HTML;
    exit;
}
