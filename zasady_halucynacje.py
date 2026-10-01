# -*- coding: utf-8 -*-
"""Zasady HALUCYNACJE 2.0 (Świat anteny) — JEDNO źródło treści: plakat A0 (plakat_a0.py), zeszyt A4 i strona /zasady (wydanie.py),
karta pomocy i plansza torów (plansza_gry.py). Liczby: siły = nadruk żetonów (warstwy/model.json); progi i zdarzenia sprawdzone
symulacją (symulacja_halucynacje.py). Wersja 1.0 (bez halucynacji) zostaje w zasady_gry.py."""
from html import escape

import plansza_gry as PG
import zasady_gry as ZG

WERSJA = "2.0"
Z, ETAPY, PKT = ZG.Z, ZG.ETAPY, ZG.PKT
zet, szansa, potrzeba, tab_akcji, tab_szans = ZG.zet, ZG.szansa, ZG.potrzeba, ZG.tab_akcji, ZG.tab_szans

ZDARZENIA = [
    (2, "Awaria prądu w serwerowni", "Kolonia ma w tej turze 2 akcje mniej."),
    (3, "Poufny gość", "Połóż „poufne” na najwcześniejszej godzinie lądu w kolumnie na żywo. Chmura nie pracuje na tym heksie do końca gry."),
    (4, "Dżingle udają mowę", "Połóż „mgła” na najwcześniejszej godzinie lądu bez mgły w kolumnie na żywo."),
    (5, "Zerwane łącze z chmurą", "Chmura nie ma w tej turze żadnej akcji."),
    (6, "Agent dopisał cytat", "Połóż znacznik „cytat” (+2) na heksie w oknie z najwyższym etapem (co najmniej Kto); remis — wyższa wartość W."),
    (7, "Zwykły dzień", "Bez zmian."),
    (8, "Redaktor dyżurny", "Redaktor (albo Redakcja) ma w tej turze 1 akcję więcej."),
    (9, "Pewność siebie", "Każdy gracz kładzie jedną kartę przekonania z ręki na wybrany heks w oknie — bez premii do rzutu."),
    (10, "Chmura drożeje", "Budżet −1."),
    (11, "Kolonia nadrabia", "Kolonia ma w tej turze 2 akcje więcej."),
    (12, "Ostatnia chwila", "Wydawca musi w tej turze opublikować jeden heks ze Sprawdzonymi (bez rzutu na Wyjście, ale z testem prawdy), jeśli jakiś jest w oknie."),
]

SKANDAL = [(0, "Czysto", ""), (1, "Sprostowanie", "−2 pkt za każdy punkt skandalu"), (3, "Ośmieszenie", "dodatkowo −10 pkt"),
           (5, "Zwolnienie", "odwróćcie 1 kartę postaci"), (7, "Drugie zwolnienie", "odwróćcie kolejną"), (9, "Koniec redakcji", "przegrana natychmiast")]


def tab_zdarzen():
    return '<table class="tab zd"><tr><th class="c">2k6</th><th>Zdarzenie</th><th>Skutek</th></tr>%s</table>' % "".join(
        '<tr><td class="n">%d</td><td><b>%s</b></td><td>%s</td></tr>' % (w, escape(n), escape(s)) for w, n, s in ZDARZENIA)


def tab_ryzyka():
    return ('<table class="tab"><tr><th>Składnik ryzyka</th><th class="c">R</th></tr>'
            '<tr><td>podstawa: 4 − Pewność (liczba transkrypcji 1–3)</td><td class="c">3 / 2 / 1</td></tr>'
            '<tr><td>każdy znacznik ASR albo „zły mówca”</td><td class="c">+1</td></tr><tr><td>każdy znacznik „nazwisko” albo „cytat”</td><td class="c">+2</td></tr>'
            '<tr><td>każda zakryta karta przekonania na heksie</td><td class="c">+ jej waga (1–3)</td></tr><tr><td>mgła na heksie</td><td class="c">+1</td></tr>'
            '<tr><td>Sprawdzone przez człowieka (RED✓)</td><td class="c">−1</td></tr></table>')


def tab_testu():
    w = ""
    for r in range(0, 6):
        w += '<tr><td class="c">%d</td><td class="c">%d%%</td><td>%s</td></tr>' % (
            r, round(100 * min(r, 6) / 6), "bezpiecznie" if r == 0 else ("halucynacja przy wyniku %s" % ("1" if r == 1 else "1–%d" % r)))
    return '<table class="tab"><tr><th class="c">Ryzyko R</th><th class="c">Szansa wpadki</th><th>k6 ≤ R</th></tr>%s</table>' % w


