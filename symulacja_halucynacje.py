# -*- coding: utf-8 -*-
"""Symulator HALUCYNACJE 1.0 — rozszerza symulacja_gry.py o: Pewność (liczbę transkrypcji), żetony szumu, karty przekonań,
tor skandalu, postacie redakcji (1–8 osób). Gracz-automat: rozsądna, zachłanna drużyna.
    python symulacja_halucynacje.py [partie]"""
import random
import statistics
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import symulacja_gry as SG  # noqa: E402

PKT = SG.PKT
WAGI = [1] * 5 + [2] * 3 + [2] * 3 + [3] * 3 + [1] * 2 + [0] * 8   # ASR, mówca, nazwisko, cytat, liczba; 0 = fałszywy alarm
SILY_KART = [3] * 17 + [2] * 43 + [1] * 12

# postacie: (nazwa, akcje w turze) — rdzeń zawsze w grze, kolejne dochodzą z liczbą osób
POSTACIE = {4: ["Wydawca", "Redaktor"], 5: ["Wydawca", "Redaktor", "Weryfikator"], 6: ["Wydawca", "Redaktor", "Weryfikator", "Reporter"],
            7: ["Wydawca", "Redaktor", "Weryfikator", "Reporter", "Realizator"], 8: ["Wydawca", "Redaktor", "Weryfikator", "Reporter", "Realizator", "Szef"]}


