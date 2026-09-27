# -*- coding: utf-8 -*-
"""Pliki do druku na kolegium 28.09.2026 (druk24h, Polna 11; plakat foto mat 180 g). Katalog Do_druku_2026-09-28/:
  A0  — 01_A0_Plansza1_Mapa_prawdy.pdf
  A2  — 02_A2_Plansza2_Idealne_radio.pdf, 03_A2_Plansza3_Noc_dla_Polonii.pdf   (skalowane z A0 ×0,5 — wektor, bez utraty jakości)
  A3  — 04_A3_Blender_orto.pdf, 05_A3_Blender_dron.pdf, 06_A3_Siedem_lat_ramowki.pdf (kilka stron), 07_A3_Karta_pomocy_i_tory.pdf,
        08_A3_Wizja_AI_vs_dane.pdf
Każdy plik: dokładnie format docelowy, bez spadów (druk plakatowy), marginesy w treści.
    python do_druku.py"""
import os
import subprocess

import pymupdf as fitz

TU = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TU, "Do_druku_2026-09-28")
os.makedirs(OUT, exist_ok=True)
MM = 72 / 25.4
A = {"A0": (841, 1189), "A2": (420, 594), "A3": (297, 420)}
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def skaluj(src, dst, fmt, strony=None, poziomo=False):
    s = fitz.open(src)
    d = fitz.open()
    w, h = A[fmt]
    if poziomo:
        w, h = h, w
    for k in strony or range(len(s)):
        p = d.new_page(width=w * MM, height=h * MM)
        p.show_pdf_page(p.rect, s, k, keep_proportion=True)
    d.save(dst, deflate=True)
    print(dst, len(d), "str.")


FONT = dict(fontname="segoe", fontfile=r"C:\Windows\Fonts\segoeui.ttf")
FONTB = dict(fontname="segoeb", fontfile=r"C:\Windows\Fonts\segoeuib.ttf")
LASERY = [("publicystyka", (1.0, 0.62, 0.05)), ("muzyka", (0.9, 0.1, 0.08)), ("kultura", (0.1, 0.75, 0.3)), ("zagranica", (0.2, 0.75, 0.95)),
          ("informacja, styl", (0.15, 0.35, 0.95)), ("wiara", (0.55, 0.2, 0.9)), ("noc bez ramówki", (0.8, 0.82, 0.86))]


def legenda3d(p, x, y, w, h):
    """Legenda świata 3D: kolory laserów, znaczenie elementów sceny, liczniki i wynik testu zgodności 2D↔3D."""
    import json
    O = json.load(open(os.path.join(TU, "blender", "eksport", "obiekty.json"), encoding="utf-8"))
    T = json.load(open(os.path.join(TU, "test_zgodnosci_raport.json"), encoding="utf-8"))
    p.draw_rect(fitz.Rect(x, y, x + w, y + h), color=(0.84, 0.88, 0.9), fill=(0.96, 0.97, 0.98), width=0.6)
    k = w / 3
    p.insert_text((x + 8, y + 16), "Lasery = rodzaj audycji", fontsize=10, color=(0.15, 0.31, 0.36), **FONTB)
    for n, (t, c) in enumerate(LASERY):
        yy = y + 30 + n * 12.5
        p.draw_line((x + 8, yy - 3.5), (x + 30, yy - 3.5), color=c, width=3.2)
        p.insert_text((x + 36, yy), t, fontsize=8.6, color=(0.1, 0.1, 0.1), **FONT)
    x2 = x + k
    p.insert_text((x2, y + 16), "Co jest czym", fontsize=10, color=(0.15, 0.31, 0.36), **FONTB)
    for n, t in enumerate(["wysokość terenu = % słowa w godzinie", "morze = godziny muzyki (poniżej progu)", "domy = głosy efektywne (4 na znak)",
                           "las = rozmowa; nagie zbocza = monolog", "latarnia = audycja od lat w tym miejscu", "wysepka = latarnia w godzinie muzyki",
                           "lustra 40 m nad terenem: wierzchołki heksów"]):
        p.insert_text((x2, y + 30 + n * 12.5), t, fontsize=8.6, color=(0.1, 0.1, 0.1), **FONT)
    x3 = x + 2 * k
    p.insert_text((x3, y + 16), "Ile tu jest", fontsize=10, color=(0.15, 0.31, 0.36), **FONTB)
    wiersze = ["%d heksów-godzin · %d domów" % (T["T1_lad_morze"]["heksow"], len(O["domy"])), "%d drzew · %d latarni (%d na wysepkach)" % (
        len(O["drzewa"]), len(O["latarnie"]), len(O["wysepki"])), "%d wiązek laserów" % len(O["lasery"]),
        "Zgodność z mapą 2D: %s" % T["wynik"], "ląd/morze, osady, latarnie, kolory: 0 różnic", "brzeg %d%% · Spearman %.2f" % (
            round(100 * T["T5_brzeg"]["zgodnosc_srodkow"]), T["T5_brzeg"]["spearman_wysokosc_slowo"])]
    for n, t in enumerate(wiersze):
        p.insert_text((x3, y + 30 + n * 12.5), t, fontsize=8.6, color=(0.05, 0.45, 0.25) if "ZGODNE" in t else (0.1, 0.1, 0.1), **(FONTB if "ZGODNE" in t else FONT))


