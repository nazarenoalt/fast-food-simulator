"""Modelo: garrafa de gas de 10 kg (id `garrafa`, etapa 4; alimenta la plancha; todavía sin
dato en accesorios.ron).

Genera:
    arte/fuentes/cocina/garrafa.blend
    godot/modelos/cocina/garrafa.glb
    docs/arte/revisiones/garrafa.jpg

Uso:
    blender -b -P tools/blender/modelos/garrafa.py
    python tools/blender/modelos/garrafa.py

Forma: garrafa argentina de 10 kg, sin marca: cuerpo de chapa redondeado arriba y abajo,
aro de pie abajo y, arriba, el cuello protector partido en dos medias lunas (para agarrarla y
llegar a la válvula). Adentro del cuello, la válvula de acero (tuerca, salida de gas hacia
+X) con su volante negro. Pintada con M_AzulAcento (un color de la paleta: no se agregó un
"color garrafa"; si se la quiere roja, es cambiar el material, guía 4.2 regla 5).

Medidas (lista: Ø 0,30 × 0,55): 0,30 × 0,55 × 0,30 justos (16 lados: radio 0,15, guía 3.2).

Objetos (hijos del Empty `garrafa`, origen = centro de la base, a nivel del piso):
- `garrafa_cuerpo`: todo lo que se ve (AzulAcento, Acero, PlasticoNegro).
- `punto_valvula`: la punta de la salida de gas (para enganchar la manguera, si algún día
  se dibuja).
- `garrafa-colonly`: un cilindro de 16 lados de Ø 0,30 × 0,55.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "garrafa"
FAMILIA = "cocina"
PRESUPUESTO = 600  # lista de modelos
PINTURA, ACERO, NEGRO = range(3)
R, ALTO = 0.15, 0.55
LADOS = 16
MEDIDAS = (2 * R, ALTO, 2 * R)

CUERPO = [(0.12, 0.04), (0.145, 0.065), (R, 0.10), (R, 0.40), (0.143, 0.44), (0.12, 0.465),
          (0.085, 0.48), (0.04, 0.488), (0.0, 0.49)]
PIE = [(0.13, 0.0), (0.13, 0.045), (0.124, 0.05), (0.118, 0.045), (0.118, 0.0)]
CUELLO = (0.082, 0.088, 0.47, ALTO)   # radio de adentro, de afuera, abajo, arriba
CUELLO_ARCO = 55                      # cada media luna cubre ±55° alrededor de ±X
Y_VALVULA = 0.488
SALIDA = (0.045, 0.52, 0.0)           # punta de la salida de gas


def arco(bm, ri, ro, y0, y1, a0, a1, segs, mat):
    """Pedazo de tubo (Godot): de a0 a a1 grados alrededor de Y (0° = +X, 90° = +Z), cerrado."""
    def pt(r, a, y):
        t = math.radians(a)
        return bm.verts.new(g2b((r * math.cos(t), y, r * math.sin(t))))
    anillos = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        anillos.append([pt(ro, a, y0), pt(ro, a, y1), pt(ri, a, y1), pt(ri, a, y0)])
    caras = []
    for p, q in zip(anillos, anillos[1:]):
        for k in range(4):
            caras.append(bm.faces.new((p[k], p[(k + 1) % 4], q[(k + 1) % 4], q[k])))
    caras.append(bm.faces.new(anillos[0]))
    caras.append(bm.faces.new(list(reversed(anillos[-1]))))
    for f in caras:
        f.material_index = mat
    return caras


def construir():
    pintura, acero, negro = comun.cargar_materiales("M_AzulAcento", "M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    eq.e2.torno(bm, CUERPO, LADOS, mats=PINTURA)  # abajo queda tapado por el aro de pie
    eq.e2.torno(bm, PIE, LADOS, mats=PINTURA)
    ri, ro, y0, y1 = CUELLO
    for centro in (0, 180):
        arco(bm, ri, ro, y0, y1, centro - CUELLO_ARCO, centro + CUELLO_ARCO, 4, PINTURA)
    # Válvula: cuerpo, tuerca de 6 lados, salida de gas hacia +X y volante negro arriba.
    piezas.cilindro(bm, 0.014, 0.045, (0, Y_VALVULA + 0.0225 - 0.002, 0), lados=8, mat=ACERO,
                    tapas=(False, True))
    piezas.cilindro(bm, 0.021, 0.012, (0, Y_VALVULA + 0.012, 0), lados=6, mat=ACERO)
    largo = SALIDA[0] - 0.012
    piezas.cilindro(bm, 0.007, largo, (0.012 + largo / 2, SALIDA[1], 0), eje="x", lados=8, mat=ACERO,
                    tapas=(False, True))
    piezas.cilindro(bm, 0.026, 0.008, (0, Y_VALVULA + 0.045, 0), lados=12, mat=NEGRO)
    piezas.caja(bm, (0.04, 0.008, 0.008), (0, Y_VALVULA + 0.053, 0), mat=NEGRO, bisel=0.002)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [pintura, acero, negro])
    eq.e2.suavizar_hasta(cuerpo, 31)

    valvula = piezas.punto("punto_valvula", SALIDA)
    bm = bmesh.new()
    piezas.cilindro(bm, R, ALTO, (0, ALTO / 2, 0), lados=LADOS)
    col = eq.colision_cajas(ID, [])
    bm.to_mesh(col.data)
    bm.free()
    raiz = piezas.raiz(ID, [cuerpo, valvula, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "valvula": valvula, "col": col}


def revisar(m):
    return comun.revisar([m["cuerpo"]], PRESUPUESTO, MEDIDAS, origen="base")


def hoja(m, revision):
    import _etapa2 as e2
    import plancha
    comun.preparar_revision()
    vis = [m["cuerpo"]]
    cuadros = e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("Arriba: cuello y válvula · día", vis, "arriba", "dia"),
        ("Desde el vendedor · día", vis, "vendedor", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
    ])
    # En el piso, del lado del vendedor, debajo de la plancha (en mostrador_izq).
    barra = e2.barra_chica()
    p = plancha.construir()
    p["raiz"].location = g2b((-0.4, 0.95, 0.0))
    m["raiz"].location = g2b((-0.35, 0.0, -0.62))
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("En el piso, al lado de la barra chica (con la plancha arriba) · día",
         vis + [p["cuerpo"], p["piloto"]] + barra, "vendedor", "dia", vis + [p["cuerpo"]], 1.6),
    ])
    comun.componer_hoja("garrafa · Ø 0,30 × 0,55 m · 10 kg, sin marca · equipo de cocina",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["cuerpo"], m["valvula"], m["col"]])


if __name__ == "__main__":
    main()
