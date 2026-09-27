# -*- coding: utf-8 -*-
"""Ścieżki zasobów: najpierw zmienne środowiskowe HAL_*, potem instalacja redakcyjna (katalog domowy stacji Szpiega+), na końcu kopia
w repozytorium. Dzięki temu ten sam kod działa u redakcji (z pełnym archiwum) i u każdego z publicznego repozytorium (z migawką danych)."""
import os
import shutil

REPO = os.path.dirname(os.path.abspath(__file__))
DOM = os.path.expanduser("~")


def _pierwsza(env, *kand):
    for p in [os.environ.get(env)] + list(kand):
        if p and os.path.exists(p):
            return p
    return kand[-1]


WARSTWY = _pierwsza("HAL_WARSTWY", os.path.join(DOM, "RadioWnet_AI_Strategia", "warstwy"), os.path.join(REPO, "vendor", "warstwy"))
RAMOWKA = _pierwsza("HAL_RAMOWKA", os.path.join(DOM, "Documents", "Ramowka-plakat", "zrodlo"), os.path.join(REPO, "vendor", "ramowka"))
FONTY = _pierwsza("HAL_FONTY", os.path.join(DOM, "RadioWnet_AI_Strategia", "czytelnia_web", "static", "fonty"), os.path.join(REPO, "fonty"))
MEDIA = _pierwsza("HAL_MEDIA", os.path.join(DOM, "szpieg_media"), os.path.join(REPO, "dane", "_brak_archiwum"))
CHROME = _pierwsza("HAL_CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                   *(p for p in (shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome")) if p), "chrome")
MIGAWKA = os.path.join(REPO, "dane", "mapa_prawdy_2026-08-31_4tyg.json")
ARCHIWUM = os.path.isdir(MEDIA) and os.environ.get("HAL_MIGAWKA") != "1"     # False → generator czyta migawkę (repozytorium publiczne)
