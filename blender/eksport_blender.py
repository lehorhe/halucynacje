# -*- coding: utf-8 -*-
"""Eksport wycinka mapy prawdy do sceny Blendera: wysokości, kolor terenu (bez nakładek 2D), obiekty na heksach.
Wycinek: 14 dni od 31.08 (kolumny 0–13) × godziny 00–13. Skala świata: 1 mm planszy = 5 m (heks ≈ 125 m), pion ×0,6 m/mm.
Wyjście (blender/dane/): wysokosc.npy (m), albedo.png, scena.json (heksy, domy, latarnie, drzewa, kadr drona).
    python blender/eksport_blender.py"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TU))
import plansza_gry as PG  # noqa: E402
import swiat_antena as SA  # noqa: E402

OUT = os.path.join(TU, "dane")
os.makedirs(OUT, exist_ok=True)
SKALA = 5.0          # m na mm planszy
PION = 0.6           # m wysokości na mm „wysokości” z generatora
PX = 4.0             # px/mm rastra
K0, K1, H0, H1 = 0, 14, 0, 14


def main():
    dni, dane = PG.dane_prawdy()
    import studio_kp as SK
    KAL = SK.audycja_godziny()                      # godzina → audycja z kalendarza „Nowa ramówka”
    PX_MM = PX
    img, W_mm, H_mm = PG.teren(dane, 28, 24, PX_MM, 77)
    P = PG.teren.pola
    e, lad, veg, z = P["e"], P["lad"], P["veg"], P["z"]
    # wycinek w mm: od lewej krawędzi kolumny K0 do prawej K1-1, od górnej krawędzi wiersza H0 do dolnej H1-1 (z zapasem pół heksu)
    xs = [SA.srodek(i, j)[0] for i in range(K0, K1) for j in (H0, H1 - 1)]
    ys = [SA.srodek(i, j)[1] for i in range(K0, K1) for j in (H0, H1 - 1)]
    x0, x1 = max(0, min(xs) - PG.S), min(W_mm, max(xs) + PG.S)
    y0, y1 = max(0, min(ys) - PG.FLAT / 2 - 1), min(H_mm, max(ys) + PG.FLAT / 2 + 1)
    c0, c1, r0, r1 = int(x0 * PX_MM), int(x1 * PX_MM), int(y0 * PX_MM), int(y1 * PX_MM)
    e, lad, veg, z = e[r0:r1, c0:c1], lad[r0:r1, c0:c1], veg[r0:r1, c0:c1], z[r0:r1, c0:c1]
    # wysokość świata: ląd = z generatora (względem progu) × PION; morze: dno opada z odległością od progu
    # ciągła przez linię brzegową (bez klifów-schodów): baza z % słowa, na lądzie dochodzi relief generatora, łagodnie od brzegu
    from PIL import ImageFilter
    baza = (e - PG.PROG) * 0.35
    wejscie = np.clip((e - PG.PROG) / 6.0, 0, 1)
    zw = baza + wejscie * np.maximum(z, 0) * PION * 0.8
    jadro = np.exp(-np.arange(-6, 7) ** 2 / (2 * 2.0 ** 2)); jadro /= jadro.sum()
    for os_ in (0, 1):
        zw = np.apply_along_axis(lambda v: np.convolve(np.pad(v, 6, mode="edge"), jadro, mode="valid"), os_, zw)
    zw = zw.astype(np.float32)
    np.save(os.path.join(OUT, "wysokosc.npy"), zw.astype(np.float32))
    # albedo: kolor terenu bez cieniowania (Blender świeci sam), roślinność i skały jak w 2D, linie heksów jak farba na makiecie
    rgb = SA.koloruj(np.clip(e, 0, 100)).astype(np.float32)
    skala = np.array([148, 138, 122], np.float32)
    rgb = np.where(lad[..., None], rgb * (0.55 + 0.45 * veg[..., None]) + skala * (0.45 * (1 - veg[..., None])), rgb)
    alb = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    alb.save(os.path.join(OUT, "albedo_bez_linii.png"))                    # heksy jako lasery (bez farby na ziemi)
    dr = ImageDraw.Draw(alb)
    heksy = []
    for i in range(K0, K1):
        for j in range(H0, H1):
            cx, cy = SA.srodek(i, j)
            pts = [((x - x0) * PX_MM, (y - y0) * PX_MM) for x, y in SA.wierzcholki(cx, cy)]
            dr.line(pts + [pts[0]], fill=(246, 240, 226), width=max(1, int(0.45 * PX_MM)))
            g = dane.get((i, j))
            a = PG.stala_audycja(i, j, dni)
            wx, wy = (cx - x0) * SKALA, -(cy - y0) * SKALA                        # Blender: Y w górę
            rec = {"i": i, "j": j, "x": round(wx, 1), "y": round(wy, 1), "dzien": dni[i], "godz": j,
                   "lad": bool(g and g["slowo"]["min"] >= PG.PROG), "slowo": round(g["slowo"]["min"]) if g else None,
                   "domy": (PG.domy_eff(g["mowcy_eff"]) if g and "mowcy_eff" in g else 0) if g and g["slowo"]["min"] >= PG.PROG else 0,
                   "latarnia": bool(a), "latarnia_nazwa": a["nazwa"] if a else None,
                   "wierzcholki": [[round((x - x0) * SKALA, 1), round(-(y - y0) * SKALA, 1)] for x, y in SA.wierzcholki(cx, cy)],
                   "kategoria": PG.kategoria_heksu(g, a),
                   "audycja": PG.nazwa_bez_prowadzacego(g["prog"]["nazwa"]) if g and g.get("prog") else (a["nazwa"] if a else None)}
            heksy.append(rec)
    alb.save(os.path.join(OUT, "albedo.png"))
    # drzewa: losowe punkty na lądzie, gęstość ∝ roślinność (bez stromych skał)
    rng = np.random.default_rng(7)
    H, W = e.shape
    n = 60000
    py, px = rng.integers(0, H, n), rng.integers(0, W, n)
    ok = lad[py, px] & (e[py, px] > PG.PROG + 3) & (rng.random(n) < (veg[py, px] - 0.45) * 1.1)
    drzewa = [[round(px_ / PX_MM * SKALA, 1), round(-py_ / PX_MM * SKALA, 1), round(float(zw[py_, px_]), 1)] for py_, px_ in zip(py[ok], px[ok])]
    # kadr drona: heks z latarnią, domami i morzem w sąsiedztwie
    lad_ij = {(h_["i"], h_["j"]): h_ for h_ in heksy}
    def morze_obok(h_):
        return sum(1 for di, dj in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1))
                   if (h_["i"] + di, h_["j"] + dj) in lad_ij and not lad_ij[(h_["i"] + di, h_["j"] + dj)]["lad"])
    kand = [h_ for h_ in heksy if h_["lad"] and h_["latarnia"] and h_["domy"] >= 2]
    cel = max(kand, key=lambda h_: (morze_obok(h_), h_["domy"])) if kand else max(heksy, key=lambda h_: h_["domy"])
    for h_ in heksy:                                        # wysokość terenu w środku heksu (do stawiania obiektów)
        cx, cy = h_["x"] / SKALA * PX_MM, -h_["y"] / SKALA * PX_MM
        h_["z"] = round(float(zw[min(H - 1, int(cy)), min(W - 1, int(cx))]), 1)
    json.dump({"skala_m_na_mm": SKALA, "px_na_mm": PX_MM, "rozmiar_m": [round(W / PX_MM * SKALA, 1), round(H / PX_MM * SKALA, 1)],
               "heks_flat_m": PG.FLAT * SKALA, "heks_R_m": PG.S * SKALA, "heksy": heksy, "drzewa": drzewa, "dron_cel": cel,
               "zakres": "%s–%s, godz. %02d–%02d" % (dni[K0], dni[K1 - 1], H0, H1 - 1)},
              open(os.path.join(OUT, "scena.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("teren %dx%d px (%.0f × %.0f m), heksów %d, drzew %d, dron: %s %02d:00 (%s)" % (W, H, W / PX_MM * SKALA, H / PX_MM * SKALA, len(heksy), len(drzewa),
                                                                                        cel["dzien"], cel["godz"], cel["audycja"]))


if __name__ == "__main__":
    main()