def tab_postaci():
    return '<table class="tab"><tr><th>Postać</th><th class="c">Akcje</th><th>Co robi</th></tr>%s</table>' % "".join(
        '<tr><td><b>%s</b><span class="o">%s</span></td><td class="c">%s</td><td>%s</td></tr>' % (escape(n), escape(o), a, escape(c)) for n, o, a, c in [
            ("Opiekun Kolonii", "rdzeń · maszyny", "4", "zielone żetony — lokalne modele, bez kosztu"),
            ("Opiekunka Chmury", "rdzeń · maszyny", "3", "niebieskie żetony — każda akcja −1 budżetu; nigdy na „poufne”"),
            ("Wydawca", "rdzeń · ekipa na mapie", "2", "WYD✓ (Kto bez rzutu, konflikty), Wyjście i test prawdy"),
            ("Redaktor", "rdzeń · ekipa na mapie", "2", "RED✓ (Sprawdzone: zdejmuje znaczniki, odwraca karty), ucho"),
            ("Weryfikatorka", "5. osoba", "1", "bez rzutu, w całym oknie: zdejmij 1 znacznik albo odwróć 1 kartę"),
            ("Reporter", "6. osoba · ekipa", "1", "notatka z terenu = transkrypcja (+1 Pewność); +1 do Kto w zasięgu"),
            ("Realizatorka dźwięku", "7. osoba", "1", "rozwiej mgłę bez rzutu w całym oknie; stale +1 do Słów na żywo"),
            ("Szef redakcji", "8. osoba", "—", "odprawa: +1 akcja dowolnej postaci na turę; raz na grę skandal −1")])


def tab_osob():
    return ('<table class="tab"><tr><th class="c">Osoby</th><th>Kto prowadzi które postacie</th></tr>'
            '<tr><td class="n">1</td><td>wszystkie cztery postacie rdzenia (solo)</td></tr>'
            '<tr><td class="n">2</td><td>A: Kolonia + Chmura · B: Wydawca + Redaktor</td></tr>'
            '<tr><td class="n">3</td><td>Kolonia · Chmura · Wydawca + Redaktor (razem 3 akcje)</td></tr>'
            '<tr><td class="n">4</td><td>cztery postacie rdzenia, po jednej</td></tr>'
            '<tr><td class="n">5–8</td><td>rdzeń + kolejno: Weryfikatorka, Reporter, Realizatorka, Szef</td></tr></table>')


def tab_punktow():
    return ('<table class="tab pkt"><tr><th>Etap na heksie</th><th class="c">●</th><th class="c">●●</th><th class="c">●●●</th></tr>%s'
            '<tr><td>konflikt „!” na heksie</td><td class="c" colspan="3">jak Głosy</td></tr>'
            '<tr><td>halucynacja w eterze (przegrany test)</td><td class="c" colspan="3">0 i skandal</td></tr></table>') % "".join(
        '<tr><td>%d · %s</td><td class="c">%d</td><td class="c">%d</td><td class="c">%d</td></tr>' % (e, ETAPY[e], PKT[e], 2 * PKT[e], 3 * PKT[e]) for e in range(1, 6))


def tab_ocen():
    return ('<table class="tab"><tr><th>Scenariusz (1–4 osoby)</th><th class="c">%s</th><th class="c">%s</th><th class="c">%s</th></tr>%s</table>'
            '<p class="drob">5–6 osób: progi +10%%, 7–8 osób: +15%% (więcej rąk w redakcji).</p>' % (
                PG.OCENY[1], PG.OCENY[2], PG.OCENY[3],
                "".join('<tr><td><b>%d · %s</b></td><td class="c">%d+</td><td class="c">%d+</td><td class="c">%d+</td></tr>' % (sc["nr"], escape(sc["nazwa"]), *sc["progi"])
                        for sc in PG.SCENARIUSZE)))


def tab_skandalu():
    return '<table class="tab"><tr><th class="c">Tor</th><th>Poziom</th><th>Skutek</th></tr>%s</table>' % "".join(
        '<tr><td class="n">%s</td><td><b>%s</b></td><td>%s</td></tr>' % (("%d+" % p) if p else "0", escape(n), escape(s)) for p, n, s in SKANDAL)


