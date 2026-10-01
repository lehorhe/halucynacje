# -*- coding: utf-8 -*-
"""Zasady „HALUCYNACJE · Świat anteny” 1.0 — JEDNO źródło treści: plakat A0 (plakat_a0.py), zeszyt A4 i strona /zasady (wydanie.py),
karta pomocy i tory (plansza_gry.py). Liczby: siły = nadruk żetonów (warstwy/model.json), progi ocen = symulacja_gry.py."""
import json
from html import escape

import plansza_gry as PG

WERSJA = "1.0"
import os as _os
import sciezki as _sc
M = json.load(open(_os.path.join(_sc.WARSTWY, "model.json"), encoding="utf-8"))
Z = {z["id"]: z for z in M["zetony"]}
ETAPY = ["", "Słowa", "Głosy", "Kto", "Sprawdzone", "Wyjście"]
PKT = {1: 1, 2: 2, 3: 3, 4: 5, 5: 8}

# (żeton, rola, etap, okno, rzut?)  okno: „na żywo” = kolumna tury; „po godzinie” = dwie poprzednie kolumny; „oba” = obie
AKCJE = [
    ("live_lokal", "Kolonia", 1, "na żywo", True), ("batch_lokal", "Kolonia", 1, "po godzinie", True),
    ("diar_live", "Kolonia", 2, "na żywo", True), ("diar_lokal", "Kolonia", 2, "po godzinie", True),
    ("kontekst", "Kolonia", 3, "na żywo", True), ("glosoteka", "Kolonia", 3, "po godzinie", True),
    ("sprawdzenie", "Kolonia", 4, "po godzinie", True),
    ("live_chmura", "Chmura", 1, "na żywo", True), ("batch_chmura", "Chmura", 1, "po godzinie", True),
    ("diar_chmura", "Chmura", 2, "po godzinie", True), ("przedstawienia", "Chmura", 3, "po godzinie", True),
    ("wydawca", "Redakcja", 3, "oba", False), ("weryfikacja", "Redakcja", 4, "oba", False),
    ("szkic_wp", "Redakcja", 5, "oba", True), ("odcinek", "Redakcja", 5, "oba", True), ("paczka", "Redakcja", 5, "oba", True),
]

ZDARZENIA = [
    (2, "Awaria prądu w serwerowni", "Kolonia ma w tej turze 2 akcje mniej."),
    (3, "Poufny gość", "Połóż „poufne” na najwcześniejszej godzinie lądu w kolumnie na żywo. Chmura nie pracuje na tym heksie do końca gry."),
    (4, "Dżingle udają mowę", "Połóż „mgła” na najwcześniejszej godzinie lądu bez mgły w kolumnie na żywo."),
    (5, "Zerwane łącze z chmurą", "Chmura nie ma w tej turze żadnej akcji."),
    (6, "Gość bez przedstawienia", "−1 do wszystkich rzutów na Kto w tej turze."),
    (7, "Zwykły dzień", "Bez zmian."),
    (8, "Redaktor dyżurny", "Redakcja ma w tej turze 1 akcję więcej (przy 4 osobach — Redaktor)."),
    (9, "Nowy głos w Głosotece", "+1 do wszystkich rzutów na Kto w tej turze."),
    (10, "Chmura drożeje", "Budżet −1."),
    (11, "Kolonia nadrabia", "Kolonia ma w tej turze 2 akcje więcej."),
    (12, "Grant na dostępność", "Budżet +2."),
]


def szansa(sila, mod=0):
    """Szansa sukcesu k6 + siła + mod ≥ 7, gdzie 1 zawsze przegrywa, a 6 zawsze wygrywa."""
    return sum(1 for w in range(1, 7) if w != 1 and (w == 6 or w + sila + mod >= 7)) / 6


def potrzeba(sila):
    return max(2, 7 - sila)


def zet(zid, a=14.0):
    return '<svg viewBox="0 0 %.1f %.1f" style="width:%.1fmm;height:%.1fmm;flex:none">%s</svg>' % (a, a, a, a, PG.zeton_lub_znacznik(0, 0, a, zid, spad=True))


