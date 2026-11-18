"""Modelo: billete (id `billete`, etapa 2; no está en el juego: la plata es solo el número del
HUD).

Genera:
    arte/fuentes/accesorios/billete.blend
    godot/modelos/accesorios/billete.glb
    docs/arte/revisiones/billete.jpg

Uso:
    python tools/blender/modelos/billete.py [--sin-hoja]

Forma: lámina de 0,15 × 0,002 × 0,065 (lista de modelos; 2 mm en vez de los 3 de la guía 2.2
para que no parezca un cartón) partida en dos a lo largo: el cuerpo del billete y una franja
clara en la punta +X (donde los billetes tienen la marca de agua). Diseño inventado: sin
caras, números ni textos (detalle fino, guía 3.5). 10 caras, 20 triángulos (presupuesto 20).

Un solo modelo para todos los valores (guía 4.2, regla 5): `pieza_billete` con dos
superficies:
    superficie 0 = cuerpo: el color del valor. El .glb trae M_TelaVerde.
    superficie 1 = franja: M_BlancoCrema (puede quedar igual en todos los valores).
Propuesta de colores por valor, todos de la paleta (se ven en la hoja): M_TelaVerde,
M_TelaBordo, M_FlorLila1, M_Terracota.

Familia `accesorios`, como la caja de dinero. Objeto que se agarra: origen en el centro,
sin colisión (si el juego le pone física, la arma el dato, guía 6.1).
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
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "billete"
FAMILIA = "accesorios"
MEDIDAS = (0.15, 0.002, 0.065)
PRESUPUESTO = 20
X_FRANJA = 0.04          # la franja va de x = 0,04 a la punta (3,5 cm)
VALORES = (("M_TelaVerde", "verde (el .glb)"), ("M_TelaBordo", "bordó"),
           ("M_FlorLila1", "lila"), ("M_Terracota", "naranja"))


def construir(nombre="pieza_billete"):
    cuerpo, franja = comun.cargar_materiales("M_TelaVerde", "M_BlancoCrema")
    w, h, p = (m / 2 for m in MEDIDAS)
    xs = (-w, X_FRANJA, w)
    bm = bmesh.new()
    v = {(i, sy, sz): bm.verts.new(g2b((x, sy * h, sz * p)))
         for i, x in enumerate(xs) for sy in (-1, 1) for sz in (-1, 1)}
    for i in range(2):
        a, b = i, i + 1
        for sy in (-1, 1):   # arriba y abajo
            bm.faces.new((v[a, sy, -1], v[b, sy, -1], v[b, sy, 1], v[a, sy, 1])).material_index = i
        for sz in (-1, 1):   # cantos largos
            bm.faces.new((v[a, -1, sz], v[b, -1, sz], v[b, 1, sz], v[a, 1, sz])).material_index = i
    for i, mat in ((0, 0), (2, 1)):   # cantos de las puntas
        bm.faces.new((v[i, -1, -1], v[i, 1, -1], v[i, 1, 1], v[i, -1, 1])).material_index = mat
    return piezas.terminar(nombre, bm, [cuerpo, franja])


def hoja_revision(billete, revision):
    import _comida4 as c4
    comun.preparar_revision()
    billete.location.z = MEDIDAS[1] / 2
    copias = []
    for i, (mat, _) in enumerate(VALORES[1:]):
        c = e2.copiar(billete, f"ref_billete_{mat}", comun.cargar_materiales(mat)[0], 0)
        c.location = (0.012 * (i + 1), -0.004 * (i + 1), MEDIDAS[1] / 2 + 0.0022 * (i + 1))
        c.rotation_euler.z = math.radians(6 * (i + 1))
        copias.append(c)
    pan = c4.pan_de_escala(0.0, -0.09)
    pan.hide_render = False
    solo = [billete]
    cuadros = e2.sacar_fotos([
        ("Arriba: cuerpo (superficie 0) y franja (1) · día", solo, "arriba", "dia", solo, 1.15),
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("3/4 · día", solo, "tres_cuartos", "dia", solo, 1.3),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", solo, 1.3),
        ("Colores por valor: verde, bordó, lila, naranja · día", [billete] + copias, "arriba", "dia"),
        ("Al lado de un pan de pancho · día", [billete, pan] + copias, "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(f"{ID} · 0,15 × 0,002 × 0,065 m · un modelo, el color lo pone el juego",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    billete = construir()
    raiz = piezas.raiz(ID, [billete])
    revision = comun.revisar(billete, PRESUPUESTO, MEDIDAS, origen="centro", tolerancia=1e-4)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, billete], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(billete, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
