# -*- coding: utf-8 -*-
"""Plansze gry „HALUCYNACJE · Świat anteny” 1.0 z proceduralnych światów rozgłośni (profile_rozglosni.py).

    python plansza_gry.py            → Zestaw_startowy_A4.pdf (scenariusz 1 + arkusz żetonów + karta pomocy),
                                       Scenariusze_A4.pdf (4 plansze scenariuszy 1:1)
    python plansza_gry.py --a0       → także Plansza_A0_klasyczne/muzyczne/informacyjne.pdf (sezon: 4 tygodnie × 24 h)
Skala zawsze 1:1: heks 25 mm, żeton 20 mm; na każdej stronie linijka 100 mm."""
import math
import json
import os
import sys
from html import escape

import numpy as np
from PIL import Image

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TU)
import profile_rozglosni as PR  # noqa: E402
import swiat_antena as SA  # noqa: E402

FLAT, S, ZET, PROG = SA.FLAT, SA.S, SA.ZET, SA.PROG
DNI = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]

# ---------------------------------------------------------------- scenariusze (progi ocen z symulacja_gry.py, 3 osoby, zaokrąglone)
SCENARIUSZE = [
    {"nr": 1, "nazwa": "Poranek Wnet", "profil": "klasyczne", "tydz": 0, "h0": 6,
     "opis": "Publicystyka od świtu: wysokie wzgórza słowa i wielu gości. Scenariusz na pierwszą partię.",
     "progi": (90, 110, 125)},
    {"nr": 2, "nazwa": "Popołudnie i wieczór", "profil": "klasyczne", "tydz": 0, "h0": 14,
     "opis": "Najbardziej zróżnicowany teren: doliny muzyki po 15:00, publicystyka, wieczorne audycje autorskie.",
     "progi": (85, 105, 130)},
    {"nr": 3, "nazwa": "Archipelag", "profil": "muzyczne", "tydz": 0, "h0": 5,
     "opis": "Radio przebojów: wyspy porannych show na morzu muzyki. Mało punktów, dużo mgły — liczy się ucho.",
     "progi": (37, 47, 57)},
    {"nr": 4, "nazwa": "Kontynent", "profil": "informacyjne", "tydz": 0, "h0": 6,
     "opis": "Radio informacyjne: sam ląd i tłum głosów. Najtrudniejszy — bez Redakcji „Kto mówi” się nie uda.",
     "progi": (70, 88, 110)},
]
OCENY = ["Poniżej progu", "Kolegium przyjmuje", "Dobry tydzień", "Wzorowa redakcja"]


def wartosc(mn):
    return 0 if mn < PROG else (1 if mn < 60 else (2 if mn < 80 else 3))


def domy(m):
    return 1 if m <= 3 else (2 if m <= 6 else 3)


def dane_okna(profil, tygodnie, h0, n_h, t0=0):
    d, zd = PR.swiat(profil, t0 + tygodnie)
    out = {}
    for i in range(tygodnie * 7):
        for j in range(n_h):
            out[(i, j)] = d[((t0 * 7) + i, h0 + j)]
    return out, [z for z in zd if t0 <= z[0] < t0 + tygodnie]