def tab_akcji(male=False, karta=False):
    wiersze = []
    for zid, rola, etap, okno, rzut in AKCJE:
        z = Z[zid]
        wynik = ("%d+ (%d%%)" % (potrzeba(z["sila"]), round(100 * szansa(z["sila"])))) if rzut else "bez rzutu"
        if karta:
            wiersze.append('<tr><td class="ik">%s</td><td><b>%s</b></td><td>%d · %s</td><td>%s</td><td class="c">%d</td><td class="c">%s</td></tr>' % (
                zet(zid, 6.5), escape(z["skrot"]), etap, ETAPY[etap], {"po godzinie": "po godz."}.get(okno, okno), z["sila"], wynik))
            continue
        wiersze.append('<tr><td class="ik">%s</td><td><b>%s</b>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="c">%d</td><td class="c">%s</td></tr>' % (
            zet(zid, 9.0 if male else 11.0), escape(z["skrot"]), "" if male else '<span class="o">' + escape(z["nazwa"]) + '</span>',
            rola, "%d · %s" % (etap, ETAPY[etap]), okno, z["sila"], wynik))
    if karta:
        return ('<table class="tab akc"><tr><th></th><th>Żeton</th><th>Etap</th><th>Okno</th><th class="c">Siła</th><th class="c">k6</th></tr>%s</table>' % "".join(wiersze))
    return ('<table class="tab akc"><tr><th></th><th>Żeton</th><th>Rola</th><th>Etap</th><th>Okno</th><th class="c">Siła</th><th class="c">Potrzeba na k6</th></tr>%s</table>'
            % "".join(wiersze))


def tab_zdarzen():
    return '<table class="tab zd"><tr><th class="c">2k6</th><th>Zdarzenie</th><th>Skutek</th></tr>%s</table>' % "".join(
        '<tr><td class="n">%d</td><td><b>%s</b></td><td>%s</td></tr>' % (w, escape(n), escape(s)) for w, n, s in ZDARZENIA)


def tab_punktow():
    return ('<table class="tab pkt"><tr><th>Etap na heksie</th><th class="c">●</th><th class="c">●●</th><th class="c">●●●</th></tr>%s'
            '<tr><td>konflikt „!” na heksie</td><td class="c" colspan="3">liczy się jak Głosy</td></tr></table>') % "".join(
        '<tr><td>%d · %s</td><td class="c">%d</td><td class="c">%d</td><td class="c">%d</td></tr>' % (e, ETAPY[e], PKT[e], 2 * PKT[e], 3 * PKT[e]) for e in range(1, 6))


def tab_ocen():
    return ('<table class="tab"><tr><th>Scenariusz</th><th class="c">%s</th><th class="c">%s</th><th class="c">%s</th></tr>%s</table>' % (
        PG.OCENY[1], PG.OCENY[2], PG.OCENY[3],
        "".join('<tr><td><b>%d · %s</b></td><td class="c">%d+</td><td class="c">%d+</td><td class="c">%d+</td></tr>' % (sc["nr"], escape(sc["nazwa"]), *sc["progi"])
                for sc in PG.SCENARIUSZE)))


def tab_szans():
    return ('<table class="tab"><tr><th>Siła + modyfikatory</th>%s</tr><tr><td>Potrzeba na k6</td>%s</tr><tr><td>Szansa</td>%s</tr></table>' % (
        "".join('<th class="c">%d</th>' % s for s in range(1, 7)),
        "".join('<td class="c">%d+</td>' % potrzeba(s) for s in range(1, 7)),
        "".join('<td class="c">%d%%</td>' % round(100 * szansa(s)) for s in range(1, 7))))


RAMKA_SKROT = ('<div class="ramka"><b>W skrócie</b>1–4 osoby grają razem przeciw czasowi. 7 tur = 7 dni tygodnia. W każdej turze antena nadaje nowy dzień, '
               'a wy rzucacie kością, by opracować jego godziny: Słowa → Głosy → Kto → Sprawdzone → Wyjście. Po niedzieli liczycie punkty. 30–45 minut.</div>')

