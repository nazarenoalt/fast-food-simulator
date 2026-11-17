"""Modelo: pan de pancho (id `pan_pancho`, godot/data/productos.ron).

Genera:
    arte/fuentes/comida/pan_pancho.blend     ← archivo de trabajo
    godot/modelos/comida/pan_pancho.glb      ← lo que usa el juego
    docs/arte/revisiones/pan_pancho.jpg      ← hoja de revisión (guía 8.1)

Uso:
    blender -b -P tools/blender/modelos/pan_pancho.py
    python tools/blender/modelos/pan_pancho.py

Forma: bollo alargado de puntas redondeadas, con el corte arriba a lo largo (miga a la
vista). El corte mide lo justo para que la salchicha del pancho (radio 0,011, centro a
0,024 del centro del pan, ver `pancho` en productos.ron) quede medio hundida.
Medidas = la colisión del dato: 0,17 × 0,045 × 0,055 m. Sombreado suave (comida, guía 3.4),
con borde marcado solo donde la corteza se encuentra con la miga.
"""
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402

ID = "pan_pancho"
MEDIDAS = (0.17, 0.045, 0.055)  # ancho X, alto Y, profundidad Z (Godot)
PRESUPUESTO = 300               # comida chica (guía 3.1)
LARGO, MEDIO_ALTO, MEDIO_ANCHO = MEDIDAS[0] / 2, MEDIDAS[1] / 2, MEDIDAS[2] / 2

# Medio perfil del corte transversal (y = ancho, z = alto), de abajo al centro de arriba.
# Se espeja para el otro lado. Con el corte abierto (centro del pan):
PERFIL_ABIERTO = [
    (0.0, -MEDIO_ALTO),       # 0  base, casi plana
    (0.016, -0.0215),         # 1
    (0.025, -0.013),          # 2
    (MEDIO_ANCHO, 0.0),       # 3  lo más ancho
    (0.026, 0.0125),          # 4
    (0.018, MEDIO_ALTO),      # 5  lomo de cada mitad (lo más alto)
    (0.0105, 0.0205),         # 6  borde del corte: acá apoya la salchicha
    (0.006, 0.012),           # 7  pared del corte (miga)
    (0.0, 0.0095),            # 8  fondo del corte
]
# Con el corte cerrado (cerca de las puntas): domo liso.
PERFIL_CERRADO = PERFIL_ABIERTO[:6] + [(0.0105, 0.0232), (0.006, 0.0238), (0.0, 0.024)]
PRIMER_MIGA = 6  # desde el punto 6 hacia el centro, las caras son miga

# Estaciones a lo largo del pan (x) y punta de cada lado.
ESTACIONES = [-0.08, -0.07, -0.052, -0.026, 0.0, 0.026, 0.052, 0.07, 0.08]
CENTRO_ESCALA_Z = -0.004  # las puntas bajan un poco y se redondean


def suave(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def escala_punta(x):
    """Superelipse: 1 en el medio, se cierra en las puntas (romas, no picudas)."""
    return (1 - (abs(x) / LARGO) ** 3) ** (1 / 3)


def apertura_corte(x):
    """1 = corte abierto, 0 = cerrado. El corte mide ~0,13 m, como el del dato."""
    return suave(0.068, 0.048, abs(x))


def anillo(x):
    s, g = escala_punta(x), apertura_corte(x)
    medio = [(ya + (yc - ya) * (1 - g), za + (zc - za) * (1 - g))
             for (ya, za), (yc, zc) in zip(PERFIL_ABIERTO, PERFIL_CERRADO)]
    completo = medio + [(-y, z) for y, z in reversed(medio[1:-1])]
    return [(x, y * s, CENTRO_ESCALA_Z + (z - CENTRO_ESCALA_Z) * s) for y, z in completo]


def es_miga(k, n_medio):
    """k = índice del vértice de inicio de la cara dentro del anillo."""
    return PRIMER_MIGA <= k < 2 * (n_medio - 1) - PRIMER_MIGA


def construir():
    corteza, miga = comun.cargar_materiales("M_PanCorteza", "M_PanMiga")
    bm = bmesh.new()
    anillos = [[bm.verts.new(p) for p in anillo(x)] for x in ESTACIONES]
    n = len(anillos[0])
    n_medio = len(PERFIL_ABIERTO)
    for i, (a, b) in enumerate(zip(anillos, anillos[1:])):
        con_corte = apertura_corte(ESTACIONES[i]) > 0.01 or apertura_corte(ESTACIONES[i + 1]) > 0.01
        for k in range(n):
            f = bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))
            f.material_index = 1 if con_corte and es_miga(k, n_medio) else 0
    # Puntas: abanico hacia un vértice, a la altura media de la punta.
    for x, a in ((-LARGO, anillos[0]), (LARGO, anillos[-1])):
        zc = sum(v.co.z for v in a) / n
        v = bm.verts.new((x, 0.0, zc))
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], v))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        # Corteza suave; paredes del corte planas, para que se lea la hendidura.
        f.smooth = f.material_index == 0
    # Borde marcado entre corteza y miga (para que el corte se lea).
    for e in bm.edges:
        mats = {f.material_index for f in e.link_faces}
        if len(mats) == 2:
            e.smooth = False
    obj = comun.objeto_desde_bmesh(ID, bm, [corteza, miga])
    return obj


def hoja_revision(pan, revision):
    """Renders de día y de atardecer + prueba de encastre con la salchicha."""
    comun.cargar_referencias()
    for nombre in ("ref_persona_1,75m", "ref_mostrador_0,95m"):
        bpy.data.objects[nombre].hide_render = True
    comun.configurar_render()
    pan.location.z = MEDIO_ALTO  # apoyado en el piso, solo para la foto

    # Salchicha cocida del pancho, con las medidas de productos.ron (no se exporta).
    cocida = comun.crear_material("ref_salchicha_cocida", "#B84C33", rugosidad=0.6)
    salchicha = comun.capsula("ref_salchicha", 0.011, 0.155, lados=8, material=cocida)
    salchicha.location = (0, 0, MEDIO_ALTO + 0.024)

    tmp = Path(tempfile.mkdtemp())
    cuadros = []

    def foto(etiqueta, vista, luz, con_salchicha=False):
        comun.poner_luz(luz)
        salchicha.hide_render = not con_salchicha
        objetos = [pan, salchicha] if con_salchicha else [pan]
        comun.encuadrar(objetos, vista)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))

    salchicha.hide_render = True
    foto("Frente (lo que ve el cliente) · día", "frente", "dia")
    foto("Costado · día", "costado", "dia")
    foto("3/4 · día", "tres_cuartos", "dia")
    foto("Arriba · día", "arriba", "dia")
    foto("3/4 · atardecer", "tres_cuartos", "atardecer")
    foto("Encastre con la salchicha (pancho) · día", "tres_cuartos", "dia", con_salchicha=True)
    comun.componer_hoja(
        "pan_pancho · 0,17 × 0,045 × 0,055 m · comida chica",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    pan = construir()
    revision = comun.revisar(pan, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/comida/{ID}.blend")
    comun.exportar_glb([pan], comun.RAIZ / f"godot/modelos/comida/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pan, revision)  # después de guardar: no ensucia el .blend
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