class Gra(SG.Gra):
    def __init__(s, H, P, rng):
        super().__init__(H, P, rng)
        s.pew = {h: 0 for h in H}        # liczba różnych transkrypcji (0–3)
        s.szum = {h: [] for h in H}      # zakryte żetony szumu: wagi
        s.wiara = {h: [] for h in H}     # zakryte karty przekonań: siły
        s.worek = WAGI[:]
        rng.shuffle(s.worek)
        s.talia = SILY_KART[:]
        rng.shuffle(s.talia)
        s.skandal = s.wylapane = s.zrozumienie = 0
        s.red = set()
        s.zwolnieni = 0
        n = P["osoby"]
        s.postacie = POSTACIE[max(4, n)][:]
        s.reka = {k: [s.talia.pop() for _ in range(3)] for k in range(max(1, n))}

    def ryz_pub(s, h):
        """Ryzyko testu prawdy: znaczniki + zakryte karty + mgła + (3 − Pewność) − 1 za sprawdzenie przez człowieka."""
        return max(0, sum(s.szum[h]) + sum(s.wiara[h]) + (1 if s.mgla[h] else 0) + (s.P["baza"] - max(1, s.pew[h])) - (1 if h in s.red else 0))

    def ryzyko(s, h, live):
        return 4 - max(1, s.pew[h]) + (1 if s.mgla[h] else 0) + (1 if live else 0)

    def losuj_szum(s, h, etap=1, kto="L"):
        """Jawny znacznik ryzyka: Słowa → ASR (1), Głosy → mówca (1), Kto z maszyny → nazwisko (2; chmura: cytat 2)."""
        s.szum[h].append({1: 1, 2: 1, 3: 2}.get(etap, 1))

    def odslon(s, h, ile=99):
        for _ in range(min(ile, len(s.szum[h]))):
            s.szum[h].remove(max(s.szum[h]))
            s.wylapane += 1
        if ile >= 99:
            s.zrozumienie += len(s.wiara[h])
            s.wiara[h] = []

    def maszyna(s, dzien, pa, kto, ev):
        for _ in range(pa):
            if kto == "C" and s.budzet <= 0:
                return
            c = s.cele(dzien, kto)
            # druga/trzecia transkrypcja na cennych heksach z szumem albo w mgle
            dod = [h for h in s.H if s.okno(h, dzien) and s.st[h] >= 1 and s.pew[h] < s.P["cel_pew"] and s.H[h]["W"] >= 2
                   and not (kto == "C" and h in s.poufne)]
            if dod and (not c or c[0][0] < s.P["prog_dod"]):
                h = max(dod, key=lambda x: (len(s.szum[x]), s.H[x]["W"]))
                if kto == "C":
                    s.budzet -= 1
                s.akcje += 1
                live = h[0] == dzien
                sila = SG.Gra.SILA[kto][(1, "live" if live else "godz")]
                d = s.k6()
                if d != 1 and (d == 6 or d + sila + s.mod(h, 1) >= 7):
                    s.pew[h] += 1
                    if 1 in s.szum[h]:
                        s.szum[h].remove(1)                         # porównanie transkrypcji usuwa znacznik ASR
                continue
            if not c or (kto == "C" and c[0][0] < s.P["prog_chmury"]):
                return
            _, h, e, sila = c[0]
            if kto == "C":
                s.budzet -= 1
            s.akcje += 1
            live = h[0] == dzien
            premia = 0
            if s.P["karty"] and s.reka.get(0) and e <= 3 and s.r.random() < s.P["p_karta"]:
                k = max(s.reka[0])
                s.reka[0].remove(k)
                s.wiara[h].append(k)
                premia = k
            d = s.k6()
            ok = d != 1 and (d == 6 or d + sila + s.mod(h, e, ev=ev) + premia >= 7)
            if ok:
                s.st[h] = e
                if e == 1:
                    s.pew[h] = max(1, s.pew[h])
                if e == 4:
                    s.odslon(h, 1)                                  # SPR: maszyna sprawdza jeden żeton
                if e <= 3 and d <= s.P["T"] - max(1, s.pew[h]) + (1 if live else 0):
                    s.losuj_szum(h, e, kto)
            elif d == 1 and e == 3:
                s.konf.add(h)

    def redakcja(s, dzien, pa):
        ak = {"Wydawca": 2, "Redaktor": 2, "Weryfikator": 1, "Reporter": 1, "Realizator": 1, "Szef": 1}
        if s.P["osoby"] <= 3:
            ak = {"Wydawca": 1, "Redaktor": 2}
        for p in s.postacie:
            for _ in range(ak.get(p, 1) + (pa if p == "Redaktor" else 0)):
                s.akcja(p, dzien)

    def akcja(s, p, dzien):
        okno = [h for h in s.H if s.okno(h, dzien)]
        if p == "Weryfikator" or p == "Szef":
            k = [h for h in okno if s.szum[h] or s.wiara[h]]
            if k:
                h = max(k, key=lambda x: (s.st[x], s.H[x]["W"]))
                s.akcje += 1
                if s.szum[h]:
                    s.odslon(h, 1)
                else:
                    s.zrozumienie += 1
                    s.wiara[h].pop()
            return
        if p == "Reporter":
            k = [h for h in okno if s.st[h] >= 1 and s.pew[h] < 3]
            if k:
                h = max(k, key=lambda x: (len(s.szum[x]), s.H[x]["W"]))
                s.pew[h] += 1
                s.odslon(h, 1)
                s.akcje += 1
            return
        if p == "Realizator":
            k = [h for h in okno if s.mgla[h]]
            if k:
                s.mgla[max(k, key=lambda x: s.H[x]["W"])] = False
                s.akcje += 1
            return
        kand = []
        for h in okno:
            e, W = s.st[h], s.H[h]["W"]
            if p == "Wydawca":
                if h in s.konf:
                    kand.append((10 + W, h, "rozstrzygnij"))
                elif e == 4:
                    R = s.ryz_pub(h)
                    p_ok = sum(1 for d in range(1, 7) if d > R) / 6
                    if p_ok >= s.P["prog_pub"]:
                        kand.append((3 * W * p_ok, h, "wyjscie"))
                elif e == 2:
                    kand.append((1 * W, h, "kto"))
            else:
                if e == 3 and h not in s.konf:
                    kand.append((2 * W + len(s.szum[h]), h, "sprawdz"))
                elif e == 4 and (s.szum[h] or s.wiara[h]):
                    kand.append((1.5 * W, h, "odslon"))
                elif s.mgla[h] and e in (0, 1):
                    kand.append((0.8, h, "ucho"))
        if not kand:
            return
        kand.sort(key=lambda x: -x[0])
        _, h, co = kand[0]
        s.akcje += 1
        if co == "rozstrzygnij":
            s.konf.discard(h)
            s.st[h] = 3
        elif co == "kto":
            s.st[h] = 3
        elif co == "sprawdz":
            s.st[h] = 4
            s.odslon(h)
            s.red.add(h)
        elif co == "odslon":
            s.odslon(h)
        elif co == "ucho":
            s.mgla[h] = False
        elif co == "wyjscie":
            if s.test(5, 0)[0]:
                s.st[h] = 5
                R, d = s.ryz_pub(h), s.k6()
                if d <= R:                              # test prawdy przegrany: halucynacja w eterze
                    s.skandal += R - d + 1
                    s.st[h] = 0
                s.szum[h], s.wiara[h] = [], []

    def zdarzenie(s, dzien):
        """2k6 HALUCYNACJE: 6 agent dopisuje cytat, 9 pewność siebie, 12 ostatnia chwila; reszta jak w symulacja_gry."""
        w = s.k6() + s.k6()
        ev = {"L": 0, "C": 0, "H": 0, "kto": 0, "musi": False}
        dz = sorted((h for h in s.H if h[0] == dzien), key=lambda h: h[1])
        okno = [h for h in s.H if s.okno(h, dzien)]
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
            k = [h for h in okno if s.st[h] >= 3]
            if k:
                s.szum[max(k, key=lambda h: (s.st[h], s.H[h]["W"]))].append(2)
        elif w == 8:
            ev["H"] = 1
        elif w == 9 and okno:
            for r in s.reka.values():
                if r:
                    c = min(r)
                    r.remove(c)
                    s.wiara[max(okno, key=lambda h: (s.st[h], s.H[h]["W"]))].append(c)
        elif w == 10:
            s.budzet = max(0, s.budzet - 1)
        elif w == 11:
            ev["L"] = 2
        elif w == 12:
            ev["musi"] = True
        return ev

    def graj(s):
        for dzien in range(7):
            ev = s.zdarzenie(dzien)
            if ev.get("musi"):
                k = [h for h in s.H if s.okno(h, dzien) and s.st[h] == 4]
                if k:
                    h = max(k, key=lambda x: s.H[x]["W"])
                    R, d = s.ryz_pub(h), s.k6()
                    s.st[h] = 5
                    if d <= R:
                        s.skandal += R - d + 1
                        s.st[h] = 0
                    s.szum[h], s.wiara[h] = [], []
            if s.P["karty"]:
                for k in s.reka:
                    while len(s.reka[k]) < 3 and s.talia:
                        s.reka[k].append(s.talia.pop())
            s.maszyna(dzien, max(0, s.P["L"] + ev["L"] + s.zwolnieni), "L", ev)
            s.maszyna(dzien, max(0, s.P["C"] + ev["C"]), "C", ev)
            s.redakcja(dzien, ev["H"])
            if s.skandal >= 5 and s.zwolnieni == 0 or s.skandal >= 7 and s.zwolnieni == 1:
                s.zwolnieni += 1
                if len(s.postacie) > 2:
                    s.postacie.pop()
            if s.skandal >= 9:
                return None
        pkt = sum(PKT[min(e, 2) if h in s.konf else e] * s.H[h]["W"] for h, e in s.st.items())
        kara = 2 * s.skandal + (10 if s.skandal >= 3 else 0)
        return pkt + s.wylapane + s.zrozumienie - kara