STR = [
    # 1 okładka
    ('okl', '<div class="logo">%(LOGO)s</div><h1 class="t1">HALUCYNACJE</h1><p class="t2">Świat anteny</p><p class="t3">zasady gry · wersja ' + WERSJA + '</p>'
     '<div class="mapa"></div><p class="t4">Kooperacyjna gra na planszy z heksów: każdy heks to godzina radia, a teren rośnie z tego, ile w niej słowa. '
     'Zespół redakcji ma tydzień, żeby z surowej anteny zrobić sprawdzoną wiedzę.</p>'
     '<p class="t5">1–4 osoby · 30–45 minut · od 16 lat · 2 kości k6 · gra.l00p.ai</p>'),
    # 2 o grze
    ('', '<h2>1 · O grze</h2><p class="lead">Gracie wspólnie jako redakcja radia. Przeciwnikiem jest czas: antena nadaje dzień po dniu, '
     'a materiał sprzed dwóch dni trafia do archiwum i nie da się go już opracować.</p>' + RAMKA_SKROT +
     '<h3>1.1 Cel</h3><p>Zdobyć jak najwięcej punktów za opracowane godziny. Wynik porównujecie z progami scenariusza (12.3): '
     'od „Kolegium przyjmuje” do „Wzorowej redakcji”. Wszyscy wygrywają albo przegrywają razem.</p>'
     '<h3>1.2 Liczba osób i role</h3><table class="tab"><tr><th>Osoby</th><th>Kto czym kieruje</th></tr>'
     '<tr><td class="n">1</td><td>jedna osoba prowadzi wszystkie trzy role (wariant solo)</td></tr>'
     '<tr><td class="n">2</td><td>A: Maszyny (Kolonia + Chmura) · B: Redakcja</td></tr>'
     '<tr><td class="n">3</td><td>Kolonia · Chmura · Redakcja — <b>najlepszy skład</b></td></tr>'
     '<tr><td class="n">4</td><td>Kolonia · Chmura · Redaktor · Wydawca (Redakcja dzieli się na dwie ekipy, 10.4)</td></tr></table>'
     '<p class="drob">Rozmawiacie o każdym ruchu, ale ostatnie słowo ma osoba prowadząca daną rolę.</p>'),
    # 3 elementy
    ('', '<h2>2 · Elementy gry</h2><ul class="lista"><li><b>Plansza scenariusza</b> — A4 w skali 1:1 (7 dni × 8 godzin); albo duża plansza A0 z ramkami scenariuszy.</li>'
     '<li><b>Arkusz 108 elementów</b> po 20 mm: 84 żetony etapów i 24 znaczniki (2.2).</li>'
     '<li><b>Karta pomocy</b> z torem tur i torem budżetu.</li><li><b>2 kości sześciościenne (k6)</b> — własne.</li>'
     '<li>Nożyczki, klej w sztyfcie i karton po pizzy na żetony.</li></ul>'
     '<h3>2.1 Żeton</h3><div class="rz3">%(Z1)s%(Z2)s%(Z3)s</div><ul class="lista"><li><b>Kolor</b> = rola: zielony Kolonia, niebieski Chmura, złoty i fioletowy Redakcja.</li>'
     '<li><b>Ikona w ramce</b> = rodzaj pracy; ramka przerywana = chmura.</li><li><b>Liczba w lewym rogu</b> = siła do rzutu (6.1).</li>'
     '<li><b>Znak w prawym rogu</b> = okno: dron — tylko na żywo, zegar — po godzinie, postać — człowiek (oba okna).</li></ul>'
     '<h3>2.2 Znaczniki</h3><div class="rz3">%(M1)s%(M2)s%(M3)s%(M4)s%(M5)s%(M6)s</div>'
     '<p class="drob">Konflikt ×6 · mgła ×3 · mgła rozwiana ×8 · poufne ×3 · ekipy Redaktora i Wydawcy · tura · budżet. Pula jest limitem: gdy żetonów danego rodzaju zabraknie, nie można ich użyć.</p>'),
    # 4 plansza i teren
    ('', '<h2>3 · Plansza i teren</h2><p class="lead">Kolumna = dzień (Pn → Nd). Heks = jedna godzina. Na heksie: godzina, kropki wartości, osada, '
     'czasem mgła i przedział „słowo X–Y%%”.</p><div class="legteren"></div>'
     '<table class="tab"><tr><th>Teren</th><th>Dolna liczba „słowo”</th><th class="c">Wartość W</th><th>Uwagi</th></tr>'
     '<tr><td class="sw morze"></td><td>poniżej 32,53%% (muzyka)</td><td class="c">—</td><td>nie opracowuje się; ekipa płynie za 2 punkty ruchu</td></tr>'
     '<tr><td class="sw plaza"></td><td>33–59%% · łąka</td><td class="c">●</td><td></td></tr>'
     '<tr><td class="sw pola"></td><td>60–79%% · pole</td><td class="c">●●</td><td></td></tr>'
     '<tr><td class="sw las"></td><td>80%% i więcej · wzgórza</td><td class="c">●●●</td><td></td></tr>'
     '<tr><td class="sw perg"></td><td>brak pomiaru · ziemia nieznana</td><td class="c">—</td><td>nieprzejezdna</td></tr></table>'
     '<h3>Jak czytać heks</h3><div class="rys">%(HEKS)s</div>' + 
     '<h3>3.1 Osady i mgła</h3><ul class="lista"><li><b>Osada 1–3 domy</b> = ile głosów w godzinie: 1–3 / 4–6 / 7 i więcej. '
     'Utrudnia rzuty maszyn na Głosy i Kto: 1 dom 0, 2 domy −1, 3 domy −2.</li>'
     '<li><b>Mgła</b> (chmurka) = dwie metody pomiaru różnią się o ponad 5 punktów. −1 do rzutów maszyn na Słowa, Głosy i Sprawdzone, '
     'dopóki na heksie nie leży znacznik „mgła rozwiana”.</li></ul><p class="drob">Linia brzegu leży na progu koncesji Radia Wnet: 32,53%% słowa.</p>'),
    # 5 przygotowanie
    ('', '<h2>4 · Przygotowanie</h2><ol class="lista big"><li>Wybierzcie scenariusz (13) i rozłóżcie jego planszę.</li>'
     '<li>Rozdzielcie role według liczby osób (1.2). Każda rola bierze swoje żetony: zielone Kolonia, niebieskie Chmura, złote i fioletowe Redakcja.</li>'
     '<li>Połóż znacznik <b>tury</b> na polu „Pn” toru tur, a znacznik <b>budżetu</b> na 10 (przy 4 osobach na 8).</li>'
     '<li>Ekipę Redakcji (przy 4 osobach obie) postaw na dowolnym heksie lądu w kolumnie Pn.</li>'
     '<li>Znaczniki (konflikt, mgła, poufne, rozwiana) połóż obok planszy. Przygotujcie 2 kości.</li></ol>'
     '<div class="ramka"><b>Pierwsza partia</b>Scenariusz 1 „Poranek Wnet”, 3 osoby. Przeczytajcie na głos rozdziały 5–7 i przykład tury (14) — reszta wyjaśni się w grze.</div>'),
    # 6 sekwencja tury
    ('', '<h2>5 · Sekwencja tury</h2><p class="lead">Tura to jeden dzień. Fazy zawsze w tej kolejności:</p><table class="tab"><tr><td class="n">A</td><td><b>Antena.</b> '
     'Przesuń znacznik tury na kolejny dzień. Rzuć 2k6 i rozpatrz zdarzenie (11).</td></tr><tr><td class="n">B</td><td><b>Kolonia</b> — 4 akcje.</td></tr>'
     '<tr><td class="n">C</td><td><b>Chmura</b> — do 3 akcji; każda kosztuje 1 budżetu.</td></tr><tr><td class="n">D</td><td><b>Redakcja</b> — ruch ekipy (do 3 heksów), potem 3 akcje.</td></tr>'
     '<tr><td class="n">E</td><td><b>Archiwum.</b> Kolumna sprzed dwóch dni przechodzi do archiwum. Po turze Nd gra się kończy (12).</td></tr></table>'
     '<h3>5.1 Okno czasu</h3><table class="tab"><tr><th>Kolumna</th><th>Stan</th><th>Co wolno</th></tr>'
     '<tr><td>dzień tury</td><td><b>na żywo</b></td><td>żetony z dronem; Redakcja</td></tr><tr><td>dwa poprzednie dni</td><td><b>po godzinie</b></td><td>żetony z zegarem; Redakcja</td></tr>'
     '<tr><td>starsze</td><td><b>archiwum</b></td><td>nic — żetony zostają i liczą się na koniec</td></tr><tr><td>przyszłe</td><td>jeszcze nie nadane</td><td>nic</td></tr></table>'
     '<p class="drob">Każdy dzień ma więc trzy tury: raz na żywo i dwa razy po godzinie. Akcje niewykorzystane w fazie przepadają.</p>'),
    # 7 akcje i rzut
    ('', '<h2>6 · Akcje i rzut</h2><p class="lead">Akcja = wybierz heks w oknie czasu, żeton swojej roli o jeden etap wyższy niż leżący na heksie, i rzuć k6.</p>'
     '<div class="ramka"><b>6.1 Rzut</b>k6 + siła żetonu + modyfikatory ≥ 7 → sukces. Wynik <em>1</em> zawsze przegrywa, wynik <em>6</em> zawsze wygrywa.</div>' + tab_szans() +
     '<h3>6.2 Modyfikatory</h3><table class="tab"><tr><td class="n">−1</td><td>mgła na heksie (maszyny: Słowa, Głosy, Sprawdzone)</td></tr>'
     '<tr><td class="n">−1/−2</td><td>osada 2/3 domy (maszyny: Głosy, Kto)</td></tr><tr><td class="n">+1</td><td><b>ten sam program</b>: Kto, jeśli heks tuż wyżej lub niżej w tej samej kolumnie ma już Kto albo wyższy etap</td></tr>'
     '<tr><td class="n">±1/2</td><td>zdarzenie tury (11)</td></tr></table>'
     '<h3>6.3 Skutek</h3><ul class="lista"><li><b>Sukces:</b> połóż żeton na heksie, a niższy zdejmij z powrotem do puli. Na heksie leży zawsze jeden żeton — najwyższy etap.</li>'
     '<li><b>Porażka:</b> akcja przepada, żeton wraca do puli.</li><li><b>Wynik 1 przy Kto:</b> dodatkowo połóż „!” (konflikt, 10.2).</li></ul>'),
    # 8 linie zaopatrzenia
    ('', '<h2>7 · Linie zaopatrzenia</h2><p class="lead">Etapy idą zawsze po kolei. Żeton można położyć tylko na heksie, który ma już poprzedni etap.</p>'
     '<ol class="lista big"><li><b>Słowa</b> — transkrypcja godziny. Wymaga tylko, by heks był w oknie czasu.</li>'
     '<li><b>Głosy</b> — podział na mówców. Wymaga Słów.</li><li><b>Kto</b> — nazwiska mówców. Wymaga Głosów i braku „!”.</li>'
     '<li><b>Sprawdzone</b> — tekst porównany zdanie po zdaniu z nagraniem. Wymaga Kto i braku „!”.</li>'
     '<li><b>Wyjście</b> — szkic na wnet.fm (WP), odcinek podcastu (POD) albo paczka licencji SI (PAK). Wymaga Sprawdzonych. Kładzie je <b>wyłącznie Redakcja</b>.</li></ol>'
     '<div class="ramka"><b>Dlaczego tak?</b>Dokładnie tak pracuje Szpieg+: bez czasu każdego słowa nie przypniesz mówcy, bez mówców nie ma nazwisk, '
     'a nic nie wychodzi na zewnątrz bez człowieka.</div><p class="drob">Etapu nie można pominąć ani cofnąć. Kilka akcji w jednej turze może trafić w ten sam heks.</p>'),
    # 9 tabela żetonów
    ('', '<h2>8 · Tabela żetonów</h2>' + tab_akcji(True) +
     '<p class="drob">„Na żywo” = tylko kolumna tury; „po godzinie” = dwie poprzednie; „oba” = obie. Pozostałe żetony z katalogu Szpiega+ nie biorą udziału w grze podstawowej.</p>'),
    # 10 maszyny
    ('', '<h2>9 · Maszyny: Kolonia i Chmura</h2><h3>9.1 Kolonia (zielone)</h3><p>Lokalne modele na serwerze redakcji. 4 akcje w turze, za darmo. '
     'Jako jedyna maszyna ma Sprawdzone (SPR) i dodatkową akcję:</p><div class="ramka"><b>Rozwiej mgłę (SMD)</b>Po godzinie, na heksie z mgłą: k6 + 4 ≥ 7 → połóż „mgła rozwiana”. Mgła nie odejmuje wtedy punktu.</div>'
     '<h3>9.2 Chmura (niebieskie)</h3><p>Płatne modele zewnętrzne: do 3 akcji w turze, <b>każda kosztuje 1 budżetu</b> — także nieudana. '
     'Budżet startuje na 10 (4 osoby: 8) i nie odnawia się. Przy budżecie 0 Chmura nie działa.</p>'
     '<ul class="lista"><li>Chmura nie ma żetonów Sprawdzonych ani Wyjścia.</li><li><b>Poufne:</b> na heksie ze znacznikiem „poufne” Chmura nie pracuje (czerwona linia: poufne źródła tylko lokalnie).</li>'
     '<li>C·LIVE ma siłę 3, L·LIVE tylko 2 — na żywo chmura jest pewniejsza, ale kosztuje.</li></ul>'),
    # 11 redakcja
    ('', '<h2>10 · Redakcja</h2><p class="lead">Ludzie pracują tam, gdzie są. Redakcję reprezentuje znacznik ekipy na planszy.</p>'
     '<h3>10.1 Ruch i zasięg</h3><ul class="lista"><li>Na początku fazy D ekipa przesuwa się o <b>do 3 heksów</b>. Heks morza kosztuje 2, ziemia nieznana jest nieprzejezdna.</li>'
     '<li>Akcje Redakcji działają na heksie ekipy i 6 sąsiednich, o ile są w oknie czasu.</li></ul>'
     '<h3>10.2 Akcje (3 w turze)</h3><table class="tab"><tr><td class="n">WYD✓</td><td><b>Kto</b> bez rzutu — osady nie przeszkadzają. Albo <b>rozstrzygnij konflikt</b>: zdejmij „!” i połóż WYD✓.</td></tr>'
     '<tr><td class="n">RED✓</td><td><b>Sprawdzone</b> bez rzutu (heks z Kto).</td></tr><tr><td class="n">ucho</td><td><b>Posłuchaj</b>: połóż „mgła rozwiana” bez rzutu.</td></tr>'
     '<tr><td class="n">WP·POD·PAK</td><td><b>Wyjście</b>: k6 + 5 ≥ 7 (2+). Tylko na heksie ze Sprawdzonymi.</td></tr></table>'
     '<h3>10.3 Konflikt</h3><p>„!” blokuje heks: nikt nie położy Kto ani wyższego etapu, dopóki Redakcja go nie rozstrzygnie.</p>'
     '<h3>10.4 Przy 4 osobach</h3><p><b>Redaktor</b> (złota ekipa): RED✓ i ucho. <b>Wydawca</b> (fioletowa ekipa): WYD✓ i Wyjście. Każdy ma własny ruch i 2 akcje. Budżet startuje na 8.</p>'),
    # 12 zdarzenia
    ('', '<h2>11 · Zdarzenia anteny</h2><p class="lead">Na początku każdej tury rzuć 2k6. Skutek działa do końca tej tury, chyba że napisano inaczej.</p>' + tab_zdarzen()),
    # 13 koniec i punktacja
    ('', '<h2>12 · Koniec gry i punktacja</h2><p class="lead">Gra kończy się po fazie E tury Nd. Każdy heks z żetonem daje punkty: wartość etapu × kropki W.</p>' + tab_punktow() +
     '<h3>12.1 Liczenie</h3><p>Idźcie kolumna po kolumnie i zapiszcie sumę. Morze i ziemia nieznana nie dają punktów. Nieużyty budżet nie daje punktów.</p>'
     '<h3>12.2 Wynik</h3>' + tab_ocen() +
     '<p class="drob">Progi pochodzą z 800 symulowanych partii na scenariusz: „Kolegium przyjmuje” osiąga 9 na 10 zespołów grających rozsądnie, „Wzorową redakcję” — 1 na 10.</p>'),
    # 14 scenariusze
    ('', '<h2>13 · Scenariusze</h2>' + "".join('<h3>%d · %s</h3><p>%s <span class="drob">Plansza: %s, godziny %02d–%02d.</span></p>' % (
        sc["nr"], escape(sc["nazwa"]), escape(sc["opis"]), escape(PG.PR.PROFILE[sc["profil"]]["nazwa"]), sc["h0"], sc["h0"] + 7) for sc in PG.SCENARIUSZE) +
     '<div class="ramka"><b>Plansze A0: trzy rozgłośnie</b>Klasyczne radio (idealna ramówka Radia Wnet), radio muzyczne i radio informacyjne — każde na sezon 4 tygodni × 24 godziny. '
     'Teren wynika z ramówki, nie z nagrań. Ramki na planszy wyznaczają scenariusze; każdy inny wycinek 7 dni × 8 godzin to nowy scenariusz (progi: jak w scenariuszu tej samej rozgłośni).</div>'),
    # 15 przykład tury
    ('', '<h2>14 · Przykład tury</h2><p class="lead">Scenariusz 1, tura Śr. Na żywo: Śr. Po godzinie: Pn i Wt. Budżet 8.</p><ol class="lista">'
     '<li><b>Antena:</b> 2k6 = 9 — „Nowy głos w Głosotece”: +1 do Kto w tej turze.</li>'
     '<li><b>Kolonia</b>, akcja 1: L·GODZ na Wt 08:00 (●●●, mgła). Rzut 3: 3 + 4 − 1 = 6 — porażka. Akcja 2: ten sam heks, rzut 5: 5 + 4 − 1 = 8 — Słowa leżą.</li>'
     '<li>Akcja 3: GŁO na Pn 09:00, gdzie leżą Głosy (●●, 2 domy). 4 + 4 − 1 (domy) + 1 (zdarzenie) = 8 — Kto. Akcja 4: L·LIVE na Śr 07:00 — rzut 6, zawsze sukces.</li>'
     '<li><b>Chmura</b> (budżet 8 → 6): C·DIAR na Wt 08:00 — rzut 4: 4 + 4 − 1 = 7 — Głosy. PRZ na Pn 10:00 (3 domy): rzut 1 — porażka i konflikt „!”.</li>'
     '<li><b>Redakcja</b> idzie 2 heksy na Pn 10:00: WYD✓ rozstrzyga konflikt (Kto), RED✓ na Pn 09:00 (Sprawdzone), WP na Pn 09:00 — rzut 2: 2 + 5 = 7 — Wyjście!</li>'
     '<li><b>Archiwum:</b> Pn przechodzi do archiwum. Jego żetony zostają na planszy i liczą się na koniec, ale w turze Cz nikt już tam nie pracuje.</li></ol>'
     '<p class="drob">Pn 09:00 (●●) z Wyjściem daje 8 × 2 = 16 punktów na koniec gry.</p>'),
    # 16 czerwone linie, warianty, słowniczek
    ('', '<h2>15 · Warianty i słowniczek</h2><h3>15.1 Czerwone linie w grze</h3><ul class="lista"><li>Wyjście kładzie tylko Redakcja — nic nie publikuje się samo.</li>'
     '<li>Chmura nie pracuje na poufnych godzinach.</li><li>Nazwisko (Kto) z maszyny może się mylić — stąd konflikty i Wydawca.</li></ul>'
     '<h3>15.2 Warianty</h3><ul class="lista"><li><b>Solo:</b> jak 3 osoby, jedna osoba prowadzi wszystko.</li>'
     '<li><b>Trudniej:</b> budżet 6 albo bez rzutu na zdarzenia 8, 11 i 12 (traktuj jak 7).</li><li><b>Kampania A0:</b> 4 kolejne tygodnie tej samej rozgłośni, budżet przechodzi na następny tydzień.</li></ul>'
     '<dl class="slow"><dt>Diaryzacja</dt><dd>podział nagrania na głosy („Mówca A, B…”).</dd><dt>Głosoteka</dt><dd>bank barw głosu redakcji, rozpoznaje lokalnie.</dd>'
     '<dt>SMD</dt><dd>rozdział mowy i muzyki.</dd><dt>Koncesja</dt><dd>co najmniej 32,53%% słowa w tygodniu, 06–23.</dd></dl>'
     '<div class="kolofon"><b>HALUCYNACJE · Świat anteny</b> — zasady ' + WERSJA + ' · Radio Wnet · Szpieg+ · gra.l00p.ai<br>Plansze generowane proceduralnie z ramówek rozgłośni. '
     'Zasady sprawdzone symulacją; czekamy na uwagi z partii. Przygotowane z pomocą AI (Claude, Anthropic) dla Lecha R. Rusteckiego. '
     'Plakat A0 = 16 kart A4: tnij po szarych liniach i zszyj według numerów.</div>'),
]