PROLOG = ('<p class="lead">Warszawa, 02:14. Antena Radia Wnet nadaje, a redakcja — osiem osób — pracuje z dziesiątkami syntetycznych kolegów: '
          'modelami, które słuchają, zapisują, rozpoznają głosy i piszą szkice.</p>'
          '<p>Codziennie przez redakcję przechodzą tysiące słów. Jedno z nich jest halucynacją: zdanie, którego nikt nie wypowiedział, '
          'zły mówca, zmyślone nazwisko, cytat przypisany nie temu człowiekowi — albo przekonanie, w które uwierzył ktoś z nas. '
          'Jeśli wyjdzie na antenę, redakcja zapłaci: sprostowaniem, śmiesznością, a w końcu posadami.</p>'
          '<div class="ramka"><b>Quest: Żółta Łódź Podwodna</b>Mapa prawdy — cztery prawdziwe tygodnie anteny — pokazuje noce pełne słowa '
          '(średnio 60%%). Idealne radio klasyczne nocą nadaje ocean muzyki (ok. 10%%); plansza 3 pokazuje trzecią drogę: powtórki i program dla Polonii prowadzony przez awatary głosów Wnet, za zgodą i z etykietą AI. O 2:00 w Warszawie w Chicago jest 19:00: kto nas wtedy słucha? '
          'Ekipa Żółtej Łodzi Podwodnej z Kapitanem Krzysztofem szuka nowej ramówki — a gra jest jej poligonem.</div>')

RAMKA_SKROT = ('<div class="ramka"><b>W skrócie</b>1–8 osób gra razem przeciw czasowi i halucynacjom. 7 tur = 7 dni. Każda godzina przechodzi etapy '
               'Słowa → Głosy → Kto → Sprawdzone → Wyjście. Maszyny są szybkie, ale zostawiają znaczniki ryzyka; ludzie są pewni, ale jest ich mało. '
               'Przed publikacją — test prawdy. 30–45 minut.</div>')