# ---------------------------------------------------------------- teren: szybka wersja (okna ±3σ) tej samej funkcji co w swiat_antena
def teren(dane, n_dni, n_godz, px_mm, ziarno):
    W_mm, H_mm = SA.rozmiar(n_dni, n_godz)
    w, h = int(W_mm * px_mm), int(H_mm * px_mm)
    sig = FLAT * 0.42
    r = int(3 * sig * px_mm)
    num_e = np.zeros((h, w), np.float32); num_u = np.zeros((h, w), np.float32); num_v = np.zeros((h, w), np.float32)
    den = np.full((h, w), 1e-6, np.float32); niez = np.zeros((h, w), np.float32)
    num_p = np.zeros((h, w), np.float32); num_t = np.zeros((h, w), np.float32); num_l = np.zeros((h, w), np.float32); num_m = np.zeros((h, w), np.float32)
    num_2 = np.zeros((h, w), np.float32); num_r = np.zeros((h, w), np.float32)
    for (i, j), g in dane.items():
        cx, cy = SA.srodek(i, j)
        px, py = int(cx * px_mm), int(cy * px_mm)
        x0, x1, y0, y1 = max(0, px - r), min(w, px + r), max(0, py - r), min(h, py + r)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32) / px_mm
        wg = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sig * sig))
        if g is None:
            niez[y0:y1, x0:x1] += wg
            continue
        num_e[y0:y1, x0:x1] += wg * g["slowo"]["min"]
        num_u[y0:y1, x0:x1] += wg * g["slowo"]["rozrzut_pp"]
        num_v[y0:y1, x0:x1] += wg * (min(1.0, g["mowcy_eff"] / 3.0) if "mowcy_eff" in g else 1.0)   # roślinność = życie rozmowy
        e1 = g.get("e1") or {}
        prawda = "e1" in g                                                                            # plansze syntetyczne: bez warstw etapu 1
        num_r[y0:y1, x0:x1] += wg * prawda
        num_p[y0:y1, x0:x1] += wg * min(1.0, e1.get("przejscia", 0) / 20.0)                         # archipelag: przejścia mowa↔muzyka
        num_t[y0:y1, x0:x1] += wg * (np.clip((e1["tempo"] - 4.1) / 1.3, 0, 1) if e1.get("tempo") else (0.4 if prawda else 0.34))  # stromizna: sylaby/s
        num_l[y0:y1, x0:x1] += wg * min(1.0, e1.get("mowa_muzyka_s", 0) / 120.0)                    # laguna: mowa na tle muzyki
        dwie = bool(e1.get("dwie_transkrypcje"))
        num_2[y0:y1, x0:x1] += wg * dwie
        num_m[y0:y1, x0:x1] += wg * (0.0 if (dwie or not prawda) else float(np.clip((e1.get("rozbieznosc_szac", 10.0) - 9.0) / 5.0, 0.0, 1.0)))  # miraż
        den[y0:y1, x0:x1] += wg
    e = num_e / den; u = num_u / den; nz = niez / (niez + den)
    pp, tt, ll, mm, d2, rr = num_p / den, num_t / den, num_l / den, num_m / den, num_2 / den, num_r / den
    drobny = np.asarray(Image.fromarray(((np.random.default_rng(ziarno + 5).random((h // int(2.2 * px_mm) + 2, w // int(2.2 * px_mm) + 2))) * 255).astype(np.uint8))
                        .resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5
    e = np.clip(e + 7.0 * SA.szum(h, w, ziarno) + 2.0 * SA.szum(h, w, ziarno + 1, 6) + 30.0 * pp * drobny, 0, 100)   # dużo przejść = poszarpany brzeg, wyspy
    rgb = SA.koloruj(e)
    grzbiet = 1 - 2 * np.abs(SA.szum(h, w, ziarno + 6, 6))                                    # grzbiety: szybka mowa = strome, żebrowane zbocza
    z = np.where(e > PROG, (e - PROG) * 0.5 * px_mm * (0.35 + 1.9 * tt) + 9.0 * px_mm * tt * rr * grzbiet, 0) + 4.0 * px_mm * SA.szum(h, w, ziarno + 2, 6)
    gy, gx = np.gradient(z)
    cien = np.clip(0.9 + 0.30 * (-gx * 0.7 - gy * 0.7) / (np.hypot(gx, gy) + 1), 0.62, 1.16)
    lad = e > PROG
    rgb = np.where(lad[..., None], rgb * cien[..., None], rgb)
    veg = np.clip(num_v / den, 0, 1)
    skala = np.array([148, 138, 122], np.float32)                                  # monolog: wysoko, ale skaliście
    rgb = np.where(lad[..., None], rgb * (0.55 + 0.45 * veg[..., None]) + skala * (0.45 * (1 - veg[..., None])), rgb)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) / px_mm
    fale = 0.5 + 0.5 * np.sin((yy * 1.9 + 3.0 * SA.szum(h, w, ziarno + 3)) * 1.3)
    rgb = np.where(lad[..., None], rgb, rgb * (0.94 + 0.08 * fale[..., None]))
    # laguny i plaże: mowa na tle muzyki — płytka turkusowa woda po stronie morza, piasek po stronie lądu
    turk, piach = np.array([96, 196, 190], np.float32), np.array([232, 214, 160], np.float32)
    wl = np.clip(ll * 1.3, 0, 1) * np.clip(1 - (PROG - e) / 16.0, 0, 1) * (~lad)
    rgb = rgb * (1 - 0.85 * wl[..., None]) + turk * 0.85 * wl[..., None]
    wp = np.clip(ll * 1.3, 0, 1) * np.clip(1 - (e - PROG) / 6.0, 0, 1) * lad
    rgb = rgb * (1 - 0.8 * wp[..., None]) + piach * 0.8 * wp[..., None]
    brzeg = lad ^ np.roll(lad, 1, 0) | lad ^ np.roll(lad, 1, 1)
    for _ in range(1, max(2, int(0.35 * px_mm))):
        brzeg = brzeg | np.roll(brzeg, 1, 0) | np.roll(brzeg, 1, 1)
    rgb = np.where(brzeg[..., None], np.array([12, 44, 60], np.float32), rgb)
    # miraż: szacowana rozbieżność transkrypcji — drgające poziome smugi; godziny z dwiema transkrypcjami czyste i jaśniejsze
    smugi = np.clip(np.sin(yy * 5.5 + 2.5 * SA.szum(h, w, ziarno + 7, 4) * 6) * 1.6 - 0.6, 0, 1)
    am = 0.26 * mm ** 1.5 * smugi
    rgb = rgb * (1 - am[..., None]) + np.array([255, 246, 228], np.float32) * am[..., None]
    rgb = rgb * (1 + 0.10 * d2[..., None]) + 8 * d2[..., None]
    mg = np.clip((u - 5.0) / 20.0, 0, 0.6) * np.clip(0.75 + 0.5 * SA.szum(h, w, ziarno + 4, 4), 0, 1)
    rgb = rgb * (1 - mg[..., None]) + 250 * mg[..., None]
    kresk = ((xx + yy) % 3.0) < 0.35
    perg = np.where(kresk[..., None], np.array([170, 150, 110], np.float32), np.array([236, 224, 196], np.float32))
    a = np.clip((nz - 0.35) * 3, 0, 1)[..., None]
    rgb = rgb * (1 - a) + perg * a
    teren.pola = {"e": e, "lad": lad, "veg": veg, "z": z / px_mm, "px_mm": px_mm}     # dla sceny 3D (Blender)
    rgb = pikseloza(rgb, dane, px_mm)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), W_mm, H_mm


def pikseloza(rgb, dane, px_mm):
    """Łącza zdalne (pasmo mowy): teren heksu „rozpada się na piksele” proporcjonalnie do udziału mowy przez łącze.
    NB (telefon wąskopasmowy, ściana ~3,4 kHz) = grube piksele 4,8 mm; WB (HD Voice / komunikator 16 kHz, ściana ~7 kHz) = drobne 2,6 mm.
    Siła = udział / 40 %% (40 %% i więcej = cały heks spikselowany). Godziny bez pomiaru pasma — bez zmian."""
    from PIL import ImageDraw
    h, w = rgb.shape[:2]
    wynik = rgb.copy()
    for klucz, blok_mm in (("tel_wb_pct", 2.6), ("tel_nb_pct", 4.8)):
        maska = Image.new("L", (w, h), 0)
        dr = ImageDraw.Draw(maska)
        jest = False
        for (i, j), g in dane.items():
            v = ((g or {}).get("e1") or {}).get(klucz, 0)
            if v <= 2:
                continue
            jest = True
            cx, cy = SA.srodek(i, j)
            dr.polygon([(x * px_mm, y * px_mm) for x, y in SA.wierzcholki(cx, cy)], fill=int(255 * min(1.0, v / 40.0)))
        if not jest:
            continue
        b = max(2, int(blok_mm * px_mm))
        im = Image.fromarray(np.clip(wynik, 0, 255).astype(np.uint8))
        pix = np.asarray(im.resize((max(1, w // b), max(1, h // b)), Image.BOX).resize((w, h), Image.NEAREST), np.float32)
        # siatka „ekranu” na pikselach: cienkie ciemniejsze linie między blokami
        yy, xx = np.mgrid[0:h, 0:w]
        pix = pix * np.where(((xx % b) == 0) | ((yy % b) == 0), 0.80, 1.0)[..., None]
        al = np.asarray(maska, np.float32)[..., None] / 255
        wynik = wynik * (1 - al) + pix * al
    return wynik


# ---------------------------------------------------------------- symbole na heksie
SKALY = '<path d="M2 20l5-9 3 4 4-8 8 13z"/><path d="M12 11l2 3"/>'
STRUMIEN = '<path d="M2 9c3-2 5 2 8 0s5-2 8 0 3 1 4 0M2 15c3-2 5 2 8 0s5-2 8 0 3 1 4 0"/>'
POLANA = '<path d="M12 3c2 3-1 4 1 7 1-1 2-2 2-4 2 2 3 4 3 6a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3-1-3 1-4 1-6z"/>'
REKORD = '<path d="M5 21V4"/><path d="M5 4h12l-2 4 2 4H5"/>'
CHMURKA = '<path d="M6.5 18.5h11a4.2 4.2 0 0 0 .6-8.4A6.2 6.2 0 0 0 6.4 11.7 3.4 3.4 0 0 0 6.5 18.5z"/>'
SLUCHAWKA = '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>'
KLODKA = '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'
POSTAC = '<circle cx="12" cy="7" r="3.8"/><path d="M4.5 21.5c.9-4.8 3.8-7.3 7.5-7.3s6.6 2.5 7.5 7.3"/>'
ZEGAR = '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.5l3.5 2"/>'
MONETA = '<circle cx="12" cy="12" r="9"/><path d="M14.8 8.6c-.6-.9-1.6-1.4-2.8-1.4-1.7 0-2.9.9-2.9 2.2 0 3 6 1.7 6 4.8 0 1.3-1.3 2.3-3.1 2.3-1.3 0-2.4-.5-3-1.5M12 5.5v1.7M12 16.8v1.7"/>'


def osada(cx, cy, k):
    h = ""
    for m_ in range(k):
        dx = (m_ - (k - 1) / 2) * 2.5
        h += '<path d="M%.2f %.2fl1.3 -1.4l1.3 1.4v1.8h-2.6z" fill="#FFF8EC" stroke="#3A2A18" stroke-width=".35"/>' % (cx - 1.3 + dx, cy - 0.4 - (m_ % 2) * 0.6)
    return h


def kropki(cx, cy, n):
    return "".join('<circle cx="%.2f" cy="%.2f" r=".95" fill="#0A1318" stroke="#fff" stroke-width=".45"/>' % (cx + (k - (n - 1) / 2) * 2.4, cy) for k in range(n))


def nakladka(dane, dni_lab, h0, ox, oy, zetony=None, z_nazwami=False):
    h = ""
    for (i, j), g in dane.items():
        cx, cy = SA.srodek(i, j)
        cx += ox; cy += oy
        h += '<polygon points="%s" fill="none" stroke="#FFFFFF" stroke-opacity=".9" stroke-width=".5"/>' % " ".join("%.2f,%.2f" % p for p in SA.wierzcholki(cx, cy))
        h += '<text x="%.2f" y="%.2f" font-size="2.5" font-weight="800" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".6" paint-order="stroke">%02d:00</text>' % (
            cx, cy - FLAT * 0.33, (h0 + j) % 24)
        if g is None:
            h += '<text x="%.2f" y="%.2f" font-size="2.2" text-anchor="middle" fill="#5A4A2A" font-style="italic">ziemia nieznana</text>' % (cx, cy + 1)
            continue
        sl = g["slowo"]
        W = wartosc(sl["min"])
        lab = ("%d%%" % round(sl["min"])) if round(sl["min"]) == round(sl["max"]) else "%d–%d%%" % (round(sl["min"]), round(sl["max"]))
        h += '<text x="%.2f" y="%.2f" font-size="2.5" font-weight="800" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".7" paint-order="stroke">%s</text>' % (
            cx, cy + FLAT * 0.39, lab)
        if W:
            h += kropki(cx, cy + (6.0 if z_nazwami else -FLAT * 0.2), W)
            dm = domy_eff(g["mowcy_eff"]) if "mowcy_eff" in g else domy(g["mowcy"])
            h += osada(cx, cy + (2.6 if z_nazwami else 1.6), dm)
            if "mowcy_eff" in g and sl["min"] >= 80 and g["mowcy_eff"] < 1.8:
                h += SA.ikona(cx - 8.4, cy - 1.2, 4.0, SKALY, "#4A4238", 2.2)            # wysoko, ale monolog: skały zamiast lasu
            if (g.get("utwory") or 0) >= 8:
                h += SA.ikona(cx - 8.4, cy + 2.6, 4.0, STRUMIEN, "#1F6F9B", 2.4)         # dużo utworów w godzinie słowa: strumień
            if (g.get("zdarzenia") or 0) > 0:
                h += SA.ikona(cx + 4.4, cy + 2.8, 3.6, POLANA, "#C98A00", 2.2)           # oklaski, śmiech…: polana z ogniskiem
        tel = (g.get("e1") or {}).get("tel_nb_pct", 0) + (g.get("e1") or {}).get("tel_wb_pct", 0)
        if tel >= 10:
            h += SA.ikona(cx + 7.4, cy - 2.8, 4.0, SLUCHAWKA, "#0A1318", 2.0)
            h += ('<text x="%.2f" y="%.2f" font-size="2.3" font-weight="900" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".6" '
                  'paint-order="stroke">%d%%</text>') % (cx + 9.4, cy + 2.9, round(tel))
        if (g.get("e1") or {}).get("dwie_transkrypcje"):
            h += ('<rect x="%.2f" y="%.2f" width="6.2" height="3.4" rx="1" fill="#FFFFFF" stroke="#0A1318" stroke-width=".35"/>'
                  '<text x="%.2f" y="%.2f" font-size="2.5" font-weight="900" text-anchor="middle" fill="#0A1318">2×T</text>') % (cx + 4.2, cy + 3.6, cx + 7.3, cy + 6.2)
        if sl.get("teksty_piosenek"):
            h += '<text x="%.2f" y="%.2f" font-size="3.4" font-weight="900" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".6" paint-order="stroke">♪</text>' % (cx + 6.2, cy + 1.2)
        if not sl["zgodne"] and W:
            h += SA.ikona(cx + 4.2, cy - 1.2, 4.2, CHMURKA, "#0A1318", 2.4).replace('fill="none"', 'fill="#FFFFFF"')
    for i, d in enumerate(dni_lab):
        cx, _ = SA.srodek(i, 0)
        h += '<text x="%.2f" y="%.2f" font-size="3" font-weight="800" text-anchor="middle" fill="#274F5C">%s</text>' % (cx + ox, oy - 1.5, escape(d))
    for (i, j), zid in (zetony or {}).items():
        cx, cy = SA.srodek(i, j)
        h += zeton_lub_znacznik(cx + ox - ZET / 2, cy + oy - ZET / 2, ZET, zid)
    return h


# ---------------------------------------------------------------- żetony i znaczniki (jedna funkcja dla mapy, arkusza i zasad)
ZNACZNIKI = {  # id: (tło, kolor, ikona, opis)
    "konflikt": ("#F9B009", "#0A1318", None, "konflikt"),
    "mgla": ("#E6EEF1", "#274F5C", CHMURKA, "mgła"),
    "rozwiana": ("#FFFFFF", "#23774F", CHMURKA + '<path d="M3 3l18 18"/>', "rozwiana"),
    "poufne": ("#0A1318", "#F9B009", KLODKA, "poufne"),
    "ekipa_r": ("#C98A00", "#FFFFFF", POSTAC, "Redaktor"),
    "ekipa_w": ("#8A5FC4", "#FFFFFF", POSTAC, "Wydawca"),
    "tura": ("#274F5C", "#FFFFFF", ZEGAR, "tura"),
    "budzet": ("#2F7C95", "#FFFFFF", MONETA, "budżet"),
    # HALUCYNACJE: znaczniki ryzyka (5. pole = waga w teście prawdy), notatka reportera, ekipa reportera, skandal
    "ryz_asr": ("#FDE8EC", "#9E1F36", '<path d="M2 12h2l2-5 3 10 3-8 2 6h1.5"/><path d="M17 8.3a2.6 2.6 0 1 1 3.1 2.5c-.6.3-1 .8-1 1.5M19.1 15.4h.01"/>', "ASR · muzyka", 1),
    "ryz_mowca": ("#FDE8EC", "#9E1F36", '<circle cx="6.5" cy="7" r="2.6"/><path d="M2 15.5c.6-2.7 2.3-4.2 4.5-4.2S10.4 12.8 11 15.5"/><circle cx="17.5" cy="7" r="2.6"/><path d="M13 15.5c.6-2.7 2.3-4.2 4.5-4.2s3.9 1.5 4.5 4.2"/><path d="M8 20l8-2M16 20l-8-2"/>', "zły mówca", 1),
    "ryz_nazwisko": ("#F6CBD3", "#7A0F24", '<rect x="2.5" y="5" width="19" height="14" rx="2"/><circle cx="8" cy="11" r="2.2"/><path d="M4.8 16.5c.6-1.8 1.8-2.7 3.2-2.7s2.6.9 3.2 2.7"/><path d="M14.5 9.5a2 2 0 1 1 2.4 2c-.5.2-.8.6-.8 1.1M16.1 15.2h.01"/>', "nazwisko", 2),
    "ryz_cytat": ("#F6CBD3", "#7A0F24", '<path d="M5 17c0-4 1-8 5-10l.8 1.5C8.7 10 8.2 12 8.3 13H11v5H5zM13 17c0-4 1-8 5-10l.8 1.5c-2.1 1.5-2.6 3.5-2.5 4.5H19v5h-6z"/>', "cytat", 2),
    "notatka": ("#C98A00", "#FFFFFF", '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>', "notatka"),
    "ekipa_rep": ("#A3601A", "#FFFFFF", '<circle cx="9" cy="7" r="3.4"/><path d="M2.5 21c.8-4.3 3.4-6.6 6.5-6.6 1.6 0 3 .6 4.1 1.7"/><rect x="16" y="8" width="4.5" height="7.5" rx="2.2"/><path d="M18.2 15.5v4M16 19.5h4.5"/>', "Reporter"),
    "skandal": ("#8A0E1E", "#FFFFFF", '<path d="M4 5h13v14H6a2 2 0 0 1-2-2z"/><path d="M17 8h3v9a2 2 0 0 1-2 2"/><path d="M7 8h7M7 11h7M7 14h4"/>', "skandal"),
}


def znacznik(x, y, a, zid):
    bg, fg, ik, opis = ZNACZNIKI[zid][:4]
    waga = ZNACZNIKI[zid][4] if len(ZNACZNIKI[zid]) > 4 else None
    h = '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>' % (x, y, a, a, bg)
    if ik is None:
        h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="900" text-anchor="middle" fill="%s">!</text>' % (x + a / 2, y + a * .62, a * .5, fg)
    else:
        r = a * .5
        h += SA.ikona(x + (a - r) / 2, y + a * .14, r, ik, fg, 2.2)
    h += '<text x="%.2f" y="%.2f" font-size="%.2f" font-weight="800" text-anchor="middle" fill="%s">%s</text>' % (x + a / 2, y + a * .88, a * .13, fg, escape(opis))
    if waga:
        h += '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/><text x="%.2f" y="%.2f" font-size="%.2f" font-weight="900" text-anchor="middle" fill="%s">+%d</text>' % (
            x + a * .82, y + a * .18, a * .15, fg, x + a * .82, y + a * .23, a * .15, bg, waga)
    return h


def zeton_lub_znacznik(x, y, a, zid, spad=False):
    return znacznik(x, y, a, zid) if zid in ZNACZNIKI else SA.zeton(x, y, a, zid, spad=spad)


# ---------------------------------------------------------------- arkusze pod zasady HALUCYNACJE 2.0 (etapy 108 + znaczniki 81)
ZESTAW = [  # (id, sztuk) — kolejność = pasy do cięcia
    ("live_lokal", 8), ("batch_lokal", 18), ("live_chmura", 6), ("batch_chmura", 10),      # etap 1 Słowa: 42 (transkrypcje się sumują)
    ("diar_live", 4), ("diar_lokal", 13), ("diar_chmura", 5),                               # etap 2 Głosy: 22
    ("kontekst", 4), ("glosoteka", 11), ("przedstawienia", 4), ("wydawca", 4),              # etap 3 Kto: 23
    ("sprawdzenie", 6), ("weryfikacja", 5),                                                 # etap 4 Sprawdzone: 11
    ("szkic_wp", 4), ("odcinek", 3), ("paczka", 3),                                         # etap 5 Wyjście: 10
]
ZESTAW_ZN = [
    ("ryz_asr", 14), ("ryz_mowca", 10), ("ryz_nazwisko", 10), ("ryz_cytat", 6), ("notatka", 6), ("mgla", 8), ("rozwiana", 10),
    ("poufne", 3), ("konflikt", 8), ("ekipa_r", 1), ("ekipa_w", 1), ("ekipa_rep", 1), ("tura", 1), ("budzet", 1), ("skandal", 1),
]
OPIS_ZESTAW = ["Etapy: Słowa 42 (L·LIVE 8, L·GODZ 18, C·LIVE 6, C·GODZ 10) · Głosy 22 · Kto 23 · Sprawdzone 11 · Wyjście 10 (WP, POD, PAK). Razem 108.",
               "Kolor = rola: zielony Kolonia · niebieski Chmura · złoty i fioletowy Redakcja. Liczba w rogu = siła do rzutu (k6 + siła ≥ 7).",
               "Różne transkrypcje tej samej godziny leżą pod żetonem najwyższego etapu — ich liczba to Pewność (1–3)."]
OPIS_ZN = ["Znaczniki ryzyka (+waga w teście prawdy): ASR 14 · zły mówca 10 · nazwisko 10 · cytat 6. Notatka reportera 6 (= transkrypcja).",
           "Mgła 8 · rozwiana 10 · poufne 3 · konflikt 8 · ekipy: Redaktor, Wydawca, Reporter · tura · budżet · skandal. Razem 81.",
           "Karty przekonań i postaci — osobny PDF do druku dwustronnego na papierze fotograficznym."]


def arkusz(zestaw=None, rz=12, opis=None, tytul="Żetony 20 mm — na karton i nożyczki"):
    a, kol = ZET, 9
    zestaw = zestaw or ZESTAW
    x0, y0 = (210 - kol * a) / 2, 38.0
    lista = [z for z, n in zestaw for _ in range(n)]
    assert len(lista) == kol * rz, len(lista)
    h = '<text x="%.1f" y="13" font-size="5.6" font-weight="800" fill="#274F5C">%s</text>' % (x0, escape(tytul))
    rady = ["1. Drukuj w skali 100% (linijka niżej musi mieć 100 mm). 2. Naklej CAŁY arkusz na czystą, wewnętrzną stronę pudełka po pizzy — klej w sztyfcie",
            "   po całej powierzchni, dociśnij książkami, odczekaj godzinę. 3. Tnij nożyczkami najpierw POZIOME pasy przez całą szerokość (wzdłuż znaczników",
            "   na marginesach), potem każdy pas na kwadraty. Tło sięga linii cięcia, więc krzywe cięcie nie zostawi białego brzegu. Żeton = 80% heksu planszy."]
    for k, t in enumerate(rady):
        h += '<text x="%.1f" y="%.1f" font-size="2.55" fill="#0A1318">%s</text>' % (x0, 19 + k * 3.6, escape(t))
    h += SA.linijka(x0, 28.7, 100).replace('sprawdź skalę: ta linijka ma 100 mm · heks 25 mm · żeton 20 mm', '')
    for n, it in enumerate(lista):
        h += zeton_lub_znacznik(x0 + (n % kol) * a, y0 + (n // kol) * a, a, it, spad=True)
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
    ys = y0 + rz * a + 8.5
    for k, t in enumerate(opis or OPIS_ZESTAW):
        h += '<text x="%.1f" y="%.1f" font-size="2.45" fill="#3F5A66">%s</text>' % (x0, ys + k * 3.6, escape(t))
    return h


# ---------------------------------------------------------------- strona mapy scenariusza (A4, 1:1)
def strona_scenariusza(sc, zetony=None, plik_obrazu=None):
    dane, _ = dane_okna(sc["profil"], 1, sc["h0"], 8, sc["tydz"])
    img, W_mm, H_mm = teren(dane, 7, 8, 12.0, 1000 + sc["nr"])
    plik_obrazu = plik_obrazu or "scen%d.jpg" % sc["nr"]
    img.save(os.path.join(TU, plik_obrazu), quality=90)
    ox, oy = (210 - W_mm) / 2, 32.0
    svg = '<text x="%.1f" y="13" font-size="6" font-weight="800" fill="#274F5C">Scenariusz %d · %s</text>' % (ox, sc["nr"], escape(sc["nazwa"]))
    svg += '<text x="%.1f" y="19.5" font-size="2.8" fill="#3F5A66">%s · tydzień 1 · godziny %02d–%02d · tura = dzień (Pn → Nd) · heks 25 mm = godzina · żeton 20 mm</text>' % (
        ox, escape(PR.PROFILE[sc["profil"]]["nazwa"]), sc["h0"], sc["h0"] + 7)
    svg += '<text x="%.1f" y="24" font-size="2.6" fill="#3F5A66">%s</text>' % (ox, escape(sc["opis"]))
    svg += nakladka(dane, DNI, sc["h0"], ox, oy, zetony)
    ly = oy + H_mm + 6
    svg += legenda_gry(ox, ly, W_mm)
    p = sc["progi"]
    svg += ('<text x="%.1f" y="%.1f" font-size="2.7" font-weight="800" fill="#274F5C">Ocena po 7 turach: poniżej %d — %s · %d+ %s · %d+ %s · %d+ %s</text>') % (
        ox, ly + 25, p[0], OCENY[0].lower(), p[0], OCENY[1].lower(), p[1], OCENY[2].lower(), p[2], OCENY[3].lower())
    svg += SA.linijka(ox, ly + 30, 100)
    svg += '<text x="%.1f" y="290" font-size="2.2" fill="#56717C">Teren wygenerowany proceduralnie z ramówki rozgłośni (nie z nagrań). HALUCYNACJE · Świat anteny 1.0 · Radio Wnet · Szpieg+ · gra.l00p.ai</text>' % ox
    return ('<div class="s"><img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
            '<svg class="p" viewBox="0 0 210 297">%s</svg></div>') % (plik_obrazu, ox, oy, W_mm, H_mm, svg)


def legenda_gry(x, y, w, pion=False):
    h = '<text x="%.1f" y="%.1f" font-size="3.3" font-weight="800" fill="#274F5C">Teren (dolna liczba „słowo”)</text>' % (x, y)
    y += 2.5
    gw = w * (0.98 if pion else 0.56)
    for k in range(200):
        c = SA.koloruj(np.array([k / 2]))[0]
        h += '<rect x="%.2f" y="%.1f" width="%.2f" height="4" fill="rgb(%d,%d,%d)"/>' % (x + gw * k / 200, y, gw / 200 + .05, *c.astype(int))
    for v, t in ((0, "morze <32,53%"), (33, "łąka ●"), (60, "pole ●●"), (80, "wzgórza ●●●")):
        xx = x + gw * v / 100
        h += '<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="#0C2C3C" stroke-width=".5"/>' % (xx, y - .8, xx, y + 4.8)
        h += '<text x="%.2f" y="%.1f" font-size="2.3" fill="#0A1318">%s</text>' % (xx + .6, y + 7.6, t)
    h += '<text x="%.1f" y="%.1f" font-size="2.3" fill="#3F5A66">kropki ● = wartość W heksu (mnożnik punktów) · morze i ziemia nieznana nie dają punktów</text>' % (x, y + 11.2)
    x2, y = (x, y + 16.5) if pion else (x + w * 0.6, y)
    it = [("domy", "osada 1–3 domy = głosy 1–3 / 4–6 / 7+: −0/−1/−2 do Głosów i Kto"), ("mgla", "mgła: metody różnią się > 5 pp: −1 maszynom (etap 1, 2, 4)"),
          ("perg", "ziemia nieznana: brak nagrania — nieprzejezdna")]
    for k, (ik, t) in enumerate(it):
        yy = y + 1 + k * 4.6
        if ik == "domy":
            h += osada(x2 + 2.5, yy - .2, 3)
        elif ik == "mgla":
            h += SA.ikona(x2 + .5, yy - 3.2, 4.2, CHMURKA, "#0A1318", 2.4).replace('fill="none"', 'fill="#FFFFFF"')
        else:
            h += '<rect x="%.1f" y="%.1f" width="5" height="3" fill="#ECE0C4" stroke="#AA966E" stroke-width=".3"/>' % (x2, yy - 2.4)
        h += '<text x="%.1f" y="%.1f" font-size="2.2" fill="#0A1318">%s</text>' % (x2 + 6.5, yy, escape(t))
    return h


# ---------------------------------------------------------------- karta pomocy (A4)
def karta_pomocy():
    import zasady_gry as ZG
    return ZG.karta_pomocy_html()


# ---------------------------------------------------------------- plansza A0 profilu (sezon 4 tygodnie × 24 h)
def plansza_a0(profil):
    dane, zd = dane_okna(profil, 4, 0, 24)
    img, W_mm, H_mm = teren(dane, 28, 24, 5.0, {"klasyczne": 11, "muzyczne": 22, "informacyjne": 33, "idealne": 44, "idealne_polonia": 44}[profil])
    plik = "a0_%s.jpg" % profil
    img.save(os.path.join(TU, plik), quality=88)
    szer, wys = 841, 1189
    ox, oy = (szer - W_mm) / 2, 175.0
    lab = ["T%d %s" % (i // 7 + 1, DNI[i % 7]) for i in range(28)]
    nr = {"idealne": "Plansza 2 · ", "idealne_polonia": "Plansza 3 · "}.get(profil, "Świat anteny · ")
    svg = '<text x="%.1f" y="95" font-size="%d" font-weight="800" fill="#274F5C">%s%s</text>' % (ox, 24 if len(PR.PROFILE[profil]["nazwa"]) < 50 else 17, nr, escape(PR.PROFILE[profil]["nazwa"]))
    svg += '<text x="%.1f" y="115" font-size="7.5" fill="#3F5A66">Sezon: 4 tygodnie × 24 godziny · heks 25 mm = godzina · kolumna = dzień · teren z ramówki, nie z nagrań · skala 1:1 z żetonami 20 mm</text>' % ox
    if zd:
        svg += '<text x="%.1f" y="130" font-size="6.5" fill="#3F5A66">Zdarzenia sezonu: %s</text>' % (ox, escape(" · ".join(
            "T%d %s: %s%s" % (t + 1, DNI[dz], n, "" if n == "Dzień świąteczny" else " %02d–%02d" % (a, b)) for t, n, dz, a, b, _ in zd)))
    svg += nakladka(dane, lab, 0, ox, oy)
    for (i, j), g in dane.items():                                   # noc dla Polonii: awatary (AI) i powtórki
        if g and g.get("kat") in ("awatar", "powt"):
            cx, cy = SA.srodek(i, j)
            cx += ox; cy += oy
            if g["kat"] == "awatar":
                svg += '<rect x="%.2f" y="%.2f" width="6.4" height="3.8" rx="1" fill="#7E57B8"/><text x="%.2f" y="%.2f" font-size="2.8" font-weight="900" text-anchor="middle" fill="#fff">AI</text>' % (
                    cx - 10.2, cy - 7.2, cx - 7.0, cy - 4.3)
            else:
                svg += '<text x="%.2f" y="%.2f" font-size="4.2" font-weight="900" text-anchor="middle" fill="#274F5C" stroke="#fff" stroke-width=".6" paint-order="stroke">↺</text>' % (cx - 7.0, cy - 3.8)
    if profil == "idealne_polonia":
        svg += ('<text x="%.1f" y="143" font-size="6" fill="#3F5A66">AI = program dla Polaków za granicą prowadzony przez awatary głosów Radia Wnet — wyłącznie na podstawie zgód '
                'w nowej wersji umów (o dzieło, zlecenia, B2B, o pracę), zawsze oznaczony na antenie · ↺ = powtórka dnia.</text>') % ox
    elif profil == "idealne":
        svg += ('<text x="%.1f" y="143" font-size="6" fill="#3F5A66">Wzorzec formatu (nie historyczna ramówka): gęste słowo w dzień jak w mówionych kanałach BBC, '
                'audycje autorskie i słuchowiska jak w Trójce ery Skowrońskiego; nocą ocean muzyki.</text>') % ox
    for t in range(1, 4):        # granice tygodni
        x = ox + SA.srodek(t * 7, 0)[0] - S * 0.75
        svg += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#274F5C" stroke-width="1.2" stroke-dasharray="6 3"/>' % (x, oy - 6, x, oy + H_mm + 2)
    for sc in SCENARIUSZE:       # ramki scenariuszy
        if sc["profil"] != profil:
            continue
        x0 = ox + SA.srodek(sc["tydz"] * 7, 0)[0] - S - 1.5
        x1 = ox + SA.srodek(sc["tydz"] * 7 + 6, 0)[0] + S + 1.5
        y0 = oy + sc["h0"] * FLAT - 1.5
        y1 = oy + (sc["h0"] + 8) * FLAT + FLAT / 2 + 1.5
        svg += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#F9B009" stroke-width="2.2" stroke-dasharray="8 3"/>' % (x0, y0, x1 - x0, y1 - y0)
        svg += '<rect x="%.1f" y="%.1f" width="58" height="9" fill="#F9B009"/><text x="%.1f" y="%.1f" font-size="5" font-weight="800" fill="#0A1318">Scenariusz %d · %s</text>' % (
            x1 + 2, y0, x1 + 4, y0 + 6.5, sc["nr"], escape(sc["nazwa"]))
    ly = oy + H_mm + 14
    import zasady_halucynacje as ZG
    svg += '<g transform="translate(%.1f %.1f) scale(1.9) translate(%.1f %.1f)">%s</g>' % (ox, ly, -ox, -ly, legenda_gry(ox, ly, 165 / 1.9, pion=True))
    svg += ZG.tory_svg(ox, ly + 78)
    svg += SA.linijka(ox, ly + 162, 100)
    yy = ly + 188
    for sc in SCENARIUSZE:
        if sc["profil"] != profil:
            continue
        p = sc["progi"]
        svg += '<rect x="%.1f" y="%.1f" width="6" height="6" fill="#F9B009"/><text x="%.1f" y="%.1f" font-size="6" font-weight="800" fill="#274F5C">Scenariusz %d · %s (T1, %02d–%02d)</text>' % (
            ox, yy - 5, ox + 9, yy, sc["nr"], escape(sc["nazwa"]), sc["h0"], sc["h0"] + 7)
        svg += '<text x="%.1f" y="%.1f" font-size="4.2" fill="#3F5A66">%s</text>' % (ox + 9, yy + 7, escape(sc["opis"]))
        svg += '<text x="%.1f" y="%.1f" font-size="4.2" fill="#0A1318">Ocena: %d+ kolegium przyjmuje · %d+ dobry tydzień · %d+ wzorowa redakcja</text>' % (ox + 9, yy + 13, *p)
        yy += 26
    svg += '<text x="%.1f" y="%.1f" font-size="4.2" fill="#3F5A66">Własny scenariusz: dowolne 7 dni × 8 godzin tej planszy; progi jak w scenariuszu tej rozgłośni.</text>' % (ox, yy + 2)
    kcss, ktresc = ZG.karta_pomocy_html(tylko_tresc=True)
    karta = '<style>%s .kpa{position:absolute;left:%.1fmm;top:%.1fmm;width:186mm;transform:scale(1.62);transform-origin:0 0} .kpa .kp{position:static}</style><div class="kpa"><div class="kp">%s</div></div>' % (
        kcss, ox + 312, ly - 4, ktresc)
    svg += '<text x="%.1f" y="%.1f" font-size="5" fill="#56717C">HALUCYNACJE · Świat anteny 1.0 · plansza proceduralna (profile_rozglosni.py) · Radio Wnet · Szpieg+ · gra.l00p.ai · przygotowane z pomocą AI (Claude)</text>' % (ox, wys - 14)
    html = ('<div class="s"><img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
            '<svg class="p" viewBox="0 0 %d %d">%s</svg>%s</div>') % (plik, ox, oy, W_mm, H_mm, szer, wys, svg, karta)
    return html


def main():
    import zasady_halucynacje as ZH
    s1 = SCENARIUSZE[0]
    przyklad = {(1, 2): "batch_lokal", (1, 3): "glosoteka", (2, 2): "live_lokal", (0, 4): "konflikt", (1, 4): "ekipa_r", (0, 3): "ryz_nazwisko"}
    strony = [strona_scenariusza(s1, przyklad, "scen1_przyklad.jpg"),
              '<div class="s"><svg class="p" viewBox="0 0 210 297">%s</svg></div>' % arkusz(),
              '<div class="s"><svg class="p" viewBox="0 0 210 297">%s</svg></div>' % arkusz(ZESTAW_ZN, 9, OPIS_ZN, "Znaczniki 20 mm — ryzyko, mgła, ekipy, tory"),
              ZH.karta_pomocy_html(), ZH.tory_html()]
    SA.drukuj(strony, 210, 297, "Zestaw_startowy_A4.pdf")
    SA.drukuj([strona_scenariusza(sc) for sc in SCENARIUSZE], 210, 297, "Scenariusze_A4.pdf")
    if "--a0" in sys.argv:
        for p in PR.PROFILE:
            SA.drukuj([plansza_a0(p)], 841, 1189, "Plansza_A0_%s.pdf" % p)

if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- MAPA PRAWDY: prawdziwa antena, 4 tygodnie × 24 h (intro HALUCYNACJE)
def dane_prawdy(start="2026-08-31", tygodnie=4):
    """Dane mapy prawdy: z archiwum Szpiega+ (redakcja) albo z migawki dane/mapa_prawdy_*.json (repozytorium publiczne).
    Po każdym przeliczeniu z archiwum migawka jest odświeżana — zawiera wyłącznie agregaty godzin (bez nagrań, transkrypcji i nazwisk)."""
    import datetime as _dt
    import sciezki
    if not sciezki.ARCHIWUM and os.path.exists(sciezki.MIGAWKA):
        m = json.load(open(sciezki.MIGAWKA, encoding="utf-8"))
        return m["dni"], {tuple(int(v) for v in k.split(",")): g for k, g in m["heksy"].items()}
    d0 = _dt.date.fromisoformat(start)
    dni = [(d0 + _dt.timedelta(days=k)).isoformat() for k in range(tygodnie * 7)]
    dane = {(i, j): godzina_prawdy(d, h) for i, d in enumerate(dni) for j, h in enumerate(range(24))}
    kal = kalendarz_godzin(dni[0], dni[-1])
    for (i, j), g in dane.items():               # meta.program jest dopiero od 12.09 — wcześniej ramówka z kalendarza (ta sama, z której 3D bierze kolory laserów)
        k = "%s %02d" % (dni[i], j)
        if g is not None and not g.get("prog") and k in kal:
            g["prog"] = dict(kal[k], z_kalendarza=True)
    for g in dane.values():                      # rodzaj audycji z PEŁNEJ nazwy (np. „Magda” = publicystyka), zanim nazwa trafi na mapę bez osób
        if g and g.get("prog") and g["prog"].get("nazwa"):
            g["prog"]["kategoria"] = kategoria(g["prog"]["nazwa"])
    if kal:                                      # migawkę zapisuje tylko pełny przebieg (z kalendarzem) — częściowy nie może jej nadpisać
        zapisz_migawke(dni, dane)
    return dni, dane


# Zajętość studia (studio_kp.py) godzina po godzinie = obecność prowadzących w redakcji — tylko do użytku redakcji, nigdy w migawce publicznej
E1_PRYWATNE = ("studio_kp", "realizator_sm7b")


def zapisz_migawke(dni, dane):
    import copy
    import sciezki
    import legenda_mapy as LM
    heksy = {}
    for (i, j), g in dane.items():
        g = copy.deepcopy(g)
        if g and g.get("prog"):
            g["prog"] = {"nazwa": nazwa_bez_prowadzacego(g["prog"]["nazwa"]), "kategoria": g["prog"].get("kategoria"),
                         "start": g["prog"].get("start"), "koniec": g["prog"].get("koniec"),
                         "z_kalendarza": bool(g["prog"].get("z_kalendarza"))}
        if g:
            g.pop("program", None)                      # surowa nazwa z metadanych (bywa z prowadzącym)
            for k in E1_PRYWATNE:
                (g.get("e1") or {}).pop(k, None)
        heksy["%d,%d" % (i, j)] = g
    os.makedirs(os.path.dirname(sciezki.MIGAWKA), exist_ok=True)
    json.dump({"opis": "HALUCYNACJE · mapa prawdy Radia Wnet: agregaty godzin anteny (bez nagrań, transkrypcji i danych osobowych)",
               "zakres": [dni[0], dni[-1]], "dni": dni, "liczniki": LM._liczniki(dane), "heksy": heksy},
              open(sciezki.MIGAWKA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


def kalendarz_godzin(od, do):
    """Godzina → {nazwa, start, koniec} z publicznego kalendarza „Nowa ramówka” (ramowka_7lat/wystapienia.json)."""
    p = os.path.join(TU, "ramowka_7lat", "wystapienia.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for x in json.load(open(p, encoding="utf-8")):
        if not (od <= x["d"] <= do):
            continue
        a = _min(x["start"])
        b = a + max(x["min"], 1)
        for m in range(a - a % 60, b, 60):
            if m >= a - 30 and m < 1440:
                out["%s %02d" % (x["d"], m // 60)] = {"nazwa": x["nazwa"], "start": x["start"], "koniec": x["koniec"]}
    return out


def statystyki(dane):
    """Liczby do porównania: godziny z pomiarem, mgła (brak pomiaru), słowo w nocy (00–05) i w oknie koncesji (06–23) — dolna granica."""
    zm = {k: g for k, g in dane.items() if g}
    noc = [g["slowo"]["min"] for (i, j), g in zm.items() if j < 6]
    dzien = [g["slowo"]["min"] for (i, j), g in zm.items() if j >= 6]
    return {"godzin": len(dane), "z_pomiarem": len(zm), "bez_pomiaru": len(dane) - len(zm),
            "noc_slowo": round(sum(noc) / len(noc), 1) if noc else None, "okno_slowo": round(sum(dzien) / len(dzien), 1) if dzien else None,
            "morze_noc": sum(1 for x in noc if x < PROG), "noc_godzin": len(noc)}


def plansza_prawdy_a0():
    dni, dane = dane_prawdy()
    img, W_mm, H_mm = teren(dane, 28, 24, 5.0, 77)
    img.save(os.path.join(TU, "a0_prawda.jpg"), quality=88)
    szer, wys = 841, 1189
    ox, oy = (szer - W_mm) / 2, 205.0
    lab = ["%s %s" % (DNI[k % 7], d[8:10] + "." + d[5:7]) for k, d in enumerate(dni)]
    mgly = {k: "mgla" for k, g in dane.items() if g is None}          # szczerze: godzina bez pomiaru = żeton mgły
    rek = rekordy(dane)
    st, ideal = statystyki(dane), statystyki(dane_okna("klasyczne", 4, 0, 24)[0])
    svg = '<text x="%.1f" y="95" font-size="17" font-weight="800" fill="#274F5C">Plansza 1 · Antena bez słuchania — mapa prawdy Radia Wnet, 31.08–27.09.2026</text>' % ox
    svg += ('<text x="%.1f" y="115" font-size="7.5" fill="#3F5A66">Prawdziwa antena: teren z pomiarów Szpiega+ (dolna granica %% słowa z dwóch metod lokalnych). '
            'Godzina bez pomiaru = żeton mgły.</text>') % ox
    svg += ('<text x="%.1f" y="130" font-size="6.5" fill="#3F5A66">Z pomiarem %d z %d godzin · pod mgłą %d · słowo w oknie 06–23: %.1f%% · w nocy 00–05: %.1f%% '
            '(idealna ramówka klasyczna: %.1f%% i %.1f%%)</text>') % (ox, st["z_pomiarem"], st["godzin"], st["bez_pomiaru"], st["okno_slowo"], st["noc_slowo"],
                                                                     ideal["okno_slowo"], ideal["noc_slowo"])
    svg += nakladka({k: g for k, g in dane.items()}, lab, 0, ox, oy, mgly, z_nazwami=True)
    svg += latarnie(dane, dni, ox, oy)                               # najpierw: dopisuje stałe sloty tam, gdzie meta nie zna ramówki
    svg += bloki_audycji(dane, lab, ox, oy)
    svg += nazwy_audycji(dane, ox, oy)
    svg += ('<text x="%.1f" y="182" font-size="5.5" fill="#3F5A66">Nowe warstwy: poszarpany brzeg i wyspy = dużo przejść mowa↔muzyka · strome, żebrowane zbocza = szybka mowa (sylaby/s, bez serwisu) · '
            'turkusowe laguny i plaże = mowa na tle muzyki (tagi: %s).</text>') % (ox, _pokrycie("tagi"))
    svg += ('<text x="%.1f" y="196" font-size="5.5" fill="#3F5A66">Piksele = mowa przez łącze zdalne (pasmo w widmie tury): drobne — HD Voice / komunikator 16 kHz (ściana ~7 kHz), '
            'grube — telefon wąskopasmowy (ściana ~3,4 kHz); słuchawka + %% = udział w mowie godziny. Łącza pełnopasmowe są nie do odróżnienia od studia. %s</text>') % (ox, "" if _pokrycie("pasmo", True) else "POMIAR W TOKU — warstwa jeszcze nie na planszy.")
    svg += ('<text x="%.1f" y="190" font-size="5.5" fill="#3F5A66">Miraż: drgające smugi = szacowana rozbieżność transkrypcji (proxy WER z pewności słów whispera, kalibracja na godzinach ze Scribe v2) · '
            '2×T = dwie niezależne transkrypcje (lokalna + chmura) — heks czysty i jaśniejszy.</text>') % ox
    svg += ('<text x="%.1f" y="166" font-size="5.5" fill="#3F5A66">Obrysy = audycje dłuższe niż godzina albo od :30 (kolor: publicystyka · muzyka · kultura · zagranica). '
            'Ramówka z metadanych godzin (od 12.09); wcześniej tylko audycje-latarnie z historii kalendarza.</text>') % ox
    svg += ('<text x="%.1f" y="174" font-size="5.5" fill="#3F5A66">Latarnie = audycje od lat w tym samym miejscu ramówki (kalendarz „Nowa ramówka”, 35 tys. wpisów 06.2019–09.2026): '
            '„8 lat” = kolejne lata kalendarzowe z min. 8 tygodniami w tym slocie; pełna — potwierdzają różne serie kalendarza, obrys — jedna seria.</text>') % ox
    OPIS_REK = {"szczyt": "najwyższy szczyt", "miasto": "największe miasto", "strumien": "najwięcej muzyki na lądzie", "mgla": "najgęstsza mgła",
                "zbocze": "najbardziej strome zbocze", "archipelag": "największy archipelag", "laguna": "największa laguna"}

    def wartosc_rek(t, g):
        e1 = g.get("e1") or {}
        if t == "szczyt":
            return "słowo %d%%, %d metody" % (round(__import__("statistics").median(g["slowo"]["metody"].values())), g["slowo"]["n"])
        return {"miasto": lambda: "%.1f głosu" % g["mowcy_eff"], "strumien": lambda: "%d utworów" % g["utwory"],
                "mgla": lambda: "rozrzut %.0f pp" % g["slowo"]["rozrzut_pp"], "zbocze": lambda: ("%.2f sylaby/s" % e1["tempo"]).replace(".", ","),
                "archipelag": lambda: "%d przejść mowa↔muzyka" % e1["przejscia"], "laguna": lambda: "%d s mowy na muzyce" % e1["mowa_muzyka_s"]}[t]()
    for n, (typ, (i, j)) in enumerate(rek.items(), 1):
        cx, cy = SA.srodek(i, j)
        svg += '<circle cx="%.2f" cy="%.2f" r="3.4" fill="#F9B009" stroke="#0A1318" stroke-width=".5"/><text x="%.2f" y="%.2f" font-size="3.6" font-weight="900" text-anchor="middle" fill="#0A1318">%d</text>' % (
            ox + cx + 7.5, oy + cy - 7.5, ox + cx + 7.5, oy + cy - 6.2, n)
    wpisy = ["%d %s — %s %02d:00 (%s)" % (n, OPIS_REK[t], lab[i], j, wartosc_rek(t, dane[(i, j)])) for n, (t, (i, j)) in enumerate(rek.items(), 1)]
    for k, grupa in enumerate((wpisy[:4], wpisy[4:])):
        if grupa:
            svg += '<text x="%.1f" y="%.1f" font-size="6.2" font-weight="800" fill="#274F5C">%s%s</text>' % (ox, 143 + k * 8, "Rekordy: " if k == 0 else "", escape(" · ".join(grupa)))
    ly = oy + H_mm + 12
    import legenda_mapy as LM
    svg += LM.legenda(dane, dni, img, 5.0, rek, 16, ly, szer - 32, wys - ly - 24)
    svg += '<text x="%.1f" y="%.1f" font-size="5" fill="#56717C">HALUCYNACJE · Świat anteny · dane: szpieg_media (meta.json: SMD i segmenty transkrypcji) · przygotowane z pomocą AI (Claude)</text>' % (ox, wys - 14)
    html = ('<div class="s"><img src="a0_prawda.jpg" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
            '<svg class="p" viewBox="0 0 %d %d">%s</svg></div>') % (ox, oy, W_mm, H_mm, szer, wys, svg)
    return html, st, ideal


# ---------------------------------------------------------------- TEREN 2.0 mapy prawdy: więcej prawd statystycznych z meta.json
def godzina_prawdy(d, h):
    """% słowa z metod: SMD (meta albo miod.json pszczoły), segmenty transkrypcji, tagi (sidecar *.tagi.json);
    głosy efektywne = odwrotność indeksu Simpsona z sekund na mówcę (krótkie wejścia ważą mało); utwory; zdarzenia audio."""
    import glob
    import json as _j
    P = SA.P
    pre = "sr_program_%s_%02d" % (d.replace("-", "_"), h)
    pm = os.path.join(SA.MEDIA, d, pre + ".meta.json")
    pom, dl, meta = {}, 3600.0, None
    if os.path.exists(pm):
        meta = _j.load(open(pm, encoding="utf-8"))
        pom, dl = P.slowo_z_meta(meta.get("statystyki"))
    else:
        mi = glob.glob(os.path.join(SA.MEDIA, "_mrowisko", d, pre, pre + ".miod.json"))
        if mi:
            m = _j.load(open(mi[0], encoding="utf-8"))
            if m.get("speech_dur") is not None:
                pom["smd"], dl = m["speech_dur"], float(m.get("dur") or 3600)
    pt = os.path.join(SA.MEDIA, d, pre + ".tagi.json")
    if os.path.exists(pt):
        t = _j.load(open(pt, encoding="utf-8"))
        if t.get("pct") is not None:
            pom["tagi"] = t["pct"] / 100.0 * dl
    ps = os.path.join(SA.MEDIA, d, pre + ".scribe_slowo.json")
    if os.path.exists(ps):                                               # czwarte, zewnętrzne źródło (Scribe v2) dla wybranych godzin
        sc = _j.load(open(ps, encoding="utf-8"))
        if sc.get("pct") is not None:
            pom["scribe"] = sc["pct"] / 100.0 * dl
    # teksty piosenek: ASR (whisper i Scribe) zapisuje śpiewane słowa — w godzinach muzyki zawyża „segmenty” o 45–60 pp
    # (sprawdzone 27.09 na 10 godzinach ~05:00 Scribe'em). Wtedy transkrypcje nie mierzą mowy: zostają SMD i tagi.
    n_utw = len((meta or {}).get("utwory") or [])
    teksty = False
    if "smd" in pom and pom["smd"] / dl * 100 < PROG and n_utw >= 5:
        asr = [pom[k] for k in ("segmenty", "scribe") if k in pom]
        if asr and max(asr) / dl * 100 - pom["smd"] / dl * 100 > 25:
            teksty = True
            pom = {k: v for k, v in pom.items() if k not in ("segmenty", "scribe")}
    sl = P.procent_slowa(pom, dl, SA.M)
    if not sl:
        return None
    sl["teksty_piosenek"] = teksty
    st = (meta or {}).get("statystyki") or {}
    spm = [v for v in (st.get("sekundy_per_mowca") or {}).values() if v > 0]
    T = sum(spm) or 1.0
    eff = 1.0 / sum((v / T) ** 2 for v in spm) if spm else 0.0
    pr = (meta or {}).get("program") if isinstance((meta or {}).get("program"), dict) else None
    return {"prog": {k: pr.get(k) for k in ("nazwa", "start", "koniec")} if pr and pr.get("nazwa") else None,
            "slowo": sl, "mowcy": len(spm), "mowcy_eff": round(eff, 2), "utwory": len((meta or {}).get("utwory") or []),
            "zdarzenia": len((meta or {}).get("zdarzenia_audio") or []), "e1": etap1(d, h), "program": ((meta or {}).get("program") or {}).get("nazwa") if isinstance((meta or {}).get("program"), dict) else (meta or {}).get("program")}


_E1 = {}


def _pokrycie(k, czy=False):
    p = os.path.join(TU, "warstwy_etap1.json")
    po = json.load(open(p, encoding="utf-8")).get("pokrycie", {}) if os.path.exists(p) else {}
    n, g = po.get(k, 0), po.get("godzin", 0) or 1
    return n / g >= 0.9 if czy else "%d z %d godzin" % (n, g)


def etap1(d, h):
    if not _E1:
        p = os.path.join(TU, "warstwy_etap1.json")
        _E1.update(json.load(open(p, encoding="utf-8"))["godziny"] if os.path.exists(p) else {"_": {}})
    return _E1.get("%s %02d" % (d, h), {})


def domy_eff(eff):
    return 1 if eff < 2 else (2 if eff < 4 else 3)


def rekordy(dane):
    """Matematycznie: najwyższy szczyt (dolna granica słowa, ≥ 2 metody), największe miasto (głosy efektywne),
    najbardziej muzyczna godzina lądu (utwory), najgęstsza mgła (rozrzut metod)."""
    zm = {k: g for k, g in dane.items() if g}
    out = {}
    kand = {k: g for k, g in zm.items() if g["slowo"]["n"] >= 2}
    if kand:                                    # rekord: MEDIANA metod (minimum karałoby godziny z większą liczbą pomiarów)
        import statistics as _st
        out["szczyt"] = max(kand, key=lambda k: (_st.median(kand[k]["slowo"]["metody"].values()), kand[k]["slowo"]["n"]))
    lad = {k: g for k, g in zm.items() if g["slowo"]["min"] >= PROG}       # na morzu diaryzacja liczy śpiewaków — miasto tylko na lądzie
    if any(g.get("mowcy_eff") for g in lad.values()):
        out["miasto"] = max(lad, key=lambda k: lad[k].get("mowcy_eff") or 0)
    if lad and any(g.get("utwory") for g in lad.values()):
        out["strumien"] = max(lad, key=lambda k: lad[k].get("utwory") or 0)
    out["mgla"] = max(zm, key=lambda k: zm[k]["slowo"]["rozrzut_pp"])
    e1 = lambda k, f: (zm[k].get("e1") or {}).get(f) or 0
    lad2 = {k: g for k, g in lad.items() if (g.get("e1") or {}).get("tempo_s", 0) >= 900}
    if lad2:
        out["zbocze"] = max(lad2, key=lambda k: e1(k, "tempo"))
    if any(e1(k, "przejscia") for k in zm):
        out["archipelag"] = max(zm, key=lambda k: e1(k, "przejscia"))
    if any(e1(k, "mowa_muzyka_s") for k in zm):
        out["laguna"] = max(zm, key=lambda k: e1(k, "mowa_muzyka_s"))
    return out


# ---------------------------------------------------------------- audycje na mapie prawdy: bloki z ramówki zapisanej przy godzinie (meta.program)
KAT_KOL = {"pub": "#F9B009", "muz": "#E0524A", "kult": "#3BB47E", "zagr": "#84B0BF", "info": "#367F96", "styl": "#3D92C9", "wiara": "#274F5C"}


def kategoria(nazwa):
    n = (nazwa or "").lower()
    for klucze, k in (("poranek odyseja popołudnie magda klub świetlik wieczór prawo taktyka podsumowanie woś limes czarne", "pub"),
                      ("muzyk muzyka chart latina tygodniówka karmienia britbit pokój hands dolce", "muz"),
                      ("kalejdoskop gawęda cienie sofa kiedyś żebyś nieregularnik festina kino solidarność", "kult"),
                      ("studio program wschodni zwyciężajmy tres ponad", "zagr"), ("serwis", "info"), ("anioł ewangelii riksza hildegardy wstać", "wiara")):
        if any(w in n for w in klucze.split()):
            return k
    return "styl"


def kategoria_heksu(g, latarnia=None):
    """Jedno źródło koloru audycji dla 2D (obrysy bloków) i 3D (lasery): ramówka godziny, a gdy jej brak — latarnia."""
    pr = (g or {}).get("prog")
    if pr and pr.get("nazwa"):
        return pr.get("kategoria") or kategoria(pr["nazwa"])
    return kategoria(latarnia["nazwa"]) if latarnia else None


def _min(t):
    try:
        return int(t[:2]) * 60 + int(t[3:5])
    except (TypeError, ValueError):
        return None


def bloki_audycji(dane, lab, ox, oy):
    """Grube, kolorowe obrysy heksów audycji dłuższych niż godzina albo zaczynających się o :30; etykieta na pierwszej godzinie bloku."""
    h = ""
    for (i, j), g in sorted(dane.items()):
        pr = (g or {}).get("prog")
        if not pr:
            continue
        a, b = _min(pr.get("start")), _min(pr.get("koniec"))
        if a is None or b is None:
            continue
        b = b if b > a else b + 1440
        if b - a <= 60 and a % 60 == 0:
            continue
        kol = KAT_KOL[kategoria_heksu(g)]
        cx, cy = SA.srodek(i, j)
        cx += ox; cy += oy
        h += '<polygon points="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-opacity=".95"/>' % (
            " ".join("%.2f,%.2f" % q for q in SA.wierzcholki(cx, cy, S * 0.9)), kol)
        if j == a // 60:                                               # pierwsza godzina bloku: etykieta
            dl = (b - a) / 60
            txt = "%s–%s" % (pr["start"][:5], pr["koniec"][:5])
            h += '<rect x="%.2f" y="%.2f" width="%.2f" height="3.4" rx=".8" fill="%s"/><text x="%.2f" y="%.2f" font-size="2.4" font-weight="800" text-anchor="middle" fill="#0A1318">%s</text>' % (
                cx - 8, cy - S * 0.98, 16, kol, cx, cy - S * 0.98 + 2.55, escape(txt))
    return h


def nazwa_bez_prowadzacego(n):
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ramowka_7lat"))
    import analiza as _A
    return _A.kanon(n, True)


def _zawin(t, szer=21):
    slowa, linie = t.split(), [""]
    for w in slowa:
        if len(linie[-1]) + len(w) + (1 if linie[-1] else 0) > szer and linie[-1]:
            linie.append(w)
        else:
            linie[-1] = (linie[-1] + " " + w).strip()
    return linie[:3]


def nazwy_audycji(dane, ox, oy):
    """Nazwa audycji w każdym heksie, który ma ramówkę (meta.program albo latarnia): gruby, wąski krój, max 2 linie."""
    h = ""
    for (i, j), g in dane.items():
        pr = (g or {}).get("prog")
        if not pr or not pr.get("nazwa"):
            continue
        cx, cy = SA.srodek(i, j)
        cx += ox; cy += oy
        linie = _zawin(nazwa_bez_prowadzacego(pr["nazwa"]))
        fs, lh = (3.1, 2.8) if len(linie) < 3 else (2.6, 2.3)
        y0 = cy - 5.0 - (1.4 if len(linie) == 3 else 0)
        for k, l in enumerate(linie):
            h += ('<text class="wz" transform="translate(%.2f %.2f) scale(.72 1)" font-size="%.1f" text-anchor="middle" fill="#0A1318" '
                  'stroke="#fff" stroke-width=".75" paint-order="stroke">%s</text>') % (cx, y0 + k * lh, fs, escape(l))
    return h


# ---------------------------------------------------------------- LATARNIE: audycje, które od lat nie zmieniły miejsca w ramówce
# Źródło: kalendarz Google „Nowa ramówka” (k18t5jce…), próbki: tydzień 3–9.06.2019 i drugi tydzień września 2019–2026 (27.09.2026).
# dowod: "rozne" = stałość potwierdzają RÓŻNE serie cykliczne w różnych latach; "jedna" = jedna seria (edycja serii mogła przepisać przeszłość).
STALE = [
    {"nazwa": "Poranek Wnet", "dni": [0, 1, 2, 3, 4], "start": "07:07", "koniec": "09:00", "od": 2023, "dowod": "rozne", "uwagi": "slot ok. 7–9 już od 2019"},
    {"nazwa": "Program Wschodni", "dni": [5], "start": "10:00", "koniec": "11:00", "od": 2019, "dowod": "rozne"},
    {"nazwa": "Muzyczna Polska Tygodniówka", "dni": [5], "start": "13:00", "koniec": "16:00", "od": 2019, "dowod": "rozne"},
    {"nazwa": "Tygodniowy Kalejdoskop Kulturalny", "dni": [5], "start": "08:00", "koniec": "10:00", "od": 2021, "dowod": "rozne"},
    {"nazwa": "Jak dobrze wstać skoro Wnet", "dni": [6], "start": "08:00", "koniec": "09:00", "od": 2023, "dowod": "rozne"},
    {"nazwa": "Riksza Miłosierdzia", "dni": [4], "start": "15:00", "koniec": "16:00", "od": 2020, "dowod": "jedna"},
    {"nazwa": "Polska muzyka", "dni": [5, 6], "start": "05:00", "koniec": "08:00", "od": 2023, "dowod": "jedna"},
]
_PL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ramowka_7lat", "latarnie.json")
if os.path.exists(_PL):                     # pełna historia kalendarza (06.2019–09.2026) zastępuje próbki
    STALE = json.load(open(_PL, encoding="utf-8"))
LATARNIA = '<path d="M9 21h6M10 21l1-12h2l1 12M9.5 9h5l-1-3h-3z"/><path d="M12 6V4"/><path d="M4 7l3 1M20 7l-3 1M4 11l3-.5M20 11l-3-.5"/>'


# Kolumna Zygmunta: prowadzący mówi z mikrofonu studia na Krakowskim Przedmieściu (odcisk toru, studio_kp.py) — był w redakcji
KOLUMNA = ('<path d="M6 22.6h12M7.6 20.8h8.8M11 20.8V9.6M13 20.8V9.6M9.6 9.6h4.8M10.2 8.4h3.6"/>'
           '<path d="M12 8.4V4.6"/><circle cx="12" cy="3.4" r=".95"/><path d="M12 5.4l3.4-3.2M14.1 2.6l1.9 1.5M12 5.6 9.4 7.2"/>')


def stala_audycja(i, h, dni):
    """Latarnia dla godziny h w kolumnie i (dzień tygodnia z daty), albo None."""
    import datetime as _dt
    wd = _dt.date.fromisoformat(dni[i]).weekday()
    for a in STALE:
        a0, b0 = _min(a["start"]), _min(a["koniec"])
        if wd in a["dni"] and a0 // 60 <= h < -(-b0 // 60):
            return a
    return None


def latarnie(dane, dni, ox, oy):
    h = ""
    for (i, j), g in dane.items():
        a = stala_audycja(i, j, dni)
        kp = bool(((g or {}).get("e1") or {}).get("studio_kp"))
        if not a and not kp:
            continue
        cx, cy = SA.srodek(i, j)
        cx += ox; cy += oy
        lx, ly = cx - 8.8, cy + 1.2
        if not a and not kp and ((g or {}).get("e1") or {}).get("realizator_sm7b"):
            pass
        if kp:                                               # Kolumna Zygmunta zastępuje latarnię (albo stoi tam, gdzie latarni nie było)
            h += '<circle cx="%.2f" cy="%.2f" r="2.9" fill="#E9E2F7" stroke="#0A1318" stroke-width=".4"/>' % (lx, ly)
            h += SA.ikona(lx - 2.3, ly - 2.4, 4.6, KOLUMNA, "#2B1F4A", 1.4)
            if not a:
                continue
        else:
            pelna = a["dowod"] == "rozne"
            h += '<circle cx="%.2f" cy="%.2f" r="2.9" fill="%s" stroke="#0A1318" stroke-width=".4"/>' % (lx, ly, "#FFF3C4" if pelna else "#FFFFFF")
            h += SA.ikona(lx - 2.1, ly - 2.1, 4.2, LATARNIA, "#0A1318" if pelna else "#75909A", 2.0)
        if g is not None and not g.get("prog"):                 # uzupełnienie obrysu audycji w tygodniach bez ramówki w metadanych
            g["prog"] = {"nazwa": a["nazwa"], "start": a["start"], "koniec": a["koniec"], "z_kalendarza": True}
        if j == _min(a["start"]) // 60:
            h += '<text x="%.2f" y="%.2f" font-size="2.3" font-weight="900" text-anchor="middle" fill="#0A1318" stroke="#fff" stroke-width=".6" paint-order="stroke">%d lat</text>' % (
                lx, ly + 5.4, a.get("lat") or (2026 - a["od"] + 1))
    return h