def heks_opis():
    """Jeden heks w skali 2:1 z objaśnieniami — ta sama nakładka co na planszy."""
    g = {"slowo": {"min": 74.2, "max": 79.4, "rozrzut_pp": 5.2, "zgodne": False}, "mowcy": 5}
    s = PG.nakladka({(0, 0): g}, [""], 7, 0, 0).replace('<text x="%.2f" y="-1.50"' % PG.SA.srodek(0, 0)[0], '<text x="0" y="-99"')
    cx, cy = PG.SA.srodek(0, 0)
    opisy = [((5.5, -8.6), -10.5, "godzina — wiersz planszy"), ((3.2, -5.0), -5.3, "wartość W: ●● = pole (60–79%)"),
             ((8.6, 0.8), 0.0, "chmurka = mgła: metody różnią się o ponad 5 pp"), ((3.0, 2.2), 5.3, "osada: 2 domy = 4–6 głosów"),
             ((7.0, 9.4), 10.5, "słowo: przedział dwóch metod; teren według dolnej liczby")]
    for (fx, fy), ly, t in opisy:
        s += '<polyline points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="none" stroke="#274F5C" stroke-width=".22"/>' % (cx + fx, cy + fy, cx + 17, cy + ly, cx + 19, cy + ly)
        s += '<text x="%.1f" y="%.1f" font-size="2.3" fill="#0A1318">%s</text>' % (cx + 19.6, cy + ly + .8, escape(t))
    return ('<svg viewBox="%.1f %.1f 98 30" style="width:100%%;height:auto" font-family="Exo 2,Lato,sans-serif">'
            '<polygon points="%s" fill="#AACE76"/>%s</svg>') % (cx - 15, cy - 15, " ".join("%.2f,%.2f" % q for q in PG.SA.wierzcholki(cx, cy)), s)


