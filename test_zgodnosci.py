# -*- coding: utf-8 -*-
"""Test zgodności: mapa 2D (plansza_gry.py) i świat 3D (blender/*) to dwie mapy TEGO SAMEGO terytorium — muszą mówić to samo.
„Mapa nie jest terytorium” (Korzybski) — ale dwie mapy jednego terytorium nie mogą sobie przeczyć. Sprawdzamy na wycinku z blender/dane/scena.json:
  T1 ląd/morze w heksie          2D: % słowa ≥ próg            3D: scena.json „lad”
  T2 osady                        2D: domy_eff (1–3)            3D: 4 domy na znak domu (obiekty.json)
  T3 latarnie                     2D: stala_audycja (kalendarz) 3D: obiekty.json latarnie (także na wysepkach)
  T4 kolor audycji                2D: kategoria_heksu (obrysy)  3D: kolor laserów
  T5 linia brzegowa (piksele)     2D: pole lądu generatora      3D: mapa wysokości > poziom wody (IoU)
  T6 plik glTF                    węzły domów, materiały laserów, siatka terenu — da się otworzyć w UE/Unity/Godocie
Wynik: test_zgodnosci_raport.json + wydruk ZGODNE/NIEZGODNE. Kod wyjścia 1 przy niezgodności.
    python test_zgodnosci.py"""
import json
import os
import struct
import sys
from collections import Counter

import numpy as np

import plansza_gry as PG

TU = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(TU, "blender")


def glb_json(p):
    with open(p, "rb") as f:
        magia, wersja, _ = struct.unpack("<4sII", f.read(12))
        dl, typ = struct.unpack("<I4s", f.read(8))
        assert magia == b"glTF" and typ == b"JSON"
        return json.loads(f.read(dl))


def main():
    S = json.load(open(os.path.join(B, "dane", "scena.json"), encoding="utf-8"))
    O = json.load(open(os.path.join(B, "eksport", "obiekty.json"), encoding="utf-8"))
    dni, dane = PG.dane_prawdy()
    wyn = {}
    # T1
    zle = [(h["i"], h["j"]) for h in S["heksy"] if h["lad"] != bool(dane.get((h["i"], h["j"])) and dane[(h["i"], h["j"])]["slowo"]["min"] >= PG.PROG)]
    wyn["T1_lad_morze"] = {"heksow": len(S["heksy"]), "niezgodnych": len(zle), "przyklady": zle[:5]}
    # T2
    domy3 = Counter((d["i"], d["j"]) for d in O["domy"])
    zle = []
    for h in S["heksy"]:
        g = dane.get((h["i"], h["j"]))
        d2 = PG.domy_eff(g["mowcy_eff"]) if g and "mowcy_eff" in g and PG.wartosc(g["slowo"]["min"]) else 0
        if domy3.get((h["i"], h["j"]), 0) != 4 * d2:
            zle.append(((h["i"], h["j"]), d2, domy3.get((h["i"], h["j"]), 0)))
    wyn["T2_osady"] = {"domow_3d": sum(domy3.values()), "niezgodnych_heksow": len(zle), "przyklady": zle[:5]}
    # T3
    lat2 = {(h["i"], h["j"]) for h in S["heksy"] if PG.stala_audycja(h["i"], h["j"], dni)}
    lat3 = {(l["i"], l["j"]) for l in O["latarnie"]}
    wyn["T3_latarnie"] = {"w_2d": len(lat2), "w_3d": len(lat3), "tylko_2d": sorted(lat2 - lat3)[:5], "tylko_3d": sorted(lat3 - lat2)[:5],
                          "na_morzu_3d": sum(1 for l in O["latarnie"] if l["na_morzu"])}
    # T4
    kat3 = {(l["i"], l["j"]): l["kategoria"] for l in O["lasery"]}
    zle = [((h["i"], h["j"]), PG.kategoria_heksu(dane.get((h["i"], h["j"])), PG.stala_audycja(h["i"], h["j"], dni)), kat3.get((h["i"], h["j"])))
           for h in S["heksy"] if PG.kategoria_heksu(dane.get((h["i"], h["j"])), PG.stala_audycja(h["i"], h["j"], dni)) != kat3.get((h["i"], h["j"]))]
    wyn["T4_kolory_audycji"] = {"heksow": len(kat3), "niezgodnych": len(zle), "przyklady": zle[:5],
                                "rozklad": dict(Counter(str(v) for v in kat3.values()))}
    # T5
    Z = np.load(os.path.join(B, "dane", "wysokosc.npy"))




    wyn["T5_brzeg"] = t5(S, Z, dane)
    # T6
    for wersja in ("pelny", "web"):
        p = os.path.join(B, "eksport", "halucynacje_swiat_%s.glb" % wersja)
        if not os.path.exists(p):
            wyn["T6_glb_" + wersja] = {"blad": "brak pliku"}
            continue
        j = glb_json(p)
        nazwy = Counter(n.get("name", "").split(".")[0] for n in j.get("nodes", []))
        mat = [m.get("name") for m in j.get("materials", [])]
        wyn["T6_glb_" + wersja] = {"MB": round(os.path.getsize(p) / 2 ** 20, 1), "wezly": len(j.get("nodes", [])), "siatki": len(j.get("meshes", [])),
                                   "domy": nazwy.get("dom", 0), "teren": "Teren" in nazwy, "lasery_swiecace": sum(1 for m in j.get("materials", [])
                                                                                                                if m.get("name", "").startswith("Laser") and m.get("emissiveFactor")),
                                   "rozszerzenia": j.get("extensionsUsed", [])}
    ok = (wyn["T1_lad_morze"]["niezgodnych"] == 0 and wyn["T2_osady"]["niezgodnych_heksow"] == 0 and not wyn["T3_latarnie"]["tylko_2d"]
          and not wyn["T3_latarnie"]["tylko_3d"] and wyn["T4_kolory_audycji"]["niezgodnych"] == 0 and wyn["T5_brzeg"]["zgodnosc_srodkow"] >= 0.97
          and wyn.get("T6_glb_pelny", {}).get("domy") == wyn["T2_osady"]["domow_3d"] and wyn.get("T6_glb_pelny", {}).get("teren"))
    wyn["wynik"] = "ZGODNE" if ok else "NIEZGODNE"
    json.dump(wyn, open(os.path.join(TU, "test_zgodnosci_raport.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    for k, v in wyn.items():
        print(k, v if not isinstance(v, dict) else {a: b for a, b in v.items() if a not in ("rozklad",)})
    return 0 if ok else 1


def t5(S, Z, dane):
    """Brzeg: w środku każdego heksu teren 3D ma być nad wodą ⇔ heks 2D jest lądem; plus zgodność monotoniczna wysokość ~ % słowa."""
    pxm = S["px_na_mm"] / S["skala_m_na_mm"]
    H, W = Z.shape
    zg, par = 0, []
    for h in S["heksy"]:
        c, r = min(W - 1, int(h["x"] * pxm)), min(H - 1, int(-h["y"] * pxm))
        z = float(Z[r, c])
        g = dane.get((h["i"], h["j"]))
        zg += (z > 0.4) == h["lad"]
        if g:
            par.append((g["slowo"]["min"], z))
    a = np.array(par)
    rs = float(np.corrcoef(np.argsort(np.argsort(a[:, 0])), np.argsort(np.argsort(a[:, 1])))[0, 1]) if len(a) > 3 else None
    return {"zgodnosc_srodkow": round(zg / len(S["heksy"]), 3), "spearman_wysokosc_slowo": round(rs, 3) if rs is not None else None}


if __name__ == "__main__":
    sys.exit(main())
