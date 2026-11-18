"""Modelo: mesa de ajedrez con bancos (id `mesa_ajedrez`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/mesa_ajedrez.blend
    godot/modelos/plaza/mesa_ajedrez.glb
    docs/arte/revisiones/mesa_ajedrez.jpg

Uso:
    python tools/blender/modelos/mesa_ajedrez.py [--sin-hoja]

Forma: la mesa de ajedrez de piedra de las plazas (para la actividad "charlar / jugar").
Tapa cuadrada sobre un pie de sección cuadrada con zócalo, y cuatro banquitos redondos
torneados, uno de cada lado. El tablero va en la tapa como una placa apenas en relieve
(8 mm) con las 64 casillas en dos piedras: claras M_Piedra y oscuras M_Vereda (el gris de
la vereda, apagado como todo el fondo). Las casillas son geometría (una cara cada una), no
textura: se ven desde los 2 m y no hace falta imagen.

Medidas (lista ≈ 1,6 × 0,75 × 1,6): 1,60 × 0,75 × 1,60 con los banquitos (centros a 0,63 del
medio, Ø 0,34). Tapa de 0,80 × 0,80 a 0,75 m (el tablero asoma hasta 0,758: se informa
aparte, la medida es la de la mesa); banquitos de 0,45 de alto. Tablero de 0,48 (casillas
de 6 cm), con la casilla clara a la derecha de cada jugador.
Biseles: piezas de piedra de 8 cm o más, bisel de 2 cm (guía 3.3, mobiliario urbano).
Lados (guía 3.2): banquitos 16 (radio de 5 a 25 cm).
Origen: centro de la base, a nivel del piso.

Objetos (hijos del Empty `mesa_ajedrez`):
    - mesa_ajedrez_cuerpo: mesa, tablero y banquitos.
    - mesa_ajedrez-colonly: cajas de la mesa y de los cuatro banquitos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "mesa_ajedrez"
PRESUPUESTO = 1200  # lista de modelos
MEDIDAS = (1.6, 0.758, 1.6)      # con el tablero en relieve (la tapa está a 0,75)
CLARA, OSCURA = 0, 1

TAPA = (0.80, 0.08, 0.80)
ALTO = 0.75
TABLERO = 0.48
RELIEVE = 0.008
D_BANCO = 0.63
R_BANCO = 0.17
ALTO_BANCO = 0.45


def tablero(bm):
    """Placa de 8 × 8 casillas en relieve sobre la tapa (sin la cara de abajo, apoyada)."""
    previas = set(bm.faces)
    n, a = 8, TABLERO / 2
    paso = TABLERO / n
    y = ALTO + RELIEVE
    grilla = [[bm.verts.new(g2b((-a + i * paso, y, -a + j * paso))) for j in range(n + 1)]
              for i in range(n + 1)]
    for i in range(n):
        for j in range(n):
            f = bm.faces.new((grilla[i][j], grilla[i + 1][j], grilla[i + 1][j + 1], grilla[i][j + 1]))
            # Casilla de la esquina de adelante a la derecha (x+, z+) clara.
            f.material_index = CLARA if (i + j) % 2 == 1 else OSCURA
    # Cantos: de cada borde de la grilla hasta la tapa.
    borde = ([grilla[i][0] for i in range(n + 1)] + [grilla[n][j] for j in range(1, n + 1)] +
             [grilla[i][n] for i in range(n - 1, -1, -1)] + [grilla[0][j] for j in range(n - 1, 0, -1)])
    abajo = [bm.verts.new((v.co.x, v.co.y, ALTO)) for v in borde]
    for k in range(len(borde)):
        k2 = (k + 1) % len(borde)
        bm.faces.new((borde[k], abajo[k], abajo[k2], borde[k2])).material_index = OSCURA
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)


def construir():
    mats = comun.cargar_materiales("M_Piedra", "M_Vereda")
    bm = bmesh.new()
    piezas.caja(bm, TAPA, (0, ALTO - TAPA[1] / 2, 0), mat=CLARA, bisel=0.02)
    piezas.caja(bm, (0.26, ALTO - TAPA[1] - 0.06, 0.26), (0, 0.06 + (ALTO - TAPA[1] - 0.06) / 2, 0),
                mat=CLARA, bisel=0.02)
    piezas.caja(bm, (0.44, 0.08, 0.44), (0, 0.04, 0), mat=CLARA, bisel=0.02, sin_abajo=True)
    tablero(bm)
    for x, z in ((D_BANCO, 0), (-D_BANCO, 0), (0, D_BANCO), (0, -D_BANCO)):
        plaza.torno(bm, [(0.16, 0.0), (0.12, 0.07), (0.12, 0.37), (R_BANCO, 0.42),
                         (0.16, ALTO_BANCO), (0.0, ALTO_BANCO)], lados=16, centro=(x, 0, z))
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)
    cajas = [((TAPA[0], ALTO, TAPA[2]), (0, ALTO / 2, 0), (0, 0, 0))]
    for x, z in ((D_BANCO, 0), (-D_BANCO, 0), (0, D_BANCO), (0, -D_BANCO)):
        cajas.append(((2 * R_BANCO, ALTO_BANCO, 2 * R_BANCO), (x, ALTO_BANCO / 2, z), (0, 0, 0)))
    col = plaza.colision_cajas(ID, cajas)
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": [col]}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    vs = plaza.verts_mundo([mod["cuerpo"]])
    tapa = max(v.z for v in vs if abs(v.x) > TABLERO / 2 + 0.03 and abs(v.y) > TABLERO / 2 + 0.03)
    banco = max(v.z for v in vs if abs(v.x) > 0.5)
    res.append((abs(tapa - ALTO) < 0.002 and abs(banco - ALTO_BANCO) < 0.002,
                "Tapa a %.3f m (tablero en relieve hasta %.3f), banquitos de %.3f m" % (
                    tapa, ALTO + RELIEVE, banco)))
    caras = sum(1 for p in mod["cuerpo"].data.polygons if abs(p.center.z - (ALTO + RELIEVE)) < 1e-5)
    res.append((caras == 64, f"Tablero de {caras} casillas (8 × 8)"))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "mesa_ajedrez · 1,6 × 0,75 × 1,6 m · banquitos de 0,45 m · mobiliario de plaza", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba (tablero) · día", c, "arriba", "dia", True),
        ], revision, persona_en=(1.2, 0, 0.6))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
