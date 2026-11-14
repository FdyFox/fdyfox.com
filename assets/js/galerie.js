// Galerie für den Hugo-Shortcode "galerie" (layouts/shortcodes/galerie.html):
// Bühne mit Vorschauleiste und Vollbildansicht. Wird pro Galerie eingebunden,
// läuft aber nur einmal pro Seite.
(function () {
  if (window.galerieReady) return;
  window.galerieReady = true;

  function init() {
    // Vollbildansicht, einmal pro Seite
    const box = document.createElement('dialog');
    box.className = 'galerie-lightbox';
    box.setAttribute('aria-label', 'Bild in groß');
    box.innerHTML =
      '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button type="button" class="galerie-close" aria-label="Schließen">×</button>' +
      '<button type="button" class="galerie-prev" aria-label="Vorheriges Bild"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></button>' +
      '<button type="button" class="galerie-next" aria-label="Nächstes Bild"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></button>' +
      '<span class="galerie-count"></span>';
    document.body.appendChild(box);

    const img = box.querySelector('img');
    const cap = box.querySelector('figcaption');
    const count = box.querySelector('.galerie-count');
    let links = [], index = 0, onClose = null;

    function show(i) {
      index = (i + links.length) % links.length;
      const a = links[index];
      img.src = a.href;
      img.alt = a.dataset.caption || '';
      cap.textContent = a.dataset.caption || '';
      count.textContent = links.length > 1 ? (index + 1) + ' / ' + links.length : '';
      box.classList.toggle('galerie-single', links.length < 2);
    }

    function open(list, i, closeHandler) {
      links = list;
      onClose = closeHandler || null;
      show(i);
      box.showModal();
    }

    box.querySelector('.galerie-close').addEventListener('click', function () { box.close(); });
    box.querySelector('.galerie-prev').addEventListener('click', function () { show(index - 1); });
    box.querySelector('.galerie-next').addEventListener('click', function () { show(index + 1); });
    // Klick neben das Bild schließt
    box.addEventListener('click', function (e) { if (e.target === box) box.close(); });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') show(index - 1);
      if (e.key === 'ArrowRight') show(index + 1);
    });
    swipe(box, function (dir) { show(index + dir); });
    box.addEventListener('close', function () {
      img.removeAttribute('src');
      if (onClose) onClose(index);
    });

    document.querySelectorAll('.galerie').forEach(function (g) {
      if (g.classList.contains('galerie-buehne')) stage(g, open);
      else grid(g, open);
    });
  }

  // Raster: jedes Vorschaubild öffnet die Vollbildansicht
  function grid(g, open) {
    const own = Array.from(g.querySelectorAll('a'));
    own.forEach(function (a, i) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        open(own, i);
      });
    });
  }

  // Bühne: Vorschaubilder wechseln das große Bild, Klick darauf öffnet die Vollbildansicht
  function stage(g, open) {
    const thumbs = Array.from(g.querySelectorAll('.galerie-strip a'));
    const strip = g.querySelector('.galerie-strip');
    const link = g.querySelector('.galerie-stage-link');
    const stageImg = link.querySelector('img');
    const caption = g.querySelector('.galerie-stage-caption');
    const counter = g.querySelector('.galerie-stage-count');
    let current = 0;

    function select(i) {
      current = (i + thumbs.length) % thumbs.length;
      const a = thumbs[current];
      stageImg.src = a.dataset.stage;
      stageImg.alt = a.dataset.caption || '';
      link.href = a.href;
      caption.textContent = a.dataset.caption || '';
      counter.textContent = (current + 1) + ' / ' + thumbs.length;
      thumbs.forEach(function (t) { t.removeAttribute('aria-current'); });
      a.setAttribute('aria-current', 'true');
      // aktives Vorschaubild in der Leiste mittig halten, ohne die Seite zu scrollen
      strip.scrollTo({ left: a.offsetLeft - (strip.clientWidth - a.offsetWidth) / 2, behavior: 'smooth' });
    }

    thumbs.forEach(function (a, i) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        select(i);
      });
    });
    link.addEventListener('click', function (e) {
      e.preventDefault();
      open(thumbs, current, select);
    });
    g.querySelectorAll('.galerie-step').forEach(function (b) {
      b.hidden = false;
      b.addEventListener('click', function () {
        select(current + (b.classList.contains('galerie-step-next') ? 1 : -1));
      });
    });
    swipe(link, function (dir) { select(current + dir); });
  }

  // Wischen auf dem Handy: dir = 1 (nächstes) oder -1 (vorheriges)
  function swipe(el, step) {
    let startX = null;
    el.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    el.addEventListener('touchend', function (e) {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
      startX = null;
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
