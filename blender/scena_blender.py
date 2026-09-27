# -*- coding: utf-8 -*-
"""Scena Blendera z danych mapy prawdy (blender/dane/*). Uruchamianie bez GUI:
    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P blender/scena_blender.py -- [orto|dron|oba] [--szybko]
Kadry: (1) orto — widok z góry jak plansza, (2) dron — konkretny heks z wysokości 90 m (DJI klasy Mini: ogniskowa 24 mm ekwiw.).
Zasada: geometria i liczba obiektów wynikają z danych (scena.json) — nic nie jest dorysowane „z wyobraźni”."""
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np

TU = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(TU, "dane")
OUT = os.path.join(TU, "render")
os.makedirs(OUT, exist_ok=True)
ARG = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TRYB = ARG[0] if ARG else "oba"
SZYBKO = "--szybko" in ARG

S = json.load(open(os.path.join(D, "scena.json"), encoding="utf-8"))
OBIEKTY = {"domy": [], "latarnie": [], "wysepki": [], "lasery": [], "drzewa": []}      # przepis sceny dla innych silników (obiekty.json)
Z = np.load(os.path.join(D, "wysokosc.npy"))
PXM = S["px_na_mm"] / S["skala_m_na_mm"]          # piksele rastra na metr
H, W = Z.shape
POZIOM_WODY = 0.4


def wys(x, y):
    c, r = min(W - 1, max(0, int(x * PXM))), min(H - 1, max(0, int(-y * PXM)))
    return float(Z[r, c])


def wyczysc():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(nazwa, kolor, szorst=0.8, metal=0.0, emisja=None):
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*kolor, 1)
    b.inputs["Roughness"].default_value = szorst
    b.inputs["Metallic"].default_value = metal
    if emisja:
        b.inputs["Emission Color"].default_value = (*emisja, 1)
        b.inputs["Emission Strength"].default_value = 6.0
    return m


def teren(krok=2):
    zz = Z[::krok, ::krok]
    h, w = zz.shape
    ys, xs = np.mgrid[0:h, 0:w]
    v = np.stack([xs * krok / PXM, -ys * krok / PXM, zz], -1).reshape(-1, 3).astype(np.float32)
    i = (ys[:-1, :-1] * w + xs[:-1, :-1]).ravel()
    quads = np.stack([i, i + 1, i + w + 1, i + w], -1).astype(np.int32)
    me = bpy.data.meshes.new("teren")
    me.vertices.add(len(v))
    me.vertices.foreach_set("co", v.ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
    me.update(calc_edges=True)
    uv = me.uv_layers.new(name="UV")
    vi = quads.ravel()
    u = (vi % w) / (w - 1)
    vv = 1 - (vi // w) / (h - 1)
    uv.data.foreach_set("uv", np.stack([u, vv], -1).astype(np.float32).ravel())
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("Teren", me)
    bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new("Teren")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(D, "albedo_bez_linii.png"))
    tx.interpolation = "Cubic"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    # drobna faktura (trawa/ziemia) — tylko relief światła, kolor zostaje z danych
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 180.0
    bm = nt.nodes.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    me.materials.append(m)
    return ob


def woda():
    sx, sy = S["rozmiar_m"]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(sx / 2, -sy / 2, POZIOM_WODY))
    ob = bpy.context.object
    ob.name = "Woda"
    ob.scale = (sx, sy, 1)
    m = material("Woda", (0.03, 0.2, 0.28), szorst=0.05)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Alpha"].default_value = 0.72
    for atr, wart in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, atr, wart)
        except (AttributeError, TypeError):
            pass
    b.inputs["Specular IOR Level"].default_value = 0.8
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 60.0
    nz.inputs["Detail"].default_value = 8.0
    bm = nt.nodes.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = 0.12
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    ob.data.materials.append(m)