STR = [
    # 1 okładka
    ('okl', '<div class="logo">%(LOGO)s</div><h1 class="t1">HALUCYNACJE</h1><p class="t2">Świat anteny</p><p class="t3">zasady gry · wersja ' + WERSJA + '</p>'
     '<div class="mapa"></div><p class="t4">Kooperacyjna gra o redakcji, która pracuje z syntetycznymi kolegami — i nie może wpuścić na antenę żadnej halucynacji.</p>'
     '<p class="t5">1–8 osób · 30–45 minut · od 16 lat · 2 kości k6 · gra.l00p.ai</p>'),
    # 2 prolog
    ('', '<h2>Prolog</h2>' + PROLOG + RAMKA_SKROT),
    # 3 osoby i postacie
    ('', '<h2>1 · Redakcja: osoby i postacie</h2><p class="lead">Każdy gracz prowadzi co najmniej jedną postać. Wszyscy wygrywają albo przegrywają razem.</p>'
     + tab_osob() + '<h3>1.1 Postacie</h3>' + tab_postaci() +
     '<p class="drob">Rozmawiacie o każdym ruchu, ale ostatnie słowo ma osoba prowadząca daną postać.</p>'),
    # 4 elementy
    ('', '<h2>2 · Elementy gry</h2><ul class="lista"><li><b>Plansza scenariusza</b> A4 1:1 (7 dni × 8 godzin) albo plansza A0; <b>mapa prawdy</b> A0.</li>'
     '<li><b>Arkusz etapów</b> (108 żetonów) i <b>arkusz znaczników</b> (81) — 20 mm, na karton po pizzy.</li>'
     '<li><b>72 karty przekonań</b> i <b>8 kart postaci</b> — 57 × 89 mm, druk dwustronny na papierze fotograficznym.</li>'
     '<li><b>Karta pomocy</b> i <b>plansza torów</b> (tura, budżet, skandal).</li><li><b>2 kości k6</b> — własne.</li></ul>'
     '<h3>2.1 Znaczniki ryzyka</h3><div class="rz3">%(R1)s%(R2)s%(R3)s%(R4)s</div>'
     '<p>Liczba w kółku to <b>waga</b> w teście prawdy. ASR — słowa „usłyszane” w muzyce; zły mówca — zdanie przypięte nie tej osobie; '
     'nazwisko — zgadnięta tożsamość; cytat — zdanie dopisane przez agenta.</p><h3>2.2 Inne znaczniki</h3><div class="rz3">%(M1)s%(M2)s%(M3)s%(M4)s%(M7)s%(M8)s</div>'),
    # 5 plansza i teren
    ('', '<h2>3 · Plansza i teren</h2><p class="lead">Kolumna = dzień, heks = godzina. Wysokość terenu = ile w godzinie słowa.</p><div class="legteren"></div>'
     '<table class="tab"><tr><th>Teren</th><th>Dolna liczba „słowo”</th><th class="c">W</th><th>Uwagi</th></tr>'
     '<tr><td class="sw morze"></td><td>poniżej 32,53%% (muzyka)</td><td class="c">—</td><td>nie opracowuje się; ekipa płynie za 2 ruchu</td></tr>'
     '<tr><td class="sw plaza"></td><td>33–59%% · łąka</td><td class="c">●</td><td></td></tr><tr><td class="sw pola"></td><td>60–79%% · pole</td><td class="c">●●</td><td></td></tr>'
     '<tr><td class="sw las"></td><td>80%% i więcej · wzgórza</td><td class="c">●●●</td><td></td></tr>'
     '<tr><td class="sw perg"></td><td>brak pomiaru · pod żetonem mgły</td><td class="c">—</td><td>nieprzejezdne</td></tr></table>'
     '<h3>Jak czytać heks</h3><div class="rys">%(HEKS)s</div><p class="drob">Osada 1–3 domy = głosy 1–3 / 4–6 / 7+: −0/−1/−2 do rzutów maszyn na Głosy i Kto. '
     'Mgła: −1 do rzutów maszyn na Słowa, Głosy i Sprawdzone oraz +1 do ryzyka.</p>'),
    # 6 przygotowanie
    ('', '<h2>4 · Przygotowanie</h2><ol class="lista big"><li>Wybierzcie scenariusz (13) i rozłóżcie planszę oraz planszę torów.</li>'
     '<li>Rozdajcie postacie (1). Każdy bierze karty swoich postaci i ich żetony.</li>'
     '<li>Tura: „Pn”. Budżet: 10 (4 osoby i więcej: 8). Skandal: 0.</li>'
     '<li>Ekipy Redaktora, Wydawcy i Reportera stawiacie na dowolnym lądzie w kolumnie Pn.</li>'
     '<li>Potasujcie 72 karty przekonań. Każdy gracz dobiera <b>3</b> i kładzie je przed sobą przekonaniem do góry.</li>'
     '<li>Znaczniki ryzyka i pozostałe — obok planszy. Przygotujcie 2 kości.</li></ol>'
     '<div class="ramka"><b>Pierwsza partia</b>Scenariusz 1 „Poranek Wnet”, 3–4 osoby. Przeczytajcie prolog, rozdziały 5–9 i przykład (15).</div>'),
    # 7 sekwencja
    ('', '<h2>5 · Sekwencja tury</h2><p class="lead">Tura = jeden dzień. Fazy zawsze w tej kolejności:</p><table class="tab">'
     '<tr><td class="n">A</td><td><b>Antena.</b> Tura +1. Rzuć 2k6 — zdarzenie (12). Gracze dobierają karty przekonań do 3.</td></tr>'
     '<tr><td class="n">B</td><td><b>Kolonia</b> — 4 akcje.</td></tr><tr><td class="n">C</td><td><b>Chmura</b> — do 3 akcji, każda −1 budżetu.</td></tr>'
     '<tr><td class="n">D</td><td><b>Ludzie</b> — ekipy ruszają się (do 3 heksów), potem akcje postaci w dowolnej kolejności.</td></tr>'
     '<tr><td class="n">E</td><td><b>Archiwum.</b> Kolumna sprzed dwóch dni zamyka się. Skandal ≥ 5 lub 7 — zwolnienie (11). Po turze Nd — koniec gry.</td></tr></table>'
     '<h3>5.1 Okno czasu</h3><table class="tab"><tr><th>Kolumna</th><th>Stan</th><th>Co wolno</th></tr>'
     '<tr><td>dzień tury</td><td><b>na żywo</b></td><td>żetony z dronem; ludzie</td></tr><tr><td>dwa poprzednie</td><td><b>po godzinie</b></td><td>żetony z zegarem; ludzie</td></tr>'
     '<tr><td>starsze</td><td><b>archiwum</b></td><td>nic — liczą się na koniec</td></tr></table>'),
    # 8 akcje i rzut
    ('', '<h2>6 · Akcje i rzut</h2><p class="lead">Akcja maszyny = wybierz heks w oknie i żeton swojej roli o jeden etap wyżej niż leżący; rzuć k6.</p>'
     '<div class="ramka"><b>6.1 Rzut</b>k6 + siła żetonu + modyfikatory ≥ 7 → sukces. Wynik <em>1</em> zawsze przegrywa, <em>6</em> zawsze wygrywa.</div>' + tab_szans() +
     '<h3>6.2 Modyfikatory</h3><table class="tab"><tr><td class="n">−1</td><td>mgła (maszyny: Słowa, Głosy, Sprawdzone)</td></tr>'
     '<tr><td class="n">−1/−2</td><td>osada 2/3 domy (maszyny: Głosy, Kto)</td></tr><tr><td class="n">+1</td><td>ten sam program: Kto, jeśli sąsiad w kolumnie ma Kto+</td></tr>'
     '<tr><td class="n">+1</td><td>Reporter w zasięgu (Kto) · Realizatorka (Słowa na żywo)</td></tr><tr><td class="n">+waga</td><td>zagrana karta przekonania (10)</td></tr></table>'
     '<h3>6.3 Sukces maszyny zostawia ślad</h3><p>Jeśli maszyna odniosła sukces, a na kości wypadło <b>≤ 5 − Pewność</b> (żeton na żywo: +1), połóż na heksie znacznik ryzyka: '
     'Słowa → ASR, Głosy → zły mówca, Kto → nazwisko. Model był pewny siebie — i mógł się mylić.</p>'),
    # 9 linie zaopatrzenia i pewność
    ('', '<h2>7 · Etapy i Pewność</h2><ol class="lista"><li><b>Słowa</b> — transkrypcja.</li><b>Głosy</b> — wymaga Słów.</li><li><b>Kto</b> — wymaga Głosów, bez „!”.</li>'
     '<li><b>Sprawdzone</b> — wymaga Kto, bez „!”.</li><li><b>Wyjście</b> — WP, POD albo PAK; tylko Wydawca, po teście prawdy (9).</li></ol>'
     '<div class="ramka"><b>7.1 Więcej transkrypcji = mniej halucynacji</b>Na heksie ze Słowami możesz położyć kolejną transkrypcję <em>innego rodzaju</em> '
     '(L·LIVE, L·GODZ, C·LIVE, C·GODZ albo notatka reportera) — zwykły rzut Słów. Transkrypcje leżą pod żetonem etapu; ich liczba to <b>Pewność</b> (1–3). '
     'Każda nowa transkrypcja od razu zdejmuje jeden znacznik ASR (porównanie wersji) i obniża ryzyko.</div>'
     '<table class="tab"><tr><th class="c">Pewność</th><th>Transkrypcje</th><th class="c">WER ok.</th><th class="c">Podstawa ryzyka</th></tr>'
     '<tr><td class="n">1</td><td>jedna</td><td class="c">5–9%%</td><td class="c">3</td></tr><tr><td class="n">2</td><td>dwie różne</td><td class="c">3%%</td><td class="c">2</td></tr>'
     '<tr><td class="n">3</td><td>trzy różne</td><td class="c">2%%</td><td class="c">1</td></tr></table>'),
    # 10 halucynacje i test prawdy
    ('', '<h2>8 · Halucynacje: test prawdy</h2><p class="lead">Kiedy Wydawca kładzie Wyjście (po udanym rzucie 2+), redakcja robi test prawdy.</p>'
     + tab_ryzyka() + '<div class="ramka"><b>8.1 Test</b>Policz ryzyko R. Rzuć k6. Wynik ≤ R — halucynacja idzie w eter: skandal + (R − wynik + 1), heks traci Wyjście i nie daje punktów. '
     'Wynik > R — czysto. Wszystkie znaczniki i karty z heksu schodzą z planszy.</div>' + tab_testu() +
     '<h3>8.2 Jak zbijać ryzyko</h3><ul class="lista"><li>Kolejne transkrypcje (7.1).</li><li>SPR (maszyna, Sprawdzone) zdejmuje 1 znacznik.</li>'
     '<li>Weryfikatorka zdejmuje 1 znacznik albo odwraca 1 kartę.</li><li>RED✓ zdejmuje wszystkie znaczniki, odwraca wszystkie karty i daje −1.</li></ul>'),
    # 11 tabela żetonów
    ('', '<h2>9 · Tabela żetonów</h2>' + tab_akcji(True) +
     '<p class="drob">„Na żywo” = kolumna tury; „po godzinie” = dwie poprzednie; „oba” = obie. Notatka reportera działa jak transkrypcja bez rzutu.</p>'),
    # 12 karty przekonań
    ('', '<h2>10 · Karty przekonań</h2><p class="lead">72 ludzkie halucynacje z różnych kultur — i ukryte prawdy o nas.</p><ul class="lista">'
     '<li>Każdy ma przed sobą 3 karty <b>przekonaniem do góry</b>. Rewers (jak jest naprawdę, ukryta prawda) leży na dole.</li>'
     '<li><b>Zagranie:</b> przed swoim rzutem połóż kartę przekonaniem do góry na heksie, na który rzucasz, i przeczytaj ją na głos. Dostajesz +waga karty (1–3). '
     'Karta zostaje na heksie — to przekonanie weszło do materiału — i do chwili odwrócenia podnosi ryzyko o swoją wagę.</li>'
     '<li><b>Odwrócenie</b> (RED✓ albo Weryfikatorka): przeczytajcie na głos „jak jest naprawdę” i „ukrytą prawdę”. Karta idzie na stos zrozumienia: +1 pkt.</li>'
     '<li>Nie wolno zagrać karty do rzutu na Wyjście ani do testu prawdy.</li><li>Zdarzenie 9 (Pewność siebie): każdy kładzie jedną kartę bez premii.</li></ul>'
     '<h3>10.1 Tor skandalu</h3>' + tab_skandalu() + '<p class="drob">Zwolnioną postać odwraca drużyna. Jej gracz przejmuje syntetycznego kolegę: Kolonia +1 akcja w każdej turze.</p>'),
    # 13 zdarzenia
    ('', '<h2>11 · Zdarzenia anteny</h2><p class="lead">Na początku tury rzuć 2k6. Skutek działa do końca tury, chyba że napisano inaczej.</p>' + tab_zdarzen()),
    # 14 punktacja
    ('', '<h2>12 · Koniec gry i punktacja</h2><p class="lead">Po fazie E tury Nd policzcie: etap × W za każdy heks, +1 za każdy zdjęty znacznik ryzyka, '
     '+1 za każdą kartę na stosie zrozumienia, −2 za każdy punkt skandalu (i −10 za ośmieszenie).</p>' + tab_punktow() +
     '<p class="drob">Zdjęte znaczniki odkładajcie na bok — na koniec łatwo je policzyć.</p>' + tab_ocen()),
    # 15 scenariusze
    ('', '<h2>13 · Scenariusze</h2>' + "".join('<h3>%d · %s</h3><p>%s <span class="drob">%s, godziny %02d–%02d.</span></p>' % (
        sc["nr"], escape(sc["nazwa"]), escape(sc["opis"]), escape(PG.PR.PROFILE[sc["profil"]]["nazwa"]), sc["h0"], sc["h0"] + 7) for sc in PG.SCENARIUSZE) +
     '<div class="ramka"><b>Mapa prawdy i kampania Żółtej Łodzi Podwodnej</b>Mapa prawdy A0 to cztery prawdziwe tygodnie Radia Wnet; godziny bez pomiaru przykrywa mgła. '
     'Dowolny wycinek 7 dni × 8 godzin to scenariusz (progi jak w scenariuszu 1). Kampania — nocna ramówka dla słuchaczy za oceanem — w przygotowaniu.</div>'),
    # 16 przykład + słowniczek
    ('', '<h2>14 · Przykład i słowniczek</h2><p class="lead">Scenariusz 1, tura Śr, 4 osoby, budżet 6, skandal 0.</p><ol class="lista">'
     '<li><b>Antena:</b> 2k6 = 6 — agent dopisał cytat: znacznik „cytat” (+2) na Pn 09:00 (Kto, ●●).</li>'
     '<li><b>Kolonia:</b> L·GODZ na Wt 08:00 (●●●): wynik 4 → 4 + 4 = 8, Słowa leżą; 4 ≤ 5 − 1, więc znacznik ASR.</li>'
     '<li><b>Chmura</b> (budżet 6 → 5): druga transkrypcja C·GODZ na Wt 08:00, wynik 5 → Pewność 2, znacznik ASR schodzi (+1 pkt).</li>'
     '<li><b>Redaktor:</b> RED✓ na Pn 09:00 — cytat schodzi (+1 pkt), Sprawdzone. Pewność 1: R = 3 − 1 = 2.</li>'
     '<li><b>Wydawca:</b> WP na Pn 09:00, rzut 3 (sukces). Test prawdy: R = 2, rzut 2 → halucynacja w eterze: skandal +1. Pn 09:00 nie daje punktów.</li></ol>'
     '<p class="drob">Gdyby Pn 09:00 miało dwie transkrypcje, R = 1 i trzeba by wyrzucić 1, by wpaść.</p>'
     '<dl class="slow"><dt>Pewność</dt><dd>liczba różnych transkrypcji godziny.</dd><dt>WER</dt><dd>odsetek błędnie zapisanych słów.</dd>'
     '<dt>ASR</dt><dd>automatyczne rozpoznawanie mowy; na muzyce potrafi „usłyszeć” zdania.</dd><dt>Diaryzacja</dt><dd>podział nagrania na głosy.</dd></dl>'
     '<div class="kolofon"><b>HALUCYNACJE · Świat anteny</b> — zasady ' + WERSJA + ' · Radio Wnet · Szpieg+ · gra.l00p.ai<br>Mechanika sprawdzona symulacją; '
     'karty przekonań: polszczyzna recenzowana przez Bielika, fakty — przez redakcję. Przygotowane z pomocą AI (Claude, Anthropic) dla Lecha R. Rusteckiego.</div>'),
]


