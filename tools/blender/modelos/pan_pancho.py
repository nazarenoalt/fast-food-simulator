"""Modelo: pan de pancho (id `pan_pancho`, godot/data/productos.ron).

Genera:
    arte/fuentes/comida/pan_pancho.blend     ← archivo de trabajo
    godot/modelos/comida/pan_pancho.glb      ← lo que usa el juego
    docs/arte/revisiones/pan_pancho.jpg      ← hoja de revisión (guía 8.1)

Uso:
    blender -b -P tools/blender/modelos/pan_pancho.py
    python tools/blender/modelos/pan_pancho.py

Forma: pan de pancho abierto, como los de panadería: cortado a lo largo desde arriba casi
hasta la base, con las dos mitades separadas hacia afuera y la miga a la vista en las caras
de adentro. El fondo del corte es una U del tamaño de la salchicha (radio 0,011), para que
en el pancho quede hundida entre las dos mitades: su centro va a SALCHICHA_Z del centro del
pan y su parte de arriba queda ~7 mm por debajo del lomo.
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

# Salchicha del pancho (productos.ron): radio 0,011. Centro, medido desde el centro del pan.
# Cuando el juego use este modelo, `pancho` en productos.ron tiene que usar este valor
# en vez de 0,024 (hoy la salchicha va apoyada arriba de la cápsula).
SALCHICHA_RADIO = 0.011
SALCHICHA_Z = 0.004
RADIO_U = SALCHICHA_RADIO + 0.0005  # un pelito de aire para que no se atraviesen

# Medio perfil del corte transversal (y = ancho, z = alto): sale del centro de la base,
# da la vuelta por afuera de una mitad, entra por el corte y termina en el fondo de la U.
# Se espeja para la otra mitad.
_a45 = math.radians(45)
PERFIL_ABIERTO = [
    (0.0, -MEDIO_ALTO),                      # 0  base, casi plana
    (0.017, -0.021),                         # 1
    (0.026, -0.010),                         # 2
    (MEDIO_ANCHO, 0.003),                    # 3  lo más ancho
    (0.0258, 0.0165),                        # 4
    (0.0215, MEDIO_ALTO),                    # 5  lomo de la mitad (lo más alto)
    (0.0172, 0.0198),                        # 6  borde del corte (corteza → miga)
    (0.0138, 0.0115),                        # 7  cara de adentro, bien abierta hacia afuera
    (RADIO_U, SALCHICHA_Z),                  # 8  a la altura del centro de la salchicha
    (RADIO_U * math.sin(_a45), SALCHICHA_Z - RADIO_U * math.cos(_a45)),  # 9  U
    (0.0, SALCHICHA_Z - RADIO_U),            # 10 fondo de la U (bisagra del pan)
]
# En las puntas el corte se cierra: las dos mitades se juntan en un domo.
PERFIL_CERRADO = PERFIL_ABIERTO[:6] + [
    (0.0172, 0.0215), (0.012, 0.0225), (0.007, 0.023), (0.0035, 0.0232), (0.0, 0.0233)]
PRIMER_MIGA = 6  # desde el punto 6 hacia el centro, las caras son miga

# Estaciones a lo largo del pan (x); el corte va de punta a punta y se cierra recién al final.
ESTACIONES = [-0.079, -0.066, -0.04, 0.0, 0.04, 0.066, 0.079]
APERTURA = {0.066: 0.85, 0.079: 0.15}  # el corte se va cerrando en las puntas
CENTRO_ESCALA_Z = -0.004  # las puntas bajan un poco y se redondean


def escala_punta(x):
    """Superelipse: 1 en el medio, se cierra en las puntas (romas, no picudas)."""
    return (1 - (abs(x) / LARGO) ** 3) ** (1 / 3)


def apertura_corte(x):
    """1 = corte abierto, 0 = cerrado."""
    return APERTURA.get(round(abs(x), 3), 1.0)


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
    for a, b in zip(anillos, anillos[1:]):
        for k in range(n):
            f = bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))
            f.material_index = 1 if es_miga(k, n_medio) else 0
    # Puntas: abanico hacia un vértice, a la altura media de la punta (todo corteza).
    for x, a in ((-LARGO, anillos[0]), (LARGO, anillos[-1])):
        zc = sum(v.co.z for v in a) / n
        v = bm.verts.new((x, 0.0, zc))
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], v))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
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
    salchicha = comun.capsula("ref_salchicha", SALCHICHA_RADIO, 0.155, lados=8, material=cocida)
    salchicha.location = (0, 0, MEDIO_ALTO + SALCHICHA_Z)

    tmp = Path(tempfile.mkdtemp())
    cuadros = []

    def foto(etiqueta, vista, luz, con_salchicha=False, de_cerca=False):
        comun.poner_luz(luz)
        salchicha.hide_render = not con_salchicha
        objetos = [pan, salchicha] if con_salchicha else [pan]
        comun.encuadrar(objetos, vista, de_cerca=de_cerca)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))

    salchicha.hide_render = True
    foto("Frente (lo que ve el cliente) · día", "frente", "dia")
    foto("Costado de cerca: la salchicha queda hundida · día", "costado", "dia",
         con_salchicha=True, de_cerca=True)
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