def dom_mesh():
    """Dom 8 × 11 m, ściany 5,5 m, dach dwuspadowy do 9 m; dwa materiały: ściany i dach."""
    me = bpy.data.meshes.new("dom")
    bm_ = bmesh.new()
    a, b, h, g = 4.0, 5.5, 5.5, 9.0
    v = [bm_.verts.new(p) for p in [(-a, -b, 0), (a, -b, 0), (a, b, 0), (-a, b, 0), (-a, -b, h), (a, -b, h), (a, b, h), (-a, b, h), (0, -b, g), (0, b, g)]]
    sc = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1)]
    for f in sc:
        bm_.faces.new([v[k] for k in f]).material_index = 0
    for f in [(4, 5, 8), (6, 7, 9)]:
        bm_.faces.new([v[k] for k in f]).material_index = 0
    for f in [(4, 8, 9, 7), (5, 6, 9, 8)]:
        bm_.faces.new([v[k] for k in f]).material_index = 1
    bm_.to_mesh(me)
    bm_.free()
    me.materials.append(material("Sciany", (0.93, 0.9, 0.84), 0.7))
    me.materials.append(material("Dach", (0.55, 0.16, 0.1), 0.6))
    return me


def drzewo_mesh(nazwa, r, wys_):
    bm_ = bmesh.new()
    bmesh.ops.create_cone(bm_, cap_ends=True, segments=7, radius1=r, radius2=0.0, depth=wys_ * 0.8,
                          matrix=__import__("mathutils").Matrix.Translation((0, 0, wys_ * 0.2 + wys_ * 0.4)))
    bmesh.ops.create_cone(bm_, cap_ends=True, segments=5, radius1=r * 0.12, radius2=r * 0.12, depth=wys_ * 0.25,
                          matrix=__import__("mathutils").Matrix.Translation((0, 0, wys_ * 0.12)))
    me = bpy.data.meshes.new(nazwa)
    bm_.to_mesh(me)
    bm_.free()
    me.materials.append(material("Iglaste", (0.11, 0.29, 0.1), 0.85))
    return me


def drzewa():
    col = bpy.data.collections.new("Drzewa")
    bpy.context.scene.collection.children.link(col)
    wzory = [drzewo_mesh("drzewo_a", 3.2, 14), drzewo_mesh("drzewo_b", 4.0, 18), drzewo_mesh("drzewo_c", 2.6, 11)]
    pkt = S["drzewa"][::3] if SZYBKO else S["drzewa"][::2]
    rnd = random.Random(5)
    for k, wz in enumerate(wzory):
        sub = [(x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.5, 1.5), z) for x, y, z in pkt[k::3]]
        OBIEKTY["drzewa"] += [[round(x, 1), round(y, 1), round(z, 1), k] for x, y, z in sub]
        me = bpy.data.meshes.new("punkty_%d" % k)
        me.from_pydata([(x, y, z) for x, y, z in sub], [], [])
        rodzic = bpy.data.objects.new("Las_%d" % k, me)
        rodzic.instance_type = "VERTS"
        col.objects.link(rodzic)
        dz = bpy.data.objects.new("drzewo_%d" % k, wz)
        dz.parent = rodzic
        col.objects.link(dz)


def osady(dom):
    rnd = random.Random(12)
    col = bpy.data.collections.new("Osady")
    bpy.context.scene.collection.children.link(col)
    for h in S["heksy"]:
        n = h["domy"] * 4
        for k in range(n):
            ang = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(6, 26)
            x, y = h["x"] + 18 + r * math.cos(ang), h["y"] - 10 + r * math.sin(ang)
            ob = bpy.data.objects.new("dom", dom)
            ob.location = (x, y, wys(x, y) - 0.3)
            OBIEKTY["domy"].append({"i": h["i"], "j": h["j"], "x": round(x, 1), "y": round(y, 1), "z": round(ob.location.z, 1), "obrot": round(ob.rotation_euler.z if False else 0, 2)})
            ob.rotation_euler = (0, 0, rnd.choice([0, math.pi / 2]) + rnd.uniform(-0.2, 0.2))
            OBIEKTY["domy"][-1]["obrot"] = round(ob.rotation_euler.z, 3)
            col.objects.link(ob)


