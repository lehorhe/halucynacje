# -*- coding: utf-8 -*-
"""Świat anteny — proceduralna mapa pod heksami z prawdziwych statystyk Szpiega+ (27.09.2026, pomysł nr 2 gry „Języki”).

Świat = kalendarz anteny: kolumna heksów = dzień, heks = godzina. Teren pod heksami rośnie z danych:
  * wysokość terenu = % SŁOWA w godzinie (ostrożnie: mniejsza z dwóch metod lokalnych — SMD i segmenty transkrypcji);
  * LINIA BRZEGOWA = próg koncesji 32,53 %: godziny poniżej progu toną w morzu (muzyka), powyżej — ląd (mowa);
  * MGŁA = niezgodność metod (rozrzut > 5 pp) — do rozwiania przez gracza (sprawdzenie uchem = ruch na planszy);
  * OSADY = liczba rozpoznanych głosów w godzinie (samotny dom → wieś → miasteczko);
  * ZIEMIA NIEZNANA = godzina bez pomiaru.
Kształt terenu liczy algorytm (deterministycznie, ziarno z daty), nie model językowy — świat jest odtwarzalny i uczciwy.

Skala stała we wszystkich formatach: heks 25 mm między bokami, żeton 20 mm (= 80 % heksu) — ta sama funkcja rysuje żetony na mapie
i na arkuszu do wycięcia. Wyjście:
    python swiat_antena.py            → Swiat_anteny_A4.pdf (1: fragment planszy 1:1, 2: żetony do naklejenia na karton i wycięcia)
    python swiat_antena.py --a2       → także Swiat_anteny_A2.pdf (2 tygodnie koncesyjne × 06–23)
    python swiat_antena.py --a1       → także Swiat_anteny_A1.pdf (3 tygodnie koncesyjne × 24 h)
Python z venv comfy (numpy, PIL)."""
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
from html import escape

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sciezki  # noqa: E402
sys.path.insert(0, sciezki.WARSTWY)
import plansza as P  # noqa: E402

TU = os.path.dirname(os.path.abspath(__file__))
MEDIA = sciezki.MEDIA
FLAT = 25.0                     # heks: odległość między przeciwległymi bokami [mm]
S = FLAT / math.sqrt(3)         # promień (środek → wierzchołek)
ZET = 20.0                      # żeton [mm] = 0,8 × FLAT
PROG = 32.53                    # koncesja: % słowa (tydzień 06–23)
DNI = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
M = P.model()
DEF = {z["id"]: z for z in M["zetony"]}
KOL_GDZIE = {"L": "#23774F", "C": "#2F7C95", "H": "#B8860B", "W": "#7E57B8"}


# ---------------------------------------------------------------- dane godzin
def godzina(d, h):
    p = os.path.join(MEDIA, d, "sr_program_%s_%02d.meta.json" % (d.replace("-", "_"), h))
    if not os.path.exists(p):
        return None
    m = json.load(open(p, encoding="utf-8"))
    pom, dl = P.slowo_z_meta(m.get("statystyki"))
    sl = P.procent_slowa(pom, dl, M)
    if not sl:
        return None
    s = m.get("statystyki") or {}
    return {"slowo": sl, "mowcy": len(s.get("sekundy_per_mowca") or {}), "program": ((m.get("program") or {}).get("nazwa") or "")}


def siatka(dni, godziny):
    return {(i, j): godzina(d, h) for i, d in enumerate(dni) for j, h in enumerate(godziny)}


# ---------------------------------------------------------------- geometria (heksy „płaskim bokiem do góry”, kolumny = dni)
def srodek(i, j):
    return i * 1.5 * S + S, j * FLAT + (FLAT / 2 if i % 2 else 0) + FLAT / 2


def wierzcholki(cx, cy, s=S):
    return [(cx + s * math.cos(math.radians(60 * k)), cy + s * math.sin(math.radians(60 * k))) for k in range(6)]


def rozmiar(n_dni, n_godz):
    return (n_dni - 1) * 1.5 * S + 2 * S, n_godz * FLAT + FLAT / 2


# ---------------------------------------------------------------- teren (raster)
def szum(h, w, ziarno, oktawy=5):
    rng = np.random.default_rng(ziarno)
    out = np.zeros((h, w), np.float32)
    amp, suma = 1.0, 0.0
    for k in range(oktawy):
        gh, gw = max(2, h // (96 >> k) + 2), max(2, w // (96 >> k) + 2)
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(g, np.float32) / 255 - 0.5)
        suma += amp
        amp *= 0.5
    return out / suma


