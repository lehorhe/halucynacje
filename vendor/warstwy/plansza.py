# -*- coding: utf-8 -*-
"""Plansza warstw Szpiega+ — silnik (stdlib, bez stanu, bez sieci). Model: `model.json` obok.

Metafora gry strategicznej na heksach:
  * POLE (hex) = warstwa; pierścień = odległość od rzeczywistości (0 = nagranie anteny w centrum, 6 = wyjście na zewnątrz).
  * ŻETON = jeden konkretny przebieg przetwarzania na polu (np. „Słowa po godzinie: kolonia”, „Słowa na żywo: Scribe”).
    Żetony się STACKUJĄ: na jednym polu może leżeć kilka, każdy z własnym zakresem czasu, siłą i źródłem (L/C/H/W).
  * RELACJE = warunki położenia żetonu (`wymaga`): pole z gotowym żetonem, konkretny żeton, znaczniki czasu słów…
    Brak warunku = ruch zablokowany z nazwaną przyczyną („diaryzacja wymaga słów z czasem każdego słowa”).
  * NAKŁADKA (człowiek, sprawdzenie) nie zastępuje stosu — podnosi go (np. weryfikacja redaktora: WER ~5% → ~2%).

Instancja żetonu (stan godziny): {"zeton": id, "zakres": [[t0, t1], …] w sekundach godziny (brak = cała), "stan": "gotowy"|"w_toku",
"konflikty": n (np. Głosoteka ≠ zapowiedź), "opis": tekst dla ludzi}. Funkcje zwracają dane — rysują je makieta, broszura i plansza PDF."""
from __future__ import annotations

import json
import math
import os

GODZINA = 3600.0
_MODEL = None


def model(sciezka=None):
    global _MODEL
    if sciezka:
        with open(sciezka, encoding="utf-8") as f:
            return json.load(f)
    if _MODEL is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json"), encoding="utf-8") as f:
            _MODEL = json.load(f)
    return _MODEL


def _defs(m):
    return {z["id"]: z for z in m["zetony"]}, {p["id"]: p for p in m["pola"]}


# ---------------------------------------------------------------- geometria heksów (osiowe q, r; heks „ostrym czubkiem w górę”)
def odleglosc(a, b):
    dq, dr = a[0] - b[0], a[1] - b[1]
    return max(abs(dq), abs(dr), abs(dq + dr))


def srodek(q, r, s):
    """Środek heksu o promieniu s (środek → wierzchołek) w pikselach/mm."""
    return s * math.sqrt(3) * (q + r / 2.0), s * 1.5 * r


def wierzcholki(cx, cy, s):
    return [(cx + s * math.cos(math.radians(60 * i - 30)), cy + s * math.sin(math.radians(60 * i - 30))) for i in range(6)]


def sasiedzi(q, r):
    return [(q + 1, r), (q + 1, r - 1), (q, r - 1), (q - 1, r), (q - 1, r + 1), (q, r + 1)]


def pierscien(pole, m=None):
    return odleglosc((pole["q"], pole["r"]), (0, 0))



# ---------------------------------------------------------------- statystyka godziny: % słowa
def procent_slowa(pomiary, dl=GODZINA, m=None):
    """pomiary: {metoda: sekundy mowy w godzinie} (smd / segmenty / tagi …; brak albo None = metoda nie liczyła).
    → {metody: {m: %}, min, max, srodek, rozrzut_pp, zgodne, n, koncesja_pct} albo None, gdy żadnej miary.
    Słowo liczymy pośrednio (godzina minus muzyka), więc różne metody dają różne wyniki — pokazujemy przedział, nie jedną liczbę."""
    m = m or model()
    st = m.get("statystyki", {}).get("slowo", {})
    dl = float(dl or GODZINA)
    pct = {k: round(100.0 * min(max(float(v), 0.0), dl) / dl, 1) for k, v in (pomiary or {}).items() if v is not None}
    if not pct:
        return None
    lo, hi = min(pct.values()), max(pct.values())
    return {"metody": pct, "min": lo, "max": hi, "srodek": round((lo + hi) / 2, 1), "rozrzut_pp": round(hi - lo, 1),
            "zgodne": (hi - lo) <= float(st.get("zgodne_pp", 5.0)), "n": len(pct),
            "koncesja_pct": (st.get("koncesja") or {}).get("prog_pct")}


def slowo_z_meta(statystyki):
    """Sekundy mowy z `meta.json → statystyki` godziny: smd (mowa_s, gdy zrodlo=smd i nie szacunek) i segmenty transkrypcji."""
    s = statystyki or {}
    pom = {}
    if s.get("zrodlo") == "smd" and not s.get("szacunek") and s.get("mowa_s") is not None:
        pom["smd"] = s["mowa_s"]
    if s.get("mowa_s_segmenty") is not None:
        pom["segmenty"] = s["mowa_s_segmenty"]
    return pom, float(s.get("dur_s") or GODZINA)
