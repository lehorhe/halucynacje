# -*- coding: utf-8 -*-
"""Etap 1 nowych warstw terenu mapy prawdy — tylko z danych, które już są (bez nowego audio):
  przejscia  — liczba przejść mowa↔muzyka z meta.utwory (bloki muzyki SMD)             → postrzępione wybrzeże / archipelag
  tempo      — sylaby/s w turach mowy, BEZ serwisu (mówca tylko w pierwszych 8 min)      → stromizna zboczy
  laguna     — sekundy „mowa na tle muzyki” z tagów EfficientAT (tylko godziny z tagami) → laguny i plaże
  rozbieznosc— szacowana rozbieżność transkrypcji (proxy WER), kalibrowana na godzinach ze Scribe → miraż
Wyjście: warstwy_etap1.json {"YYYY-MM-DD HH": {...}} + kalibracja.
    python warstwy_etap1.py"""
import glob
import json
import os
import re
import statistics as S

import numpy as np

MEDIA = os.path.join(os.path.expanduser("~"), "szpieg_media")
TU = os.path.dirname(os.path.abspath(__file__))
SAMOGL = re.compile("[aeiouyąęó]", re.I)
NORM = re.compile(r"[^\wąćęłńóśźż]+", re.I)


def w_muzyce(t, utwory):
    return any(u["start"] <= t <= u["end"] for u in utwory)


def przejscia(meta, dl):
    n = 0
    for u in meta.get("utwory") or []:
        n += (u["start"] > 5) + (u["end"] < dl - 5)
    return n


def serwis_mowcy(words):
    """Mówcy, którzy mówią tylko w pierwszych 8 min godziny i łącznie ≥ 45 s — lektor serwisu (heurystyka, bez listy nazwisk)."""
    zakres, czas = {}, {}
    for x in words:
        sp = x.get("speaker")
        a, b = zakres.get(sp, (1e9, 0))
        zakres[sp] = (min(a, x["s"]), max(b, x["e"]))
        czas[sp] = czas.get(sp, 0) + (x["e"] - x["s"])
    return {sp for sp, (a, b) in zakres.items() if b <= 480 and czas[sp] >= 45}


def tempo(words, utwory, pomin):
    syl = dur = 0.0
    a = b = None
    n = 0
    for x in words:
        if x.get("speaker") in pomin or w_muzyce(x["s"], utwory):
            continue
        if b is not None and x["s"] - b < 0.6:
            b = x["e"]; n += len(SAMOGL.findall(x["w"])); continue
        if b is not None and b - a > 3:
            syl += n; dur += b - a
        a, b, n = x["s"], x["e"], len(SAMOGL.findall(x["w"]))
    if b is not None and b - a > 3:
        syl += n; dur += b - a
    return (round(syl / dur, 2), round(dur)) if dur > 120 else (None, round(dur))


def niska_pewnosc(words, utwory):
    lp = [x["lp"] for x in words if x.get("lp") is not None and not w_muzyce(x["s"], utwory)]
    return (sum(1 for v in lp if v < -1.0) / len(lp), len(lp)) if len(lp) > 200 else (None, len(lp))


def tekst(ws):
    return " ".join(t for t in (NORM.sub(" ", w).strip().lower() for w in ws) if t)


def kalibracja():
    import jiwer
    pary = []
    for ps in sorted(glob.glob(os.path.join(MEDIA, "2026-*", "*.scribe.json"))):
        pre = ps[:-len(".scribe.json")]
        if not (os.path.exists(pre + ".words.json") and os.path.exists(pre + ".meta.json")):
            continue
        meta = json.load(open(pre + ".meta.json", encoding="utf-8"))
        ut = meta.get("utwory") or []
        ww = json.load(open(pre + ".words.json", encoding="utf-8"))["words"]
        sc = [x for x in json.load(open(ps, encoding="utf-8")).get("words") or [] if x.get("type") == "word"]
        hyp = tekst(x["w"] for x in ww if not w_muzyce(x["s"], ut))
        ref = tekst(x["text"] for x in sc if not w_muzyce(x["start"], ut))
        if len(ref.split()) < 300:
            continue
        d = jiwer.wer(ref, hyp)
        low, n = niska_pewnosc(ww, ut)
        smd = (meta.get("statystyki") or {}).get("mowa_s", 0) / (meta.get("dur_s") or 3600) * 100
        pary.append({"godz": os.path.basename(pre)[11:], "rozbieznosc": round(d * 100, 1), "niska_pewnosc": round(low * 100, 2) if low is not None else None,
                     "slow_ref": len(ref.split()), "smd_pct": round(smd, 1)})
    return pary


