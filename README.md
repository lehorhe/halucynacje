# HALUCYNACJE · Świat anteny

Kooperacyjna gra planszowa o redakcji Radia Wnet, w której ludzie i maszyny słuchają anteny i mylą się na różne sposoby. Strona gry: **https://gra.l00p.ai**

> „Mapa nie jest terytorium.” — Alfred Korzybski, 1931

To repozytorium zawiera **dwie mapy jednego terytorium**: cztery tygodnie anteny Radia Wnet (31.08–27.09.2026, 672 godziny) narysowane

- **generatorem 2D** (`plansza_gry.py`) — plansze do gry i do czytania, z legendą, która pokazuje, ile o antenie wiadomo bez słuchania;
- **proceduralnie w Blenderze** (`blender/`) — świat 3D z tych samych danych, przenośny do Unreal Engine 5.8, Unity i Godota (glTF 2.0);

oraz **test zgodności** (`test_zgodnosci.py`), który sprawdza, że obie mapy mówią to samo.

## Co tu jest

| Katalog / plik | Zawartość |
|---|---|
| `plansza_gry.py`, `swiat_antena.py`, `legenda_mapy.py` | generator plansz 2D (teren z procentu słowa, osady, latarnie, legenda) |
| `zasady_halucynacje.py`, `karty_*.py`, `symulacja_*.py` | zasady, 72 karty przekonań + 8 postaci, symulacje balansu |
| `dane/mapa_prawdy_2026-08-31_4tyg.json` | **migawka danych**: agregaty godzin (procent słowa z 2–4 metod, głosy efektywne, warstwy terenu, ramówka) |
| `blender/` | eksport danych do sceny, skrypt sceny (render, glTF), gotowe pliki w `blender/eksport/` |
| `test_zgodnosci.py` | 2D ↔ 3D: ląd/morze, osady, latarnie, kolory audycji, linia brzegowa, plik glTF |
| `pdf/` | plansze, karty i zasady do druku (A4–A0), wydruki kolegium |
| `strona/` | strona gra.l00p.ai (serwer Pythona bez zależności + pliki statyczne) |
| `vendor/` | minimalne moduły pomocnicze (model żetonów, ramówka), `fonty/` — Exo 2 i Lato (SIL OFL 1.1) |
| `silniki/` | jak przenieść świat do UE 5.8, Unity, Godota |

## Uruchomienie

Python 3.11+ z `numpy`, `Pillow`, `pymupdf`; do PDF — Chrome lub Chromium (ścieżka w zmiennej `HAL_CHROME`, jeśli nie ma go w PATH).

```bash
pip install numpy pillow pymupdf
python -c "import plansza_gry as PG, swiat_antena as SA; h,_,_ = PG.plansza_prawdy_a0(); SA.drukuj([h], 841, 1189, 'Mapa_prawdy_A0.pdf')"
python plansza_gry.py --a0          # plansze scenariuszy (radio klasyczne, muzyczne, informacyjne, idealne)
python blender/eksport_blender.py   # dane sceny 3D z generatora
blender -b -P blender/scena_blender.py -- oba    # dwa kadry (orto i dron 90 m)
blender -b -P blender/scena_blender.py -- glb    # glTF + przepis sceny
python test_zgodnosci.py            # czy 2D i 3D mówią to samo
```

Bez archiwum Szpiega+ generator czyta migawkę `dane/…json` (tryb wymuszany zmienną `HAL_MIGAWKA=1`). Redakcja z dostępem do archiwum przelicza mapę z pomiarów i odświeża migawkę.

## Dane i prywatność

W repozytorium **nie ma nagrań, transkrypcji, głosów ani danych osobowych**. Migawka zawiera wyłącznie agregaty godzin anteny. Nazwy audycji pochodzą z publicznej ramówki; wpisy nazwane imieniem lub nazwiskiem prowadzącego są zastąpione napisem „Audycja autorska”. Liczba rozpoznanych głosów jest podana tylko jako liczba.

## Licencja — decyzja nr 1

**Licencja nie jest jeszcze wybrana.** Jej wybór to pierwsza decyzja tworzącej się społeczności (zob. `LICENCJA_DO_WYBORU.md` i zgłoszenie nr 1). Do tego czasu obowiązują wszelkie prawa zastrzeżone: wolno czytać kod, drukować plansze do własnej gry i dyskutować; rozpowszechnianie zmienionych wersji — po wyborze licencji.

Wyjątki już licencjonowane: fonty Exo 2 i Lato (SIL Open Font License 1.1), `strona/static/model-viewer.min.js` (Google, BSD-3-Clause).

## Autorzy

Radio Wnet · Szpieg+ · pomysł i redakcja: Lech R. Rustecki. Kod, teksty i grafika przygotowane z pomocą AI (Claude, Anthropic); polszczyzna kart recenzowana lokalnym modelem Bielik, fakty — przez redakcję.