def wypelnij(tresc, logo=""):
    wart = {"LOGO": logo, "HEKS": ZG.heks_opis(), "R1": zet("ryz_asr", 16), "R2": zet("ryz_mowca", 16), "R3": zet("ryz_nazwisko", 16), "R4": zet("ryz_cytat", 16),
            "M1": zet("konflikt", 14), "M2": zet("mgla", 14), "M3": zet("rozwiana", 14), "M4": zet("poufne", 14), "M7": zet("notatka", 14), "M8": zet("skandal", 14)}
    for k, v in wart.items():
        tresc = tresc.replace("%(" + k + ")s", v)
    return tresc.replace("%%", "%")


# ---------------------------------------------------------------- plansza torów (A4) i karta pomocy
def tory_html():
    a = 22.0
    h = '<text x="12" y="16" font-size="6" font-weight="800" fill="#274F5C">Plansza torów · HALUCYNACJE %s</text>' % WERSJA
    h += '<text x="12" y="22" font-size="2.8" fill="#3F5A66">Pola 22 mm pod żetony 20 mm. Tura: dzień tygodnia. Budżet Chmury: każda akcja −1. Skandal: poziomy i skutki niżej.</text>'
    y = 34
    h += '<text x="12" y="%.1f" font-size="3.6" font-weight="800" fill="#274F5C">Tor tur</text>' % (y - 2)
    for k, d in enumerate(PG.DNI):
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#FBF8F2" stroke="#274F5C" stroke-width=".5"/>' % (12 + k * a, y, a, a)
        h += '<text x="%.1f" y="%.1f" font-size="4.5" font-weight="800" text-anchor="middle" fill="#274F5C" opacity=".35">%s</text>' % (12 + k * a + a / 2, y + a * .6, d)
    y = 72
    h += '<text x="12" y="%.1f" font-size="3.6" font-weight="800" fill="#2F7C95">Tor budżetu Chmury</text>' % (y - 2)
    for k in range(13):
        r, c = divmod(k, 7)
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#EEF4F6" stroke="#2F7C95" stroke-width=".5"/>' % (12 + c * a, y + r * a, a, a)
        h += '<text x="%.1f" y="%.1f" font-size="6" font-weight="800" text-anchor="middle" fill="#2F7C95" opacity=".35">%d</text>' % (12 + c * a + a / 2, y + r * a + a * .64, k)
    y = 132
    h += '<text x="12" y="%.1f" font-size="3.6" font-weight="800" fill="#8A0E1E">Tor skandalu</text>' % (y - 2)
    kol = {0: "#F4F7F2", 1: "#FBE3E6", 2: "#FBE3E6", 3: "#F4B7C1", 4: "#F4B7C1", 5: "#E27083", 6: "#E27083", 7: "#C43550", 8: "#C43550", 9: "#8A0E1E"}
    etyk = {0: "czysto", 1: "sprostowanie", 3: "ośmieszenie −10", 5: "zwolnienie", 7: "2. zwolnienie", 9: "KONIEC"}
    for k in range(10):
        r, c = divmod(k, 5)
        x, yy = 12 + c * (a + 14), y + r * (a + 12)
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8A0E1E" stroke-width=".5"/>' % (x, yy, a, a, kol[k])
        h += '<text x="%.1f" y="%.1f" font-size="7" font-weight="900" text-anchor="middle" fill="%s" opacity=".5">%d</text>' % (x + a / 2, yy + a * .66, "#fff" if k >= 5 else "#8A0E1E", k)
        if k in etyk:
            h += '<text x="%.1f" y="%.1f" font-size="2.7" font-weight="800" fill="#8A0E1E">%s</text>' % (x, yy + a + 4, etyk[k])
    y = 212
    h += '<text x="12" y="%.1f" font-size="3.6" font-weight="800" fill="#274F5C">Stos zrozumienia i zdjęte znaczniki</text>' % y
    h += '<rect x="12" y="%.1f" width="60" height="89" rx="3" fill="none" stroke="#274F5C" stroke-width=".5" stroke-dasharray="3 2"/>' % (y + 4)
    h += '<text x="42" y="%.1f" font-size="3" text-anchor="middle" fill="#75909A">odwrócone karty (+1)</text>' % (y + 50)
    h += '<rect x="80" y="%.1f" width="118" height="60" rx="3" fill="none" stroke="#9E1F36" stroke-width=".5" stroke-dasharray="3 2"/>' % (y + 4)
    h += '<text x="139" y="%.1f" font-size="3" text-anchor="middle" fill="#9E1F36">zdjęte znaczniki ryzyka (+1)</text>' % (y + 36)
    h += PG.SA.linijka(80, 283, 100)
    return '<div class="s"><svg class="p" viewBox="0 0 210 297">%s</svg></div>' % h


