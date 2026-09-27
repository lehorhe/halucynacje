/* intro.js — HALUCYNACJE: sceny intro jedna po drugiej (czas w data-czas), sterowanie strzałkami/spacją, pominięcie do planszy tytułowej.
   Bez innerHTML z danych; bez stylów w atrybutach HTML (CSP) — pozycje nadawane przez CSSOM. */
(function () {
  var sc = [].slice.call(document.querySelectorAll('.scena'));
  var i = -1, t = null, pauza = false, start = 0, dlug = 0, raf = null;
  var postep = document.getElementById('postep'), bPauza = document.getElementById('pauza');
  var ruch = !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  function pasek() {
    if (!dlug) { postep.style.width = '100%'; return; }
    var p = Math.min(1, (Date.now() - start) / dlug);
    postep.style.width = ((i + p) / (sc.length - 1) * 100).toFixed(2) + '%';
    if (!pauza) raf = requestAnimationFrame(pasek);
  }
  function idz(n) {
    n = Math.max(0, Math.min(sc.length - 1, n));
    clearTimeout(t); cancelAnimationFrame(raf);
    if (i >= 0) sc[i].classList.remove('jest');
    i = n;
    void sc[i].offsetWidth;                                   // restart animacji CSS w scenie
    sc[i].classList.add('jest');
    dlug = +sc[i].getAttribute('data-czas') || 0;
    start = Date.now();
    if (dlug && !pauza) t = setTimeout(function () { idz(i + 1); }, dlug);
    pasek();
    document.body.classList.toggle('koniec', i === sc.length - 1);
  }
  document.getElementById('dalej').onclick = function () { idz(i + 1); };
  document.getElementById('wstecz').onclick = function () { idz(i - 1); };
  document.getElementById('pomin').onclick = function () { idz(sc.length - 1); };
  document.getElementById('znowu').onclick = function () { idz(0); };
  bPauza.onclick = function () {
    pauza = !pauza; bPauza.textContent = pauza ? '▶' : '❚❚'; bPauza.setAttribute('aria-label', pauza ? 'Wznów' : 'Pauza');
    if (pauza) { clearTimeout(t); cancelAnimationFrame(raf); } else idz(i);
  };
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') idz(i + 1); else if (e.key === 'ArrowLeft') idz(i - 1);
    else if (e.key === ' ') { e.preventDefault(); bPauza.click(); } else if (e.key === 'Escape') idz(sc.length - 1);
  });

  // syntetyczni koledzy: siatka świateł (zielone = Kolonia, niebieskie = Chmura)
  var m = document.querySelector('.maszyny');
  for (var k = 0; k < 48; k++) {
    var el = document.createElement('i');
    if (k % 3 === 2) el.className = 'c';
    el.style.animationDelay = (-Math.random() * 2.4).toFixed(2) + 's';
    m.appendChild(el);
  }
  // strumień słów: „halucynacja” we wszystkich językach (Wikidane) — płynie jak antena
  var st = document.getElementById('strumien'), napis = document.getElementById('slowo');
  fetch('/api/slowa').then(function (r) { return r.json(); }).then(function (d) {
    var s = (d.slowa || []).map(function (x) { return x.slowo; });
    for (var n = 0; n < 34 && s.length; n++) {
      var sp = document.createElement('span');
      sp.textContent = s[n % s.length];
      sp.style.top = (Math.random() * 90).toFixed(1) + '%';
      sp.style.fontSize = (14 + Math.random() * 20).toFixed(0) + 'px';
      sp.style.opacity = (.35 + Math.random() * .6).toFixed(2);
      sp.style.animationDuration = (9 + Math.random() * 12).toFixed(1) + 's';
      sp.style.animationDelay = (-Math.random() * 20).toFixed(1) + 's';
      st.appendChild(sp);
    }
    if (s.length && ruch) {
      var j = 0;
      setInterval(function () {
        napis.style.opacity = 0;
        setTimeout(function () { j = (j + 1) % s.length; napis.textContent = s[j]; napis.style.opacity = 1; }, 400);
      }, 1700);
    }
  }).catch(function () {});
  idz(0);
})();
