# -*- coding: utf-8 -*-
"""Karty HALUCYNACJE do druku dwustronnego na papierze fotograficznym — 72 przekonania + 8 postaci.

Format: 57 × 89 mm („bridge size” 2,25 × 3,5″ — węższy od pokerowego 63,5 × 88,9 mm, w standardzie kart kasynowych USA).
Arkusz A4: 3 × 3 karty stykające się krawędziami (tło do linii cięcia — przesunięcie dupleksu o 1–2 mm nie zostawi białego paska),
znaczniki cięcia na marginesach. Strony: nieparzyste = AWERSY (strona błyszcząca), parzyste = REWERSY (strona matowa), lustrzane
w poziomie pod obracanie wzdłuż DŁUŻSZEJ krawędzi. Rewers zaprojektowany pod matowy papier: jasne tło, czarny tekst, jednolite
grube ramki koloru kategorii, bez gradientów (mat spłaszcza paletę).
    python karty_druk.py        → Karty_HALUCYNACJE_duplex_A4.pdf"""
import json
import os
import sys
from html import escape

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TU)
import swiat_antena as SA  # noqa: E402

W, H = 57.15, 88.9
KOL, RZ = 3, 3
X0, Y0 = (210 - KOL * W) / 2, (297 - RZ * H) / 2

KAT = {  # kolor (awers nasycony), kolor ramki rewersu (ciemniejszy, pewny w macie), ikona 24×24
    "zdrowie": ("#C8384E", "#9E1F36", '<path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z"/>'),
    "zwierzeta": ("#2E8B57", "#1D6040", '<circle cx="7" cy="9" r="1.9"/><circle cx="11" cy="5.8" r="1.9"/><circle cx="15.5" cy="6.4" r="1.9"/><circle cx="18.6" cy="10" r="1.9"/><path d="M8.3 17.2c0-3.4 2.4-6 4.8-6s4.8 2.6 4.8 6c0 2-1.6 2.8-3 2.3-1.1-.4-2.5-.4-3.6 0-1.4.5-3-.3-3-2.3z"/>'),
    "historia": ("#9A6324", "#6E4415", '<path d="M7 3h10M7 21h10M8 3c0 5 8 5 8 9s-8 4-8 9M16 3c0 5-8 5-8 9s8 4 8 9"/>'),
    "kultura": ("#7E57B8", "#583A8C", '<path d="M12 3v2M8 6h8l1.5 3v7L16 19H8l-1.5-3V9z"/><path d="M6.5 12h11M10 21h4"/>'),
    "jezyk": ("#2F7C95", "#1C5668", '<path d="M3.5 5h17v11H11l-5 4v-4H3.5z"/><path d="M7.5 9h9M7.5 12.5h6"/>'),
    "swiat": ("#1F7A6E", "#115247", '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18"/>'),
    "kuchnia": ("#D88A1E", "#9C5E08", '<path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M16 21V3c-2.5 1.5-3.5 4-3.5 8h3.5"/>'),
    "cytaty": ("#1B2A33", "#0A1318", '<path d="M5 17c0-4 1-8 5-10l.8 1.5C8.7 10 8.2 12 8.3 13H11v5H5zM13 17c0-4 1-8 5-10l.8 1.5c-2.1 1.5-2.6 3.5-2.5 4.5H19v5h-6z"/>'),
    "postac": ("#274F5C", "#16323B", '<circle cx="12" cy="7" r="3.8"/><path d="M4.5 21.5c.9-4.8 3.8-7.3 7.5-7.3s6.6 2.5 7.5 7.3"/>'),
}
NAZWY_KAT = {"zdrowie": "Ciało i zdrowie", "zwierzeta": "Zwierzęta", "historia": "Historia", "kultura": "Obyczaje i święta", "jezyk": "Języki i znaki",
             "swiat": "Świat i mapy", "kuchnia": "Kuchnia i przybysze", "cytaty": "Cytaty i media", "postac": "Postać redakcji"}

POSTACIE = [
    ("Szefowa lub szef redakcji", "8. osoba", "Odprawa: raz na turę daj dowolnej postaci 1 dodatkową akcję.", "Biorę to na siebie: raz na grę cofnij tor skandalu o 1."),
    ("Wydawca", "ekipa na mapie", "2 akcje. WYD✓: Kto bez rzutu albo rozstrzygnięcie konfliktu.", "Wyjście (WP, POD): rzut 2+, potem test prawdy."),
    ("Redaktor lub redaktorka", "ekipa na mapie", "2 akcje. RED✓: Sprawdzone bez rzutu — zdejmij wszystkie znaczniki ryzyka i odwróć karty przekonań.", "Ucho: rozwiej mgłę bez rzutu."),
    ("Weryfikatorka lub weryfikator", "5. osoba", "1 akcja bez rzutu, dowolny heks w oknie czasu:", "zdejmij 1 znacznik ryzyka albo odwróć 1 kartę przekonania."),
    ("Opiekun Kolonii", "maszyny", "Prowadzi lokalne modele: 4 akcje zielonymi żetonami, bez kosztu.", "Wie, że maszyna bywa pewna siebie i myli się."),
    ("Opiekunka Chmury", "maszyny", "Prowadzi płatne modele: do 3 akcji niebieskimi żetonami, każda −1 budżetu.", "Nigdy na heksie „poufne”."),
    ("Reporterka lub reporter", "6. osoba · ekipa", "1 akcja bez rzutu: notatka z terenu — dodatkowa transkrypcja (Pewność +1) na heksie ekipy lub sąsiednim.", "+1 do rzutów na Kto w zasięgu ekipy."),
    ("Realizator dźwięku", "7. osoba", "1 akcja bez rzutu: rozwiej mgłę na dowolnym heksie w oknie czasu.", "Stale: +1 do rzutów na Słowa na żywo."),
]

