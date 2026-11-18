"""Modelo: tostador de pan de contacto (id `tostador`, etapa 4; todavía sin dato en
accesorios.ron). Para el "pan tostado" de la hoja de ruta.

Genera:
    arte/fuentes/cocina/tostador.blend
    godot/modelos/cocina/tostador.glb
    docs/arte/revisiones/tostador.jpg

Uso:
    blender -b -P tools/blender/modelos/tostador.py
    python tools/blender/modelos/tostador.py

Forma: tostadora de dos planchas (como las de bar, de "tostados"), mismo estilo que el
hervidor: base de acero sobre 4 patas negras con la plancha de abajo (M_MetalOscuro), y una
tapa de acero con la plancha de arriba, abisagrada del lado del cliente (+Z), con el mango
negro corrido del lado del vendedor (−Z), que es quien la abre. En la cara del vendedor de la
base: la perilla del termostato y la luz piloto.

Medidas (lista: ≈ 0,40 × 0,20 × 0,30): 0,40 × 0,20 × 0,30 justos, con la tapa cerrada
(del mango a la base).
- Superficie de trabajo (la plancha de abajo): 0,34 × 0,23 m, arriba a 0,10 m del apoyo,
  centrada en el origen. Ahí va `punto_superficie`. Con la tapa cerrada quedan 4 mm entre
  planchas: el pan levanta la tapa (eso lo resuelve el código).

Objetos (hijos del Empty `tostador`, origen = centro de la superficie, a nivel del mostrador):
- `tostador_cuerpo`: base, plancha de abajo, bisagras, perilla y patas.
- `pieza_tapa`: la tapa (acero, plancha de arriba y mango). **Origen en el eje de la
  bisagra** (0; 0,11; 0,13), con el eje sobre X: el juego la abre girándola en X
  (rotation.x positivo levanta el mango; abierta ≈ 75°).
- `pieza_piloto` (M_PilotoApagado): la lente de la luz piloto; el juego la enciende.
- `punto_superficie`: centro de la plancha de abajo (0; 0,10; 0).
- `tostador-colonly`: la base hasta la plancha (una caja). `tostador_tapa-colonly`: la tapa
  (una caja), hija de `pieza_tapa` para que la siga al abrirse (guía v1.5).

Chequeo de origen propio: el mango y la perilla salen solo hacia el vendedor y corren la caja
total; se mide la superficie centrada en el origen y la base a nivel del mostrador.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402

ID = "tostador"
FAMILIA = "cocina"
PRESUPUESTO = 1000  # lista de modelos
ACERO, OSCURO, NEGRO = range(3)

W = 0.40
Z_VEND, Z_CLI = -0.13, 0.14          # caras de la base
Y_PATA, Y_BASE = 0.015, 0.088
SUP = (0.34, 0.23)
Y_SUP = 0.10
BISAGRA = (0.11, 0.13)               # (y, z) del eje
TAPA_Y0, TAPA_Y1 = 0.112, 0.20       # carcasa de la tapa
TAPA_Z0, TAPA_Z1 = -0.118, 0.137
Y_CONTROLES = 0.05
PERILLA_X, PILOTO_X = -0.12, 0.12
MANGO_Z = -0.149                     # centro de la barra del mango
MANGO = (0.22, 0.022, 0.022)

MEDIDAS = (W, TAPA_Y1, Z_CLI - (MANGO_Z - MANGO[2] / 2))


def construir():
    acero, oscuro, negro, piloto_m = comun.cargar_materiales(
        "M_Acero", "M_MetalOscuro", "M_PlasticoNegro", "M_PilotoApagado")
    bm = bmesh.new()
    alto = Y_BASE - Y_PATA
    piezas.caja(bm, (W, alto, Z_CLI - Z_VEND), (0, Y_PATA + alto / 2, (Z_CLI + Z_VEND) / 2),
                mat=ACERO, bisel=0.005, sin_abajo=True)
    caras = piezas.caja(bm, (SUP[0] + 0.004, Y_SUP - Y_BASE + 0.002, SUP[1] + 0.004),
                        (0, (Y_SUP + Y_BASE - 0.002) / 2, 0), mat=OSCURO, bisel=0.002)
    eq.borrar_caras(bm, caras, (0, -1, 0))
    # Bisagras: dos orejas de acero atrás y el eje (de lado a lado de la oreja).
    yb, zb = BISAGRA
    for x in (-0.15, 0.15):
        caras = piezas.caja(bm, (0.03, yb - Y_BASE + 0.012, 0.018), (x, (yb + 0.012 + Y_BASE) / 2 - 0.002, zb),
                            mat=ACERO, bisel=0.004)
        eq.borrar_caras(bm, caras, (0, -1, 0))
    for x in (-0.15, 0.15):
        piezas.cilindro(bm, 0.006, 0.036, (x, yb, zb), eje="x", lados=8, mat=OSCURO)
    for x in (-0.16, 0.16):
        for z in (Z_VEND + 0.035, Z_CLI - 0.035):
            piezas.cilindro(bm, 0.012, Y_PATA + 0.002, (x, (Y_PATA + 0.002) / 2, z), lados=12, mat=NEGRO,
                            tapas=(False, False))
    eq.perilla(bm, PERILLA_X, Y_CONTROLES, Z_VEND, NEGRO)
    eq.aro_piloto(bm, PILOTO_X, Y_CONTROLES, Z_VEND, ACERO)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero, oscuro, negro])

    # Tapa: carcasa, plancha de arriba, mango corrido hacia el vendedor con dos soportes.
    bm = bmesh.new()
    piezas.caja(bm, (W - 0.02, TAPA_Y1 - TAPA_Y0, TAPA_Z1 - TAPA_Z0),
                (0, (TAPA_Y0 + TAPA_Y1) / 2, (TAPA_Z0 + TAPA_Z1) / 2), mat=0, bisel=0.006)
    caras = piezas.caja(bm, (SUP[0], 0.008 + 0.002, SUP[1]), (0, Y_SUP + 0.004 + 0.004, 0), mat=1,
                        bisel=0.002)
    eq.borrar_caras(bm, caras, (0, 1, 0))
    for x in (-0.08, 0.08):
        largo = TAPA_Z0 - MANGO_Z + 0.004
        caras = piezas.caja(bm, (0.016, 0.014, largo), (x, 0.15, TAPA_Z0 - largo / 2 + 0.004), mat=0,
                            bisel=0.004)
        eq.borrar_caras(bm, caras, (0, 0, 1))
    piezas.caja(bm, MANGO, (0, 0.15, MANGO_Z), mat=2, bisel=0.007)
    tapa = eq.objeto_en("pieza_tapa", bm, [acero, oscuro, negro], (0, yb, zb))

    piloto = eq.lente_piloto(PILOTO_X, Y_CONTROLES, Z_VEND, piloto_m)
    sup = piezas.punto("punto_superficie", (0, Y_SUP, 0))
    col = eq.colision_cajas(ID, [((W, Y_SUP, Z_CLI - Z_VEND), (0, Y_SUP / 2, (Z_CLI + Z_VEND) / 2))])
    col_tapa = eq.colision_cajas(f"{ID}_tapa", [((W - 0.02, TAPA_Y1 - Y_SUP - 0.004, TAPA_Z1 - TAPA_Z0),
                                                 (0, (TAPA_Y1 + Y_SUP + 0.004) / 2, (TAPA_Z0 + TAPA_Z1) / 2))],
                                 padre=tapa)
    raiz = piezas.raiz(ID, [cuerpo, tapa, piloto, sup, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "tapa": tapa, "piloto": piloto, "sup": sup, "col": col,
            "col_tapa": col_tapa}


def chequeo_bisagra(tapa):
    p = tapa.location
    ok = (Vector((p.x, -p.y, p.z)) - Vector((0, BISAGRA[1], BISAGRA[0]))).length < 1e-5
    return ok, "pieza_tapa con el origen en el eje de la bisagra (0; %.2f; %.2f), gira sobre X" % BISAGRA


def revisar(m):
    vis = [m["cuerpo"], m["tapa"], m["piloto"]]
    res = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base", max_materiales=6)
    sup = eq.chequeo_superficie(m["cuerpo"], OSCURO, SUP, Y_SUP, m["sup"])
    res = eq.reemplazar(res, "Origen", eq.chequeo_base(
        vis, "Origen en el centro de la superficie, a nivel del mostrador (mango y perilla corren la caja total)")
        if sup[0] else (False, "Origen: la superficie no está centrada"))
    res.insert(1, sup)
    res.insert(2, chequeo_bisagra(m["tapa"]))
    return res


def hoja(m, revision):
    import math
    comun.preparar_revision()
    vis = [m["cuerpo"], m["tapa"], m["piloto"]]
    pan = eq.ref_pan_hamburguesa("ref_pan")
    pan.location = piezas.g2b((0.0, Y_SUP + 0.0375, 0.0))
    cuadros = eq.e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", vis, "frente", "dia"),
        ("Lado del vendedor: mango, perilla y piloto · día", vis, "vendedor", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
    ])
    m["tapa"].rotation_euler.x = math.radians(75)  # Godot X = Blender X
    bpy.context.view_layer.update()
    cuadros += eq.e2.sacar_fotos([
        ("Tapa abierta (pieza_tapa a 75°), con un pan de referencia · día", vis + [pan], "vendedor", "dia"),
    ])
    import _etapa2 as e2
    barra = e2.barra_chica()
    m["raiz"].location = piezas.g2b((-0.4, 0.95, 0.0))
    pan.location += piezas.g2b((-0.4, 0.95, 0.0))
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("Sobre la barra chica (mostrador_izq), abierto · día", vis + [pan] + barra, "vendedor_alto", "dia",
         vis, 2.6),
    ])
    m["tapa"].rotation_euler.x = 0
    comun.componer_hoja("tostador · plancha 0,34 × 0,23 m a 0,10 m, tapa abisagrada · equipo de cocina",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["cuerpo"], m["tapa"], m["piloto"], m["sup"], m["col"],
                              m["col_tapa"]])


if __name__ == "__main__":
    main()
