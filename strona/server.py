# -*- coding: utf-8 -*-
"""Gra „Halucynacje” (dawniej „Języki”) — meta-gra Szpiega+ (strona dla wszystkich, docelowo gra.l00p.ai). Osobny proces, stdlib, 127.0.0.1.

    python server.py [port]      (domyślnie 8781)

Co robi dziś: nazwa gry „pisze się” po kolei we wszystkich językach (dane/slowa.json, Wikidane CC0 + dopełnienia dostawcy),
animowane logo z ludzkich języków, zapis e-maila „powiadom, gdy świat gry zostanie zresetowany dla nowych graczy”.
Zasady:
  * zapis e-maili jest ZAMKNIĘTY, dopóki nie ma administratora danych i kontaktu IOD (JEZYKI_ADMINISTRATOR, JEZYKI_IOD) — fail-closed;
  * /api/wypisz: wycofanie zgody = usunięcie adresu (ta sama odpowiedź niezależnie od tego, czy adres był na liście);
  * przechowujemy wyłącznie e-mail, czas, wersję klauzuli i pierwszy język przeglądarki; bez IP (limit w pamięci po skrócie IP);
  * /ustawienia (dostawcy tłumaczeń, klucze DeepL/LibreTranslate) wyłącznie operator: pętla zwrotna BEZ nagłówków pośrednika;
  * klucze i zapisy poza gitem: %USERPROFILE%\\szpieg_media\\jezyki\\ (ustawienia.json, zapisy.sqlite3)."""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jezyki import tlumacz as T  # noqa: E402

STATIC = os.path.join(HERE, "static")
DANE = os.path.join(HERE, "dane")
KATALOG = os.environ.get("JEZYKI_DIR") or os.path.join(os.path.expanduser("~"), "szpieg_media", "jezyki")
def pobrania():
    """PDF gry do samodzielnego druku — poza gitem; buduje je Documents/Plansza-warstw/wydanie.py."""
    return os.path.join(KATALOG, "do_pobrania")



def manifest():
    try:
        with open(os.path.join(pobrania(), "pliki.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"pliki": [], "podglady": {}}


def do_pobrania(nazwa):
    """Ścieżka pliku tylko z białej listy manifestu (PDF + podglądy) — nic innego z katalogu nie wychodzi."""
    m = manifest()
    dozwolone = {p["plik"] for p in m.get("pliki", [])} | set((m.get("podglady") or {}).values())
    return os.path.join(pobrania(), nazwa) if nazwa in dozwolone and "/" not in nazwa and "\\" not in nazwa else None


KLAUZULA = "2026-09-28.1"
POSREDNIK = ("X-Forwarded-For", "Forwarded", "Cf-Connecting-Ip", "Cf-Access-Jwt-Assertion", "X-Real-Ip")
TYPY = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".svg": "image/svg+xml", ".woff2": "font/woff2", ".json": "application/json; charset=utf-8", ".png": "image/png",
        ".pdf": "application/pdf", ".jpg": "image/jpeg", ".glb": "model/gltf-binary"}
EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.\-]{1,190}\.[A-Za-z]{2,24}$")
LIMIT_IP_H, LIMIT_DOBA = 5, 500
_limity = {}
_lock = threading.Lock()


def administrator():
    return (os.environ.get("JEZYKI_ADMINISTRATOR") or "").strip()


def iod():
    return (os.environ.get("JEZYKI_IOD") or "").strip()


def wypisz(email):
    """Wycofanie zgody = usunięcie adresu. Ta sama odpowiedź, czy adres był na liście, czy nie (nie zdradzamy zawartości listy)."""
    email = (email or "").strip().lower()
    if not EMAIL.match(email):
        return 400, {"blad": "email", "komunikat": "To nie wygląda na adres e-mail."}
    if os.path.exists(os.path.join(KATALOG, "zapisy.sqlite3")):
        con = baza()
        try:
            con.execute("DELETE FROM zapisy WHERE email=?", (email,))
            con.commit()
        finally:
            con.close()
    return 200, {"ok": True, "komunikat": "Jeśli ten adres był na liście, właśnie go usunęliśmy. Zgoda wycofana."}


