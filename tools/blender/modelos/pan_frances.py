"""Modelo: pan francés para el choripán (id `pan_frances`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/pan_frances.blend
    godot/modelos/comida/pan_frances.glb
    docs/arte/revisiones/pan_frances.jpg

Uso:
    blender -b -P tools/blender/modelos/pan_frances.py
    python tools/blender/modelos/pan_frances.py

Forma: pan francés de 0,16 × 0,06 × 0,08 (lista de modelos), abierto como el de pancho (guía
5.1, referencia `pan_pancho`): cortado a lo largo desde arriba casi hasta la base, con las
dos mitades separadas hacia afuera y la miga (M_PanMiga) a la vista en las caras de adentro.
El fondo del corte es una U del tamaño del chorizo (radio 0,015 + 1,5 mm de aire), para que
en el choripán quede hundido: su centro va a CHORIZO_Y = 0,017 del centro del pan y su
parte de arriba asoma 2 mm sobre el lomo de las mitades.
Más ancho que alto, con las puntas más finitas y bajas que el de pancho. Los cortes
diagonales de arriba van solo como forma (guía 3.5, sin detalle fino): el lomo de cada mitad
sube y baja 3,5 mm a lo largo, con las lomitas de una mitad corridas respecto de la otra, y
eso dibuja la greña en diagonal con la luz.
Medidas = la lista: 0,16 × 0,06 × 0,08. Sombreado suave, con borde marcado solo entre corteza
y miga.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pan_frances"
MEDIDAS = c4.PAN_FRANCES
PRESUPUESTO = 300
LARGO, MEDIO_ALTO, MEDIO_ANCHO = MEDIDAS[0] / 2, MEDIDAS[1] / 2, MEDIDAS[2] / 2

CHORIZO_Y = c4.CHORIZO_Y
RADIO_U = c4.R_CHORIZO + 0.0015
_a45 = math.radians(45)

# Medio perfil del corte transversal (y = ancho, z = alto), del centro de la base al fondo
# de la U, por afuera de una mitad. Se espeja para la otra.
PERFIL_ABIERTO = [
    (0.0, -MEDIO_ALTO),                      # 0 base
    (0.027, -0.0262),                        # 1
    (0.0388, -0.0115),                       # 2
    (MEDIO_ANCHO, 0.004),                    # 3 lo más ancho
    (0.0352, 0.0215),                        # 4 hombro
    (0.0282, MEDIO_ALTO),                    # 5 lomo de la mitad (lo más alto)
    (0.0222, 0.0262),                        # 6 borde del corte (corteza → miga)
    (RADIO_U, CHORIZO_Y),                    # 7 a la altura del centro del chorizo
    (RADIO_U * math.sin(_a45), CHORIZO_Y - RADIO_U * math.cos(_a45)),  # 8 U
    (0.0, CHORIZO_Y - RADIO_U),              # 9 fondo de la U
]
# En las puntas el corte se cierra en un domo.
PERFIL_CERRADO = PERFIL_ABIERTO[:6] + [(0.0215, 0.0292), (0.012, 0.0298), (0.0055, 0.03), (0.0, 0.03)]
PRIMER_MIGA = 6

ESTACIONES = [-0.077, -0.062, -0.036, -0.012, 0.012, 0.036, 0.062, 0.077]
APERTURA = {0.062: 0.8, 0.077: 0.12}
CENTRO_ESCALA_Z = -0.008  # las puntas bajan
GRENA = 0.0035            # cuánto baja el lomo entre greña y greña


def escala_punta(x):
    """Superelipse más finita que la del pan de pancho: puntas de pan francés."""
    return (1 - (abs(x) / LARGO) ** 2.4) ** (1 / 2.4)


def apertura_corte(x):
    return APERTURA.get(round(abs(x), 3), 1.0)


def grena(x, lado):
    """Baja del lomo en la estación x para la mitad `lado` (±1): alterna, corrida entre
    mitades, así las lomitas quedan en diagonal."""
    i = ESTACIONES.index(x)
    if i in (0, len(ESTACIONES) - 1):
        return 0.0
    return GRENA if (i + (lado > 0)) % 2 else 0.0


def anillo(x):
    s, g = escala_punta(x), apertura_corte(x)
    medio = [(ya + (yc - ya) * (1 - g), za + (zc - za) * (1 - g))
             for (ya, za), (yc, zc) in zip(PERFIL_ABIERTO, PERFIL_CERRADO)]
    n = len(medio)
    completo = [(y, z, 1) for y, z in medio] + [(-y, z, -1) for y, z in reversed(medio[1:-1])]
    pts = []
    for j, (y, z, lado) in enumerate(completo):
        k = j if lado > 0 else 2 * (n - 1) - j  # índice en el medio perfil
        if k in (4, 5, 6):
            z -= grena(x, lado) * (1.0 if k == 5 else 0.6)
        pts.append((x, y * s, CENTRO_ESCALA_Z + (z - CENTRO_ESCALA_Z) * s))
    return pts


def es_miga(k, n_medio=len(PERFIL_ABIERTO)):
    return PRIMER_MIGA <= k < 2 * (n_medio - 1) - PRIMER_MIGA


def puntas(anillos):
    return [(x, 0.0, sum(p[2] for p in a) / len(a)) for x, a in ((-LARGO, anillos[0]), (LARGO, anillos[-1]))]


def construir(nombre=ID):
    materiales = comun.cargar_materiales("M_PanCorteza", "M_PanMiga")
    anillos = [anillo(x) for x in ESTACIONES]
    return comun.lofteo(nombre, anillos, puntas(anillos), materiales,
                        lambda banda, k: 1 if es_miga(k) else 0)


def hoja_revision(pan, revision):
    comun.preparar_revision()
    pan.location.z = MEDIO_ALTO
    import chorizo as mod_chorizo
    ch = mod_chorizo.construir("ref_chorizo")
    ch.data.materials[0] = c4.material_ref("chorizo_cocido", c4.COCCION_CHORIZO[1][1])
    ch.location = (0, 0, MEDIO_ALTO + CHORIZO_Y)
    ref = c4.pan_de_escala(0.0, -0.09)
    solo, con = [pan], [pan, ch]
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", solo, "frente", "dia"),
        ("Costado de cerca: el chorizo queda hundido · día", con, "costado", "dia", con, 1.1),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Arriba · día", solo, "arriba", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Al lado de un pan de pancho · día", [pan, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · 0,16 × 0,06 × 0,08 m · comida chica", cuadros, revision)


def main():
    comun.escena_vacia()
    pan = construir()
    revision = comun.revisar(pan, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [pan])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pan, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
