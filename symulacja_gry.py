# -*- coding: utf-8 -*-
"""Symulator zasad „Świat anteny” 1.0 na proceduralnych światach rozgłośni (profile_rozglosni.py).

Zasady w skrócie (pełne: zasady_dane.py):
  tura = dzień (kolumna) · 7 tur · kolumna dnia nadaje NA ŻYWO, dwie poprzednie są ZAMKNIĘTE, starsze — w ARCHIWUM (nietykalne)
  etapy heksu: 1 Słowa → 2 Głosy → 3 Kto → 4 Sprawdzone → 5 Wyjście;  punkty = wartość etapu × W (1–3 kropki terenu)
  rzut: k6 + siła żetonu + modyfikatory ≥ 7;  1 = zawsze porażka (przy Kto: konflikt „!”), 6 = zawsze sukces
  PA: Kolonia 4 · Chmura 3 (każda akcja = 1 budżetu) · Redakcja 3 (ekipa na mapie, zasięg 1, ruch 3)
Gracz-automat to rozsądna, zachłanna drużyna — ludzie grający razem zwykle grają lepiej.
    python symulacja_gry.py [partie]"""
import collections
import random
import statistics
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import profile_rozglosni as PR  # noqa: E402

PROG = 32.53
PKT = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 8}


def wartosc(mn):
    return 0 if mn < PROG else (1 if mn < 60 else (2 if mn < 80 else 3))


def domy(m):
    return 1 if m <= 3 else (2 if m <= 6 else 3)


def wycinek(profil, tydz, h0, n_h=8):
    d, _ = PR.swiat(profil, tydz + 1)
    H = {}
    for i in range(7):
        for j in range(n_h):
            g = d[(tydz * 7 + i, h0 + j)]
            if not g or g["slowo"]["min"] < PROG:
                continue
            H[(i, j)] = {"W": wartosc(g["slowo"]["min"]), "domy": domy(g["mowcy"]), "mgla": not g["slowo"]["zgodne"]}
    return H