def obraz_a3(png, dst, tytul, podpis, poziomo=False, legenda=False):
    w, h = A["A3"]
    if poziomo:
        w, h = h, w
    d = fitz.open()
    p = d.new_page(width=w * MM, height=h * MM)
    m = 14 * MM
    p.insert_text((m, m + 18), tytul, fontsize=22, color=(0.153, 0.31, 0.36), **FONTB)
    reszta = p.insert_textbox(fitz.Rect(m, m + 28, w * MM - m, m + 82), podpis, fontsize=9.6, color=(0.25, 0.35, 0.4), **FONT)
    assert reszta >= 0, "podpis nie mieści się w ramce"
    dol = 118 if legenda else 0
    ramka = fitz.Rect(m, m + 86, w * MM - m, h * MM - m - dol)
    p.insert_image(ramka, filename=png, keep_proportion=True)
    if legenda:
        legenda3d(p, m, h * MM - m - dol + 8, w * MM - 2 * m, dol - 14)
    p.insert_text((m, h * MM - m / 2), "HALUCYNACJE · Szpieg+ · Radio Wnet · render: Blender 5.2 z danych mapy prawdy (bez generowania obrazu przez AI) · 28.09.2026",
                  fontsize=7.5, color=(0.35, 0.44, 0.48))
    d.save(dst, deflate=True)
    print(dst)


def html_a3(src, dst):
    """Dokument „Siedem lat ramówki” (strona HTML) → PDF A3 przez Chrome; @page A3 wstrzyknięte w kopię."""
    t = open(src, encoding="utf-8").read()
    t = "<style>@page{size:297mm 420mm;margin:16mm 18mm}body{font-size:15px}.kartka{max-width:none}figure,table,.tezy li{break-inside:avoid}</style>" + t
    tmp = os.path.join(TU, "ramowka_7lat", "_druk_a3.html")
    open(tmp, "w", encoding="utf-8").write("<!doctype html><html lang='pl'><head><meta charset='utf-8'></head><body>" + t + "</body></html>")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    "--print-to-pdf=" + dst, "file:///" + tmp.replace("\\", "/")], check=True, capture_output=True)
    print(dst, len(fitz.open(dst)), "str.")


def main():
    skaluj(os.path.join(TU, "Mapa_prawdy_A0.pdf"), os.path.join(OUT, "01_A0_Plansza1_Mapa_prawdy.pdf"), "A0")
    skaluj(os.path.join(TU, "Plansza_A0_idealne.pdf"), os.path.join(OUT, "02_A2_Plansza2_Idealne_radio.pdf"), "A2")
    skaluj(os.path.join(TU, "Plansza_A0_idealne_polonia.pdf"), os.path.join(OUT, "03_A2_Plansza3_Noc_dla_Polonii.pdf"), "A2")
    r = os.path.join(TU, "blender", "render")
    if os.path.exists(os.path.join(r, "kadr_orto.png")):
        obraz_a3(os.path.join(r, "kadr_orto.png"), os.path.join(OUT, "04_A3_Blender_orto.pdf"), "Plansza 1 w 3D: widok z góry",
                 "Ten sam świat co na mapie prawdy: 31.08–13.09.2026, godziny 00–13. Wysokość = % słowa, domy = głosy efektywne, las = życie rozmowy, "
                 "woda = godziny muzyczne, latarnie = audycje od lat w tym samym miejscu. 1 heks = 1 godzina anteny ≈ 125 m. Heksy wyznaczają lasery między lustrami na "
                 "niewidzialnych wieżach, 40 m nad najwyższym punktem okolicy; kolor = rodzaj audycji z kalendarza (bursztyn publicystyka, czerwień muzyka, "
                 "zieleń kultura, błękit zagranica, niebieski informacja/styl, fiolet wiara, biel noc bez ramówki).", legenda=True)
    if os.path.exists(os.path.join(r, "kadr_dron.png")):
        obraz_a3(os.path.join(r, "kadr_dron.png"), os.path.join(OUT, "05_A3_Blender_dron.pdf"), "Sobota 12.09, 10:00 — z drona, 90 m",
                 "Heks Programu Wschodniego (latarnia: 8 lat w tym samym miejscu ramówki), osada z głosów tej godziny, brzeg morza muzyki z porannego pasma. "
                 "Kamera jak w dronie cywilnym klasy Mini: 24 mm ekwiwalentu, 90 m nad terenem. Lasery heksów świecą barwą audycji i rzucają poblask na korony drzew i dachy.", poziomo=True, legenda=True)
    html_a3(os.path.join(TU, "ramowka_7lat", "Siedem_lat_ramowki.html"), os.path.join(OUT, "06_A3_Siedem_lat_ramowki.pdf"))
    skaluj(os.path.join(TU, "Zestaw_startowy_A4.pdf"), os.path.join(OUT, "07_A3_Karta_pomocy_i_tory.pdf"), "A3", strony=[3, 4])
    obraz_a3(os.path.join(TU, "wizja_blender", "porownanie.jpg"), os.path.join(OUT, "08_A3_Wizja_AI_vs_dane.pdf"), "Kiedy obraz halucynuje",
             "Ten sam wycinek planszy oddany dwóm modelom graficznym. gpt-image-2.5 przesunął brzeg i dostawił latarnie, których nie ma w danych; "
             "gemini-3-pro-image zachował układ. Wniosek: obrazy AI tylko jako wzór stylu — plansza powstaje z danych (Blender).")


if __name__ == "__main__":
    main()