PALETA = [(0, (16, 58, 94)), (18, (32, 96, 140)), (32.53, (120, 190, 208)),       # morze: głębia → płycizna (muzyka)
          (32.54, (236, 224, 176)), (42, (206, 220, 150)), (55, (170, 206, 118)),  # plaża → łąki
          (68, (222, 204, 118)), (80, (150, 190, 96)), (90, (96, 150, 78)),        # złote pola → bujne zielenie (dużo mowy = urodzaj)
          (97, (70, 118, 66)), (100, (226, 220, 200))]


def koloruj(e):
    xs = np.array([p[0] for p in PALETA]); cs = np.array([p[1] for p in PALETA], np.float32)
    return np.stack([np.interp(e, xs, cs[:, c]) for c in range(3)], -1)


def teren(dane, n_dni, n_godz, px_mm, ziarno):
    W_mm, H_mm = rozmiar(n_dni, n_godz)
    w, h = int(W_mm * px_mm), int(H_mm * px_mm)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) / px_mm
    sig = FLAT * 0.42
    num_e = np.zeros((h, w), np.float32); num_u = np.zeros((h, w), np.float32)
    den = np.full((h, w), 1e-6, np.float32); nieznane = np.zeros((h, w), np.float32)
    for (i, j), g in dane.items():
        cx, cy = srodek(i, j)
        wgt = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sig * sig))
        if g is None:
            nieznane += wgt
            continue
        num_e += wgt * g["slowo"]["min"]; num_u += wgt * g["slowo"]["rozrzut_pp"]; den += wgt
    e = num_e / den; u = num_u / den
    niez = nieznane / (nieznane + den)
    e = np.clip(e + 7.0 * szum(h, w, ziarno) + 2.0 * szum(h, w, ziarno + 1, 6), 0, 100)
    rgb = koloruj(e)
    # cieniowanie rzeźby lądu (światło z północnego zachodu)
    z = np.where(e > PROG, (e - PROG) * 0.5 * px_mm, 0) + 4.0 * px_mm * szum(h, w, ziarno + 2, 6)
    gy, gx = np.gradient(z)
    cien = np.clip(0.9 + 0.22 * (-gx * 0.7 - gy * 0.7) / (np.hypot(gx, gy) + 1), 0.72, 1.12)
    lad = e > PROG
    rgb = np.where(lad[..., None], rgb * cien[..., None], rgb)
    # fale na morzu
    fale = 0.5 + 0.5 * np.sin((yy * 1.9 + 3.0 * szum(h, w, ziarno + 3)) * 1.3)
    rgb = np.where(lad[..., None], rgb, rgb * (0.94 + 0.08 * fale[..., None]))
    # linia brzegowa = próg koncesji
    brzeg = lad ^ np.roll(lad, 1, 0) | lad ^ np.roll(lad, 1, 1)
    for d in range(1, max(2, int(0.35 * px_mm))):
        brzeg = brzeg | np.roll(brzeg, 1, 0) | np.roll(brzeg, 1, 1)
    rgb = np.where(brzeg[..., None], np.array([12, 44, 60], np.float32), rgb)
    # mgła niepewności (metody różnią się o > 5 pp)
    mg = np.clip((u - 5.0) / 20.0, 0, 0.75) * np.clip(0.75 + 0.5 * szum(h, w, ziarno + 4, 4), 0, 1)
    rgb = rgb * (1 - mg[..., None]) + 250 * mg[..., None]
    # ziemia nieznana: pergamin z kreskowaniem
    kresk = ((xx + yy) * 1.0 % 3.0) < 0.35
    perg = np.where(kresk[..., None], np.array([170, 150, 110], np.float32), np.array([236, 224, 196], np.float32))
    a = np.clip((niez - 0.35) * 3, 0, 1)[..., None]
    rgb = rgb * (1 - a) + perg * a
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), W_mm, H_mm


# ---------------------------------------------------------------- żeton 20 mm — JEDNA funkcja dla mapy i arkusza
IKONY = json.load(open(os.path.join(sciezki.WARSTWY, "ikony_zetonow.json"), encoding="utf-8"))