def operator(adres, naglowki):
    return adres in ("127.0.0.1", "::1") and not any(naglowki.get(h) for h in POSREDNIK)


def baza():
    os.makedirs(KATALOG, exist_ok=True)
    con = sqlite3.connect(os.path.join(KATALOG, "zapisy.sqlite3"), timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS zapisy(id INTEGER PRIMARY KEY, ts TEXT, email TEXT UNIQUE, jezyk TEXT, klauzula TEXT)")
    return con


def zapis(email, zgoda, pulapka, jezyk, klucz_ip):
    """→ (kod, odpowiedź). Ta sama odpowiedź dla nowego i powtórzonego adresu (nie zdradzamy, kto już jest na liście)."""
    if not (administrator() and iod()):
        return 503, {"stan": "zamkniete", "komunikat": "Zapisy ruszą, gdy wskażemy administratora danych. Zajrzyj wkrótce."}
    if pulapka:
        return 200, {"ok": True}                     # pole-pułapka dla botów: udajemy sukces, nic nie zapisujemy
    email = (email or "").strip().lower()
    if not EMAIL.match(email):
        return 400, {"blad": "email", "komunikat": "To nie wygląda na adres e-mail."}
    if zgoda is not True:
        return 400, {"blad": "zgoda", "komunikat": "Zaznacz zgodę na jedną wiadomość o resecie świata gry."}
    teraz = time.time()
    with _lock:
        h = [t for t in _limity.get(klucz_ip, []) if teraz - t < 3600]
        if len(h) >= LIMIT_IP_H:
            return 429, {"blad": "limit", "komunikat": "Za dużo prób — spróbuj za godzinę."}
        _limity[klucz_ip] = h + [teraz]
    con = baza()
    try:
        dzis = time.strftime("%Y-%m-%d")
        if con.execute("SELECT COUNT(*) FROM zapisy WHERE substr(ts,1,10)=?", (dzis,)).fetchone()[0] >= LIMIT_DOBA:
            return 429, {"blad": "limit", "komunikat": "Na dziś lista jest pełna — wróć jutro."}
        con.execute("INSERT OR IGNORE INTO zapisy(ts,email,jezyk,klauzula) VALUES(?,?,?,?)",
                    (time.strftime("%Y-%m-%dT%H:%M:%S"), email, (jezyk or "")[:12], KLAUZULA))
        con.commit()
    finally:
        con.close()
    return 200, {"ok": True, "komunikat": "Zapisane. Napiszemy raz — gdy świat gry zacznie się od nowa."}


class H(BaseHTTPRequestHandler):
    server_version = "Jezyki/0.1"
    sys_version = ""

    def log_message(self, *a):
        pass

    def _op(self):
        return operator(self.client_address[0], self.headers)

    def _wyslij(self, kod, tresc, typ, cache="no-store"):
        self.send_response(kod)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if typ.startswith("text/html"):          # CSP tylko na stronach — w SVG logo działa jego własna animacja <style>
            if self.path.split("?")[0] == "/swiat3d":   # model-viewer: tekstury GLB jako blob:, dekoder WASM, style komponentu — tylko na tej stronie
                self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; connect-src 'self' blob: data:; "
                                 "style-src 'self' 'unsafe-inline'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self' blob:; frame-ancestors 'none'")
            else:
                self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(tresc)))
        self.end_headers()
        self.wfile.write(tresc)

    def _json(self, kod, obj):
        self._wyslij(kod, json.dumps(obj, ensure_ascii=False).encode("utf-8"), TYPY[".json"])

    def _plik(self, sciezka, cache="no-cache"):
        if not os.path.isfile(sciezka):
            return self._json(404, {"blad": "brak"})
        with open(sciezka, "rb") as f:
            self._wyslij(200, f.read(), TYPY.get(os.path.splitext(sciezka)[1].lower(), "application/octet-stream"), cache)

    def _cialo(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8192:
            raise ValueError("za duże")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._plik(os.path.join(STATIC, "index.html"))
        if p == "/ustawienia":
            if not self._op():
                return self._json(403, {"blad": "tylko operator przy ZBooku"})
            return self._plik(os.path.join(STATIC, "ustawienia.html"))
        if p == "/intro":
            return self._plik(os.path.join(STATIC, "intro.html"))
        if p == "/zasady":
            return self._plik(os.path.join(STATIC, "zasady.html"))
        if p in ("/legenda", "/swiat3d", "/spolecznosc"):
            return self._plik(os.path.join(STATIC, p[1:] + ".html"))
        if p.startswith("/pobierz/"):
            sc = do_pobrania(p[len("/pobierz/"):])
            if not sc or not os.path.isfile(sc):
                return self._json(404, {"blad": "brak"})
            with open(sc, "rb") as f:
                tresc = f.read()
            self.send_response(200)
            self.send_header("Content-Type", TYPY.get(os.path.splitext(sc)[1].lower(), "application/octet-stream"))
            self.send_header("Cache-Control", "max-age=600")
            self.send_header("X-Content-Type-Options", "nosniff")
            if os.path.splitext(sc)[1].lower() in (".pdf", ".glb", ".json", ".zip"):
                self.send_header("Content-Disposition", 'attachment; filename="%s"' % os.path.basename(sc))
            self.send_header("Content-Length", str(len(tresc)))
            self.end_headers()
            self.wfile.write(tresc)
            return
        if p == "/api/pliki":
            m = manifest()
            return self._json(200, {k: m.get(k) for k in ("wersja", "data", "pliki", "podglady")})
        if p.startswith("/s/"):
            m = re.fullmatch(r"/s/((?:fonty/|img/)?[A-Za-z0-9_-][A-Za-z0-9._-]*)", p)
            if not m or ".." in m.group(1) or os.path.splitext(m.group(1))[1].lower() not in (".js", ".css", ".svg", ".woff2", ".png", ".jpg", ".glb"):
                return self._json(404, {"blad": "brak"})
            return self._plik(os.path.join(STATIC, *m.group(1).split("/")), "max-age=3600")
        if p == "/api/slowa":
            return self._plik(os.path.join(DANE, "slowa.json"), "max-age=3600")
        if p == "/api/stan":
            return self._json(200, {"zapisy_otwarte": bool(administrator() and iod()), "administrator": administrator() or None, "iod": iod() or None,
                                    "klauzula": KLAUZULA, "reset": os.environ.get("JEZYKI_RESET") or None})
        if p == "/api/ustawienia":
            if not self._op():
                return self._json(403, {"blad": "tylko operator przy ZBooku"})
            return self._json(200, T.jawne(T.ustawienia()))
        if p == "/robots.txt":
            return self._wyslij(200, b"User-agent: *\nAllow: /\n", "text/plain; charset=utf-8")
        return self._json(404, {"blad": "brak"})

    def do_POST(self):
        p = self.path.split("?")[0]
        try:
            d = self._cialo()
        except Exception:
            return self._json(400, {"blad": "zadanie"})
        if p == "/api/zapis":
            ip = self.headers.get("Cf-Connecting-Ip") or self.client_address[0]
            klucz = hashlib.sha256((ip + time.strftime("%Y-%m-%d")).encode()).hexdigest()[:16]
            kod, odp = zapis(d.get("email"), d.get("zgoda"), d.get("www"), (self.headers.get("Accept-Language") or "").split(",")[0], klucz)
            return self._json(kod, odp)
        if p == "/api/wypisz":
            kod, odp = wypisz(d.get("email"))
            return self._json(kod, odp)
        if p in ("/api/ustawienia", "/api/przebuduj"):
            if not self._op():
                return self._json(403, {"blad": "tylko operator przy ZBooku"})
            if p == "/api/ustawienia":
                return self._json(200, T.zapisz_ustawienia(d))
            r = subprocess.run([sys.executable, os.path.join(HERE, "narzedzia", "zbuduj_slowa.py")], capture_output=True, timeout=600,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            return self._json(200 if r.returncode == 0 else 500, {"wynik": r.stdout.decode("utf-8", "replace")[-400:], "rc": r.returncode})
        return self._json(404, {"blad": "brak"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8781
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    srv.daemon_threads = True
    print("gra Halucynacje: http://127.0.0.1:%d/ · zapisy %s" % (port, "OTWARTE" if (administrator() and iod()) else "zamknięte (brak administratora danych)"), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
