# -*- coding: utf-8 -*-
"""Buduje static/logo.svg — HALUCYNACJE: sześć języków wokół ust (kwiatek czy języki?).
Każdy język ma WŁASNE węzły i własną sekwencję póz (SMIL `d`), własny czas (liczby pierwsze → układ prawie się nie powtarza)
i własne kołysanie (CSS, inne tempo i amplituda). Ziarno stałe → ten sam plik przy każdym przebiegu.
    python narzedzia/zbuduj_logo.py"""
import os
import random

TU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = random.Random(20260928)
CZASY = [7.3, 11.3, 8.9, 13.1, 9.7, 12.7]          # s — morfing kształtu
KOLYS = [10.1, 7.9, 12.3, 8.3, 11.9, 9.1]          # s — kołysanie całego języka


def jezyk(k):
    """Kształt: nasada ±w u dołu, czubek wysoko; 5 póz: spoczynek, zwinięcie czubka w lewo/prawo, wygięcie, „liźnięcie” (wydłużenie)."""
    w = R.uniform(20, 25)
    dl = R.uniform(80, 90)

    def poza(zw, wyg, wydl, grub):
        # zw: zwinięcie czubka (−1 lewo, +1 prawo), wyg: wygięcie trzonu, wydl: wydłużenie, grub: pogrubienie
        L = dl * wydl
        cx = wyg * 14
        tx = cx + zw * 16
        ty = -L + abs(zw) * 10
        return ("M %.1f -18 C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f -18 Z" % (
            -w * grub, -w * grub - 5 + cx * .3, -L * .5, -w * .75 + cx, -L * .82, tx - 9, ty - 1,
            tx - 2, ty - 6, tx + 7, ty - 4, tx + 9, ty + 3,
            w * .8 + cx, -L * .8, w * grub + 5 + cx * .3, -L * .5, w * grub))

    def bruzda_p(zw, wyg, wydl, grub):
        L = dl * wydl
        cx = wyg * 14
        tx, ty = cx + zw * 16, -L + abs(zw) * 10
        return "M %.1f -26 C %.1f %.1f %.1f %.1f %.1f %.1f" % (cx * .15, cx * .45, -L * .45, cx * .9 + zw * 4, -L * .7, tx * .85, ty + 12)

    parametry = [(0, 0, 1, 1)]
    for _ in range(3):
        parametry.append((R.choice([-1, 1]) * R.uniform(.7, 1.35), R.uniform(-1, 1), R.uniform(.9, 1.1), R.uniform(.9, 1.08)))
    parametry.append((R.uniform(-.2, .2), R.uniform(-.3, .3), R.uniform(1.08, 1.16), .92))          # „liźnięcie”
    parametry.append(parametry[0])
    kol = [poza(*p) for p in parametry]
    br = [bruzda_p(*p) for p in parametry]
    kt = sorted(R.uniform(.12, .9) for _ in range(len(kol) - 2))
    kt = [0] + [round(x, 3) for x in kt] + [1]
    ks = ";".join("%.2f 0 %.2f 1" % (R.uniform(.25, .55), R.uniform(.45, .75)) for _ in range(len(kol) - 1))

    def bruzda(p):
        # środek języka: od nasady ku czubkowi, podąża za wygięciem
        return p
    return (w, CZASY[k], ";\n                    ".join(kol), ";".join(str(x) for x in kt), ks, ";".join(br))


def main():
    rozowe = ["#EE7A90", "#E86C84", "#F08497", "#E97389", "#EC7D93", "#E5667F"]
    defs, uzycia, css = [], [], []
    for k in range(6):
        w, t, vals, kt, ks, brz = jezyk(k)
        poczatek = R.uniform(0, t)
        defs.append('''  <g id="j%d">
   <path fill="url(#mieso%d)" stroke="#A8354E" stroke-width="1.7" stroke-linejoin="round" d="%s">
    <animate attributeName="d" dur="%.1fs" begin="-%.1fs" repeatCount="indefinite" calcMode="spline" keyTimes="%s" keySplines="%s"
             values="%s"/>
   </path>
   <path fill="none" stroke="#A8354E" stroke-width="2.3" stroke-linecap="round" opacity=".7" d="%s">
    <animate attributeName="d" dur="%.1fs" begin="-%.1fs" repeatCount="indefinite" calcMode="spline" keyTimes="%s" keySplines="%s" values="%s"/>
   </path>
   <ellipse cx="-8" cy="-60" rx="3.6" ry="8.5" fill="#fff" opacity=".28"><animate attributeName="opacity" dur="%.1fs" repeatCount="indefinite" values=".18;.34;.2;.3;.18"/></ellipse>
  </g>''' % (k, k, vals.split(";")[0].strip(), t, poczatek, kt, ks, vals, brz.split(";")[0], t, poczatek, kt, ks, brz, t * .7))
        defs.append('  <radialGradient id="mieso%d" cx="0" cy="-30" r="78" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#FFBFCB"/>'
                    '<stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="#C24560"/></radialGradient>' % (k, rozowe[k]))
        amp = R.uniform(6, 11)
        css.append(" .w%d{animation:wij%d %.1fs cubic-bezier(.45,.05,.4,.95) -%.1fs infinite alternate}\n @keyframes wij%d{0%%{transform:rotate(%.1fdeg) scale(1,1)}"
                   "38%%{transform:rotate(%.1fdeg) scale(1.03,.97)}71%%{transform:rotate(%.1fdeg) scale(.98,1.03)}100%%{transform:rotate(%.1fdeg) scale(1.05,.95)}}" % (
                       k, k, KOLYS[k], R.uniform(0, KOLYS[k]), k, -amp, amp * R.uniform(.2, .6), -amp * R.uniform(.1, .5), amp))
        uzycia.append('<g transform="rotate(%d)%s"><g class="w w%d"><use href="#j%d" transform="scale(.9)"/></g></g>' % (
            k * 60 + R.uniform(-4, 4), " scale(-1,1)" if k % 2 else "", k, k))
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200" role="img" aria-label="Halucynacje — logo: sześć wijących się języków wokół ust. Kwiatek czy języki?">
<title>Halucynacje</title>
<defs>
 <radialGradient id="gardlo" cx="0" cy="0" r="30" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#1A0509"/><stop offset=".75" stop-color="#3D0D18"/><stop offset="1" stop-color="#5A1424"/>
 </radialGradient>
%s
</defs>
<style>
 .w{transform-origin:0 0}
%s
 @media (prefers-reduced-motion:reduce){.w{animation:none}}
</style>
%s
<!-- usta: wargi wokół gardła -->
<circle r="27" fill="url(#gardlo)"/>
<path d="M -30 0 C -30 -18 -16 -30 0 -24 C 16 -30 30 -18 30 0 C 30 20 14 31 0 31 C -14 31 -30 20 -30 0 Z" fill="none" stroke="#C8304D" stroke-width="7" stroke-linejoin="round"/>
<path d="M -22 -12 C -12 -20 -4 -18 0 -14 C 4 -18 12 -20 22 -12" fill="none" stroke="#FF9AAD" stroke-width="1.6" stroke-linecap="round" opacity=".7"/>
</svg>
''' % ("\n".join(defs), "\n".join(css), "\n".join(uzycia))
    p = os.path.join(TU, "static", "logo.svg")
    open(p, "w", encoding="utf-8", newline="\n").write(svg)
    print(p, len(svg), "B")


if __name__ == "__main__":
    main()
