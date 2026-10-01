# jezyki_web — gra „Języki” (SZPIEG-157)

Meta-gra Szpiega+ dla wszystkich (docelowo **gra.l00p.ai**). Dziś strona wejściowa:
- nazwa gry „pisze się” po kolei we wszystkich językach (efekt jak „hello” w iPhonie: kontur słowa, potem wypełnienie) — 228 słów;
- logo: trzy wijące się ludzkie języki wychodzące z ust (po polsku „język” to i mowa, i narząd) — `static/logo.svg`, SMIL + CSS;
- zapis e-maila na **jedną** wiadomość, gdy świat gry zostanie zresetowany dla nowych graczy.

## Słowa

`dane/slowa.json` buduje `narzedzia/zbuduj_slowa.py` (ręcznie albo przyciskiem w Ustawieniach): **Wikidane Q34770** (etykiety „język”, CC0)
+ dopełnienie brakujących języków pierwszym działającym dostawcą z Ustawień. Źródło przy każdym słowie (`wikidata` / `mymemory` / `deepl` / `libre` / `gra`).
Tłumaczymy RAZ przy budowie — nie przy wizycie gracza (0 zł, żadnych danych gracza u dostawców).

## Ustawienia (tylko operator przy ZBooku)

`/ustawienia` — kolejność dostawców (Wikidane, MyMemory bez klucza, DeepL z kluczem, LibreTranslate z adresem/kluczem) i „Przebuduj słownik”.
Klucze w `%USERPROFILE%\szpieg_media\jezyki\ustawienia.json` (poza gitem), na ekranie tylko `••••` + 4 ostatnie znaki; puste pole nie zmienia, „-” usuwa.
Operator = pętla zwrotna BEZ nagłówków pośrednika (tunel Cloudflare je dokłada). Docelowo ten sam panel w Ustawieniach Szpiega+
(wymaga zmiany `index.html` — zamrożony do ~20.10 — i restartu `:8765`).

## Zapisy e-mail — fail-closed

Zamknięte, dopóki `JEZYKI_ADMINISTRATOR` nie wskazuje administratora danych (decyzja Lecha; L00P.ai nie istnieje w KRS).
Przechowujemy tylko e-mail, czas, wersję klauzuli i pierwszy język przeglądarki (`zapisy.sqlite3` poza gitem); **bez IP** (limit 5/h liczony
w pamięci po skrócie IP+dnia, 500 zapisów na dobę); pole-pułapka dla botów; ta sama odpowiedź dla nowego i powtórzonego adresu.

## Uruchomienie i testy

- **Produkcja od 27.09.2026: https://gra.l00p.ai** (publicznie, BEZ Access) — tunel `szpieg-test`, reguła w `~/.cloudflared/config.yml` (kopia `config.yml.bak_20260927_przed_gra`), CNAME przez `cloudflared tunnel route dns`. Proces `server.py 8781` (127.0.0.1) startuje `python start_odlaczony.py` — konfiguracja z `szpieg_media\jezyki\jezyki.env` (poza gitem); **bez autostartu** (po restarcie maszyny uruchomić ręcznie).
- Administrator danych: **Radio Wnet Sp. z o.o.**, IOD `iod@perfectinfo.pl` (decyzja Lecha 27.09). Zapis wymaga OBU (`JEZYKI_ADMINISTRATOR`, `JEZYKI_IOD`); klauzula art. 13 RODO na stronie (`J.klauzula`, wersja `KLAUZULA` = `2026-09-28.1`) — **zaakceptowana przez IOD 01.10.2026**. Każda zmiana treści klauzuli = nowa wersja `KLAUZULA` i ponowna akceptacja IOD; `/api/wypisz` = wycofanie zgody.
- testy: `python -m unittest discover -s tests` (9; w tym klauzula, wypis, czyste funkcje frontu i lista języków pod node).
- lista „Nazwy języków”: polski + najpopularniejsze na górze, reszta alfabetycznie wg nazwy własnej; tylko języki, które przeglądarka umie nazwać (`Intl.DisplayNames`); wybór w `localStorage`.
- CSP `default-src 'self'` tylko na stronach HTML (SVG logo ma własną animację `<style>`); zero stylów w atrybutach; zasoby z `?v=` przy zmianie.