def karta_pomocy_html(tylko_tresc=False):
    sek = ('<table class="tab"><tr><td class="n">A</td><td>Antena: tura +1, 2k6 → zdarzenie, karty do 3</td></tr><tr><td class="n">B</td><td>Kolonia: 4 akcje</td></tr>'
           '<tr><td class="n">C</td><td>Chmura: do 3, każda −1 budżetu</td></tr><tr><td class="n">D</td><td>Ludzie: ruch ekip 3, potem akcje postaci</td></tr>'
           '<tr><td class="n">E</td><td>Archiwum; skandal 5/7 → zwolnienie</td></tr></table>')
    mod = ('<p><b>k6 + siła + mod ≥ 7</b> · 1 porażka · 6 sukces · 1 przy Kto → „!”</p><table class="tab"><tr><td class="n">−1</td><td>mgła (maszyny: Słowa/Głosy/Sprawdzone)</td></tr>'
           '<tr><td class="n">−1/−2</td><td>2/3 domy (maszyny: Głosy/Kto)</td></tr><tr><td class="n">+1</td><td>ten sam program · Reporter · Realizatorka</td></tr>'
           '<tr><td class="n">+w</td><td>karta przekonania (zostaje na heksie)</td></tr></table>'
           '<p><b>Ślad maszyny:</b> sukces z k6 ≤ 5 − Pewność (+1 na żywo) → znacznik ryzyka.</p>')
    test = ('<p><b>Test prawdy</b> (po Wyjściu): R = (4 − Pewność) + znaczniki (1/2) + karty (waga) + mgła − RED✓. k6 ≤ R → skandal + (R − k6 + 1), heks 0 pkt.</p>')
    kr = {2: "Kolonia −2", 3: "„poufne” na 1. lądzie na żywo", 4: "„mgła” na 1. lądzie na żywo", 5: "Chmura 0 akcji", 6: "„cytat” +2 na najwyższym etapie",
          7: "bez zmian", 8: "Redaktor +1 akcja", 9: "każdy kładzie kartę", 10: "budżet −1", 11: "Kolonia +2", 12: "Wydawca musi publikować"}
    wz = ['<tr><td class="n">%d</td><td><b>%s</b> — %s</td></tr>' % (w, escape(n), escape(kr[w])) for w, n, _ in ZDARZENIA]
    zd = '<div class="k2"><div><table class="tab">%s</table></div><div><table class="tab">%s</table></div></div>' % ("".join(wz[:6]), "".join(wz[6:]))
    tresc = ('<h1>Karta pomocy · HALUCYNACJE %s</h1><div class="k2"><div><h2>Sekwencja tury</h2>%s<h2>Rzut i modyfikatory</h2>%s%s<h2>Punkty = etap × W</h2>%s</div>'
             '<div><h2>Żetony i akcje</h2>%s</div></div><h2>Zdarzenia anteny (2k6)</h2>%s') % (WERSJA, sek, mod, test, tab_punktow(), tab_akcji(karta=True), zd)
    tresc = tresc.replace('style="width:6.5mm;height:6.5mm;flex:none"', 'width="24" height="24"')
    if tylko_tresc:
        return ZG.KP_CSS, tresc
    return '<div class="s"><style>%s</style><div class="kp">%s</div></div>' % (ZG.KP_CSS, tresc)


