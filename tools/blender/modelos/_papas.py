"""Piezas y fotos compartidas por los modelos de las papas fritas (SPEC-026).

Lo usan: papa_cruda, papa_pelada, papa_cortada, papas_fritas y cajita_papas (comida), y la
bolsa de papas (stock, para las unidades de referencia). Complementa a comun.py, piezas.py,
_etapa2.py, _equipos.py y _comida4.py (que no se tocan).

Todo en ejes de Godot (X derecha, Y arriba, Z hacia el cliente), como piezas.py.

Formas (pedido: nada de cajas ni esferas perfectas, proporciones reales):
    - papa(): elipsoide acostado sobre X con lomas al azar (fijas por semilla), un poco
      arriñonado y achatado abajo; los ojos son caras hundidas de otro material.
    - baston(): bastón de papa a lo largo de X, de sección cuadrada con las esquinas
      ochavadas, que se puede arquear, afinar en una punta y torcer.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

FAMILIA = "comida"
PRESUPUESTO_CHICA = 300   # comida chica (guía 3.1): una papa
PRESUPUESTO_PORCION = 600  # comida armada (guía 3.1): porción de varios bastones, cajita

# Medidas de los datos (productos.ron), ancho X × alto Y × profundidad Z.
MEDIDAS = {
    "papa_cruda": (0.095, 0.058, 0.068),
    "papa_pelada": (0.086, 0.052, 0.062),
    "papa_cortada": (0.084, 0.031, 0.045),
    "papas_fritas": (0.09, 0.034, 0.05),
    "cajita_papas": (0.09, 0.11, 0.056),
}
ESTADOS = ["papa_cruda", "papa_pelada", "papa_cortada", "papas_fritas"]
NOMBRES = {"papa_cruda": "cruda", "papa_pelada": "pelada", "papa_cortada": "cortada",
           "papas_fritas": "frita"}


# ── Papa entera ────────────────────────────────────────────────────────

def papa(bm, medidas, semilla, lados=12, anillos=7, ojos=0, mat_ojo=1, lomas=0.07, rinon=0.08):
    """Papa entera, centrada, de medidas exactas (caja envolvente).

    Esfera UV con el eje de los polos sobre X (las puntas son los polos, así quedan
    redondeadas), deformada con lomas suaves (armónicos al azar con la semilla), arriñonada
    (se arquea `rinon` hacia +Z en el medio) y con la panza de abajo más chata. Los ojos son
    `ojos` caras de los anillos del medio, achicadas y hundidas 0,8 mm, repartidas, con material mat_ojo.
    Devuelve las caras.
    """
    rnd = random.Random(semilla)
    terminos = [(rnd.choice((2, 3)), rnd.choice((1, 2, 3)), rnd.uniform(-lomas, lomas),
                 rnd.uniform(0, 2 * math.pi), rnd.uniform(0, 2 * math.pi)) for _ in range(4)]

    def f(u, v):
        return 1 + sum(a * math.sin(n * v + p) * math.sin(m * u + q) for n, m, a, p, q in terminos)

    previas = set(bm.faces)
    polo_a = bm.verts.new(g2b((-1.0, 0.0, 0.0)))
    polo_b = bm.verts.new(g2b((1.0, 0.0, 0.0)))
    filas = []
    for i in range(1, anillos):
        u = math.pi * i / anillos
        fila = []
        for k in range(lados):
            v = 2 * math.pi * (k + 0.5 * (i % 2)) / lados
            r = math.sin(u) * f(u, v)
            x = -math.cos(u) * (1 + 0.04 * f(u, v + 1))
            y, z = r * math.cos(v), r * math.sin(v)
            if y < 0:          # panza de abajo más chata (apoya mejor)
                y *= 0.82
            z += rinon * (1 - x * x)
            fila.append(bm.verts.new(g2b((x, y, z))))
        filas.append(fila)
    n = lados
    for k in range(n):
        bm.faces.new((polo_a, filas[0][(k + 1) % n], filas[0][k]))
        bm.faces.new((polo_b, filas[-1][k], filas[-1][(k + 1) % n]))
    for a, b in zip(filas, filas[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    nuevas = [f_ for f_ in bm.faces if f_ not in previas]
    for f_ in nuevas:
        f_.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    # Medidas exactas (el ruido corre la caja): se escala la papa sola.
    _ajustar(bm, nuevas, medidas)
    if ojos:
        quads = [f_ for f_ in nuevas if len(f_.verts) == 4]
        medio = [f_ for f_ in quads if abs(f_.calc_center_median().x) < medidas[0] * 0.3]
        # Repartidos: cada ojo nuevo es la cara más lejana de los ya elegidos (nada de
        # tres ojos juntos que parezcan una cara).
        elegidas = [rnd.choice(medio)]
        while len(elegidas) < min(ojos, len(medio)):
            elegidas.append(max(medio, key=lambda f_: min(
                (f_.calc_center_median() - e.calc_center_median()).length for e in elegidas)
                + rnd.uniform(0, 0.002)))
        for cara in elegidas:
            res = bmesh.ops.inset_individual(bm, faces=[cara], thickness=0.0, depth=0.0)
            centro = cara.calc_center_median()
            for v in cara.verts:
                v.co = centro + (v.co - centro) * 0.2
            cara.normal_update()
            bmesh.ops.translate(bm, vec=-cara.normal * 0.0008, verts=list(cara.verts))
            cara.material_index = mat_ojo
            nuevas += [f_ for f_ in res["faces"] if f_ not in nuevas]
    return [f_ for f_ in nuevas if f_.is_valid]


def _ajustar(bm, caras, medidas):
    """Centra unas caras en su caja y la estira a `medidas` (Godot) exactas."""
    vs = list({v for f in caras for v in f.verts})
    mn = Vector([min(v.co[i] for v in vs) for i in range(3)])
    mx = Vector([max(v.co[i] for v in vs) for i in range(3)])
    centro, tam = (mn + mx) / 2, mx - mn
    obj = piezas.medidas_g2b(medidas)
    for v in vs:
        for i in range(3):
            v.co[i] = (v.co[i] - centro[i]) * obj[i] / tam[i]


# ── Bastones ───────────────────────────────────────────────────────────

def seccion(lado, ochave, afinar=1.0):
    """Sección cuadrada de `lado` con las esquinas ochavadas (8 puntos en el plano (a, b))."""
    h = lado / 2 * afinar
    c = min(ochave, h * 0.9) * afinar
    return [(h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c),
            (-h + c, -h), (h - c, -h)]


def baston(bm, largo, lado, centro, rot=(0.0, 0.0, 0.0), ochave=0.0025, curva=(0.0, 0.0),
           afinar=(1.0, 1.0), torsion=0.0, mat=0, cuadrado=False):
    """Bastón de papa a lo largo de X (Godot), centrado en `centro` y girado `rot` (grados,
    como piezas.caja). curva = (arco en Y, arco en Z) del medio, en metros; afinar = escala de
    la sección en (punta −X, punta +X); torsion = grados que gira la sección de punta a punta.
    cuadrado=True: sección de 4 puntos y una sola banda (corte crudo, de aristas vivas).
    Devuelve las caras."""
    previas = set(bm.faces)
    if cuadrado:
        estaciones = [(-0.5, afinar[0], 0.0), (0.5, afinar[1], 0.0)]
    else:
        estaciones = [(-0.5, afinar[0], 0.0), (0.0, (afinar[0] + afinar[1]) / 2 + 0.06, 1.0),
                      (0.5, afinar[1], 0.0)]
    anillos = []
    for t, esc, arco in estaciones:
        if cuadrado:
            h = lado / 2 * esc
            pts = [(h, -h), (h, h), (-h, h), (-h, -h)]
        else:
            pts = seccion(lado, ochave, esc)
        g = math.radians(torsion * (t + 0.5))
        anillo = []
        for a, b in pts:
            ar, br = a * math.cos(g) - b * math.sin(g), a * math.sin(g) + b * math.cos(g)
            anillo.append(bm.verts.new(g2b((t * largo, ar + curva[0] * arco, br + curva[1] * arco))))
        anillos.append(anillo)
    caras = e2._unir(bm, anillos, mat, True, True)
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    piezas._transformar(bm, nuevas, centro, rot)
    return caras


def ajustar_caja(bm, medidas):
    """Todo el bmesh centrado y estirado a `medidas` exactas (porciones de bastones)."""
    c4.ajustar_caja(bm, medidas)


# ── Main y fotos ───────────────────────────────────────────────────────

def main_comida(id_, construir, revisar, titulo, escena=None):
    """construir(nombre) → objeto; revisar(obj) → revisión. Guarda, exporta y arma la hoja
    (la de los utensilios: frente, costado, arriba, 3/4 y al lado de un pan de pancho)."""
    import _equipos as eq
    comun.escena_vacia()
    obj = construir(id_)
    revision = revisar(obj)
    ok = comun.imprimir_revision(id_, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb([obj], comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")
    if "--sin-hoja" not in sys.argv:
        eq.hoja_mano(id_, titulo, obj, revision, escena=escena or escena_estados(id_))
    if not ok:
        sys.exit(1)


def construir_estado(id_, nombre):
    """El modelo de un estado de la papa, por su script (para las fotos de comparación)."""
    import importlib
    return importlib.import_module(id_).construir(nombre)


def escena_estados(actual):
    """Foto extra de la hoja: los cuatro estados en fila, sobre la mesada (comparación)."""
    def escena(obj):
        objs = []
        x = 0.18   # en la vista desde el vendedor, +X queda a la izquierda
        for id_ in ESTADOS:
            o = obj if id_ == actual else construir_estado(id_, f"ref_{id_}")
            mn, mx = e2.limites_godot([o])
            o.location = g2b((x, (mx.y - mn.y) / 2, 0.0))
            objs.append(o)
            x -= 0.12
        bpy.context.view_layer.update()
        etiqueta = "Los cuatro estados: " + ", ".join(NOMBRES[i] for i in ESTADOS) + " · día"
        return etiqueta, objs, objs, 1.35
    return escena


def material_ojo_y_cascara():
    return comun.cargar_materiales("M_PapaCascara", "M_Tronco")


def girar_z(bm, grados):
    """Gira todo el bmesh alrededor del eje Y de Godot (Z de Blender)."""
    bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.radians(grados), 3, "Z"))


# ── Utensilios (cuchillo, pelapapas, colador) ─────────────────────────

def mango(bm, estaciones, mat=0, segs=2, tapas=(True, True)):
    """Mango a lo largo de X (Godot): estaciones = [(x, medio_y, medio_z, radio)] con una
    sección de rectángulo redondeado en el plano YZ en cada x (centro y = z = 0). Las puntas
    se cierran con una cara plana. Devuelve las caras."""
    anillos = []
    for x, my, mz, r in estaciones:
        pts = e2.anillo_rr(my, mz, r, 0.0, segs=segs)   # (a, 0, b) en el plano XZ
        anillos.append([bm.verts.new(g2b((x, -p[0], p[2]))) for p in pts])
    previas = set(bm.faces)
    e2._unir(bm, anillos, mat, tapas[0], tapas[1])
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas
