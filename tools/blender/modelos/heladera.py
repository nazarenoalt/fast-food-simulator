"""Modelo: heladera bajo mesada (id `heladera`, etapa 4; todavía sin dato en accesorios.ron).
Para la cadena de frío de la hoja de ruta (medallones y chorizos).

Genera:
    arte/fuentes/cocina/heladera.blend
    godot/modelos/cocina/heladera.glb
    docs/arte/revisiones/heladera.jpg

Uso:
    blender -b -P tools/blender/modelos/heladera.py
    python tools/blender/modelos/heladera.py

Forma: heladera chica de piso (como las bajo mesada de los bares): mueble blanco crema con
tapa de acero arriba, zócalo negro (la rejilla del motor) y la puerta del lado del vendedor
(−Z), con burlete negro, tirador vertical de acero del lado −X y bisagras del lado +X.
Adentro: el hueco (paredes de 4 cm) con 2 estantes de acero: 3 niveles, 2 lugares por nivel.

Medidas (lista: ≈ 0,60 × 0,85 × 0,55): 0,60 × 0,85 × 0,55 justos (del tirador al fondo).
- Hueco: 0,52 × 0,69 × 0,44 (de y = 0,10 a 0,79). Estantes arriba a 0,336 y 0,566.
- Lugares (2 por nivel, en x = ±0,13, z = 0), de arriba hacia abajo y de −X a +X, como el
  estante de depósito: (−0,13; 0,566; 0), (0,13; 0,566; 0), (−0,13; 0,336; 0),
  (0,13; 0,336; 0), (−0,13; 0,10; 0), (0,13; 0,10; 0). Entran 22 cm de alto por nivel (la
  caja de medallones mide 8 cm; la bandeja de chorizos, 5).

Objetos (hijos del Empty `heladera`, origen = centro de la base del mueble con la puerta
cerrada, a nivel del piso):
- `heladera_cuerpo`: mueble, tapa, zócalo y estantes (BlancoCrema, Acero, PlasticoNegro).
- `pieza_puerta`: la puerta (panel, burlete, tirador y bisagras). **Origen en el eje de las
  bisagras** (0,30; 0,06; −0,225), eje vertical: el juego la abre girándola en Y
  (rotation.y negativo abre hacia el vendedor; abierta ≈ −100°).
- `punto_lugar_1..6`: los lugares de depósito, sobre el piso y los estantes.
- `heladera-colonly`: el mueble hueco (fondo, costados, techo, piso y estantes: varias cajas,
  como el estante de depósito) para que los paquetes entren y se apoyen.
  `heladera_puerta-colonly`: la puerta, hija de `pieza_puerta` para que la siga (guía v1.5).

Chequeo de origen propio: el tirador sale solo hacia el vendedor y corre la caja total; se
mide el mueble con la puerta cerrada (0,60 × 0,52) centrado en el origen.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "heladera"
FAMILIA = "cocina"
PRESUPUESTO = 1000  # lista de modelos
CREMA, ACERO, NEGRO = range(3)

W, H = 0.60, 0.85
Z_FONDO, Z_BOCA = 0.26, -0.22        # atrás del mueble / cara de adelante (vendedor)
Z_PUERTA = -0.26                     # cara de afuera de la puerta
Y_ZOCALO, Y_MUEBLE = 0.06, 0.83      # el mueble va de 0,06 a 0,83; la tapa de acero hasta 0,85
PARED = 0.04
HUECO_Y = (Y_ZOCALO + PARED, Y_MUEBLE - PARED)    # 0,10 a 0,79
ESTANTES_Y = (0.33, 0.56)            # centro de los estantes (arriba a +0,006)
ESP_ESTANTE = 0.012
LUGARES_X = (-0.13, 0.13)
TIRADOR_Z = -0.281                   # centro de la barra del tirador
BISAGRA = (W / 2, Y_ZOCALO, Z_BOCA - 0.005)

MEDIDAS = (W, H, Z_FONDO - (TIRADOR_Z - 0.009))


def lugares():
    niveles = [y + ESP_ESTANTE / 2 for y in reversed(ESTANTES_Y)] + [HUECO_Y[0]]
    return [(x, round(y, 4), 0.0) for y in niveles for x in LUGARES_X]


def construir():
    crema, acero, negro = comun.cargar_materiales("M_BlancoCrema", "M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    # Mueble: una caja con bisel y el hueco hundido desde la cara del vendedor.
    alto = Y_MUEBLE - Y_ZOCALO
    prof = Z_FONDO - Z_BOCA
    caras = piezas.caja(bm, (W, alto, prof), (0, Y_ZOCALO + alto / 2, (Z_FONDO + Z_BOCA) / 2),
                        mat=CREMA, bisel=0.01)
    for f in caras:
        f.normal_update()
    boca = next(f for f in caras if f.normal.dot(g2b((0, 0, -1))) > 0.999)
    arriba = next(f for f in caras if f.normal.dot(g2b((0, 1, 0))) > 0.999)
    abajo = next(f for f in caras if f.normal.dot(g2b((0, -1, 0))) > 0.999)
    bmesh.ops.delete(bm, geom=[arriba, abajo], context="FACES_ONLY")  # tapadas por la tapa y el zócalo
    bmesh.ops.inset_region(bm, faces=[boca], thickness=PARED - 0.01, depth=0.0)
    ext = bmesh.ops.extrude_face_region(bm, geom=[boca])
    nuevos = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=g2b((0, 0, prof - PARED)), verts=nuevos)
    if boca.is_valid:  # la cara original queda tapando la boca: se borra
        bmesh.ops.delete(bm, geom=[boca], context="FACES_ONLY")
    for f in bm.faces:
        f.material_index = CREMA
    # Tapa de acero y zócalo negro (metido 3 cm del lado del vendedor).
    piezas.caja(bm, (W, H - Y_MUEBLE, Z_FONDO - Z_PUERTA), (0, (H + Y_MUEBLE) / 2, (Z_FONDO + Z_PUERTA) / 2),
                mat=ACERO, bisel=0.006)
    caras = piezas.caja(bm, (W - 0.04, Y_ZOCALO + 0.002, prof - 0.04),
                        (0, (Y_ZOCALO + 0.002) / 2, (Z_FONDO + Z_BOCA) / 2 + 0.01), mat=NEGRO, bisel=0.004,
                        sin_abajo=True)
    eq.borrar_caras(bm, caras, (0, 1, 0))
    # Rejilla: tres listones de acero sobre el zócalo, del lado del vendedor.
    z_zocalo = (Z_FONDO + Z_BOCA) / 2 + 0.01 - (prof - 0.04) / 2
    for i in range(3):
        piezas.caja(bm, (W - 0.12, 0.008, 0.006), (0, 0.016 + i * 0.014, z_zocalo - 0.0025), mat=ACERO)
    # Estantes de acero (encastrados 1 mm en los costados del hueco).
    for y in ESTANTES_Y:
        piezas.caja(bm, (W - 2 * PARED + 0.002, ESP_ESTANTE, prof - PARED - 0.03),
                    (0, y, Z_BOCA + 0.03 + (prof - PARED - 0.03) / 2), mat=ACERO, bisel=0.003)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [crema, acero, negro])

    # Puerta: panel crema, burlete negro atrás, tirador vertical de acero en −X, bisagras en +X.
    bm = bmesh.new()
    y0, y1 = Y_ZOCALO + 0.005, Y_MUEBLE - 0.005
    zc = (Z_PUERTA + Z_BOCA - 0.005) / 2
    piezas.caja(bm, (W, y1 - y0, Z_BOCA - 0.005 - Z_PUERTA), (0, (y0 + y1) / 2, zc), mat=CREMA, bisel=0.01)
    piezas.caja(bm, (W - 0.06, y1 - y0 - 0.06, 0.006), (0, (y0 + y1) / 2, Z_BOCA - 0.003), mat=NEGRO)
    xt = -W / 2 + 0.05
    for yt in (0.47, 0.73):
        piezas.caja(bm, (0.018, 0.024, 0.022), (xt, yt, Z_PUERTA - 0.009), mat=ACERO, bisel=0.004)
    piezas.cilindro(bm, 0.009, 0.32, (xt, 0.60, TIRADOR_Z), lados=12, mat=ACERO)
    for yb in (y0 + 0.03, y1 - 0.03):
        piezas.caja(bm, (0.02, 0.04, 0.008), (W / 2 - 0.014, yb, Z_PUERTA - 0.002), mat=ACERO, bisel=0.003)
    puerta = eq.objeto_en("pieza_puerta", bm, [crema, acero, negro], BISAGRA)
    eq.e2.suavizar_hasta(puerta, 31)

    puntos = [piezas.punto(f"punto_lugar_{i + 1}", p) for i, p in enumerate(lugares())]
    ancho_h = W - 2 * PARED
    col = eq.colision_cajas(ID, [
        ((W, H - Y_MUEBLE + PARED, Z_FONDO - Z_PUERTA), (0, (H + Y_MUEBLE - PARED) / 2, (Z_FONDO + Z_PUERTA) / 2)),
        ((W, HUECO_Y[0], prof), (0, HUECO_Y[0] / 2, (Z_FONDO + Z_BOCA) / 2)),
        ((PARED, HUECO_Y[1] - HUECO_Y[0], prof), (-(W - PARED) / 2, sum(HUECO_Y) / 2, (Z_FONDO + Z_BOCA) / 2)),
        ((PARED, HUECO_Y[1] - HUECO_Y[0], prof), ((W - PARED) / 2, sum(HUECO_Y) / 2, (Z_FONDO + Z_BOCA) / 2)),
        ((ancho_h, HUECO_Y[1] - HUECO_Y[0], PARED), (0, sum(HUECO_Y) / 2, Z_FONDO - PARED / 2)),
    ] + [((ancho_h, ESP_ESTANTE, prof - PARED), (0, y, Z_BOCA + (prof - PARED) / 2)) for y in ESTANTES_Y])
    col_puerta = eq.colision_cajas(f"{ID}_puerta", [((W, y1 - y0, Z_BOCA - Z_PUERTA), (0, (y0 + y1) / 2,
                                                     (Z_PUERTA + Z_BOCA) / 2))], padre=puerta)
    raiz = piezas.raiz(ID, [cuerpo, puerta, col] + puntos)
    return {"raiz": raiz, "cuerpo": cuerpo, "puerta": puerta, "col": col, "col_puerta": col_puerta,
            "puntos": puntos}


def chequeo_origen(m):
    vs = [v for o in (m["cuerpo"], m["puerta"]) for v in eq.verts_godot(o) if v.z >= Z_PUERTA - 1e-5]
    cx = max(v.x for v in vs) + min(v.x for v in vs)
    cz = max(v.z for v in vs) + min(v.z for v in vs)
    base = min(v.y for v in vs)
    ok = abs(cx) < 1e-4 and abs(cz) < 1e-4 and abs(base) < 1e-4
    return ok, "Origen en el centro de la base del mueble con la puerta cerrada (el tirador corre la caja total)"


def chequeo_lugares(m):
    ok = all((p.location - g2b(l)).length < 1e-6 for p, l in zip(m["puntos"], lugares()))
    p = m["puerta"].location
    ok = ok and (p - g2b(BISAGRA)).length < 1e-6
    return ok, ("punto_lugar_1..6 sobre los estantes (0,336 y 0,566) y el piso del hueco (0,10); "
                "pieza_puerta con el origen en el eje de las bisagras")


def revisar(m):
    vis = [m["cuerpo"], m["puerta"]]
    res = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base", max_materiales=6)
    res = eq.reemplazar(res, "Origen", chequeo_origen(m))
    res.insert(1, chequeo_lugares(m))
    return res


def hoja(m, revision):
    import _etapa2 as e2
    comun.preparar_revision()
    vis = [m["cuerpo"], m["puerta"]]
    carton, = comun.cargar_materiales("M_Carton")
    cajas = []
    for i, p in enumerate(m["puntos"]):
        if i in (0, 3, 4):
            bm = bmesh.new()
            piezas.caja(bm, (0.22, 0.08, 0.22), (0, 0.04, 0), bisel=0.004)
            c = piezas.terminar(f"ref_caja_{i}", bm, [carton])
            c.location = p.location
            c.parent = m["raiz"]
            cajas.append(c)
    persona = bpy.data.objects["ref_persona_1,75m"]
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", vis, "frente", "dia"),
        ("Lado del vendedor: puerta, tirador y zócalo · día", vis, "vendedor", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
    ])
    m["puerta"].rotation_euler.z = math.radians(-100)   # Y de Godot = Z de Blender
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("Puerta abierta (−100°), cajas en lugares 1, 4 y 5", vis + cajas,
         "vendedor_frente", "dia", vis),
    ])
    barra = e2.barra_chica()
    m["raiz"].location = g2b((1.16, 0.0, -0.1))
    persona.location = g2b((-0.45, 0.0, -0.75))
    persona.hide_render = False
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("Al lado de la barra chica, con la silueta de 1,75 m · día", vis + cajas + barra + [persona],
         "vendedor", "dia", vis + barra + [persona], 1.0),
    ])
    m["puerta"].rotation_euler.z = 0
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("Al lado de la barra chica, cerrada · atardecer", vis + barra + [persona], "vendedor_alto",
         "atardecer", vis + barra, 1.0),
    ])
    comun.componer_hoja("heladera · 0,60 × 0,85 × 0,55 m, 6 lugares · equipo de cocina",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["cuerpo"], m["puerta"], m["col"], m["col_puerta"]] + m["puntos"])


if __name__ == "__main__":
    main()