def latarnie():
    biel = material("Latarnia_biel", (0.95, 0.95, 0.93), 0.5)
    czerw = material("Latarnia_czerw", (0.72, 0.08, 0.06), 0.5)
    lamp = material("Latarnia_lampa", (1, 0.85, 0.5), 0.2, emisja=(1, 0.8, 0.45))
    for h in S["heksy"]:
        if not h["latarnia"]:
            continue
        x, y = h["x"] - 30, h["y"] + 8
        z0 = wys(x, y) - 0.5
        if not h["lad"]:                                   # latarnia na morzu (jak w 2D): stoi na skalistej wysepce
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=9, location=(x, y, POZIOM_WODY - 3))
            wy = bpy.context.object
            wy.scale = (1.3, 1.0, 0.55)
            wy.data.materials.append(material("Skala", (0.38, 0.36, 0.33), 0.95))
            OBIEKTY["wysepki"].append([round(x, 1), round(y, 1)])
            z0 = POZIOM_WODY + 1.2
        OBIEKTY["latarnie"].append({"i": h["i"], "j": h["j"], "x": round(x, 1), "y": round(y, 1), "z": round(z0, 1), "na_morzu": not h["lad"]})
        for k in range(5):
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=3.2 - k * 0.3, radius2=3.2 - (k + 1) * 0.3, depth=5, location=(x, y, z0 + 2.5 + 5 * k))
            bpy.context.object.data.materials.append(czerw if k % 2 else biel)
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.6, depth=2.4, location=(x, y, z0 + 26.2))
        bpy.context.object.data.materials.append(lamp)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=2.2, radius2=0, depth=2.2, location=(x, y, z0 + 28.5))
        bpy.context.object.data.materials.append(czerw)


KOLOR_LASERA = {"pub": (1.0, 0.45, 0.0), "muz": (1.0, 0.0, 0.02), "kult": (0.0, 1.0, 0.1), "zagr": (0.0, 0.85, 1.0),
                "info": (0.0, 0.15, 1.0), "styl": (0.05, 0.25, 1.0), "wiara": (0.6, 0.0, 1.0), None: (0.9, 0.93, 1.0)}
NAD_TERENEM = 40.0          # m: lustra nad drzewami (≤ 18 m) i latarniami (≈ 30 m)
WSUNIECIE = 0.955           # obwód heksu lekko do środka: sąsiednie heksy = dwie równoległe wiązki


def lasery():
    """Heksy jako wiązki laserów między lustrami na niewidzialnych wieżach w wierzchołkach. Każda wiązka: świecący pręt (widać go z góry
    w dzień) + prostokątne światło powierzchniowe w jej kolorze skierowane w dół — barwi korony drzew i dachy pod spodem."""
    import mathutils
    from collections import defaultdict
    siatki = defaultdict(bmesh.new)
    lustra = bmesh.new()
    r_ = S["heks_R_m"]
    n_swiatel = 0
    for h in S["heksy"]:
        kol = KOLOR_LASERA.get(h.get("kategoria"), KOLOR_LASERA[None])
        cx, cy = h["x"], h["y"]
        pts = []
        for vx, vy in h["wierzcholki"]:
            x, y = cx + (vx - cx) * WSUNIECIE, cy + (vy - cy) * WSUNIECIE
            zmax = max(wys(x + dx, y + dy) for dx in (-25, 0, 25) for dy in (-25, 0, 25))      # wieża ponad najwyższym punktem okolicy
            pts.append(mathutils.Vector((x, y, max(zmax, POZIOM_WODY) + NAD_TERENEM)))
        for a, b in zip(pts, pts[1:] + pts[:1]):
            d = b - a
            srodek = (a + b) / 2
            rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
            OBIEKTY["lasery"].append({"i": h["i"], "j": h["j"], "kategoria": h.get("kategoria"), "a": [round(v, 1) for v in a], "b": [round(v, 1) for v in b]})
            bmesh.ops.create_cone(siatki[h.get("kategoria")], cap_ends=False, segments=6, radius1=0.9, radius2=0.9, depth=d.length,
                                  matrix=mathutils.Matrix.Translation(srodek) @ rot)
            sw = bpy.data.lights.new("laser_swiatlo", "AREA")
            sw.shape = "RECTANGLE"
            sw.size, sw.size_y = d.length, 3.0
            sw.color = kol
            sw.energy = 5000.0
            sw.use_shadow = False                                         # poblask bez cieni: szybko i bez przepełnienia bufora cieni
            try:
                sw.spread = math.radians(70)
            except AttributeError:
                pass
            ob = bpy.data.objects.new("laser_swiatlo", sw)
            ob.location = srodek - mathutils.Vector((0, 0, 1.2))
            ob.rotation_euler = (0, 0, math.atan2(d.y, d.x))                  # obszar w płaszczyźnie XY, świeci w dół (-Z)
            bpy.context.scene.collection.objects.link(ob)
            n_swiatel += 1
        for p_ in pts:                                                       # lustro: mała tarcza, jedyny widoczny ślad wieży
            bmesh.ops.create_circle(lustra, cap_ends=True, segments=10, radius=2.2, matrix=mathutils.Matrix.Translation(p_))
    for kat, bm_ in siatki.items():
        me = bpy.data.meshes.new("laser_%s" % kat)
        bm_.to_mesh(me)
        bm_.free()
        m = bpy.data.materials.new("Laser_%s" % kat)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == "BSDF_PRINCIPLED":
                nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*KOLOR_LASERA.get(kat, KOLOR_LASERA[None]), 1)
        em.inputs["Strength"].default_value = 3.0
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        me.materials.append(m)
        ob = bpy.data.objects.new("Lasery_%s" % kat, me)
        ob.visible_shadow = False
        bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new("lustra")
    lustra.to_mesh(me)
    lustra.free()
    me.materials.append(material("Lustro", (0.9, 0.92, 0.95), 0.05, metal=1.0))
    bpy.context.scene.collection.objects.link(bpy.data.objects.new("Lustra", me))
    print("lasery: %d wiązek" % n_swiatel, flush=True)


