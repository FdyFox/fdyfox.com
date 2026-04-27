---
title: "Kontakt"
layout: "kontakt"
---

Du hast eine Frage, einen Fehler gefunden oder willst einfach Hallo sagen? Schreib mir - ich freue mich über Nachrichten.

---

<div id="msg-success" class="callout callout-tip" style="display:none">
  <div class="callout-title"><span class="callout-icon">💡</span> Nachricht gesendet</div>
  <div class="callout-content"><p>Danke! Ich melde mich so schnell wie möglich.</p></div>
</div>

<div id="msg-error" class="callout callout-caution" style="display:none">
  <div class="callout-title"><span class="callout-icon">🔥</span> Fehler</div>
  <div class="callout-content"><p>Etwas ist schiefgelaufen. Versuch es erneut oder schreib mir direkt an <a href="mailto:ferdy@ferdyverse.de">ferdy@ferdyverse.de</a>.</p></div>
</div>

<form class="contact-form" action="/contact.php" method="POST">
  <div class="form-group">
    <label for="name">Name</label>
    <input type="text" id="name" name="name" required autocomplete="name">
  </div>
  <div class="form-group">
    <label for="email">E-Mail</label>
    <input type="email" id="email" name="email" required autocomplete="email">
  </div>
  <div class="form-group">
    <label for="message">Nachricht</label>
    <textarea id="message" name="message" rows="6" required></textarea>
  </div>
  <div style="display:none" aria-hidden="true">
    <input type="text" name="website" tabindex="-1" autocomplete="off">
  </div>
  <button type="submit" class="contact-submit">Absenden</button>
</form>

<script>
  const p = new URLSearchParams(window.location.search);
  if (p.get('success')) document.getElementById('msg-success').style.display = 'block';
  if (p.get('error'))   document.getElementById('msg-error').style.display = 'block';
</script>
