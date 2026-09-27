# -*- coding: utf-8 -*-
"""Inteligentna legenda mapy prawdy (A0): gracz ma w minutę zobaczyć, ILE informacji ukrywa mapa i jak ją czytać.
Trzy kolumny:
  1. Anatomia heksu — prawdziwy heks z tej mapy (ten sam co w kadrze z drona w Blenderze), powiększony, z numerami znaków
  2. Jak czytać teren — osiem prawdziwych heksów-rekordów z tej mapy, każdy z liczbą, która go tworzy
  3. Ile wiesz, nie słuchając — liczniki danych ukrytych w mapie + pytania, na które mapa odpowiada; motto Korzybskiego
Wszystko liczone z tych samych danych co mapa (dane_prawdy) — legenda nie może obiecywać więcej, niż mapa wie."""
import glob
import json
import os
import statistics as S
from html import escape

import numpy as np

import plansza_gry as PG
import swiat_antena as SA

TU = os.path.dirname(os.path.abspath(__file__))
LEG = os.path.join(TU, "legenda")
os.makedirs(LEG, exist_ok=True)
PET, SZARY, ZLOTY = "#274F5C", "#3F5A66", "#F9B009"
HEKS_DRONA = ("2026-09-12", 10)            # ten sam heks co kadr drona (blender/eksport_blender.py → dron_cel)


def _txt(x, y, t, fs=4.2, w=400, kol="#0A1318", anchor="start"):
    return '<text x="%.1f" y="%.1f" font-size="%.1f" font-weight="%d" fill="%s" text-anchor="%s">%s</text>' % (x, y, fs, w, kol, anchor, escape(t))


def _zawin(t, n):
    out, cur = [], ""
    for s in t.split():
        if len(cur) + len(s) + 1 > n and cur:
            out.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    return out + ([cur] if cur else [])


def _heks_wycinek(img, px_mm, i, j, nazwa):
    """Teren heksu (i, j) jako osobny obraz PNG + jego środek w mm mapy."""
    cx, cy = SA.srodek(i, j)
    r = PG.S + 1
    box = (int((cx - r) * px_mm), int((cy - r) * px_mm), int((cx + r) * px_mm), int((cy + r) * px_mm))
    p = os.path.join(LEG, nazwa + ".png")
    img.crop(box).save(p)
    return p, cx, cy, r


def _heks_duzy(dane, dni, img, px_mm, i, j, X, Y, skala, nazwa, znaki=True):
    """Heks narysowany w skali: teren przycięty do heksu + nakładka mapy (te same funkcje co plansza)."""
    p, cx, cy, r = _heks_wycinek(img, px_mm, i, j, nazwa)
    cid = "clip_" + nazwa
    pts = " ".join("%.2f,%.2f" % q for q in SA.wierzcholki(cx, cy))
    g = '<g transform="translate(%.2f %.2f) scale(%.3f) translate(%.2f %.2f)">' % (X, Y, skala, -cx, -cy)
    g += '<clipPath id="%s"><polygon points="%s"/></clipPath>' % (cid, pts)
    g += '<image href="file:///%s" x="%.2f" y="%.2f" width="%.2f" height="%.2f" clip-path="url(#%s)" preserveAspectRatio="none"/>' % (
        p.replace("\\", "/"), cx - r, cy - r, 2 * r, 2 * r, cid)
    if znaki:
        pod = {(i, j): dane.get((i, j))}
        g += PG.nakladka(pod, [], 0, 0, 0, None, z_nazwami=True)
        g += PG.latarnie(pod, dni, 0, 0)
        g += PG.bloki_audycji(pod, [], 0, 0)
        g += PG.nazwy_audycji(pod, 0, 0)
    g += '<polygon points="%s" fill="none" stroke="#0A1318" stroke-width="%.2f"/>' % (pts, 0.9 / skala)
    return g + "</g>"


def _liczniki(dane):
    import sciezki
    if not sciezki.ARCHIWUM and os.path.exists(sciezki.MIGAWKA):
        return json.load(open(sciezki.MIGAWKA, encoding="utf-8"))["liczniki"]
    n_slow = n_utw = 0
    glosy, mowcy, h_meta = set(), 0, 0
    for p in glob.glob(os.path.join(SA.MEDIA, "2026-0*", "*.meta.json")):
        d = os.path.basename(os.path.dirname(p))
        if not ("2026-08-31" <= d <= "2026-09-27"):
            continue
        m = json.load(open(p, encoding="utf-8"))
        st = m.get("statystyki") or {}
        n_slow += st.get("n_slow") or 0
        n_utw += len(m.get("utwory") or [])
        h_meta += 1
        for v in (m.get("mowcy") or {}).values():
            mowcy += 1
            if v.get("zrodlo") == "glos" and v.get("pid"):
                glosy.add(v["pid"])
    zm = [g for g in dane.values() if g]
    metody = sum(g["slowo"]["n"] for g in zm)
    e1 = [g.get("e1") or {} for g in zm]
    return {"godzin": len(dane), "zmierzone": len(zm), "slow": n_slow, "utworow": n_utw, "glosow": len(glosy), "tur_mowcow": mowcy,
            "pomiarow_slowa": metody, "tagi": sum(1 for e in e1 if "mowa_muzyka_s" in e), "scribe": sum(1 for e in e1 if e.get("dwie_transkrypcje")),
            "tempo": sum(1 for e in e1 if e.get("tempo"))}


