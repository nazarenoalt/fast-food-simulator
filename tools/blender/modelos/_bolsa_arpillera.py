"""Bolsa de papas de arpillera (REQ-PAP-03): lo comparten bolsa_papas_2kg y bolsa_papas_5kg.

Forma: bolsa de tela de verdulería (M_Arpillera), **blanda**, acostada en el estante con el
atado hacia el vendedor (−Z), como las otras bolsas. Es un loft de anillos a lo largo de Z:

    - adelante (+Z) el fondo de la bolsa: la tela se junta en una **costura** recta y
      horizontal, marcada con un ribete cosido (M_PapelMadera, más oscuro que la tela);
    - el cuerpo se abulta por las papas: un anillo gordo en el medio de cada fila de la
      grilla y uno más flaco entre filas, y arriba dos lomas (las dos columnas) con un valle
      en el medio; los costados panzones y la base plana (apoya). Cada vértice se infla un
      poco al azar (semilla fija): la tela no es una caja;
    - atrás se angosta en un hombro, la boca se **frunce** (pliegues: el anillo alterna radio
      grande y chico), la ata un hilo rojo (M_RojoAcento, cilindro de 8 lados) y arriba del
      atado sale la cola de tela fruncida, un poco levantada.

La bolsa es opaca y está cerrada: las papas que pone el juego por la grilla del dato
(REQ-DEP-03) no se ven; se ve la forma abultada. La revisión comprueba que cada papa de la
grilla queda adentro de la tela (ninguna asoma) y que la bolsa entra en un lugar del estante.

Origen: el centro de la grilla del dato a nivel de apoyo (centro de la base del cuerpo, guía
2.4): así las unidades del juego caen adentro. La costura y el atado sobresalen (chequeo propio).
Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready).
Sombreado suave (tela).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "stock"
PRESUPUESTO = 400  # empaques y bloques de stock (guía 3.1)
ESTANTE = (0.22, 0.30, 0.40)
PAPA = (0.095, 0.058, 0.068)         # papa_cruda (productos.ron)
TELA, COSTURA, HILO = range(3)
MARGEN = (0.01, 0.02, 0.0)         # aire de la tela alrededor de la grilla (medio X, arriba Y)

# Sección del cuerpo: (u, v) con u de −1 a 1 (ancho) y v de 0 a 1 (alto). 14 puntos, en
# sentido antihorario mirando desde +Z: base plana, costados panzones y arriba dos lomas
# (las columnas de papas, en u = ±0,45) con un valle en el medio.
SECCION = [(0.0, 0.0), (0.8, 0.0), (0.97, 0.08), (1.0, 0.38), (0.98, 0.7), (0.88, 0.91), (0.47, 0.99),
           (0.0, 0.96), (-0.47, 0.99), (-0.88, 0.91), (-0.98, 0.7), (-1.0, 0.38), (-0.97, 0.08),
           (-0.8, 0.0)]
N = len(SECCION)


def medidas_cuerpo(grilla, sep):
    cols, filas, capas = grilla
    ancho = cols * sep[0] + 2 * MARGEN[0]
    alto = capas * sep[1] + MARGEN[1]
    largo = filas * sep[2]
    return ancho, alto, largo


def construir(id_, grilla, sep, semilla):
    """Arma la bolsa. Devuelve {"obj", "estaciones"}."""
    mats = comun.cargar_materiales("M_Arpillera", "M_PapelMadera", "M_RojoAcento")
    rnd = random.Random(semilla)
    cols, filas, capas = grilla
    W, H, L = medidas_cuerpo(grilla, sep)
    a = W / 2
    bm = bmesh.new()

    def anillo(z, ex, ey, yc=None, pliegue=0.0, abajo=0.0, jitter=True):
        """ex, ey: escala de la sección; yc: centro en Y (None = base en `abajo`, apoya)."""
        vs = []
        for k, (u, v) in enumerate(SECCION):
            # Ruido de la tela solo en los costados: arriba doblaría las caras entre lomas.
            r = 1 + (rnd.uniform(0.0, 0.02) if jitter and v < 0.8 else 0.0)
            if pliegue:
                r *= 1 + (pliegue if k % 2 else -pliegue)
            x = u * a * ex * r
            if yc is None:
                y = abajo + v * H * ey * (r if v > 0.05 else 1.0)
            else:
                y = yc + (v - 0.5) * H * ey * r
            vs.append(bm.verts.new(g2b((x, y, z))))
        return vs

    zf = L / 2                                    # frente de la grilla
    filas_z = [zf - (j + 0.5) * sep[2] for j in range(filas)]
    anillos, estaciones = [], []

    def agregar(nombre, vs):
        anillos.append(vs)
        estaciones.append(nombre)

    # Fondo de la bolsa: costura (la tela junta en una línea) y la panza que redondea.
    yc_cost = H * 0.42
    agregar("costura", anillo(zf + 0.026, 0.86, 0.06, yc=yc_cost, jitter=False))
    agregar("fondo", anillo(zf + 0.01, 0.9, 0.8, abajo=0.006))
    for j, z in enumerate(filas_z):
        agregar(f"fila_{j + 1}", anillo(z, 1.0, 1.0))
        if j < filas - 1:
            agregar(f"entre_{j + 1}", anillo(z - sep[2] / 2, 0.965, 0.96))
    # Atrás: hombro, boca fruncida y cola de tela arriba del atado.
    z_hombro = -zf - 0.012
    agregar("hombro", anillo(z_hombro, 0.9, 0.84, abajo=0.006))
    y_boca = H * 0.55
    r_boca = 0.022
    z_boca = z_hombro - 0.024
    agregar("boca", anillo(z_boca, r_boca / a, 2 * r_boca / H, yc=y_boca, pliegue=0.16))
    z_cola = z_boca - 0.034
    agregar("cola", anillo(z_cola, 0.042 / a, 0.07 / H, yc=y_boca + 0.012, pliegue=0.18))

    previas = set(bm.faces)
    e2._unir(bm, anillos, TELA, True, True)
    caras = [f for f in bm.faces if f not in previas]
    for f in caras:
        f.material_index = TELA
    bmesh.ops.recalc_face_normals(bm, faces=caras)
    # Ribete de la costura (adelante, a lo ancho) e hilo del atado.
    piezas.caja(bm, (0.86 * W + 0.006, 0.012, 0.01), (0, yc_cost, zf + 0.027), mat=COSTURA, bisel=0.002)
    piezas.cilindro(bm, r_boca * 0.95, 0.01, (0, y_boca, z_boca - 0.002), eje="z", lados=8, mat=HILO,
                    tapas=(False, False), radio_a_caras=True)
    obj = piezas.terminar(id_, bm, mats, sombreado="suave")   # tela (guía 3.4)
    # Solo para los renders de Cycles (no viaja en el .glb): evita las manchas oscuras del
    # "terminador de sombra" en una malla suave de pocas caras.
    obj.shadow_terminator_geometry_offset = 0.6
    return {"obj": obj, "estaciones": estaciones, "cuerpo": (W, H, L)}


# ── Revisión ───────────────────────────────────────────────────────────

def posiciones(grilla, sep):
    return eq.posiciones(grilla, sep)


def chequeo_papas_adentro(obj, grilla, sep):
    """Cada papa de la grilla (todos los vértices del modelo papa_cruda, el que dibuja el juego)
    queda adentro de la tela: un rayo desde cada vértice cruza la malla una cantidad impar de
    veces."""
    import papa_cruda
    ref = papa_cruda.construir("ref_papa_chequeo")
    bpy.context.view_layer.update()
    locales = [ref.matrix_world @ v.co for v in ref.data.vertices]
    bpy.data.objects.remove(ref)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    arbol = BVHTree.FromBMesh(bm)
    dir_ = Vector((0.31, 0.17, 0.93)).normalized()
    fuera = puntos = 0
    for pos in posiciones(grilla, sep):
        c = g2b(pos)
        for v in locales:
            puntos += 1
            cruces, origen = 0, c + v
            for _ in range(20):
                hit = arbol.ray_cast(origen, dir_)
                if hit[0] is None:
                    break
                cruces += 1
                origen = hit[0] + dir_ * 1e-5
            fuera += cruces % 2 == 0
    bm.free()
    n = grilla[0] * grilla[1] * grilla[2]
    return fuera == 0, ("Las %d papas de la grilla (modelo papa_cruda) quedan adentro de la tela: %d vértices, "
                        "%d afuera" % (n, puntos, fuera))


def chequeo_origen(obj, grilla, sep):
    vs = eq.verts_godot(obj)
    W, H, L = medidas_cuerpo(grilla, sep)
    cuerpo = [v for v in vs if abs(v.z) <= L / 2 + 1e-4]
    cx = max(v.x for v in cuerpo) + min(v.x for v in cuerpo)
    base = min(v.y for v in vs)
    ok = abs(cx) < 0.004 and abs(base) < 1e-4
    return ok, ("Origen en el centro de la grilla del dato, a nivel de apoyo (la costura sobresale a +Z y "
                "el atado a −Z)")


def chequeo_estante(obj):
    mn, mx = e2.limites_godot([obj])
    tam = mx - mn
    ok = tam.x <= ESTANTE[0] and tam.y <= ESTANTE[1] and tam.z <= ESTANTE[2]
    return ok, ("Entra en un lugar del estante: %.3f × %.3f × %.3f (máx. %.2f × %.2f × %.2f)"
                % (tam.x, tam.y, tam.z, *ESTANTE))


def revisar(m, grilla, sep):
    obj = m["obj"]
    mn, mx = e2.limites_godot([obj])
    tam = tuple(mx - mn)
    res = comun.revisar(obj, PRESUPUESTO, tam, origen="base", max_materiales=3)
    res = eq.reemplazar(res, "Origen", chequeo_origen(obj, grilla, sep))
    res.insert(1, chequeo_estante(obj))
    res.insert(2, chequeo_papas_adentro(obj, grilla, sep))
    return res


def hoja(id_, titulo, m, grilla, sep, revision):
    import papa_cruda
    papas = eq.unidades(lambda n: papa_cruda.construir(n), grilla, sep, "ref_papa")
    eq.hoja_stock(id_, titulo, [m["obj"]], [m["obj"]] + papas, revision)


def main(id_, grilla, sep, semilla, titulo):
    eq.main_modelo(id_, FAMILIA, lambda: construir(id_, grilla, sep, semilla),
                   lambda m: revisar(m, grilla, sep),
                   lambda m, r: hoja(id_, titulo, m, grilla, sep, r), lambda m: [m["obj"]])