def ikona(x, y, rozm, d, kol, gr=2.0):
    """Ikona liniowa 24×24 wpisana w kwadrat rozm × rozm."""
    return '<g transform="translate(%.2f %.2f) scale(%.4f)" fill="none" color="%s" stroke="currentColor" stroke-width="%.2f" stroke-linecap="round" stroke-linejoin="round">%s</g>' % (
        x, y, rozm / 24, kol, gr, d)


def zeton(x, y, a, zid, spad=False):
    """Żeton w stylu gier heksowych o współczesnym polu walki: ramka jednostki z ikoną rodzaju pracy,
    siła w lewym górnym rogu, modyfikator trybu w prawym (dron = na żywo, zegar = po godzinie, postać = człowiek),
    u dołu kod miejsca (L/C/H/W) i oznaczenie jednostki. Chmura = ramka przerywana (cudza jednostka).
    Pełne tło do krawędzi (spad), treść odsunięta ~1,6 mm."""
    z = DEF[zid]
    kol = KOL_GDZIE[z["gdzie"]]
    h = '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s"%s/>' % (
        x, y, a, a, 0 if spad else a * .08, kol, "" if spad else ' stroke="#fff" stroke-width=".5"')
    h += '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#000" opacity=".16"/>' % (x, y + a * .76, a, a * .24)
    if z.get("nakladka"):
        h += '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx=".6" fill="none" stroke="#F9B009" stroke-width="1"/>' % (x + .75, y + .75, a - 1.5, a - 1.5)
    fw, fh = a * .58, a * .44
    fx, fy = x + (a - fw) / 2, y + a * .28
    ramka = ' stroke-dasharray="%.2f %.2f"' % (a * .05, a * .03) if z["gdzie"] == "C" else ""
    h += '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx=".5" fill="#FFFDF6" stroke="#10262E" stroke-width=".5"%s/>' % (fx, fy, fw, fh, ramka)
    ri = fh * .86
    h += ikona(x + (a - ri) / 2, fy + (fh - ri) / 2, ri, IKONY["zetony"][zid], kol, 2.1)
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="900" fill="#fff">%d</text>' % (x + a * .1, y + a * .225, a * .19, min(z["sila"], 9))
    rt = a * .17
    h += ikona(x + a * .9 - rt, y + a * .07, rt, IKONY["tryb"][z["tryb"]], "#fff", 2.4)
    kb = a * .15
    h += '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#fff" rx=".3"/>' % (x + a * .09, y + a * .8, kb, kb)
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="900" text-anchor="middle" fill="%s">%s</text>' % (x + a * .09 + kb / 2, y + a * .8 + kb * .8, kb * .85, kol, z["gdzie"])
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="700" text-anchor="end" fill="#fff">%s</text>' % (x + a * .91, y + a * .925, a * .115, escape(z["skrot"]))
    return h


def znacznik(x, y, a, sym, bg, fg, opis):
    h = '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>' % (x, y, a, a, bg)
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="900" text-anchor="middle" fill="%s">%s</text>' % (x + a / 2, y + a * .58, a * .42, fg, escape(sym))
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" text-anchor="middle" fill="%s">%s</text>' % (x + a / 2, y + a * .86, a * .12, fg, escape(opis))
    return h


# ---------------------------------------------------------------- nakładka SVG na mapę
def osada(cx, cy, n):
    if n <= 0:
        return ""
    k = 1 if n <= 2 else (2 if n <= 5 else 3)
    h = ""
    for m_ in range(k + 1):
        dx = (m_ - k / 2) * 2.1
        h += '<path d="M%.2f %.2fl1.3 -1.4l1.3 1.4v1.8h-2.6z" fill="#FFF8EC" stroke="#3A2A18" stroke-width=".35"/>' % (cx - 1.3 + dx, cy - 0.4 - (m_ % 2) * 0.7)
    return h