def tory_svg(x, y, _skala=None):
    """Tory na planszy A0: tura, budżet i skandal (pola 22 mm)."""
    a = 22.0
    h = ZG.tory_svg(x, y)
    y3 = y + a + 9 + 2 * a + 11
    h += '<text x="%.1f" y="%.1f" font-size="3.4" font-weight="800" fill="#8A0E1E">Tor skandalu</text>' % (x, y3 - 2)
    etyk = {0: "czysto", 1: "sprostowanie", 3: "ośmieszenie", 5: "zwolnienie", 7: "2. zwolnienie", 9: "KONIEC"}
    for k in range(10):
        h += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8A0E1E" stroke-width=".5"/>' % (
            x + k * a, y3, a, a, ["#F4F7F2", "#FBE3E6", "#FBE3E6", "#F4B7C1", "#F4B7C1", "#E27083", "#E27083", "#C43550", "#C43550", "#8A0E1E"][k])
        h += '<text x="%.1f" y="%.1f" font-size="6" font-weight="900" text-anchor="middle" fill="#8A0E1E" opacity=".45">%d</text>' % (x + k * a + a / 2, y3 + a * .64, k)
        if k in etyk:
            h += '<text x="%.1f" y="%.1f" font-size="2.6" font-weight="800" fill="#8A0E1E">%s</text>' % (x + k * a, y3 + a + 3.6, etyk[k])
    return h
