// Vollbildansicht für den Hugo-Shortcode "galerie" (layouts/shortcodes/galerie.html).
// Wird pro Galerie eingebunden, läuft aber nur einmal pro Seite.
(function () {
  if (window.galerieReady) return;
  window.galerieReady = true;

  function init() {
    const box = document.createElement('dialog');
    box.className = 'galerie-lightbox';
    box.setAttribute('aria-label', 'Bild in groß');
    box.innerHTML =
      '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button type="button" class="galerie-close" aria-label="Schließen">×</button>' +
      '<button type="button" class="galerie-prev" aria-label="Vorheriges Bild">‹</button>' +
      '<button type="button" class="galerie-next" aria-label="Nächstes Bild">›</button>' +
      '<span class="galerie-count"></span>';
    document.body.appendChild(box);

    const img = box.querySelector('img');
    const cap = box.querySelector('figcaption');
    const count = box.querySelector('.galerie-count');
    let links = [], index = 0;

    function show(i) {
      index = (i + links.length) % links.length;
      const a = links[index];
      img.src = a.href;
      img.alt = a.dataset.caption || '';
      cap.textContent = a.dataset.caption || '';
      count.textContent = links.length > 1 ? (index + 1) + ' / ' + links.length : '';
      box.classList.toggle('galerie-single', links.length < 2);
    }

    // Blättern bleibt innerhalb der jeweiligen Galerie
    document.querySelectorAll('.galerie').forEach(function (g) {
      const own = Array.from(g.querySelectorAll('a'));
      own.forEach(function (a, i) {
        a.addEventListener('click', function (e) {
          e.preventDefault();
          links = own;
          show(i);
          box.showModal();
        });
      });
    });

    box.querySelector('.galerie-close').addEventListener('click', function () { box.close(); });
    box.querySelector('.galerie-prev').addEventListener('click', function () { show(index - 1); });
    box.querySelector('.galerie-next').addEventListener('click', function () { show(index + 1); });
    // Klick neben das Bild schließt
    box.addEventListener('click', function (e) { if (e.target === box) box.close(); });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') show(index - 1);
      if (e.key === 'ArrowRight') show(index + 1);
    });
    // Wischen auf dem Handy
    let startX = null;
    box.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    box.addEventListener('touchend', function (e) {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
      startX = null;
    });
    box.addEventListener('close', function () { img.removeAttribute('src'); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
