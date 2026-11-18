"""Modelo: maceta con planta (id `maceta`, lista de modelos, etapa 5).

Genera:
    arte/fuentes/accesorios/maceta.blend
    godot/modelos/accesorios/maceta.glb
    docs/arte/revisiones/maceta.jpg

Uso:
    python tools/blender/modelos/maceta.py [--sin-hoja]

Forma: maceta de barro cocido (M_Terracota, color nuevo de la paleta) de forma clásica:
cuerpo cónico y un borde grueso arriba, con la tierra un poco más abajo del borde. La planta
es como el arbusto de los canteros (arbusto.py / _arbol.py) en chico: 3 bollos irregulares
facetados con los tres verdes (M_Hojas1/2/3), aplastados abajo contra la tierra.
Semilla fija: siempre da la misma planta.
Medidas: Ø 0,30 × 0,50 (lista): borde de la maceta de Ø 0,30 a 0,28 m de alto y la planta
hasta 0,50, sin salirse del borde (la huella es la de la maceta).
Origen: centro de la base, a nivel del piso.
Objetos (hijos del Empty `maceta`): maceta_cuerpo (barro, sombreado duro), maceta_planta
(sombreado plano) y `maceta-colonly` (cilindro de la maceta; la planta no choca).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _arbol  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "maceta"
PRESUPUESTO = 400
RADIO, ALTO = 0.15, 0.50
MEDIDAS = (2 * RADIO, ALTO, 2 * RADIO)
BORDE = 0.28                 # arriba del borde de la maceta
TIERRA = 0.262
PERFIL = [(0.105, 0.0), (0.128, 0.215), (RADIO, 0.222), (RADIO, BORDE), (0.136, BORDE),
          (0.134, TIERRA), (0.0, TIERRA)]
SEMILLA = 30
# centro (Godot), radios (x, y, z), puntos, verde (1, 2 o 3); se ajustan al final.
BOLLOS = [
    ((0.0, 0.35, 0.0), (0.14, 0.13, 0.14), 26, 2),
    ((-0.06, 0.30, 0.05), (0.10, 0.09, 0.10), 18, 1),
    ((0.06, 0.30, -0.04), (0.10, 0.09, 0.10), 18, 3),
]


def construir():
    (barro,) = comun.cargar_materiales("M_Terracota")
    hojas = comun.cargar_materiales("M_Hojas1", "M_Hojas2", "M_Hojas3")
    bm = bmesh.new()
    plaza.torno(bm, PERFIL, 16, mats=[0] * (len(PERFIL) - 1))   # sin tapa abajo (apoya)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [barro])

    rng = random.Random(SEMILLA)
    bm = bmesh.new()
    for centro, radios, puntos, verde in BOLLOS:
        m = verde - 1
        _arbol.bollo(bm, rng, centro, radios, puntos, m, [o for o in (0, 1, 2) if o != m],
                     aplastar=0.7, piso=TIERRA + 0.004, tope=0.95)
    # Ajuste: la planta no sale del borde (X y Z) y llega justo a ALTO.
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2     # centrada sobre la maceta
    s = min(1.0, (RADIO - 0.004) / max(max(xs) - cx, max(ys) - cy))
    sy = (ALTO - TIERRA - 0.004) / (max(zs) - TIERRA - 0.004)
    for v in bm.verts:
        v.co.x = (v.co.x - cx) * s
        v.co.y = (v.co.y - cy) * s
        v.co.z = TIERRA + 0.004 + (v.co.z - TIERRA - 0.004) * sy
    bm.normal_update()
    plaza.borrar_apoyadas(bm, TIERRA + 0.004)   # lo apoyado en la tierra no se ve (guía 3.6)
    planta = piezas.terminar(f"{ID}_planta", bm, list(hojas), sombreado="plano")

    col = a5.colision_cilindro(ID, RADIO, 0.0, BORDE)
    raiz = piezas.raiz(ID, [cuerpo, planta, col])
    return raiz, cuerpo, planta, col


def revisar(cuerpo, planta, col):
    res = comun.revisar([cuerpo, planta], PRESUPUESTO, MEDIDAS, origen="base")
    res = a5.chequeo_normales(res, [cuerpo, planta])
    mn, mx = a5.limites([planta])
    partes = _arbol._componentes(planta)
    caras = [len(c) for c in partes]
    res.append((max(abs(mn.x), mx.x, abs(mn.z), mx.z) <= RADIO and mn.y >= TIERRA - 1e-4,
                "Planta: %d bollos (%s caras), de la tierra (%.3f) a %.3f, sin salirse del borde"
                % (len(partes), ", ".join(map(str, caras)), mn.y, mx.y)))
    res.append(a5.chequeo_cilindro_colision(col, RADIO, 0.0, BORDE))
    return res


def hoja_revision(cuerpo, planta, revision):
    comun.preparar_revision()
    solo = [cuerpo, planta]
    carro, b = a5.carrito("barra_chica")
    copias = []
    for i, (x, z) in enumerate(((1.0, 0.25), (-1.15, 0.2))):
        for o in solo:
            c = a5.e2.copiar(o, f"ref_{o.name}_{i}")
            c.location = piezas.g2b((x, 0, z))
            copias.append(c)
    persona = a5.persona()
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Arriba · día (la planta no sale del borde)", solo, "arriba", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Con la persona de 1,75 m · día", solo + [persona], "tres_cuartos", "dia", None,
         a5.mover_persona((0.4, 0, -0.1))),
        ("A los costados de la barra chica · 3/4 · día", carro + copias, "tres_cuartos", "dia", None,
         None, 1.0),
        ("Ídem · lado del vendedor · día", carro + copias, "vendedor", "dia", None, None, 1.0),
        ("Ídem · atardecer", carro + copias, "tres_cuartos", "atardecer", None, None, 1.0),
    ]
    a5.hoja(ID, "maceta · Ø 0,30 × 0,50 m · accesorio (barro: M_Terracota)", pedidos, revision)


def main():
    comun.escena_vacia()
    raiz, cuerpo, planta, col = construir()
    revision = revisar(cuerpo, planta, col)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [raiz, cuerpo, planta, col])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, planta, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