CSS = """@font-face{font-family:'Exo 2';src:url('file:///%(f)s/exo2-600-900.woff2') format('woff2');font-weight:500 900}
@font-face{font-family:'Lato';src:url('file:///%(f)s/lato-400.woff2') format('woff2');font-weight:400}
@font-face{font-family:'Lato';src:url('file:///%(f)s/lato-700.woff2') format('woff2');font-weight:700}
@page{size:210mm 297mm;margin:0}html,body{margin:0;padding:0}
.s{position:relative;width:210mm;height:297mm;overflow:hidden;page-break-after:always;break-after:page}
.k{position:absolute;width:%(w).2fmm;height:%(h).2fmm;box-sizing:border-box;overflow:hidden;font-family:Lato,sans-serif}
.aw{color:#fff;padding:4.2mm 4.2mm 3.6mm}
.aw .gl{display:flex;justify-content:space-between;font:800 6.2pt 'Exo 2';letter-spacing:.09em;text-transform:uppercase;opacity:.9}
.aw .ik{position:absolute;right:-6mm;top:15mm;width:44mm;height:44mm;opacity:.16}
.aw .tw{position:absolute;left:4.2mm;right:4.2mm;top:17mm;font:800 12.2pt/1.2 'Exo 2';hyphens:auto}
.aw .tw.dl{font-size:10.4pt}.aw .tw.bdl{font-size:9.2pt}
.aw .gd{position:absolute;left:4.2mm;right:4.2mm;bottom:15mm;font:700 7pt/1.3 Lato;opacity:.95}
.aw .gd b{display:block;font:800 5.8pt 'Exo 2';letter-spacing:.08em;text-transform:uppercase;opacity:.8}
.aw .st{position:absolute;left:4.2mm;right:4.2mm;bottom:3.8mm;display:flex;align-items:center;justify-content:space-between;border-top:.35mm solid rgba(255,255,255,.55);padding-top:1.6mm}
.aw .st .p{font:800 7pt 'Exo 2'}.aw .st .kr{display:flex;gap:1.1mm}.aw .st .kr i{display:block;width:3.2mm;height:3.2mm;border-radius:50%%;background:#fff}
.aw .st .kr i.o{background:transparent;border:.35mm solid #fff}
.rw{background:#fff;color:#000;border:3.2mm solid;padding:3.4mm 3.4mm 3mm}
.rw h4{margin:0 0 1.2mm;font:900 7.4pt 'Exo 2';letter-spacing:.08em;text-transform:uppercase}
.rw p{margin:0 0 2.4mm;font:400 8.1pt/1.34 Lato}.rw p.u{font-size:7.9pt}
.rw .kr2{position:absolute;left:3.4mm;right:3.4mm;bottom:2.6mm;display:flex;justify-content:space-between;font:800 5.8pt 'Exo 2';letter-spacing:.06em;text-transform:uppercase}
.rw .lin{height:.6mm;margin:1.6mm 0 2mm}
.po .tw{top:30mm;font-size:12pt}.po .op{position:absolute;left:4.2mm;right:4.2mm;top:48mm;font:400 7.4pt/1.35 Lato}
.ciecie{position:absolute;left:0;top:0;width:210mm;height:297mm}
.inf{position:absolute;left:12mm;right:12mm;bottom:3mm;font:400 6.5pt Lato;color:#666}
""" % {"f": SA.FONTY.replace("\\", "/"), "w": W, "h": H}


def ikona(kat, kolor="#fff", gr=1.6):
    return '<svg class="ik" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (kolor, gr, KAT[kat][2])


def awers(k):
    kol = KAT[k["kat"]][0]
    dl = len(k["tw"])
    klasa = "tw" + (" bdl" if dl > 95 else (" dl" if dl > 62 else ""))
    kr = "".join('<i%s></i>' % ("" if n < k["sila"] else ' class="o"') for n in range(3))
    return ('<div class="k aw" style="background:%s;left:%%.2fmm;top:%%.2fmm">%s<div class="gl"><span>Halucynacje · przekonanie</span><span>%d</span></div>'
            '<div class="%s">%s</div><div class="gd"><b>Wierzą w to</b>%s</div>'
            '<div class="st"><span class="p">Zagraj: +%d do rzutu</span><span class="kr">%s</span></div></div>') % (
        kol, ikona(k["kat"]), k["nr"], klasa, escape(k["tw"]), escape(k["gdzie"]), k["sila"], kr)