def main():
    kal = kalibracja()
    mowa = [p for p in kal if p["smd_pct"] >= 50 and p["niska_pewnosc"] is not None]     # godziny muzyczne (teksty piosenek) poza kalibracją
    x = np.array([p["niska_pewnosc"] for p in mowa]); y = np.array([p["rozbieznosc"] for p in mowa])
    b, a = np.polyfit(x, y, 1) if len(mowa) >= 4 else (0.0, float(np.median(y)) if len(y) else 10.0)
    r = float(np.corrcoef(x, y)[0, 1]) if len(mowa) >= 4 else None
    print("kalibracja: %d godzin, %d mówionych; rozbieżność = %.2f + %.2f × niska_pewność%%  (r=%s)" % (len(kal), len(mowa), a, b, "%.2f" % r if r is not None else "—"))
    for p in kal:
        print("  ", p)
    pkp = os.path.join(TU, "studio_kp.json")
    KP = json.load(open(pkp, encoding="utf-8"))["godziny"] if os.path.exists(pkp) else {}
    out = {}
    for pm in sorted(glob.glob(os.path.join(MEDIA, "2026-*", "*.meta.json"))):
        pre = pm[:-len(".meta.json")]
        m = re.search(r"sr_program_(\d{4})_(\d\d)_(\d\d)_(\d\d)$", pre)
        if not m:
            continue
        k = "%s-%s-%s %s" % m.groups()
        meta = json.load(open(pm, encoding="utf-8"))
        dl = meta.get("dur_s") or 3600
        ut = meta.get("utwory") or []
        g = {"przejscia": przejscia(meta, dl)}
        if os.path.exists(pre + ".words.json"):
            ww = json.load(open(pre + ".words.json", encoding="utf-8"))["words"]
            sv = serwis_mowcy(ww)
            g["tempo"], g["tempo_s"] = tempo(ww, ut, sv)
            g["serwis"] = bool(sv)
            low, n = niska_pewnosc(ww, ut)
            if low is not None:
                g["niska_pewnosc_pct"] = round(low * 100, 2)
                g["rozbieznosc_szac"] = round(min(40.0, max(1.0, a + b * low * 100)), 1)     # poza zakresem kalibracji (2,3 % niskiej pewności) nie ekstrapolujemy
        if os.path.exists(pre + ".tagi.json"):
            t = json.load(open(pre + ".tagi.json", encoding="utf-8"))
            g["mowa_muzyka_s"] = t["sekundy"]["mowa_muzyka"]
        if os.path.exists(pre + ".pasmo.json"):
            pa = json.load(open(pre + ".pasmo.json", encoding="utf-8"))
            g["tel_nb_pct"], g["tel_wb_pct"] = pa["udzial_nb_pct"], pa["udzial_wb_pct"]
        if k in KP:
            g["studio_kp"] = KP[k]["studio"]
            g["realizator_sm7b"] = KP[k].get("realizator_sm7b", False)
        if os.path.exists(pre + ".scribe.json"):
            g["dwie_transkrypcje"] = True
            hit = [p for p in kal if p["godz"] == os.path.basename(pre)[11:]]
            if hit:
                g["rozbieznosc_zmierzona"] = hit[0]["rozbieznosc"]
        out[k] = g
    # warstwy w toku (pasmo): na planszę tylko przy pokryciu ≥ 90 % godzin — inaczej wydruk mylnie sugerowałby „brak łącz”
    pokr_pasmo = sum(1 for g in out.values() if "tel_nb_pct" in g) / max(1, len(out))
    if pokr_pasmo < 0.9:
        for g in out.values():
            g.pop("tel_nb_pct", None); g.pop("tel_wb_pct", None)
        print("pasmo: pokrycie %.0f%% < 90%% — warstwa łącz wyłączona z planszy" % (100 * pokr_pasmo))
    tem = [g["tempo"] for g in out.values() if g.get("tempo")]
    prz = [g["przejscia"] for g in out.values()]
    lag = [g["mowa_muzyka_s"] for g in out.values() if "mowa_muzyka_s" in g]
    roz = [g["rozbieznosc_szac"] for g in out.values() if "rozbieznosc_szac" in g]
    print("godzin %d · tempo mediana %.2f (p10 %.2f, p90 %.2f) · przejścia mediana %d (p90 %d) · laguna: %d godzin z tagami, mediana %.0f s · rozbieżność szac. mediana %.1f%% (p90 %.1f)" % (
        len(out), S.median(tem), np.percentile(tem, 10), np.percentile(tem, 90), S.median(prz), np.percentile(prz, 90), len(lag), S.median(lag) if lag else 0,
        S.median(roz), np.percentile(roz, 90)))
    tel = [g["tel_nb_pct"] + g["tel_wb_pct"] for g in out.values() if "tel_nb_pct" in g]
    if tel:
        print("łącza zdalne: %d godzin z pomiarem, mediana %.1f%%, godzin ≥ 10%%: %d, NB łącznie w %d godzinach" % (
            len(tel), S.median(tel), sum(1 for t in tel if t >= 10), sum(1 for g in out.values() if g.get("tel_nb_pct", 0) > 0)))
    print("serwis wykryty w %d godzinach" % sum(1 for g in out.values() if g.get("serwis")))
    pokrycie = {"tagi": sum(1 for g in out.values() if "mowa_muzyka_s" in g), "pasmo": sum(1 for g in out.values() if "tel_nb_pct" in g), "godzin": len(out)}
    json.dump({"pokrycie": pokrycie, "kalibracja": {"a": round(float(a), 3), "b": round(float(b), 3), "r": r, "godziny": kal}, "godziny": out},
              open(os.path.join(TU, "warstwy_etap1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)


if __name__ == "__main__":
    main()
