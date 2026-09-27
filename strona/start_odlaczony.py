# -*- coding: utf-8 -*-
"""Start gry „Języki” (:8781, 127.0.0.1, za tunelem jako gra.l00p.ai) ODŁĄCZONY od sesji, która go uruchamia.

Konfigurację (administrator danych, IOD) czyta z pliku POZA gitem: %USERPROFILE%\\szpieg_media\\jezyki\\jezyki.env
(setdefault — zmienna ustawiona ręcznie w env wygrywa). Nigdy nie wypisuje wartości. Użycie: python start_odlaczony.py [port]"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KONFIG = os.path.join(os.path.expanduser("~"), "szpieg_media", "jezyki", "jezyki.env")
PY = os.environ.get("JEZYKI_PY") or sys.executable
FL = 0x00000008 | 0x00000200 | 0x01000000        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB

env = os.environ.copy()
try:
    for linia in open(KONFIG, encoding="utf-8"):
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", linia)
        if m and not linia.lstrip().startswith("#") and m.group(2):
            env.setdefault(m.group(1), m.group(2))
except FileNotFoundError:
    print("uwaga: brak", KONFIG, "— zapisy e-mail zostaną zamknięte")
env["PYTHONIOENCODING"] = "utf-8"
port = sys.argv[1] if len(sys.argv) > 1 else "8781"
os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
out = open(os.path.join(HERE, "logs", "jezyki_%s.log" % port), "ab")
cmd = [PY, os.path.join(HERE, "server.py"), port]
try:
    p = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=out, stderr=out, stdin=subprocess.DEVNULL, creationflags=FL)
except OSError:
    p = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=out, stderr=out, stdin=subprocess.DEVNULL, creationflags=FL & ~0x01000000)
print("PID", p.pid, "· konfiguracja", "OK" if os.path.exists(KONFIG) else "BRAK")