def rewers(k):
    kol = KAT[k["kat"]][1]
    return ('<div class="k rw" style="border-color:%s;left:%%.2fmm;top:%%.2fmm"><h4 style="color:%s">Jak jest naprawdę</h4><p>%s</p>'
            '<div class="lin" style="background:%s"></div><h4 style="color:%s">Ukryta prawda</h4><p class="u">%s</p>'
            '<div class="kr2" style="color:%s"><span>%s</span><span>nr %d · waga %d</span></div></div>') % (
        kol, kol, escape(k["naprawde"]), kol, kol, escape(k["ukryta"]), kol, escape(NAZWY_KAT[k["kat"]]), k["nr"], k["sila"])


def awers_postaci(i, p):
    kol = KAT["postac"][0]
    return ('<div class="k aw po" style="background:%s;left:%%.2fmm;top:%%.2fmm">%s<div class="gl"><span>Postać</span><span>%s</span></div>'
            '<div class="tw">%s</div><div class="op">%s<br><br>%s</div>'
            '<div class="st"><span class="p">Redakcja 8 osób</span><span class="p">%d / 8</span></div></div>') % (
        kol, ikona("postac"), escape(p[1]), escape(p[0]), escape(p[2]), escape(p[3]), i + 1)


def rewers_postaci(i, p):
    kol = KAT["postac"][1]
    return ('<div class="k rw" style="border-color:%s;left:%%.2fmm;top:%%.2fmm"><h4 style="color:%s">Zwolniona postać</h4>'
            '<p>Gdy tor skandalu dojdzie do 5 (i do 7), drużyna odwraca jedną kartę postaci. Ta postać traci swoje akcje.</p>'
            '<div class="lin" style="background:%s"></div><h4 style="color:%s">Syntetyczny kolega</h4>'
            '<p class="u">Osoba, która ją prowadziła, zostaje w grze: przejmuje syntetycznego kolegę — Kolonia dostaje +1 akcję w każdej turze.</p>'
            '<div class="kr2" style="color:%s"><span>Postać redakcji</span><span>%d / 8</span></div></div>') % (kol, kol, kol, kol, kol, i + 1)


def arkusz(elementy, lustro):
    """elementy: szablony HTML z dwoma %.2f (left, top). lustro=True: kolumny odwrócone pod dupleks wzdłuż dłuższej krawędzi."""
    h = ""
    for n, el in enumerate(elementy):
        r, c = divmod(n, KOL)
        if lustro:
            c = KOL - 1 - c
        h += el % (X0 + c * W, Y0 + r * H)
    svg = '<svg class="ciecie" viewBox="0 0 210 297">'
    for c in range(KOL + 1):
        x = X0 + c * W
        svg += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width=".25"/><line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width=".25"/>' % (
            x, Y0 - 7, x, Y0 - 1.5, x, Y0 + RZ * H + 1.5, x, Y0 + RZ * H + 7)
    for r in range(RZ + 1):
        y = Y0 + r * H
        svg += '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width=".25"/><line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width=".25"/>' % (
            X0 - 7, y, X0 - 1.5, y, X0 + KOL * W + 1.5, y, X0 + KOL * W + 7, y)
    return h + svg + "</svg>"


def main():
    dane = json.load(open(os.path.join(TU, "karty_przekonan.json"), encoding="utf-8"))
    karty = dane["karty"]
    aw = [awers(k) for k in karty] + [awers_postaci(i, p) for i, p in enumerate(POSTACIE)]
    rw = [rewers(k) for k in karty] + [rewers_postaci(i, p) for i, p in enumerate(POSTACIE)]
    strony = []
    for a in range(0, len(aw), KOL * RZ):
        nr = a // (KOL * RZ) + 1
        strony.append('<div class="s">%s<div class="inf">Arkusz %d · AWERSY — strona błyszcząca · 57 × 89 mm · drukuj dwustronnie, obracanie wzdłuż dłuższej krawędzi, skala 100%%</div></div>' % (
            arkusz(aw[a:a + 9], False), nr))
        strony.append('<div class="s">%s<div class="inf">Arkusz %d · REWERSY — strona matowa (lustro pod dupleks)</div></div>' % (arkusz(rw[a:a + 9], True), nr))
    html = "<!doctype html><html lang='pl'><head><meta charset='utf-8'><style>%s</style></head><body>%s</body></html>" % (CSS, "".join(strony))
    hp = os.path.join(TU, "karty_druk.html")
    open(hp, "w", encoding="utf-8").write(html)
    import subprocess
    pdf = os.path.join(TU, "Karty_HALUCYNACJE_duplex_A4.pdf")
    subprocess.run([SA.sciezki.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=15000", "--print-to-pdf=" + pdf, "file:///" + hp.replace("\\", "/")],
                   capture_output=True, timeout=300)
    print(pdf, os.path.getsize(pdf), "B ·", len(aw), "kart ·", len(strony), "stron")


if __name__ == "__main__":
    main()
