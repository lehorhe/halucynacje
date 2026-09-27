# -*- coding: utf-8 -*-
"""Analiza 7 lat kalendarza „Nowa ramówka”: sezony, lato, etapowe wprowadzanie zmian, stałe miejsca (latarnie), dawne formaty.
Wejście: wystapienia.json (rozwin.py). Wyjście: analiza.json (+ wykresy SVG do dokumentu dla naczelnego).
Uwaga metodologiczna: kalendarz to plan redakcji (ok. 100–120 h tygodnia, bez nocy), a nie zapis emisji; edycja serii „wszystkie wydarzenia”
w Google przepisuje też przeszłość — dlatego stałość liczymy po latach potwierdzonych, a zmiany po tygodniach."""
import collections as C
import datetime as dt
import json
import os
import re
import statistics as S

TU = os.path.dirname(os.path.abspath(__file__))

# kanoniczne nazwy: prefiks nazwy bazowej (małe litery, bez prowadzącego po „ - ”) → nazwa
ALIASY = [
    ("porankowe", "Poranek Wnet"), ("poranek", "Poranek Wnet"),
    ("popołudnie", "Popołudnie Wnet"),
    ("kurier ekonomiczny", "Kurier ekonomiczny"), ("kurier", "Kurier w samo południe"), ("w samo południe", "Kurier w samo południe"), ("południe", "Kurier w samo południe"),
    ("magazyn", "Magazyn Wnet"),
    ("polish chart", "Polish Chart"), ("poliszczart", "Polish Chart"),
    ("república latina", "Republica Latina"), ("republica latina", "Republica Latina"),
    ("studio londyn", "Studio Londyn"), ("sztuka jest magią", "Sztuka jest magią"), ("złote lata piosenki", "Złote lata piosenki francuskiej"),
    ("na poczatku był chaos", "Na początku był chaos"), ("konfrontacje muzyczne", "Konfrontacje muzyczne"), ("muzyczne konfrontacje", "Konfrontacje muzyczne"),
    ("medycyna", "Medycyna św. Hildegardy"), ("prze-moc", "Prze-moc po Poranku"), ("czas na realizatora", "Czas na realizatora"), ("pora na realizatora", "Czas na realizatora"),
    ("muzyczne iq", "Muzyczne IQ"), ("radio solidarność", "Radio Solidarność"), ("studio wilno", "Studio Wilno"), ("riksza", "Riksza Miłosierdzia"),
    ("tygodniowy kalejdoskop", "Tygodniowy Kalejdoskop Kulturalny"), ("kalejdoskop kulturalny", "Tygodniowy Kalejdoskop Kulturalny"),
    ("program wschodni", "Program Wschodni"), ("wschodni", "Program Wschodni"), ("dobry wieczór w radio wnet", "Dobry wieczór w Radiu Wnet"),
    ("odnalezione pudełko", "Odnalezione pudełko"), ("muzyczny wtorek", "Muzyczny wtorek"), ("4 po pierwszej", "4 po pierwszej"), ("rapsy", "Rapsy"),
    ("beatlemania", "Beatlemania"), ("solarium", "Solarium"), ("świetlik", "Świetlik Wnet"), ("studio lwów", "Studio Lwów"),
    ("czas nie tylko na country", "Czas nie tylko na Country"), ("czas na country", "Czas nie tylko na Country"), ("czas na motorsport", "Czas na motorsport"),
    ("zwyciężajmy", "Zwyciężajmy razem"), ("nieregularnik", "Nieregularnik literacki"), ("kiedyś to było", "Kiedyś to było"),
    ("studio 37 muzycznie", "Studio 37 muzycznie"), ("studio 37", "Studio 37"), ("popart", "PopArt"), ("muzyczna polska tygodniówka", "Muzyczna Polska Tygodniówka"),
    ("pora karmienia", "Pora karmienia"), ("playlista", "Playlista / In the mix"), ("in the mix", "Playlista / In the mix"), ("in a mix", "Playlista / In the mix"), ("inny mix", "Playlista / In the mix"),
    ("serwis latynoski", "Serwis latynoski"), ("serwis watykański", "Serwis Watykański"), ("serwis międzynarodowy", "Serwis Międzynarodowy"),
    ("radiowy słup", "Radiowy słup ogłoszeniowy"), ("co słychać", "Co słychać?"), ("podsumowanie tygodnia", "Podsumowanie tygodnia"), ("polityczne podsumowanie", "Podsumowanie tygodnia"),
    ("podsumowanie dnia", "Podsumowanie dnia"), ("podsumowanie", "Podsumowanie dnia"), ("podsumoanie", "Podsumowanie dnia"),
    ("studio białoruskie", "Studio Białoruskie"), ("białoruskie noce", "Białoruskie noce"), ("sekcja lewacka", "Sekcja lewacka"),
    ("klub przyjaciół metali", "Klub Przyjaciół Metali Ziem Rzadkich"), ("odyseja wyborcza", "Odyseja wyborcza"), ("odyseja", "Odyseja"),
    ("wojna na ukrainie", "Wojna na Ukrainie (specjalne)"), ("studio dziki zachód", "Studio Dziki Zachód"), ("studio dublin", "Studio Dublin"),
    ("studio bejrut", "Studio Bejrut"), ("studio bałkany", "Studio Bałkany"), ("bałkany", "Studio Bałkany"), ("żebyś wiedział", "Żebyś wiedział"),
    ("mazzoll", "Mazzoll Arhythmic Radio"), ("duży pokój", "Duży Pokój"), ("bardzo duży pokój", "Bardzo duży pokój"), ("jak dobrze wstać", "Jak dobrze wstać skoro Wnet"),
    ("miś", "MiŚ"), ("mis", "MiŚ"),
]
ALIASY.sort(key=lambda a: -len(a[0]))
PROWADZACY = {"kondziu", "miki", "jaśmina", "hania", "łukasz", "magda", "ks", "arek", "igor", "kuba", "gosia", "kasia", "adi", "wybran", "konrad", "tomek"}
PROWADZACY_ROZSZ = PROWADZACY | {"jakubiak", "orzeł"}
OSOBY = {"rafał woś", "stanisław bukowski", "łukasz jankowski", "tomasz wybranowski", "ela mazzoll", "joanna rawik", "jerzy głuszyk"}
# rodzaj (przybliżony, po nazwie) — do udziałów słowo/muzyka w planie
MUZ = ("muzyk", "polska muzyka", "chart", "latina", "tygodniówka", "karmienia", "britbit", "mazzoll", "beatlemania", "jazz", "country", "rap", "mix",
       "playlista", "hands up", "piosenki", "pudełko", "konfrontacje", "ruletka", "nieprzeboj", "pojedynek", "iq", "dolce", "kabaret", "piaf", "śpiewnik",
       "klasyczna niedziela", "radioaktywni", "sofa", "na żywo u pieśniarzy", "pofolkuj", "rapsy", "studio 37 muzycznie", "miś", "czas na realizatora", "plejka")