def wypelnij(tresc, logo=""):
    """Podstawia %(KLUCZ)s bez formatowania % (tabele zawierają zwykłe znaki %); „%%” w tekstach = „%”."""
    wart = {"LOGO": logo, "Z1": zet("batch_lokal", 20), "Z2": zet("live_chmura", 20), "Z3": zet("weryfikacja", 20),
            "HEKS": heks_opis(), "M1": zet("konflikt", 14), "M2": zet("mgla", 14), "M3": zet("rozwiana", 14), "M4": zet("poufne", 14), "M5": zet("ekipa_r", 14), "M6": zet("budzet", 14)}
    for k, v in wart.items():
        tresc = tresc.replace("%(" + k + ")s", v)
    return tresc.replace("%%", "%")


# ---------------------------------------------------------------- tory i karta pomocy
def tory_svg(x, y, _skala=None):
    a = 22.0
    h = '<text x="%.1f" y="%.1f" font-size="3.4" font-weight="800" fill="#274F5C">Tor tur</text>' % (x, y - 2)
    for k, d in enumerate(PG.DNI):
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#FBF8F2" stroke="#274F5C" stroke-width=".5"/>' % (x + k * a, y, a, a)
        h += '<text x="%.1f" y="%.1f" font-size="4" font-weight="800" text-anchor="middle" fill="#274F5C" opacity=".35">%s</text>' % (x + k * a + a / 2, y + a * .6, d)
    y2 = y + a + 9
    h += '<text x="%.1f" y="%.1f" font-size="3.4" font-weight="800" fill="#274F5C">Tor budżetu Chmury</text>' % (x, y2 - 2)
    for k in range(13):
        r, c = divmod(k, 7)
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#EEF4F6" stroke="#2F7C95" stroke-width=".5"/>' % (x + c * a, y2 + r * a, a, a)
        h += '<text x="%.1f" y="%.1f" font-size="6" font-weight="800" text-anchor="middle" fill="#2F7C95" opacity=".35">%d</text>' % (x + c * a + a / 2, y2 + r * a + a * .64, k)
    return h