def odl(a, b):
    def kub(i, j):
        z = j - (i - (i & 1)) // 2
        return i, -i - z, z
    ax, ay, az = kub(*a)
    bx, by, bz = kub(*b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


class Gra:
    def __init__(s, H, P, rng):
        s.P, s.r, s.H = P, rng, H
        s.st = {h: 0 for h in H}
        s.mgla = {h: H[h]["mgla"] for h in H}
        s.konf, s.poufne = set(), set()
        s.budzet = P["budzet"]
        s.akcje = s.rzuty = 0
        start = min(H, key=lambda h: (h[0], -H[h]["W"])) if H else (0, 0)
        s.ekipy = [start] * P["ekip"]

    def k6(s):
        s.rzuty += 1
        return s.r.randint(1, 6)

    def test(s, sila, mod):
        w = s.k6()
        if w == 1:
            return False, True
        return (w == 6 or w + sila + mod >= 7), False

    def okno(s, h, dzien):
        return dzien - 2 <= h[0] <= dzien

    def mod(s, h, etap, maszyna=True, ev=None):
        m, c = 0, s.H[h]
        if maszyna and s.mgla[h] and etap in (1, 2, 4):
            m -= 1
        if etap in (2, 3):
            m -= c["domy"] - 1
        if etap == 3:
            i, j = h
            if any(s.st.get(n, 0) >= 3 for n in ((i, j - 1), (i, j + 1))):
                m += 1
            m += (ev or {}).get("kto", 0)
        return m

    # sila żetonu: (etap, tryb) → siła;  na żywo słabiej
    # siły = liczby wydrukowane na żetonach (warstwy/model.json): L·LIVE 2, L·GODZ 4, L·ECAPA 2, L·DIAR 4, KTX 2, GŁO 4, SPR 5 · C·LIVE 3, C·GODZ 4, C·DIAR 4, PRZ 3
    SILA = {"L": {(1, "live"): 2, (1, "godz"): 4, (2, "live"): 2, (2, "godz"): 4, (3, "live"): 2, (3, "godz"): 4, (4, "godz"): 5},
            "C": {(1, "live"): 3, (1, "godz"): 4, (2, "godz"): 4, (3, "godz"): 3}}

    def cele(s, dzien, kto):
        out = []
        for h in s.H:
            if not s.okno(h, dzien) or (kto == "C" and h in s.poufne) or h in s.konf:
                continue
            e = s.st[h] + 1
            if e > 4 or (kto == "C" and e == 4):
                continue
            tryb = "live" if h[0] == dzien else "godz"
            sila = s.SILA[kto].get((e, tryb))
            if sila is None:
                continue
            p = max(1, min(5, 6 - max(1, 7 - sila - s.mod(h, e)) + 1)) / 6
            zysk = (PKT[e] - PKT[e - 1]) * s.H[h]["W"]
            pilne = 1.4 if h[0] == dzien - 2 else 1.0
            out.append((p * zysk * pilne, h, e, sila))
        out.sort(key=lambda x: -x[0])
        return out

    def maszyna(s, dzien, pa, kto, ev):
        for _ in range(pa):
            if kto == "C" and s.budzet <= 0:
                return
            c = s.cele(dzien, kto)
            if not c or (kto == "C" and c[0][0] < s.P["prog_chmury"]):
                return
            _, h, e, sila = c[0]
            if kto == "C":
                s.budzet -= 1
            s.akcje += 1
            ok, jed = s.test(sila, s.mod(h, e, ev=ev))
            if ok:
                s.st[h] = e
            elif jed and e == 3:
                s.konf.add(h)

    def ocena_red(s, h, dzien):
        if not s.okno(h, dzien):
            return 0
        e = s.st[h]
        if h in s.konf:
            return 3 * s.H[h]["W"]
        return {2: 1, 3: 2, 4: 3}.get(e, 0) * s.H[h]["W"] + (1 if s.mgla[h] and e in (0, 1) else 0)

    def redakcja(s, dzien, pa):
        for k in range(len(s.ekipy)):
            s.ekipy[k] = max((h for h in s.H if odl(h, s.ekipy[k]) <= s.P["ruch"]),
                             key=lambda c: sum(s.ocena_red(h, dzien) for h in s.H if odl(h, c) <= 1) - (9 if c in s.ekipy[:k] else 0))
            for _ in range(pa[k]):
                z = [h for h in s.H if odl(h, s.ekipy[k]) <= 1 and s.okno(h, dzien)]
                kand = []
                for h in z:
                    e, W = s.st[h], s.H[h]["W"]
                    if h in s.konf:
                        kand.append((10 + W, h, "rozstrzygnij"))
                    elif e == 4:
                        kand.append((3 * W * 5 / 6, h, "wyjscie"))
                    elif e == 3:
                        kand.append((2 * W, h, "sprawdz"))
                    elif e == 2:
                        kand.append((1 * W, h, "kto"))
                    elif s.mgla[h] and e in (0, 1):
                        kand.append((0.8, h, "ucho"))
                if not kand:
                    break
                kand.sort(key=lambda x: -x[0])
                _, h, co = kand[0]
                s.akcje += 1
                if co == "rozstrzygnij":
                    s.konf.discard(h)
                    s.st[h] = 3
                elif co == "wyjscie":
                    if s.test(5, 0)[0]:
                        s.st[h] = 5
                elif co == "sprawdz":
                    s.st[h] = 4
                elif co == "kto":
                    s.st[h] = 3
                elif co == "ucho":
                    s.mgla[h] = False

    def zdarzenie(s, dzien):
        w = s.k6() + s.k6()
        ev = {"L": 0, "C": 0, "H": 0, "kto": 0}
        dz = sorted((h for h in s.H if h[0] == dzien), key=lambda h: h[1])
        if w == 2:
            ev["L"] = -2
        elif w == 3 and dz:
            s.poufne.add(dz[0])
        elif w == 4 and dz:
            for h in dz:
                if not s.mgla[h]:
                    s.mgla[h] = True
                    break
        elif w == 5:
            ev["C"] = -99
        elif w == 6:
            ev["kto"] = -1
        elif w == 8:
            ev["H"] = 1
        elif w == 9:
            ev["kto"] = 1
        elif w == 10:
            s.budzet = max(0, s.budzet - 1)
        elif w == 11:
            ev["L"] = 2
        elif w == 12:
            s.budzet += 2
        return ev

    def graj(s):
        for dzien in range(7):
            ev = s.zdarzenie(dzien)
            s.maszyna(dzien, max(0, s.P["L"] + ev["L"]), "L", ev)
            s.maszyna(dzien, max(0, s.P["C"] + ev["C"]), "C", ev)
            s.redakcja(dzien, [s.P["H"] + (ev["H"] if k == 0 else 0) for k in range(s.P["ekip"])])
        pkt = 0
        for h, e in s.st.items():
            if h in s.konf:
                e = min(e, 2)
            pkt += PKT[e] * s.H[h]["W"]
        return pkt


BAZA = {"L": 4, "C": 3, "H": 3, "ekip": 1, "budzet": 10, "ruch": 3, "prog_chmury": 0.8}
SCEN = [("klasyczne", 0, 6, "Poranek Wnet"), ("klasyczne", 0, 14, "Popołudnie i wieczór"), ("muzyczne", 0, 5, "Archipelag"),
        ("informacyjne", 0, 6, "Kontynent")]


def seria(H, P, n, ziarno=7):
    rng = random.Random(ziarno)
    wyn, akc, rz = [], [], []
    for _ in range(n):
        g = Gra(H, P, rng)
        wyn.append(g.graj())
        akc.append(g.akcje)
        rz.append(g.rzuty)
    q = statistics.quantiles(wyn, n=10)
    return {"p10": round(q[0]), "med": round(statistics.median(wyn)), "p90": round(q[8]), "akcje": round(statistics.mean(akc)), "rzuty": round(statistics.mean(rz)),
            "max_teor": sum(PKT[5] * v["W"] for v in H.values())}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    for prof, t, h0, nazwa in SCEN:
        H = wycinek(prof, t, h0)
        print("== %s (%s, %02d–%02d): ląd %d, W %s, domy %s, mgła %d" % (nazwa, prof, h0, h0 + 7, len(H), dict(sorted(collections.Counter(v["W"] for v in H.values()).items())),
              dict(sorted(collections.Counter(v["domy"] for v in H.values()).items())), sum(v["mgla"] for v in H.values())))
        for opis, zm in [("3 osoby", {}), ("4 osoby (2 ekipy×2, budżet 8)", {"ekip": 2, "H": 2, "budzet": 8}), ("bez chmury", {"budzet": 0})]:
            print("   %-32s %s" % (opis, seria(H, dict(BAZA, **zm), n)))
