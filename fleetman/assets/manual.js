/* Fleetman — filtr kart, lightbox zrzutów i menu mobilne. */
(function () {
  // --- Menu mobilne ---
  var toggle = document.querySelector('.navtoggle');
  var aside = document.querySelector('aside');
  if (toggle && aside) {
    toggle.addEventListener('click', function () { aside.classList.toggle('open'); });
    document.addEventListener('click', function (e) {
      if (aside.classList.contains('open') && !aside.contains(e.target) && e.target !== toggle) aside.classList.remove('open');
    });
  }

  // --- Filtr kart na stronie startowej ---
  var q = document.getElementById('q');
  var cards = [].slice.call(document.querySelectorAll('#cards .card'));
  var empty = document.getElementById('empty');
  if (q && cards.length) {
    q.addEventListener('input', function () {
      var t = q.value.trim().toLowerCase(), n = 0;
      cards.forEach(function (c) {
        var hit = !t || ((c.dataset.name || '') + ' ' + c.textContent).toLowerCase().indexOf(t) !== -1;
        c.style.display = hit ? '' : 'none'; if (hit) n++;
      });
      if (empty) empty.style.display = n ? 'none' : 'block';
    });
  }

  // --- Lightbox dla zrzutów w treści ---
  var imgs = [].slice.call(document.querySelectorAll('figure img'));
  if (!imgs.length) return;
  var lb = document.createElement('div');
  lb.id = 'lb';
  lb.innerHTML = '<button class="close" aria-label="Zamknij">×</button>' +
    '<button class="nav prev" aria-label="Poprzedni">‹</button>' +
    '<img alt=""><div class="cap"></div>' +
    '<button class="nav next" aria-label="Następny">›</button>';
  document.body.appendChild(lb);
  var lbImg = lb.querySelector('img'), lbCap = lb.querySelector('.cap'), idx = 0;
  function cap(el) { var f = el.closest('figure'); var c = f && f.querySelector('figcaption'); return el.getAttribute('alt') || (c ? c.textContent : ''); }
  function show(i) { idx = (i + imgs.length) % imgs.length; lbImg.src = imgs[idx].src; lbImg.alt = imgs[idx].alt; lbCap.textContent = cap(imgs[idx]); lb.classList.add('open'); }
  function close() { lb.classList.remove('open'); }
  imgs.forEach(function (el, i) { el.addEventListener('click', function () { show(i); }); });
  lb.querySelector('.close').addEventListener('click', close);
  lb.querySelector('.prev').addEventListener('click', function (e) { e.stopPropagation(); show(idx - 1); });
  lb.querySelector('.next').addEventListener('click', function (e) { e.stopPropagation(); show(idx + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') show(idx - 1); if (e.key === 'ArrowRight') show(idx + 1);
  });
})();