KP_CSS = """.kp{position:absolute;left:12mm;top:10mm;width:186mm;font-family:Lato,sans-serif;color:#0A1318;font-size:7.4pt;line-height:1.3}
.kp h1{font:800 15pt 'Exo 2';color:#274F5C;margin:0 0 1mm}.kp h2{font:800 9pt 'Exo 2';color:#274F5C;margin:2.2mm 0 .8mm;text-transform:uppercase;letter-spacing:.04em}
.kp .k2{display:flex;gap:5mm}.kp .k2>div{flex:1}.kp p{margin:0 0 1mm}
.kp .tab{width:100%;border-collapse:collapse}.kp .tab td,.kp .tab th{padding:.5mm 1mm;border-bottom:.2mm dotted #C8D3D7;vertical-align:middle;text-align:left}
.kp .tab th{font:800 6.8pt 'Exo 2';color:#3F5A66}.kp .c{text-align:center!important}.kp .n{font:800 8pt 'Exo 2';color:#274F5C;text-align:center;width:9mm}
.kp .ik{width:7mm}.kp .akc td{padding:.25mm 1mm}.kp .ik svg{display:block}.kp .o{display:block;font-size:6pt;color:#56717C}"""


def karta_pomocy_html(tylko_tresc=False):
    sek = ('<table class="tab"><tr><td class="n">A</td><td>Antena: tura +1, rzut 2k6 → zdarzenie</td></tr><tr><td class="n">B</td><td>Kolonia: 4 akcje</td></tr>'
           '<tr><td class="n">C</td><td>Chmura: do 3 akcji, każda −1 budżetu</td></tr><tr><td class="n">D</td><td>Redakcja: ruch 3, potem 3 akcje (zasięg 1)</td></tr>'
           '<tr><td class="n">E</td><td>Archiwum: kolumna sprzed 2 dni zamknięta</td></tr></table>')
    mod = ('<p><b>k6 + siła + mod ≥ 7</b> · 1 = porażka · 6 = sukces · 1 przy Kto → „!”</p><table class="tab"><tr><td class="n">−1</td><td>mgła: maszyny, Słowa/Głosy/Sprawdzone</td></tr>'
           '<tr><td class="n">−1/−2</td><td>2/3 domy: maszyny, Głosy/Kto</td></tr><tr><td class="n">+1</td><td>ten sam program: Kto, sąsiad w kolumnie ma Kto+</td></tr></table>')
    kr = {2: "Kolonia −2 akcje", 3: "„poufne” na 1. godzinie lądu na żywo", 4: "„mgła” na 1. godzinie lądu na żywo bez mgły", 5: "Chmura 0 akcji",
          6: "Kto −1 w tej turze", 7: "bez zmian", 8: "Redakcja +1 akcja", 9: "Kto +1 w tej turze", 10: "budżet −1", 11: "Kolonia +2 akcje", 12: "budżet +2"}
    wz = ['<tr><td class="n">%d</td><td><b>%s</b> — %s</td></tr>' % (w, escape(n), escape(kr[w])) for w, n, _ in ZDARZENIA]
    zd = '<div class="k2"><div><table class="tab">%s</table></div><div><table class="tab">%s</table></div></div>' % ("".join(wz[:6]), "".join(wz[6:]))
    tresc = ('<h1>Karta pomocy · Świat anteny %s</h1><div class="k2"><div><h2>Sekwencja tury</h2>%s<h2>Rzut i modyfikatory</h2>%s<h2>Punkty = etap × W</h2>%s</div>'
             '<div><h2>Żetony i akcje</h2>%s</div></div><h2>Zdarzenia anteny (2k6)</h2>%s') % (WERSJA, sek, mod, tab_punktow(), tab_akcji(karta=True), zd)
    tresc = tresc.replace('style="width:6.5mm;height:6.5mm;flex:none"', 'width="24" height="24"')
    if tylko_tresc:
        return KP_CSS, tresc
    tory = '<svg class="p" viewBox="0 0 210 297" style="pointer-events:none">%s%s</svg>' % (tory_svg(12, 212), PG.SA.linijka(170, 287, 30).replace("sprawdź skalę: ta linijka ma 30 mm · heks 25 mm · żeton 20 mm", ""))
    return '<div class="s"><style>%s</style><div class="kp">%s</div>%s</div>' % (KP_CSS, tresc, tory)