SPECJALNE = ("wojna na ukrainie", "wybory", "olimpi", "mundial", "mistrzostwa", "studio olimpijskie", "pkp", "pociąg do lata", "górskie popołudnia",
             "zza parawanu", "wielka wyprawa", "program specjalny", "muza wielkanoc", "sterem i okrętem")


def kanon(nazwa, wielkosc=False):
    """Nazwa audycji bez prowadzącego. wielkosc=True: nieznane nazwy zachowują pisownię z kalendarza (do etykiet na planszy)."""
    czesci = re.split(r"\s+[-–]\s+|\s*\(|\s*,\s*wyd\.", nazwa or "")
    orig = czesci[0].strip()
    if orig.lower() in PROWADZACY and len(czesci) > 1 and czesci[1].strip():     # „Miki - Paryż”: prowadzący na początku
        orig = czesci[1].strip().rstrip(")")
    orig = re.sub(r"(?i)\s+salvatti$", "", orig)
    b = orig.lower()
    for pre, k in ALIASY:
        if b.startswith(pre):
            return k
    if wielkosc:
        slowa = set(re.findall(r"[a-ząćęłńóśźż]+", b))
        if slowa & PROWADZACY or b in OSOBY or re.search(r"\b(x|i)\b", b) and slowa & PROWADZACY_ROZSZ:
            return "Audycja autorska"                   # wpis kalendarza nazwany imieniem/nazwiskiem prowadzącego — na mapie bez osób
        return orig
    return b[:1].upper() + b[1:] if b else "?"


def czy_muz(k):
    n = k.lower()
    return any(m in n for m in MUZ)


def czy_spec(k):
    n = k.lower()
    return any(m in n for m in SPECJALNE)


def poniedzialek(d):
    return d - dt.timedelta(d.weekday())