def nakladka(dane, dni_lab, godz_lab, ox, oy, stosy=None):
    h = ""
    for (i, j), g in dane.items():
        cx, cy = srodek(i, j)
        cx += ox; cy += oy
        h += '<polygon points="%s" fill="none" stroke="#FFFFFF" stroke-opacity=".85" stroke-width=".5"/>' % " ".join("%.2f,%.2f" % p for p in wierzcholki(cx, cy))
        h += '<text x="%.2f" y="%.2f" font-size="2.5" font-weight="800" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".6" paint-order="stroke">%s</text>' % (
            cx, cy - FLAT * 0.33, godz_lab[j])
        if g is None:
            h += '<text x="%.2f" y="%.2f" font-size="2.3" text-anchor="middle" fill="#5A4A2A" font-style="italic">ziemia nieznana</text>' % (cx, cy + 1)
            continue
        sl = g["slowo"]
        lab = ("%d%%" % round(sl["min"])) if sl["n"] < 2 or round(sl["min"]) == round(sl["max"]) else "%d–%d%%" % (round(sl["min"]), round(sl["max"]))
        h += '<text x="%.2f" y="%.2f" font-size="2.6" font-weight="800" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".7" paint-order="stroke">słowo %s</text>' % (
            cx, cy + FLAT * 0.39, lab)
        if not (stosy and (i, j) in stosy):
            h += osada(cx, cy, g["mowcy"] if sl["min"] > PROG else 0)
    for i, d in enumerate(dni_lab):                     # nagłówki kolumn = dni
        cx, _ = srodek(i, 0)
        h += '<text x="%.2f" y="%.2f" font-size="3" font-weight="800" text-anchor="middle" fill="#274F5C">%s</text>' % (cx + ox, oy - 1.5, d)
    for (i, j), lista in (stosy or {}).items():
        cx, cy = srodek(i, j)
        cx += ox; cy += oy
        for k, zid in enumerate(lista):
            h += zeton(cx - ZET / 2 + k * 1.3, cy - ZET / 2 - k * 1.3, ZET, zid)
    return h


# ---------------------------------------------------------------- strona A4: legenda i linijka
def linijka(x, y, dl=100):
    h = '<rect x="%.1f" y="%.1f" width="%d" height="2" fill="#0A1318"/>' % (x, y, dl)
    for k in range(0, dl + 1, 10):
        h += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#0A1318" stroke-width=".3"/>' % (x + k, y - 1.2, x + k, y + 3.2)
    h += '<text x="%.1f" y="%.1f" font-size="2.6" fill="#0A1318">sprawdź skalę: ta linijka ma %d mm · heks 25 mm · żeton 20 mm</text>' % (x, y + 6.8, dl)
    return h


def legenda(x, y, w):
    h = '<text x="%.1f" y="%.1f" font-size="3.6" font-weight="800" fill="#274F5C">Jak czytać teren</text>' % (x, y)
    y += 3
    gx0, gw = x, w * 0.62
    for k in range(200):
        v = k / 2
        c = koloruj(np.array([v]))[0]
        h += '<rect x="%.2f" y="%.1f" width="%.2f" height="4.5" fill="rgb(%d,%d,%d)"/>' % (gx0 + gw * k / 200, y, gw / 200 + .05, *c.astype(int))
    xp = gx0 + gw * PROG / 100
    h += '<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="#0C2C3C" stroke-width=".8"/>' % (xp, y - 1, xp, y + 5.5)
    for v, t in ((0, "0%"), (PROG, "32,53% koncesja = brzeg"), (60, "60%"), (100, "100% słowa")):
        h += '<text x="%.2f" y="%.1f" font-size="2.3" text-anchor="%s" fill="#0A1318">%s</text>' % (gx0 + gw * v / 100, y + 8.3, "start" if v == 0 else ("end" if v == 100 else "middle"), t)
    h += '<text x="%.1f" y="%.1f" font-size="2.3" fill="#3F5A66">morze = godzina pod progiem (muzyka) · plaże, łąki, pola, lasy, wzgórza = coraz więcej mowy</text>' % (gx0, y + 12)
    x2 = x + w * 0.66
    items = [("mgła", "metody różnią się o > 5 pp — sprawdź uchem"), ("domy", "osada: liczba rozpoznanych głosów w godzinie"),
             ("perg", "ziemia nieznana: godzina bez pomiaru"), ("sł", "„słowo 77–83%”: przedział z SMD i segmentów transkrypcji")]
    for k, (ik, t) in enumerate(items):
        yy = y + 1 + k * 4.2
        if ik == "mgła":
            h += '<rect x="%.1f" y="%.1f" width="5" height="3" fill="#F2F2F0" stroke="#bbb" stroke-width=".2"/>' % (x2, yy - 2.4)
        elif ik == "domy":
            h += osada(x2 + 2.5, yy - 0.3, 2)
        elif ik == "perg":
            h += '<rect x="%.1f" y="%.1f" width="5" height="3" fill="#ECE0C4" stroke="#AA966E" stroke-width=".3"/>' % (x2, yy - 2.4)
        else:
            h += '<text x="%.1f" y="%.1f" font-size="2.3" font-weight="800">%%</text>' % (x2 + 1, yy)
        h += '<text x="%.1f" y="%.1f" font-size="2.3" fill="#0A1318">%s</text>' % (x2 + 6.5, yy, escape(t))
    return h