def poswiata():
    """Kompozytor: poświata (glare) wokół wiązek — laser widać z góry w pełnym słońcu."""
    sc = bpy.context.scene
    try:
        ng = bpy.data.node_groups.new("Poswiata", "CompositorNodeTree")
        sc.compositing_node_group = ng
        wej = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        wyj = ng.nodes.new("NodeGroupOutput")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        for atr, wart in (("glare_type", "BLOOM"), ("quality", "HIGH")):
            try:
                setattr(gl, atr, wart)
            except (AttributeError, TypeError):
                pass
        for nazwa, wart in (("Threshold", 0.9), ("Strength", 0.55), ("Size", 0.45)):
            if nazwa in gl.inputs:
                gl.inputs[nazwa].default_value = wart
        ng.links.new(wej.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], wyj.inputs[0])
    except Exception as ex:                                                    # starsze API kompozytora
        print("poświata: pomijam (%s)" % ex, flush=True)


def swiat(dron):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Niebo")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1) if not dron else (0.62, 0.6, 0.62, 1)
    bg.inputs["Strength"].default_value = 0.8 if not dron else 0.5
    sc.world = w
    sl = bpy.data.lights.new("Slonce", "SUN")
    sl.energy = 4.2 if not dron else 7.0
    sl.angle = math.radians(1.2)
    sl.color = (1.0, 0.97, 0.92) if not dron else (1.0, 0.82, 0.62)
    ob = bpy.data.objects.new("Slonce", sl)
    sc.collection.objects.link(ob)
    # plansza: niskie światło z północnego zachodu (jak cieniowanie 2D); dron: złota godzina z zachodu
    ob.rotation_euler = (math.radians(58), 0, math.radians(135)) if not dron else (math.radians(79), 0, math.radians(240))


def silnik(szer, wys_):
    sc = bpy.context.scene
    for nazwa in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = nazwa
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y = szer, wys_
    sc.render.resolution_percentage = 50 if SZYBKO else 100
    try:
        sc.eevee.taa_render_samples = 16 if SZYBKO else 64
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.view_settings.exposure = 0.35 if sc.camera and sc.camera.data.type != "ORTHO" else 0.0
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"


def kamera_orto():
    sx, sy = S["rozmiar_m"]
    c = bpy.data.cameras.new("Orto")
    c.type = "ORTHO"
    c.ortho_scale = max(sx, sy)
    c.clip_end = 5000
    ob = bpy.data.objects.new("Kamera_orto", c)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (sx / 2, -sy / 2, 1500)
    bpy.context.scene.camera = ob
    return int(2400 * sx / max(sx, sy)), int(2400 * sy / max(sx, sy))