def main():
    w = json.load(open(os.path.join(TU, "wystapienia.json"), encoding="utf-8"))
    for x in w:
        x["k"] = kanon(x["nazwa"])
        x["dd"] = dt.date.fromisoformat(x["d"])
    tyg = C.defaultdict(list)
    for x in w:
        tyg[poniedzialek(x["dd"])].append(x)
    tygodnie = sorted(t for t in tyg if t >= dt.date(2019, 6, 3) and t <= dt.date(2026, 9, 21))

    # siatka tygodnia: (dzień, godzina) → audycja; wystąpienia specjalne pomijamy (to nie ramówka)
    def siatka(t):
        s = {}
        for x in tyg[t]:
            if czy_spec(x["k"]):
                continue
            a = int(x["start"][:2]) * 60 + int(x["start"][3:])
            b = a + max(x["min"], 1)
            for m in range(a - a % 60, b, 60):
                if m >= a - 30 and m < 1440:
                    s[(x["wd"], m // 60)] = x["k"]
        return s
    SI = {t: siatka(t) for t in tygodnie}

    # 1) zmiany tydzień do tygodnia: odsetek slotów (dzień×godzina), w których zmieniła się audycja — ale tylko wobec tygodni „typowych”:
    # porównujemy z medianą z 3 poprzednich tygodni (jednorazowe zastępstwa nie są zmianą ramówki), a zmianę uznajemy za trwałą,
    # jeśli nowy układ utrzymał się także w 2 następnych tygodniach.
    def zgodnosc(a, b):
        kl = set(a) | set(b)
        return sum(1 for q in kl if a.get(q) == b.get(q)) / max(1, len(kl))
    zmiany = []
    for n, t in enumerate(tygodnie):
        if n < 1 or n + 2 >= len(tygodnie):
            continue
        prev, cur, nxt = SI[tygodnie[n - 1]], SI[t], [SI[tygodnie[n + 1]], SI[tygodnie[n + 2]]]
        kl = set(prev) | set(cur)
        trwale = [q for q in kl if prev.get(q) != cur.get(q) and all(z.get(q) == cur.get(q) for z in nxt)]
        zmiany.append({"tydzien": t.isoformat(), "trwale_sloty": len(trwale), "sloty": len(kl), "pct": round(100 * len(trwale) / max(1, len(kl)), 1),
                       "nowe": sorted({cur[q] for q in trwale if cur.get(q)} - set(prev.values())),
                       "zniknely": sorted({prev[q] for q in trwale if prev.get(q)} - set(cur.values()))})
    # miesiąc roku: średni odsetek trwałych zmian
    mies = C.defaultdict(list)
    for z in zmiany:
        mies[int(z["tydzien"][5:7])].append(z["pct"])
    sezonowosc = {m: round(sum(v), 1) for m, v in sorted(mies.items())}          # suma % trwałych zmian w danym miesiącu przez 7 lat
    duze = [z for z in zmiany if z["pct"] >= 8]

    # 2) fale ramówkowe: skupiska tygodni z trwałymi zmianami (przerwa ≤ 3 tygodnie spokoju), z sumą zmian ≥ 15 %
    fale, cur = [], None
    for z in zmiany:
        if z["pct"] >= 2.5:
            t = dt.date.fromisoformat(z["tydzien"])
            if cur and (t - cur["koniec"]).days <= 28:
                cur["koniec"] = t
                cur["tyg"].append(z)
            else:
                cur = {"poczatek": t, "koniec": t, "tyg": [z]}
                fale.append(cur)
    fale_out = []
    for f in fale:
        suma = sum(z["pct"] for z in f["tyg"])
        if suma < 12:
            continue
        glowny = max(f["tyg"], key=lambda z: z["pct"])
        nowe = sorted({n for z in f["tyg"] for n in z["nowe"]})
        znik = sorted({n for z in f["tyg"] for n in z["zniknely"]})
        fale_out.append({"poczatek": f["poczatek"].isoformat(), "koniec": f["koniec"].isoformat(), "tygodni_ze_zmianami": len(f["tyg"]),
                         "rozciagniecie_tyg": (f["koniec"] - f["poczatek"]).days // 7 + 1, "suma_pct": round(suma, 1),
                         "najwiekszy_tydzien": glowny["tydzien"], "najwiekszy_pct": glowny["pct"], "udzial_najwiekszego": round(glowny["pct"] / suma, 2),
                         "nowe": nowe[:25], "zniknely": znik[:25]})

    # 3) lato: plan lipca–sierpnia vs czerwiec i wrzesień tego samego roku
    lato = []
    for r in range(2019, 2027):
        def sr(miesiace):
            ts = [t for t in tygodnie if t.year == r and t.month in miesiace]
            if not ts:
                return None
            godz = S.mean(sum(x["min"] for x in tyg[t] if not czy_spec(x["k"])) / 60 for t in ts)
            slowo = S.mean(sum(x["min"] for x in tyg[t] if not czy_spec(x["k"]) and not czy_muz(x["k"])) / 60 for t in ts)
            aud = C.Counter(x["k"] for t in ts for x in tyg[t])
            return {"h_tydz": round(godz, 1), "h_slowo_tydz": round(slowo, 1), "aud": aud, "tyg": len(ts)}
        cz, lp, wr = sr([6]), sr([7, 8]), sr([9])
        if not lp or not cz:
            continue
        tylko_lato = sorted(k for k, v in lp["aud"].items() if cz and v >= 2 and cz["aud"].get(k, 0) == 0 and (not wr or wr["aud"].get(k, 0) == 0))
        pauza = sorted(k for k, v in cz["aud"].items() if v >= 3 and lp["aud"].get(k, 0) == 0)
        lato.append({"rok": r, "czerwiec_h": cz["h_tydz"], "lato_h": lp["h_tydz"], "wrzesien_h": wr["h_tydz"] if wr else None,
                     "czerwiec_slowo_h": cz["h_slowo_tydz"], "lato_slowo_h": lp["h_slowo_tydz"], "wrzesien_slowo_h": wr["h_slowo_tydz"] if wr else None,
                     "tylko_latem": tylko_lato, "pauza_na_lato": pauza})
    spec_lato = C.Counter()
    spec = []
    for k, xs in C.groupby if False else []:
        pass
    grupy = C.defaultdict(list)
    for x in w:
        grupy[x["k"]].append(x)
    for k, xs in grupy.items():
        if czy_spec(k):
            spec.append({"nazwa": k, "od": xs[0]["d"], "do": xs[-1]["d"], "h": round(sum(x["min"] for x in xs) / 60)})
    spec.sort(key=lambda s: s["od"])

    # 4) stałe miejsca: audycja × dzień × godzina startu → lata z ≥ 8 tygodniami w tym miejscu
    miejsca = C.defaultdict(lambda: C.defaultdict(set))
    for t in tygodnie:
        for x in tyg[t]:
            miejsca[(x["k"], x["wd"], x["start"][:2])][t.year].add(t)
    stale = []
    for (k, wd, g), lata in miejsca.items():
        ok = sorted(r for r, ts in lata.items() if len(ts) >= 8)
        if len(ok) >= 3:
            ciag, naj, poprz = 1, 1, None
            for r in ok:
                ciag = ciag + 1 if poprz is not None and r == poprz + 1 else 1
                naj, poprz = max(naj, ciag), r
            stale.append({"nazwa": k, "wd": wd, "godz": g, "lata": ok, "lat": len(ok), "ciag": naj, "tygodni": sum(len(ts) for ts in lata.values())})
    stale.sort(key=lambda s: (-s["ciag"], -s["tygodni"]))
    for s_ in stale:
        xs = [x for x in w if x["k"] == s_["nazwa"] and x["wd"] == s_["wd"] and x["start"][:2] == s_["godz"]]
        s_["serii"] = len({x["uid"] for x in xs})
        ost = [x for x in xs if x["d"] >= "2026"] or xs
        s_["start"] = C.Counter(x["start"] for x in ost).most_common(1)[0][0]
        s_["koniec"] = C.Counter(x["koniec"] for x in ost).most_common(1)[0][0]
    # scal dni tej samej audycji o tej samej godzinie
    scal = C.OrderedDict()
    for s in stale:
        key = (s["nazwa"], s["godz"], tuple(s["lata"]))
        scal.setdefault(key, dict(s, dni=[]))["dni"].append(s["wd"])
    stale = list(scal.values())
    lat_out = []
    for s_ in stale:
        if s_["ciag"] >= 5 and 2026 in s_["lata"] and not czy_spec(s_["nazwa"]):
            lat_out.append({"nazwa": s_["nazwa"], "dni": sorted(s_["dni"]), "start": s_["start"], "koniec": s_["koniec"], "lat": s_["ciag"],
                            "od": s_["lata"][-s_["ciag"]], "dowod": "rozne" if s_["serii"] >= 2 else "jedna"})
    json.dump(lat_out, open(os.path.join(TU, "latarnie.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("latarnie:", [(l["nazwa"], l["dni"], l["start"], l["lat"], l["dowod"]) for l in lat_out])

    # 5) dawne formaty: ≥ 40 h, żyły ≥ 9 miesięcy, zniknęły przed 03.2026
    dawne, zycie = [], []
    for k, xs in grupy.items():
        h = sum(x["min"] for x in xs) / 60
        od, do = xs[0]["dd"], xs[-1]["dd"]
        if h >= 30 and not czy_spec(k):
            zycie.append((do - od).days / 365.25)
        if h >= 40 and (do - od).days >= 270 and do < dt.date(2026, 3, 1) and not czy_spec(k):
            sl = C.Counter((x["wd"], x["start"][:2]) for x in xs).most_common(1)[0][0]
            dawne.append({"nazwa": k, "od": od.isoformat()[:7], "do": do.isoformat()[:7], "lat": round((do - od).days / 365.25, 1), "h": round(h),
                          "slot": "%s %s:00" % ("pn wt śr cz pt so nd".split()[sl[0]], sl[1]), "muzyczna": czy_muz(k)})
    dawne.sort(key=lambda d: -d["h"])

    # 6) rok po roku
    lata_stat = []
    for r in range(2019, 2027):
        ts = [t for t in tygodnie if t.year == r]
        xs = [x for t in ts for x in tyg[t] if not czy_spec(x["k"])]
        if not ts:
            continue
        aud = {x["k"] for x in xs}
        nowe = {k for k in aud if grupy[k][0]["dd"].year == r}
        konczace = {k for k in aud if grupy[k][-1]["dd"].year == r and r < 2026}
        h = sum(x["min"] for x in xs) / 60 / len(ts)
        hm = sum(x["min"] for x in xs if czy_muz(x["k"])) / 60 / len(ts)
        lata_stat.append({"rok": r, "tygodni": len(ts), "audycji": len(aud), "nowych": len(nowe), "zakonczonych": len(konczace),
                          "h_tydz": round(h, 1), "udzial_muzycznych_pct": round(100 * hm / h, 1) if h else None})

    out = {"zrodlo": "kalendarz Google „Nowa ramówka” (publiczny iCal, pobrany 2026-09-27)", "wystapien": len(w), "audycji_kanon": len(grupy),
           "tygodni": len(tygodnie), "sezonowosc_suma_pct_zmian_wg_miesiaca": sezonowosc, "fale": fale_out, "duze_tygodnie": duze,
           "lato": lato, "specjalne": spec, "stale_miejsca": stale[:60], "dawne_formaty": dawne[:60], "lata": lata_stat,
           "mediana_zycia_audycji_lat": round(S.median(zycie), 2), "zmiany_tygodniowe": [{"t": z["tydzien"], "pct": z["pct"]} for z in zmiany]}
    json.dump(out, open(os.path.join(TU, "analiza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("fale:", len(fale_out), "· stałe miejsca:", len(stale), "· dawne:", len(dawne))
    print("sezonowość:", sezonowosc)
    for f in fale_out:
        print(f["poczatek"], "→", f["koniec"], "%2d tyg. zmian / %2d tyg." % (f["tygodni_ze_zmianami"], f["rozciagniecie_tyg"]), "suma %5.1f%%" % f["suma_pct"],
              "najw.", f["najwiekszy_tydzien"], f["najwiekszy_pct"])
    for l in lato:
        print(l["rok"], "cz", l["czerwiec_h"], l["czerwiec_slowo_h"], "| lato", l["lato_h"], l["lato_slowo_h"], "| wrz", l["wrzesien_h"], l["wrzesien_slowo_h"],
              "| tylko latem:", l["tylko_latem"][:6], "| pauza:", l["pauza_na_lato"][:8])
    for s in stale[:25]:
        print("%-38s %-12s %s:00 lat %d ciąg %d %s" % (s["nazwa"], ",".join("pn wt śr cz pt so nd".split()[d] for d in s["dni"]), s["godz"], s["lat"], s["ciag"], s["lata"]))
    for l in lata_stat:
        print(l)
    print("mediana życia audycji (lata):", out["mediana_zycia_audycji_lat"])


if __name__ == "__main__":
    main()
