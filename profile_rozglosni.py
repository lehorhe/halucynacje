# -*- coding: utf-8 -*-
"""Proceduralne „światy anteny” dla rozgłośni o różnym profilu — zamiast zrzutu z archiwum Szpiega+.

Każda godzina = mieszanka minut z audycji (typ audycji → zamierzony udział słowa i liczba głosów) i minut rotacji
muzycznej (luki w siatce). Dwie „metody pomiaru” (jak SMD i segmenty transkrypcji) różnią się tym bardziej, im bardziej
godzina miesza mowę z muzyką → mgła. Ziarno = profil + tydzień + dzień + godzina, więc plansza jest powtarzalna.

Profile:
    klasyczne  — idealna ramówka Radia Wnet (siatka z Documents/Ramowka-plakat/zrodlo/dane_ramowka.py)
    muzyczne   — komercyjne radio przebojów: poranny show, prezenterzy między piosenkami, noc bez słowa
    informacyjne — całodobowe radio newsowe: informacja, rozmowy, reportaż; w nocy powtórki
Wynik: {(kolumna_dnia, wiersz_godziny): {"slowo": {...jak plansza.procent_slowa}, "mowcy": n, "program": nazwa, "kat": kategoria}}"""
import hashlib
import random
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sciezki  # noqa: E402
sys.path.insert(0, sciezki.RAMOWKA)
import dane_ramowka as R  # noqa: E402

DNI_R = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

# kategoria → (udział słowa: średnia, rozrzut) · (głosy: min, max) · skłonność do mieszania mowy z muzyką 0..1
KAT = {
    "info":  ((0.94, 0.03), (4, 10), 0.10),
    "pub":   ((0.88, 0.05), (3, 8), 0.15),
    "zagr":  ((0.80, 0.07), (2, 6), 0.25),
    "wiara": ((0.82, 0.08), (1, 3), 0.20),
    "kult":  ((0.72, 0.09), (2, 5), 0.35),
    "styl":  ((0.60, 0.10), (2, 6), 0.55),
    "show":  ((0.42, 0.08), (2, 5), 0.85),       # poranny show w radiu muzycznym: mowa na podkładach
    "muz":   ((0.22, 0.07), (1, 2), 0.70),       # audycja muzyczna z prowadzącym
    "rot":   ((0.07, 0.03), (1, 1), 0.30),       # rotacja muzyczna, jingle, serwis co godzinę
    "powt":  ((0.86, 0.05), (3, 7), 0.15),       # nocne powtórki w radiu informacyjnym
    "sport": ((0.78, 0.08), (3, 9), 0.40),
    "koncert": ((0.12, 0.05), (1, 3), 0.80),
    "autorska": ((0.36, 0.08), (1, 2), 0.80),    # audycja autorska: prowadzący opowiada o muzyce, muzyka gra
    "sluchowisko": ((0.82, 0.07), (3, 8), 0.35), # słuchowisko / dokument dźwiękowy / reportaż
    "noc": ((0.05, 0.03), (1, 1), 0.25),         # nocny ocean muzyki
    "awatar": ((0.72, 0.07), (2, 3), 0.55),      # program dla Polonii prowadzony przez awatary głosów (AI, za zgodą)
}