# ---------------------------------------------------------------- arkusz żetonów pod karton po pizzy
ZESTAW = ([("batch_lokal", 6), ("batch_chmura", 4), ("live_lokal", 4), ("live_chmura", 4), ("weryfikacja", 6), ("archiwum", 6), ("strumien", 3),
           ("swiadek", 3), ("smd", 5), ("tagi", 5), ("diar_lokal", 5), ("diar_live", 3), ("diar_chmura", 3), ("glosoteka", 5), ("kontekst", 4),
           ("przedstawienia", 3), ("wydawca", 4), ("pii", 4), ("encje_model", 3), ("rozdz_model", 3), ("odcisk", 3), ("typ_sluchacza", 2),
           ("paczka", 3), ("gem", 2), ("sprawdzenie", 3), ("szkic_wp", 2), ("odcinek", 1), ("wideo_sync", 1), ("zewnetrzna", 1)])
ZNACZNIKI = [("!", "#F9B009", "#0A1318", "konflikt", 5), ("…", "#E6EEF1", "#274F5C", "w toku", 4), ("½", "#FFFFFF", "#2F7C95", "luka / na żywo", 4)]


def arkusz():
    a = ZET
    kol, rz = 9, 12
    x0, y0 = (210 - kol * a) / 2, 38.0
    lista = [z for z, n in ZESTAW for _ in range(n)]
    znaczniki = [(s, b, f, o) for s, b, f, o, n in ZNACZNIKI for _ in range(n)]
    pola = kol * rz
    lista = (lista + [None] * pola)[:pola - len(znaczniki)] + znaczniki
    h = '<text x="%.1f" y="13" font-size="5.6" font-weight="800" fill="#274F5C">Żetony 20 mm — na karton i nożyczki</text>' % x0
    rady = ["1. Drukuj w skali 100% (linijka niżej musi mieć 100 mm). 2. Naklej CAŁY arkusz na czystą, wewnętrzną stronę pudełka po pizzy — klej w sztyfcie",
            "   po całej powierzchni, dociśnij książkami, odczekaj godzinę. 3. Tnij nożyczkami najpierw POZIOME pasy przez całą szerokość (wzdłuż znaczników",
            "   na marginesach), potem każdy pas na kwadraty. Tło sięga linii cięcia, więc krzywe cięcie nie zostawi białego brzegu. Żeton = 80% heksu planszy."]
    for k, t in enumerate(rady):
        h += '<text x="%.1f" y="%.1f" font-size="2.55" fill="#0A1318">%s</text>' % (x0, 19 + k * 3.6, escape(t))
    h += linijka(x0, 31.2 - 2.5, 100).replace('sprawdź skalę: ta linijka ma 100 mm · heks 25 mm · żeton 20 mm', '')
    for n, it in enumerate(lista):
        x, y = x0 + (n % kol) * a, y0 + (n // kol) * a
        if it is None:
            h += '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#F4F1EA"/>' % (x, y, a, a)
        elif isinstance(it, tuple):
            h += znacznik(x, y, a, *it)
        else:
            h += zeton(x, y, a, it, spad=True)
    # linie cięcia: grube, przez całą siatkę + znaczniki na marginesach (widać je po naklejeniu)
    for i in range(kol + 1):
        X = x0 + i * a
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".45"/>' % (X, y0, X, y0 + rz * a)
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".6"/>' % (X, y0 - 5, X, y0 - 1)
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".6"/>' % (X, y0 + rz * a + 1, X, y0 + rz * a + 5)
    for j in range(rz + 1):
        Y = y0 + j * a
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".45"/>' % (x0, Y, x0 + kol * a, Y)
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".6"/>' % (x0 - 5, Y, x0 - 1, Y)
        h += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1A1A1A" stroke-width=".6"/>' % (x0 + kol * a + 1, Y, x0 + kol * a + 5, Y)
        if j < rz:
            h += '<text x="%.2f" y="%.2f" font-size="2.4" text-anchor="end" fill="#75909A">✂ %d</text>' % (x0 - 1.2, Y + a / 2 + 1, j + 1)
    ys = y0 + rz * a + 9
    h += ('<text x="%.1f" y="%.1f" font-size="2.45" fill="#3F5A66">Kolory: zielony L lokalnie 0 zł · niebieski C chmura · złoty H człowiek · fiolet W wyjście. Złota ramka = nakładka człowieka.</text>' % (x0, ys))
    h += ('<text x="%.1f" y="%.1f" font-size="2.45" fill="#3F5A66">Ikona = rodzaj pracy (ramka przerywana = chmura) · liczba = siła (wyższa na wierzch) · róg: dron na żywo, zegar po godzinie, postać człowiek.</text>' % (x0, ys + 3.6))
    h += ('<text x="%.1f" y="%.1f" font-size="2.45" fill="#3F5A66">Znaczniki: ! konflikt (rozstrzyga człowiek) · … w toku · ½ luka w czasie albo tylko na żywo. Puste pola — na własne żetony. '
          '%d żetonów i znaczników.</text>' % (x0, ys + 7.2, sum(1 for i in lista if i)))
    return h


# ---------------------------------------------------------------- składanie PDF
FONTY = sciezki.FONTY
CSS = ("@font-face{font-family:'Exo 2';src:url('file:///%s/exo2-600-900.woff2') format('woff2');font-weight:500 900}"
       "@font-face{font-family:'Lato';src:url('file:///%s/lato-400.woff2') format('woff2');font-weight:400}"
       "@font-face{font-family:'NovaCond';src:url('file:///C:/Windows/Fonts/ArialNovaCond-Bold.ttf');font-weight:700}"
       ".wz{font-family:'NovaCond','Arial Narrow',sans-serif;font-weight:700}"
       "html,body{margin:0;padding:0}.s{position:relative;overflow:hidden;page-break-after:always;break-after:page}"
       "svg.p{position:absolute;left:0;top:0;font-family:'Exo 2',Lato,sans-serif}img{position:absolute}") % (FONTY.replace("\\", "/"), FONTY.replace("\\", "/"))


def drukuj(html_strony, szer, wys, plik):
    html = ("<!doctype html><html lang='pl'><head><meta charset='utf-8'><style>@page{size:%smm %smm;margin:0}%s.s{width:%smm;height:%smm}"
            "svg.p{width:%smm;height:%smm}</style></head><body>%s</body></html>") % (szer, wys, CSS, szer, wys, szer, wys, "".join(html_strony))
    hp = os.path.join(TU, os.path.splitext(plik)[0] + ".html")
    open(hp, "w", encoding="utf-8").write(html)
    pdf = os.path.join(TU, plik)
    subprocess.run([sciezki.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=15000", "--print-to-pdf=" + pdf, "file:///" + hp.replace("\\", "/")],
                   capture_output=True, timeout=300)
    print(pdf, os.path.getsize(pdf), "B")


def okno_i_tygodnie(dane, dni, godziny, ox, oy, W_mm, H_mm):
    """Klamra okna koncesji 06–23 na lewym marginesie + bilans % słowa każdego tygodnia pod mapą
    (średnia z dolnych granic godzin 06–23 — ostrożnie, jak teren; godziny bez pomiaru pominięte)."""
    h = ""
    if 6 in godziny and 23 in godziny:
        y0 = oy + godziny.index(6) * FLAT + 1
        y1 = oy + godziny.index(23) * FLAT + FLAT * 1.5 - 1
        x = ox - 5
        h += '<path d="M%.2f %.2fh-2V%.2fh2" fill="none" stroke="#274F5C" stroke-width=".8"/>' % (x, y0, y1)
        h += ('<text transform="translate(%.2f %.2f) rotate(-90)" font-size="3.2" font-weight="800" text-anchor="middle" fill="#274F5C">'
              'okno koncesji 06–23 · tu liczy się 32,53%% słowa</text>') % (x - 3.5, (y0 + y1) / 2)
        if godziny[0] < 6:
            h += ('<text transform="translate(%.2f %.2f) rotate(-90)" font-size="2.8" text-anchor="middle" fill="#75909A">noc 00–05 · poza oknem</text>') % (
                x - 3.5, oy + godziny.index(5) * FLAT / 2 + FLAT / 2)
    for t0 in range(0, len(dni), 7):
        tyd = range(t0, min(t0 + 7, len(dni)))
        w = [dane[(i, j)]["slowo"]["min"] for i in tyd for j, g in enumerate(godziny) if 6 <= g <= 23 and dane.get((i, j))]
        xa, xb = srodek(tyd[0], 0)[0] - S + ox, srodek(tyd[-1], 0)[0] + S + ox
        y = oy + H_mm + 5
        h += '<path d="M%.2f %.2fv2H%.2fv-2" fill="none" stroke="#274F5C" stroke-width=".6"/>' % (xa + 1, y - 2, xb - 1)
        if not w:
            continue
        sr = sum(w) / len(w)
        ok = sr >= PROG
        h += ('<text x="%.2f" y="%.2f" font-size="3.4" font-weight="800" text-anchor="middle" fill="%s">tydzień %s–%s: słowo ≈ %.0f%% %s</text>'
              '<text x="%.2f" y="%.2f" font-size="2.4" text-anchor="middle" fill="#56717C">średnia dolnych granic %d godzin 06–23</text>') % (
            (xa + xb) / 2, y + 5.2, "#23774F" if ok else "#B23A2E", dni[tyd[0]][8:10] + "." + dni[tyd[0]][5:7], dni[tyd[-1]][8:10] + "." + dni[tyd[-1]][5:7],
            sr, "≥ 32,53% ✓ koncesja" if ok else "< 32,53% ✗ poniżej progu", (xa + xb) / 2, y + 8.6, len(w))
    return h


def strona_mapy(dni, godziny, szer, wys, px_mm, tytul, podtytul, stosy=None, plik_obrazu="swiat.jpg", legenda_y=None, tygodnie=False):
    dane = siatka(dni, godziny)
    ziarno = int(hashlib.sha1(("|".join(dni) + str(godziny)).encode()).hexdigest()[:8], 16)
    img, W_mm, H_mm = teren(dane, len(dni), len(godziny), px_mm, ziarno)
    img.save(os.path.join(TU, plik_obrazu), quality=90, dpi=(int(px_mm * 25.4),) * 2)
    k_t = 1.8 if szer >= 594 else 1.0                  # plakat A1: czytelny z metra (nagłówek i legenda ×1,8; linijka zawsze 1:1)
    ox, oy = (szer - W_mm) / 2, (70.0 if k_t > 1 else 30.0)
    dni_lab = ["%s %s" % (DNI[dt.date.fromisoformat(d).weekday()], d[8:10] + "." + d[5:7]) for d in dni]
    godz_lab = ["%02d:00" % g for g in godziny]
    pod = podtytul.split(" | ")
    svg = '<text x="%.1f" y="%.1f" font-size="%.2f" font-weight="800" fill="#274F5C">%s</text>' % (ox, 12 * k_t + (8 if k_t > 1 else 0), 6.5 * k_t, escape(tytul))
    svg += "".join('<text x="%.1f" y="%.1f" font-size="%.2f" fill="#3F5A66">%s</text>' % (ox, (18 + k * 3.6) * k_t + (10 if k_t > 1 else 0), 2.8 * k_t, escape(t))
                   for k, t in enumerate(pod))
    svg += nakladka(dane, dni_lab, godz_lab, ox, oy, stosy)
    ly = legenda_y or (oy + H_mm + 8)
    if tygodnie:
        svg += okno_i_tygodnie(dane, dni, godziny, ox, oy, W_mm, H_mm)
        ly += 12
    svg += '<g transform="translate(%.2f %.2f) scale(%.2f) translate(%.2f %.2f)">%s</g>' % (ox, ly, k_t, -ox, -ly, legenda(ox, ly, W_mm / k_t))
    svg += linijka(ox, ly + 21 * k_t, 100)
    svg += ('<text x="%.1f" y="%.1f" font-size="2.2" fill="#56717C">Teren wygenerowany algorytmem z prawdziwych statystyk godzin (szpieg_media, meta.json: SMD i segmenty transkrypcji);</text>'
            '<text x="%.1f" y="%.1f" font-size="2.2" fill="#56717C">osady = rozpoznane głosy; żetony na mapie: przykład. Oprac. Claude (Anthropic) dla L. R. Rusteckiego · Radio Wnet · Szpieg+.</text>') % (ox, wys - 8, ox, wys - 5)
    html = ('<div class="s"><img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
            '<svg class="p" viewBox="0 0 %s %s">%s</svg></div>') % (plik_obrazu, ox, oy, W_mm, H_mm, szer, wys, svg)
    return html, dane


def main():
    tydzien = ["2026-09-%02d" % d for d in range(14, 21)]                  # tydzień koncesyjny pn–nd
    godziny_a4 = list(range(6, 14))                                        # 06–13: poranek i przedpołudnie
    stosy = {(0, 1): ["archiwum", "smd", "batch_lokal"], (4, 0): ["archiwum", "smd"], (2, 3): ["diar_lokal", "glosoteka", "wydawca"]}
    s1, dane = strona_mapy(tydzien, godziny_a4, 210, 297, 12.0, "Świat anteny · fragment planszy 1:1",
                           "tydzień koncesyjny 14–20.09.2026 (pn–nd) · godziny 06–13 · heks 25 mm = godzina anteny · żeton 20 mm | wysokość terenu = % słowa (ostrożnie: mniejsza z dwóch metod lokalnych) · linia brzegu = próg koncesji 32,53%",
                           stosy=stosy, plik_obrazu="swiat_a4.jpg")
    s2 = '<div class="s"><svg class="p" viewBox="0 0 210 297">%s</svg></div>' % arkusz()
    drukuj([s1, s2], 210, 297, "Swiat_anteny_A4.pdf")
    zm = [g for g in dane.values() if g]
    print("A4: godzin z pomiarem", len(zm), "z", len(dane), "· pod progiem:", sum(1 for g in zm if g["slowo"]["min"] < PROG),
          "· mgła:", sum(1 for g in zm if not g["slowo"]["zgodne"]))
    if "--a2" in sys.argv:
        dwa = ["2026-09-%02d" % d for d in range(7, 21)]
        s, dane2 = strona_mapy(dwa, list(range(6, 24)), 420, 594, 8.0, "Świat anteny · dwa tygodnie koncesyjne",
                               "7–20.09.2026 · godziny 06–23 (okno koncesji) · heks 25 mm = godzina anteny · żetony 20 mm | wysokość terenu = % słowa (ostrożnie) · linia brzegu = próg koncesji 32,53%",
                               plik_obrazu="swiat_a2.jpg")
        drukuj([s], 420, 594, "Swiat_anteny_A2.pdf")
        zm = [g for g in dane2.values() if g]
        print("A2: godzin z pomiarem", len(zm), "z", len(dane2), "· pod progiem:", sum(1 for g in zm if g["slowo"]["min"] < PROG))
    if "--a1" in sys.argv:
        trzy = [(dt.date(2026, 8, 31) + dt.timedelta(days=k)).isoformat() for k in range(21)]   # trzy pełne tygodnie koncesyjne pn–nd
        stosy1 = {(15, 9): ["archiwum", "smd", "batch_lokal", "weryfikacja"], (18, 20): ["strumien", "tagi", "live_lokal"], (3, 2): ["archiwum", "batch_chmura"]}
        s, dane3 = strona_mapy(trzy, list(range(24)), 594, 841, 6.0, "Świat anteny · trzy tygodnie koncesyjne, cała doba",
                               "31.08–20.09.2026 (pn–nd) · 24 godziny na dobę · heks 25 mm = godzina anteny · żetony 20 mm | wysokość terenu = % słowa (ostrożnie: mniejsza z dwóch metod lokalnych) · linia brzegu = próg koncesji 32,53% · noc poza oknem koncesji",
                               stosy=stosy1, plik_obrazu="swiat_a1.jpg", tygodnie=True)
        drukuj([s], 594, 841, "Swiat_anteny_A1.pdf")
        zm = [g for g in dane3.values() if g]
        print("A1: godzin z pomiarem", len(zm), "z", len(dane3), "· pod progiem:", sum(1 for g in zm if g["slowo"]["min"] < PROG),
              "· mgła:", sum(1 for g in zm if not g["slowo"]["zgodne"]))


if __name__ == "__main__":
    main()
