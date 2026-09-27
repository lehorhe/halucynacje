# Świat 3D w innych silnikach

Świat jest budowany proceduralnie z danych (`blender/dane/scena.json` + `blender/dane/wysokosc.npy`), a nie modelowany ręcznie. Do innych silników są dwie drogi:

## A. Gotowy model glTF 2.0

`blender/eksport/halucynacje_swiat_pelny.glb` (ok. 30 MB: teren z teksturą, 1560 domów, 62 latarnie, las, świecące lasery) i `halucynacje_swiat_web.glb` (ok. 6 MB, bez lasu).

| Silnik | Import |
|---|---|
| **Unreal Engine 5.8** | przeciągnij `.glb` do Content Browser (Interchange glTF). Lasery mają materiał emisyjny (`KHR_materials_emissive_strength`); poświatę daje Bloom w Post Process Volume. |
| **Unity 6** | pakiet `com.unity.cloud.gltfast` → przeciągnij `.glb` do Assets. Emisja: włącz Bloom w Volume (URP/HDRP). |
| **Godot 4** | skopiuj `.glb` do projektu — import natywny. Emisja: `WorldEnvironment` → Glow. |
| **Przeglądarka** | `<model-viewer src="halucynacje_swiat_web.glb">` albo three.js `GLTFLoader` (strona `/swiat3d` na gra.l00p.ai). |

Układ: glTF ma oś Y w górę; 1 jednostka = 1 m; heks ≈ 125 m (1 mm planszy = 5 m).

## B. Przepis sceny (zbuduj świat sam)

| Plik | Do czego |
|---|---|
| `blender/eksport/wysokosc_16bit.png` + `wysokosc_16bit.json` | mapa wysokości 16-bit: Landscape (UE), Terrain (Unity), HeightMapShape3D / Terrain3D (Godot). Zakres metrów: `min_m`, `max_m`. |
| `blender/dane/albedo_bez_linii.png` | kolor terenu (ta sama projekcja co mapa wysokości) |
| `blender/eksport/obiekty.json` | `domy` (x, y, z, obrót), `drzewa` (x, y, z, wariant), `latarnie` (x, y, z, `na_morzu`), `wysepki`, `lasery` (punkty a→b, kategoria), `kolory_laserow`, `poziom_wody_m` |

Współrzędne w `obiekty.json`: metry, X na wschód (kolumny = dni), Y na północ (późniejsze godziny mają ujemne Y), Z w górę — jak w Blenderze. W silnikach Y-up zamień (x, y, z) → (x, z, −y).

Instancjonowanie: domy i drzewa jako Hierarchical Instanced Static Mesh (UE), GPU instancing / `Graphics.RenderMeshInstanced` (Unity), `MultiMeshInstance3D` (Godot). Lasery: cienkie walce z materiałem emisyjnym w kolorze `kolory_laserow[kategoria]`, 40 m nad terenem.

## Zgodność

Po każdej zmianie danych: `python test_zgodnosci.py` — sprawdza, że świat 3D i plansza 2D się nie różnią (T1–T6).