BAZA = dict(SG.BAZA, osoby=3, karty=True, p_karta=0.25, cel_pew=2, prog_dod=1.2, prog_pub=0.8, T=5, baza=4)


def seria(H, P, n, ziarno=11):
    rng = random.Random(ziarno)
    wyn, sk, prz, akc, wyl, zr = [], [], 0, [], [], []
    for _ in range(n):
        g = Gra(H, P, rng)
        w = g.graj()
        sk.append(g.skandal)
        akc.append(g.akcje)
        wyl.append(g.wylapane)
        zr.append(g.zrozumienie)
        if w is None:
            prz += 1
        else:
            wyn.append(w)
    q = statistics.quantiles(wyn, n=10) if len(wyn) > 10 else [0] * 9
    return {"p10": round(q[0]), "med": round(statistics.median(wyn)), "p90": round(q[8]), "skandal_sr": round(statistics.mean(sk), 1),
            "skandal>=1%": round(100 * sum(1 for x in sk if x >= 1) / n), "osmieszenie%": round(100 * sum(1 for x in sk if x >= 3) / n), "zwolnienia%": round(100 * sum(1 for x in sk if x >= 5) / n),
            "koniec%": round(100 * prz / n, 1), "wylapane": round(statistics.mean(wyl), 1), "zrozum": round(statistics.mean(zr), 1), "akcje": round(statistics.mean(akc))}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    for prof, t, h0, nazwa in SG.SCEN:
        H = SG.wycinek(prof, t, h0)
        print("== %s" % nazwa)
        for opis, zm in [("3 osoby", {}), ("3 os. cel 3 transkrypcje", {"cel_pew": 3}), ("3 os. bez drugich transkrypcji", {"cel_pew": 1}),
                         ("3 os. ryzykanci 50%", {"prog_pub": 0.5}), ("3 os. ryzykanci 50% + 3 transkr.", {"prog_pub": 0.5, "cel_pew": 3}),
                         ("4 osoby", {"osoby": 4, "ekip": 2, "H": 0, "budzet": 8}), ("6 osób", {"osoby": 6, "H": 0, "budzet": 8}), ("8 osób", {"osoby": 8, "H": 0, "budzet": 8})]:
            print("   %-38s %s" % (opis, seria(H, dict(BAZA, **zm), n)))