def _m(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


# ---------------------------------------------------------------- siatki tygodnia (dzień → [(start_min, koniec_min, tytuł, kat)])
def siatka_klasyczna():
    return {d: [(_m(a), _m(b), t, k) for a, b, t, _p, k in R.DNI[d]] for d in DNI_R}


def siatka_muzyczna():
    rob = [("06:00", "10:00", "Poranny show", "show"), ("10:00", "15:00", "Przeboje z prezenterem", "muz"),
           ("15:00", "19:00", "Popołudnie z przebojami", "muz"), ("19:00", "21:00", "Lista przebojów", "muz")]
    wkd = [("08:00", "12:00", "Weekendowy poranek", "show"), ("12:00", "20:00", "Przeboje weekendu", "muz")]
    return {d: [(_m(a), _m(b), t, k) for a, b, t, k in (rob if i < 5 else wkd)] for i, d in enumerate(DNI_R)}


def siatka_informacyjna():
    rob = [("00:00", "05:00", "Powtórki nocne", "powt"), ("05:00", "09:00", "Poranek informacyjny", "info"),
           ("09:00", "12:00", "Rozmowy dnia", "pub"), ("12:00", "13:00", "Serwis południowy", "info"),
           ("13:00", "16:00", "Rozmowy popołudnia", "pub"), ("16:00", "19:00", "Wydanie wieczorne", "info"),
           ("19:00", "21:00", "Debata", "pub"), ("21:00", "24:00", "Reportaż i kultura", "kult")]
    wkd = [("00:00", "06:00", "Powtórki nocne", "powt"), ("06:00", "10:00", "Weekend informacyjny", "info"),
           ("10:00", "14:00", "Magazyn reporterów", "kult"), ("14:00", "18:00", "Rozmowy weekendu", "pub"),
           ("18:00", "20:00", "Sport na żywo", "sport"), ("20:00", "24:00", "Reportaż i muzyka", "styl")]
    return {d: [(_m(a), _m(b), t, k) for a, b, t, k in (rob if i < 5 else wkd)] for i, d in enumerate(DNI_R)}


def siatka_idealna(noc_dla_polonii=False):
    """Idealne radio klasyczne: format wzorowany na Programie III PR z czasów dyrekcji Krzysztofa Skowrońskiego i mówionych
    kanałach BBC (Radio 4) — gęste słowo w dzień, audycje autorskie wieczorem, reportaż i słuchowisko, nocą ocean muzyki.
    To wzorzec formatu, nie odtworzenie historycznej ramówki. noc_dla_polonii: 23–05 powtórki dnia + program dla Polaków
    za granicą prowadzony przez awatary głosów (zgody w umowach, oznaczenie AI)."""
    rob = [("05:00", "06:00", "Serwis i muzyka na dzień dobry", "styl"), ("06:00", "09:00", "Poranek: informacja i rozmowy", "pub"),
           ("09:00", "10:00", "Magazyn kulturalny", "kult"), ("10:00", "12:00", "Rozmowy przedpołudnia", "pub"),
           ("12:00", "13:00", "Serwis południowy i reportaż", "info"), ("13:00", "15:00", "Audycja autorska z muzyką", "autorska"),
           ("15:00", "18:00", "Popołudnie publicystyczne", "pub"), ("18:00", "19:00", "Dokument dźwiękowy", "sluchowisko"),
           ("19:00", "21:00", "Audycja autorska wieczorna", "autorska"), ("21:00", "23:00", "Wieczór rozmów i słuchowisko", "sluchowisko")]
    wkd = [("06:00", "08:00", "Poranek weekendowy", "styl"), ("08:00", "10:00", "Magazyn tygodnia", "kult"), ("10:00", "12:00", "Reportaż i rozmowa", "sluchowisko"),
           ("12:00", "14:00", "Rozmowy o świecie", "zagr"), ("14:00", "18:00", "Sport i rozmowy", "sport"), ("18:00", "20:00", "Słuchowisko", "sluchowisko"),
           ("20:00", "23:00", "Audycje autorskie", "autorska")]
    noc_zwykla = [("00:00", "05:00", "Nocny ocean muzyki", "noc"), ("23:00", "24:00", "Nocny ocean muzyki", "noc")]
    noc_polonii = [("23:00", "24:00", "Powtórka dnia", "powt"), ("00:00", "04:00", "Program dla Polonii — awatary głosów Wnet (AI)", "awatar"),
                   ("04:00", "05:00", "Powtórka poranka", "powt")]
    noc = noc_polonii if noc_dla_polonii else noc_zwykla
    out = {}
    for i, d in enumerate(DNI_R):
        dzien = rob if i < 5 else wkd
        if i == 4:      # piątek wieczorem: lista przebojów z prowadzącym (muzyka + słowo)
            dzien = [b for b in dzien if b[0] not in ("19:00", "21:00")] + [("19:00", "22:00", "Lista przebojów", "autorska"), ("22:00", "23:00", "Rozmowa na koniec tygodnia", "pub")]
        out[d] = [(_m(a), _m(b) if b != "24:00" else 1440, t, k) for a, b, t, k in dzien + noc]
    return out


PROFILE = {
    "klasyczne": {"nazwa": "Radio klasyczne — idealna ramówka Radia Wnet", "siatka": siatka_klasyczna, "serwis": True},
    "muzyczne": {"nazwa": "Radio muzyczne — przeboje i poranny show", "siatka": siatka_muzyczna, "serwis": True},
    "informacyjne": {"nazwa": "Radio informacyjne — całodobowe słowo", "siatka": siatka_informacyjna, "serwis": False},
    "idealne": {"nazwa": "Radio klasyczne — ideał (wzór: Trójka ery Skowrońskiego i mówione BBC)", "siatka": siatka_idealna, "serwis": True},
    "idealne_polonia": {"nazwa": "Radio klasyczne — ideał + noc dla Polonii (powtórki i awatary głosów Wnet)", "siatka": lambda: siatka_idealna(True), "serwis": True},
}

ZDARZENIA = [  # (nazwa, dzień_tyg | None=losowy, od, do, kat) — tygodniowe odstępstwa od siatki
    ("Wieczór wyborczy", None, 19, 24, "pub"),
    ("Koncert na żywo", None, 20, 23, "koncert"),
    ("Transmisja sportowa", None, 18, 21, "sport"),
    ("Awaria łącza", None, None, None, None),
    ("Dzień świąteczny", None, 0, 24, "swieto"),
]


def _rng(*klucz):
    klucz = tuple("idealne" if k == "idealne_polonia" else k for k in klucz)   # plansze 2 i 3: ten sam dzień, inna tylko noc
    return random.Random(int(hashlib.sha1("|".join(map(str, klucz)).encode()).hexdigest()[:12], 16))


def zdarzenia_tygodnia(profil, tydz):
    r = _rng(profil, "zdarzenia", tydz)
    n = 1 if tydz == 0 else r.choice([1, 2])
    out = []
    for z in r.sample(ZDARZENIA, n):
        dz = r.randrange(7) if z[0] != "Wieczór wyborczy" else 6
        if z[0] == "Awaria łącza":
            h0 = r.randrange(24)
            out.append((z[0], dz, h0, h0 + r.choice([1, 2]), None))
        else:
            out.append((z[0], dz, z[2], z[3], z[4]))
    return out


def godzina(profil, tydz, dzien, h, siatka, zd):
    """Udział słowa, rozrzut dwóch metod i głosy dla jednej godziny."""
    r = _rng(profil, tydz, dzien, h)
    for nazwa, dz, h0, h1, k in zd:
        if dz == dzien and h0 <= h < h1:
            if nazwa == "Awaria łącza":
                return None
            if nazwa == "Dzień świąteczny":
                siatka = {DNI_R[dzien]: PROFILE[profil]["siatka"]()["Niedziela"]}
                break
            (mu, sd), (g0, g1), mix = KAT[k]
            p = min(0.99, max(0.02, r.gauss(mu, sd)))
            return _wynik(r, p, mix, r.randint(g0, g1), nazwa, k)
    bloki = siatka.get(DNI_R[dzien]) or next(iter(siatka.values()))
    t0, t1 = h * 60, h * 60 + 60
    mowa, glosy, mix_w, tytul, kat, najd = 0.0, set(), 0.0, "Rotacja muzyczna", "rot", 0
    zajete = 0
    for a, b, t, k in bloki:
        o = max(0, min(t1, b) - max(t0, a))
        if not o:
            continue
        (mu, sd), (g0, g1), mix = KAT[k]
        p = min(0.99, max(0.02, r.gauss(mu, sd)))
        mowa += p * o
        mix_w += mix * o
        glosy.add((t, r.randint(g0, g1)))
        zajete += o
        if o > najd:
            najd, tytul, kat = o, t, k
    wolne = 60 - zajete
    if wolne:
        (mu, sd), _, mix = KAT["rot"]
        mowa += min(0.99, max(0.0, r.gauss(mu, sd))) * wolne
        mix_w += mix * wolne
    if PROFILE[profil]["serwis"] and 6 <= h <= 22 and kat in ("rot", "muz", "show"):
        mowa += 3.0          # serwis informacyjny o pełnej godzinie (3 min mowy)
    p = min(0.99, mowa / 60)
    mieszanie = 1 - abs(2 * (zajete / 60) - 1) if 0 < zajete < 60 else 0   # audycja + rotacja w jednej godzinie
    mix = min(1.0, mix_w / 60 + 0.6 * mieszanie)
    n = sum(g for _, g in glosy) + (1 if wolne and PROFILE[profil]["serwis"] else 0)
    return _wynik(r, p, mix, max(1, n), tytul, kat)


def _wynik(r, p, mix, glosy, tytul, kat):
    roz = abs(r.gauss(0, 1.5 + 9 * mix))                 # różnica metod w pp
    s = 100 * p
    a, b = max(0.0, s - roz / 2), min(100.0, s + roz / 2)
    return {"slowo": {"min": round(a, 1), "max": round(b, 1), "srodek": round(s, 1), "rozrzut_pp": round(b - a, 1), "n": 2,
                      "zgodne": b - a <= 5, "metody": {"smd": round(a, 1), "segmenty": round(b, 1)}},
            "mowcy": glosy, "program": tytul, "kat": kat}


def swiat(profil, tygodnie=4, godziny=range(24)):
    siatka = PROFILE[profil]["siatka"]()
    dane, zd_all = {}, []
    godziny = list(godziny)
    for t in range(tygodnie):
        zd = zdarzenia_tygodnia(profil, t)
        zd_all += [(t,) + z for z in zd]
        for d in range(7):
            for j, h in enumerate(godziny):
                dane[(t * 7 + d, j)] = godzina(profil, t, d, h, siatka, zd)
    return dane, zd_all


if __name__ == "__main__":
    for p in PROFILE:
        d, zd = swiat(p)
        wart = [g["slowo"]["min"] for g in d.values() if g]
        okno = [g["slowo"]["srodek"] for (i, j), g in d.items() if g and 6 <= j <= 23]
        lad = [x for x in wart if x >= 32.53]
        print("%-13s godzin %d · ląd %d%% · mgła %d · słowo w oknie 06–23: %.1f%% · zdarzenia: %s" % (
            p, len(d), 100 * len(lad) / len(d), sum(1 for g in d.values() if g and not g["slowo"]["zgodne"]),
            sum(okno) / len(okno), "; ".join("t%d %s %s %s–%s" % (t + 1, n, DNI_R[dz][:3], a, b) for t, n, dz, a, b, _ in zd)))
