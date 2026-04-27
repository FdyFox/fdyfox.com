<?php
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /kontakt/');
    exit;
}

// Honeypot - bots fill hidden fields, humans don't
if (!empty($_POST['website'])) {
    header('Location: /kontakt/?success=1');
    exit;
}

$name    = trim($_POST['name']    ?? '');
$email   = trim($_POST['email']   ?? '');
$message = trim($_POST['message'] ?? '');

if (empty($name) || empty($email) || empty($message)) {
    header('Location: /kontakt/?error=1');
    exit;
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    header('Location: /kontakt/?error=1');
    exit;
}

// Prevent header injection
$name  = str_replace(["\r", "\n"], '', $name);
$email = str_replace(["\r", "\n"], '', $email);

$to      = 'ferdy@ferdyverse.de';
$subject = '[ferdyverse.de] Neue Nachricht von ' . $name;
$body    = "Name:    {$name}\nE-Mail:  {$email}\n\nNachricht:\n{$message}";
$headers = implode("\r\n", [
    'From: noreply@ferdyverse.de',
    'Reply-To: ' . $email,
    'Content-Type: text/plain; charset=UTF-8',
    'X-Mailer: PHP/' . PHP_VERSION,
]);

if (mail($to, $subject, $body, $headers)) {
    header('Location: /kontakt/?success=1');
} else {
    header('Location: /kontakt/?error=1');
}
exit;
