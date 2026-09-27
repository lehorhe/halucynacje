/* Języki · Świat anteny — lista bezpłatnych PDF z manifestu (/api/pliki). Bez innerHTML: dane idą przez textContent. */
(function () {
  var cel = document.getElementById("pliki");
  if (!cel) return;
  var pelne = cel.getAttribute("data-pelne") === "1";
  var GRUPY = [["start", "Na start — domowa drukarka A4"], ["plansza", "Duże plansze na kartkach A4 (sklej, skala 1:1)"], ["drukarnia", "Do drukarni lub plotera"], ["3d", "Świat 3D — Blender, Unreal Engine, Unity, Godot"]];
  function el(tag, klasa, tekst) { var e = document.createElement(tag); if (klasa) e.className = klasa; if (tekst) e.textContent = tekst; return e; }
  function strony(n) { return n + (n === 1 ? " strona" : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? " strony" : " stron")); }
  fetch("/api/pliki").then(function (r) { return r.json(); }).then(function (m) {
    var pl = (m && m.pliki) || [];
    if (!pl.length) { cel.appendChild(el("p", "uwaga", "Pliki do pobrania są właśnie przygotowywane — zajrzyj za chwilę.")); return; }
    GRUPY.forEach(function (g) {
      var w = pl.filter(function (p) { return p.grupa === g[0]; });
      if (!w.length || (!pelne && g[0] !== "start")) return;
      cel.appendChild(el("h3", "", g[1]));
      w.forEach(function (p) {
        var r = el("div", "plik"), t = el("div");
        t.appendChild(el("div", "t", p.tytul));
        t.appendChild(el("div", "o", p.opis));
        t.appendChild(el("div", "m", (p.typ || "PDF") + " · " + p.format + (p.strony ? " · " + strony(p.strony) : "") + " · " + p.rozmiar));
        var a = el("a", "", "Pobierz");
        a.href = "/pobierz/" + encodeURIComponent(p.plik);
        a.setAttribute("download", p.plik);
        a.setAttribute("aria-label", "Pobierz: " + p.tytul + " (" + p.format + ", " + p.rozmiar + ")");
        r.appendChild(t); r.appendChild(a); cel.appendChild(r);
      });
    });
    cel.appendChild(el("p", "uwaga", "Wersja robocza " + (m.wersja || "") + " z " + (m.data || "") + " · bezpłatnie do gry w domu, w szkole i w redakcji · drukuj w skali 100%."));
  }).catch(function () { cel.appendChild(el("p", "uwaga", "Nie udało się wczytać listy plików.")); });
})();