# warstwy informacji w jednym heksie (to, co mapa koduje — do licznika „faktów”)
WARSTWY = ["godzina", "audycja (ramówka)", "blok audycji i jej długość", "latarnia: lata w tym samym miejscu", "osada: głosy efektywne",
           "wartość W", "% słowa: dolna i górna granica", "wysokość i kolor terenu", "roślinność: dialog czy monolog", "zbocza: tempo mowy",
           "brzeg: przejścia mowa↔muzyka", "laguna: mowa na muzyce", "♪ teksty piosenek", "miraż: rozbieżność transkrypcji",
           "2×T: dwie transkrypcje", "mgła: niezgodne metody", "strumień: utwory", "polana: oklaski, śmiech", "łącza zdalne (w toku)",
           "studio KP (w toku)"]


def legenda(dane, dni, img, px_mm, rek, x0, y0, szer, wys):
    h = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="#F4F8F9" stroke="#D6E1E5" stroke-width=".6"/>' % (x0, y0, szer, wys)
    h += _txt(x0 + 8, y0 + 14, "LEGENDA · Ile ta mapa wie o antenie, choć nikt jej nie słuchał", 9.0, 800, PET)
    h += _txt(x0 + 8, y0 + 22, "Każdy heks to jedna godzina Radia Wnet. Teren, osady, latarnie i znaki wynikają wyłącznie z pomiarów i ramówki — nic nie jest dorysowane.",
              4.3, 400, SZARY)
    kol = szer / 3
    # --- 1. anatomia heksu
    i, j = dni.index(HEKS_DRONA[0]), HEKS_DRONA[1]
    g = dane.get((i, j))
    X, Y, sk = x0 + kol / 2 - 4, y0 + 100, 4.0
    h += _txt(x0 + 8, y0 + 36, "1 · Anatomia heksu", 6.2, 800, PET)
    h += _txt(x0 + 8, y0 + 42.5, "sobota 12.09, 10:00 — ten sam heks co w kadrze z drona (Blender)", 3.9, 400, SZARY)
    h += _heks_duzy(dane, dni, img, px_mm, i, j, X, Y, sk, "anatomia")
    punkty = [((0, -8.3), "godzina anteny"), ((0, -5.0), "audycja z ramówki (bez prowadzących)"), ((0, -14.1), "blok audycji: godziny od–do, obrys w kolorze rodzaju"),
              ((-8.8, 1.2), "latarnia: audycja od lat w tym miejscu (kalendarz 2019–2026)"), ((-8.8, 5.4), "ile lat w tym samym miejscu ramówki"),
              ((2.6, 2.3), "osada: głosy efektywne (krótkie wejścia ważą mało)"), ((1.2, 6.0), "wartość W — mnożnik punktów w grze"),
              ((0, 9.75), "% słowa: dolna–górna granica z kilku metod"), ((7.0, -1.5), "teren: wysokość i kolor = % słowa, las = rozmowa")]
    pr = (g or {}).get("prog") or {}
    if not pr or (PG._min(pr.get("koniec") or "00:00") or 0) - (PG._min(pr.get("start") or "00:00") or 0) <= 60 and (PG._min(pr.get("start") or "00:00") or 0) % 60 == 0:
        punkty = [p_ for p_ in punkty if not p_[1].startswith("blok audycji")]           # ten heks nie ma bloku — nie obiecujemy znaku, którego nie widać
    krawedz = PG.S * sk + 6
    for n, ((dx, dy), t) in enumerate(punkty, 1):
        px, py = X + dx * sk, Y + dy * sk
        bok = 1 if dx > 0 or (dx == 0 and "audycja" in t) else -1
        nx = X + bok * krawedz
        h += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width=".45"/>' % (px, py, nx - bok * 3.2, py, PET)
        h += '<circle cx="%.1f" cy="%.1f" r=".9" fill="%s"/>' % (px, py, PET)
        h += '<circle cx="%.1f" cy="%.1f" r="3.1" fill="%s" stroke="#0A1318" stroke-width=".4"/>' % (nx, py, ZLOTY)
        h += _txt(nx, py + 1.5, str(n), 4.0, 900, "#0A1318", "middle")
    yl = y0 + 158
    for n, (_, t) in enumerate(punkty, 1):
        yy = yl + (n - 1) * 6.4
        h += '<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s"/>' % (x0 + 11, yy - 1.4, ZLOTY) + _txt(x0 + 11, yy, str(n), 3.3, 900, "#0A1318", "middle")
        h += _txt(x0 + 16, yy, t, 4.0)
    # inne znaki (mini-ikony)
    yz = yl + len(punkty) * 6.4 + 6
    h += _txt(x0 + 8, yz, "Inne znaki na mapie", 4.8, 800, PET)
    znaki = [("♪", "teksty piosenek: ASR zapisał śpiew — to nie mowa"), ("2×T", "dwie niezależne transkrypcje (lokalna + chmura)"),
             ("mg", "mgła: metody pomiaru się nie zgadzają"), ("sk", "skały: wysoko, ale monolog"), ("st", "strumień: dużo utworów w godzinie słowa"),
             ("po", "polana: oklaski, śmiech (zdarzenia audio)"), ("re", "rekord mapy (lista u góry)"), ("te", "słuchawka + piksele: łącza zdalne — pomiar w toku"),
             ("ko", "Kolumna Zygmunta: studio na Krakowskim Przedmieściu zajęte — pomiar w toku")]
    for k, (ik, t) in enumerate(znaki):
        yy = yz + 7 + k * 6.2
        xi = x0 + 9
        if ik in ("♪", "2×T"):
            h += _txt(xi + 3, yy, ik, 4.2, 900, "#0A1318", "middle")
        elif ik == "mg":
            h += SA.ikona(xi, yy - 4, 5, PG.CHMURKA, "#0A1318", 2.2).replace('fill="none"', 'fill="#FFFFFF"')
        elif ik == "sk":
            h += SA.ikona(xi, yy - 4, 5, PG.SKALY, "#4A4238", 2.2)
        elif ik == "st":
            h += SA.ikona(xi, yy - 4, 5, PG.STRUMIEN, "#1F6F9B", 2.2)
        elif ik == "po":
            h += SA.ikona(xi, yy - 4, 5, PG.POLANA, "#C98A00", 2.2)
        elif ik == "re":
            h += '<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s" stroke="#0A1318" stroke-width=".4"/>' % (xi + 2.5, yy - 1.5, ZLOTY)
        elif ik == "te":
            h += SA.ikona(xi, yy - 4, 5, PG.SLUCHAWKA, "#0A1318", 2.0)
        elif ik == "ko":
            h += SA.ikona(xi, yy - 4.2, 5.2, PG.KOLUMNA, "#2B1F4A", 1.5)
        h += _txt(x0 + 17, yy, t, 3.9)
    # --- 2. jak czytać teren: rekordy tej mapy
    x2 = x0 + kol + 4
    h += _txt(x2, y0 + 36, "2 · Jak czytać teren — przykłady z tej mapy", 6.2, 800, PET)
    zm = {k: v for k, v in dane.items() if v}
    przyk = []
    for typ, opis, f in (("szczyt", "Szczyt: najwięcej słowa", lambda g: "słowo %d%%" % round(g["slowo"]["min"])),
                         ("archipelag", "Archipelag: rwana godzina", lambda g: "%d przejść mowa↔muzyka" % g["e1"]["przejscia"]),
                         ("zbocze", "Strome zbocze: szybka mowa", lambda g: ("%.1f sylaby/s" % g["e1"]["tempo"]).replace(".", ",")),
                         ("laguna", "Laguna: mowa na muzyce", lambda g: "%d s mowy na tle muzyki" % g["e1"]["mowa_muzyka_s"])):
        if typ in rek:
            przyk.append((rek[typ], opis, f(zm[rek[typ]])))
    mir = [k for k, g in zm.items() if (g.get("e1") or {}).get("rozbieznosc_szac") and g["slowo"]["min"] >= PG.PROG]
    if mir:
        k = max(mir, key=lambda k: zm[k]["e1"]["rozbieznosc_szac"])
        przyk.append((k, "Miraż: transkrypcja niepewna", ("szac. rozbieżność %.0f%%" % zm[k]["e1"]["rozbieznosc_szac"])))
    if "mgla" in rek:
        przyk.append((rek["mgla"], "Mgła: metody się kłócą", "rozrzut %d pp" % round(zm[rek["mgla"]]["slowo"]["rozrzut_pp"])))
    tek = [k for k, g in zm.items() if g["slowo"].get("teksty_piosenek")]
    if tek:
        k = max(tek, key=lambda k: zm[k]["utwory"])
        przyk.append((k, "Morze muzyki z ♪", "%d utworów, słowo %d%%" % (zm[k]["utwory"], round(zm[k]["slowo"]["min"]))))
    nz = [k for k, g in dane.items() if g is None]
    if nz:
        przyk.append((nz[0], "Ziemia nieznana", "brak nagrania tej godziny"))
    DN = "pn wt śr cz pt so nd".split()
    import datetime as _dt
    for n, ((i2, j2), tyt, war) in enumerate(przyk[:8]):
        kx, ky = x2 + (n % 2) * (kol / 2), y0 + 52 + (n // 2) * 58
        h += _heks_duzy(dane, dni, img, px_mm, i2, j2, kx + 24, ky + 22, 1.75, "przyklad_%d" % n, znaki=False)
        d = _dt.date.fromisoformat(dni[i2])
        h += _txt(kx + 50, ky + 12, tyt, 4.1, 800, PET)
        for m_, l in enumerate(_zawin(war, 24)):
            h += _txt(kx + 50, ky + 18.5 + m_ * 5, l, 3.9)
        h += _txt(kx + 50, ky + 30, "%s %s, %02d:00" % (DN[d.weekday()], d.strftime("%d.%m"), j2), 3.6, 400, SZARY)
    yb = y0 + 52 + 4 * 58 + 4
    h += PG.legenda_gry(x2, yb, kol - 10, pion=True).replace('font-size="2.3"', 'font-size="3.4"').replace('font-size="2.2"', 'font-size="3.3"').replace(
        'font-size="3.3" font-weight="800" fill="#274F5C">Teren', 'font-size="4.8" font-weight="800" fill="#274F5C">Teren')
    # --- 3. ile wiesz, nie słuchając
    x3 = x0 + 2 * kol + 6
    L = _liczniki(dane)
    h += _txt(x3, y0 + 36, "3 · Ile wiesz, nie słuchając", 6.2, 800, PET)
    fakty = len(dane) * len(WARSTWY)
    duze = [("%d" % L["godzin"], "godzin anteny, %d z pomiarem" % L["zmierzone"]),
            ("%s" % "{:,}".format(L["slow"]).replace(",", " "), "słów w transkrypcjach, których nie trzeba czytać"),
            ("%d" % L["pomiarow_slowa"], "niezależnych pomiarów „ile słowa”"),
            ("%d" % L["utworow"], "bloków muzyki (utworów) na antenie"),
            ("%d" % L["glosow"], "rozpoznanych głosów (bez nazwisk na mapie)"),
            ("35 392", "wpisy ramówki z 7 lat — latarnie i kolory"),
            ("%d" % len(WARSTWY), "warstw informacji w jednym heksie"),
            ("≈ %s" % "{:,}".format(fakty).replace(",", " "), "faktów o antenie na jednej planszy")]
    for k, (liczba, opis) in enumerate(duze):
        yy = y0 + 54 + k * 17
        h += _txt(x3, yy, liczba, 10.5, 800, PET)
        for m_, l in enumerate(_zawin(opis, 40)):
            h += _txt(x3 + 70, yy - 4 + m_ * 5, l, 4.1)
    yq = y0 + 54 + len(duze) * 17 + 4
    h += _txt(x3, yq, "Na te pytania odpowiesz z samej mapy", 5.0, 800, PET)
    for k, q in enumerate(["Kiedy Radio Wnet mówi najwięcej, a kiedy gra?", "Gdzie słowo jest rozmową, a gdzie monologiem?",
                           "Które audycje stoją w tym samym miejscu od lat?", "Które godziny znamy pewnie, a które to miraż?",
                           "Gdzie ASR pomylił śpiew z mową?"]):
        h += _txt(x3 + 2, yq + 7 + k * 6, "• " + q, 4.1)
    yk = yq + 7 + 5 * 6 + 8
    h += '<rect x="%.1f" y="%.1f" width="%.1f" height="30" rx="2" fill="#FFFFFF" stroke="%s" stroke-width=".6"/>' % (x3 - 2, yk - 8, kol - 14, ZLOTY)
    h += _txt(x3 + 3, yk + 1, "„Mapa nie jest terytorium.”", 6.4, 800, "#0A1318")
    h += _txt(x3 + 3, yk + 8, "— Alfred Korzybski, 1931", 4.2, 400, SZARY)
    h += _txt(x3 + 3, yk + 15, "Ta mapa to wynik pomiarów, nie antena. Grasz, żeby odróżniać jedno od drugiego.", 3.6, 400, SZARY)
    return h
