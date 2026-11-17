"""Modelo: servilletero (id `servilletero`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/servilletero.blend
    godot/modelos/accesorios/servilletero.glb
    docs/arte/revisiones/servilletero.jpg

Uso:
    blender -b -P tools/blender/modelos/servilletero.py
    python tools/blender/modelos/servilletero.py

Forma: el servilletero de chapa de bar. Una base de acero y dos chapas paradas, una del lado
del cliente (+Z) y otra del vendedor (−Z), con las esquinas de arriba redondeadas y una
muesca en U en el medio para sacar la servilleta. Entre las chapas, las servilletas paradas
(abiertas a los costados) asoman 2 cm por arriba, con el lomo de los dobleces ondulado.
Medidas: 0,12 × 0,11 × 0,08 m, como las dos cajas de hoy (cuerpo 0,10 de alto + servilletas
hasta 0,115; acá las chapas llegan a 0,09 y las servilletas a 0,11).
Origen: centro de la base, a nivel del mostrador. Colisión: una caja `servilletero-colonly`.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402

ID = "servilletero"
FAMILIA = "accesorios"
MEDIDAS = (0.12, 0.11, 0.08)
PRESUPUESTO = 300  # lista de modelos (utensilios y objetos chicos: 500)

BASE = (0.12, 0.008, 0.08)
CHAPA_ESPESOR = 0.005         # mínimo de equipos de mostrador (guía 2.2)
CHAPA_Z = 0.0315              # centro de cada chapa (±Z)
CHAPA_ALTO = 0.09
ESQUINA = 0.012               # radio de las esquinas de arriba de la chapa
MUESCA_ANCHO, MUESCA_HONDO = 0.026, 0.022  # media boca y profundidad de la U
SERV_MEDIO_X = 0.05           # las servilletas son un poco más angostas que las chapas
SERV_MEDIO_Z = CHAPA_Z - CHAPA_ESPESOR / 2 - 0.0005
SERV_ALTO, SERV_ONDA = 0.103, 0.007  # lomo medio y amplitud: de 0,096 a 0,11


def alto_chapa(x):
    """Borde de arriba de la chapa: esquinas redondeadas y la muesca en U del medio."""
    ax = abs(x)
    medio = MEDIDAS[0] / 2
    if ax > medio - ESQUINA:
        d = ax - (medio - ESQUINA)
        return CHAPA_ALTO - ESQUINA + math.sqrt(max(ESQUINA ** 2 - d ** 2, 0.0))
    if ax < MUESCA_ANCHO:
        return CHAPA_ALTO - MUESCA_HONDO * (1 - (ax / MUESCA_ANCHO) ** 2.5)  # U: fondo ancho
    return CHAPA_ALTO


def perfil_servilletas():
    """Tres dobleces de lomo redondeado, con el pliegue fino entre uno y otro: [(z, alto)]."""
    columnas = []
    ancho = 2 * SERV_MEDIO_Z / 3
    for d in range(3):
        for t in (0.0, 0.2, 0.5, 0.8):
            alto = SERV_ALTO - SERV_ONDA + 2 * SERV_ONDA * math.sin(math.pi * t) ** 0.5
            columnas.append((-SERV_MEDIO_Z + (d + t) * ancho, alto))
    columnas.append((SERV_MEDIO_Z, SERV_ALTO - SERV_ONDA))
    return columnas


def prisma_perfil(bm, columnas, y0, desde, hasta, plano, mat, abajo=False):
    """Pieza plana de borde de arriba curvo: perfil [(u, alto)] sobre la línea y = y0,
    extruido entre desde y hasta. plano "xy": u = X, se extruye en Z; "zy": u = Z, en X.
    Todo en ejes de Godot. abajo=False no hace la cara de abajo (apoyada, guía 3.6)."""
    def p(u, y, w):
        return piezas.g2b((u, y, w) if plano == "xy" else (w, y, u))
    previas = set(bm.faces)
    lados = []
    for w in (desde, hasta):
        lados.append([(bm.verts.new(p(u, y0, w)), bm.verts.new(p(u, alto, w))) for u, alto in columnas])
    a, b = lados
    for i in range(len(columnas) - 1):
        bm.faces.new((a[i][0], a[i + 1][0], a[i + 1][1], a[i][1]))
        bm.faces.new((b[i][0], b[i][1], b[i + 1][1], b[i + 1][0]))
        bm.faces.new((a[i][1], a[i + 1][1], b[i + 1][1], b[i][1]))
        if abajo:
            bm.faces.new((a[i][0], b[i][0], b[i + 1][0], a[i + 1][0]))
    bm.faces.new((a[0][0], a[0][1], b[0][1], b[0][0]))
    bm.faces.new((a[-1][0], b[-1][0], b[-1][1], a[-1][1]))
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def construir():
    m_acero, m_papel = comun.cargar_materiales("M_Acero", "M_BlancoCrema")
    bm = bmesh.new()
    piezas.caja(bm, BASE, (0, BASE[1] / 2, 0), mat=0, bisel=0.003, sin_abajo=True)
    medio = MEDIDAS[0] / 2
    xs = [-medio, -0.0565, -0.048, -MUESCA_ANCHO, -0.0175, -0.009, 0.0]
    xs += [-x for x in reversed(xs[:-1])]
    columnas = [(x, alto_chapa(x)) for x in xs]
    for lado in (1, -1):
        z = lado * CHAPA_Z
        prisma_perfil(bm, columnas, BASE[1], z - CHAPA_ESPESOR / 2, z + CHAPA_ESPESOR / 2, "xy", 0)
    prisma_perfil(bm, perfil_servilletas(), BASE[1],
                  -SERV_MEDIO_X, SERV_MEDIO_X, "zy", 1)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [m_acero, m_papel], sombreado="duro")
    col = piezas.colision_caja(ID, MEDIDAS, (0, MEDIDAS[1] / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


def hoja_revision(cuerpo, revision):
    import pan_pancho
    comun.preparar_revision()
    pan = pan_pancho.construir("ref_pan")
    pan.location = piezas.g2b((0.16, pan_pancho.MEDIO_ALTO, 0.0))
    solo, con_pan = [cuerpo], [cuerpo, pan]
    cuadros = comun.sacar_fotos([
        ("Frente (cliente, +Z): muesca en U · día", solo, "frente", "dia", True),
        ("Costado: servilletas entre las chapas · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Arriba · día", solo, "arriba", "dia", True),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
        ("Escala: al lado de un pan de pancho · día", con_pan, "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        f"{ID} · 0,12 × 0,11 × 0,08 m · utensilio (mostrador)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