def kamera_dron():
    import mathutils
    cel = S["dron_cel"]
    tx, ty = cel["x"], cel["y"]
    tz = wys(tx, ty)
    c = bpy.data.cameras.new("Dron")
    c.lens, c.sensor_width = 24, 36            # 24 mm ekwiwalentu pełnej klatki (DJI Mini 4 Pro)
    c.clip_end = 6000
    ob = bpy.data.objects.new("Kamera_dron", c)
    bpy.context.scene.collection.objects.link(ob)
    # 90 m nad terenem, ok. 115 m od środka heksu, od strony słońca na tle (lekko pod światło daje głębię)
    ob.location = (tx + 70, ty - 92, tz + 90)
    kier = mathutils.Vector((tx, ty, tz + 4)) - ob.location
    ob.rotation_euler = kier.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return 3000, 2000


def eksport(web=False):
    """Przenośny świat: glTF 2.0 (.glb) — UE 5.8 (Interchange), Unity (glTFast), Godot 4 (natywnie), przeglądarka (model-viewer/three.js).
    Plus „przepis”: mapa wysokości 16-bit PNG, albedo i obiekty.json — każdy silnik może zbudować scenę sam (teren + instancje)."""
    wyczysc()
    teren(krok=8 if web else 2)
    woda()
    if not web:
        drzewa()
    osady(dom_mesh())
    latarnie()
    lasery_bez_swiatel = True
    lasery()
    for ob in list(bpy.data.objects):                    # światła powierzchniowe laserów nie istnieją w glTF — zostaje świecąca wiązka
        if ob.type == "LIGHT":
            bpy.data.objects.remove(ob)
    ex = os.path.join(TU, "eksport")
    os.makedirs(ex, exist_ok=True)
    plik = os.path.join(ex, "halucynacje_swiat_%s.glb" % ("web" if web else "pelny"))
    bpy.ops.export_scene.gltf(filepath=plik, export_format="GLB", export_apply=True, export_lights=False, export_cameras=False)
    print("GLB", plik, os.path.getsize(plik) // 1024, "KB", flush=True)
    if not web:
        json.dump({"uklad": "metry; X na wschód (kolumny = dni), Y na północ (w dół mapy = późniejsze godziny ujemne), Z w górę; glTF zamienia na Y-up",
                   "zakres": S["zakres"], "rozmiar_m": S["rozmiar_m"], "poziom_wody_m": POZIOM_WODY, "lasery_nad_terenem_m": NAD_TERENEM,
                   "kolory_laserow": {str(k): v for k, v in KOLOR_LASERA.items()}, **OBIEKTY},
                  open(os.path.join(ex, "obiekty.json"), "w", encoding="utf-8"), ensure_ascii=False)
        zz = Z - Z.min()
        h16 = (zz / max(1e-6, zz.max()) * 65535).astype(np.uint16)
        img = bpy.data.images.new("wysokosc16", W, H, alpha=False, float_buffer=True)
        img.pixels.foreach_set(np.repeat((h16[::-1] / 65535.0).astype(np.float32)[..., None], 4, axis=2).ravel())
        img.filepath_raw = os.path.join(ex, "wysokosc_16bit.png")
        img.file_format = "PNG"
        img.save_render(img.filepath_raw, scene=None) if False else None
        sc = bpy.context.scene
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_depth = "16"
        sc.render.image_settings.color_mode = "BW"
        img.save_render(filepath=img.filepath_raw, scene=sc)
        json.dump({"min_m": float(Z.min()), "max_m": float(Z.max()), "px_na_m": PXM, "szer_px": W, "wys_px": H},
                  open(os.path.join(ex, "wysokosc_16bit.json"), "w"))


def main():
    if TRYB == "glb":
        eksport(web=False)
        eksport(web=True)
        return
    for kadr in (["orto", "dron"] if TRYB == "oba" else [TRYB]):
        wyczysc()
        teren()
        woda()
        drzewa()
        osady(dom_mesh())
        latarnie()
        lasery()
        swiat(kadr == "dron")
        poswiata()
        szer, wys_ = kamera_orto() if kadr == "orto" else kamera_dron()
        silnik(szer, wys_)
        bpy.context.scene.render.filepath = os.path.join(OUT, "kadr_%s%s.png" % (kadr, "_szkic" if SZYBKO else ""))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scena_%s.blend" % kadr))
        bpy.ops.render.render(write_still=True)
        print("RENDER", kadr, bpy.context.scene.render.filepath, flush=True)


main()
