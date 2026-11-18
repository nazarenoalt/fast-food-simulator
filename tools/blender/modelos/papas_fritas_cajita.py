"""Modelo: cajita rebosando de papas fritas (id `papas_fritas_cajita`, productos.ron, REQ-PAP-02).

Genera:
    arte/fuentes/comida/papas_fritas_cajita.blend
    godot/modelos/comida/papas_fritas_cajita.glb
    docs/arte/revisiones/papas_fritas_cajita.jpg

Uso:
    python tools/blender/modelos/papas_fritas_cajita.py [--sin-hoja]

Forma: la misma cajita de `cajita_papas.py` llena de bastones fritos **parados y
desordenados** que desbordan por arriba de la boca curva: cada uno sale de un punto al azar del
fondo o de entre los otros, inclinado hasta 18° hacia cualquier lado (más hacia afuera), con su
punta a una altura distinta y algo torcido, como sale servida. Fijos por semilla. Cada bastón
se prueba contra el interior de la cajita (el cartón de 3 mm y la boca curva): si atraviesa
una pared se sortea de nuevo, así ninguno sale por el costado. El ochavado de las papas fritas
(`_papas.seccion`, 8 lados, M_PapaFrita), recto y con la punta un poco más fina; para que entren
más en el tope de triángulos, uno de cada tres (los que quedan más metidos) es de 6 lados. Abajo
quedan abiertos (adentro de la cajita no se ven). Sin relleno: entre los bastones se ve el
cartón de adentro. Sombreado suave en las papas, duro en el cartón.

Medidas: las de la caja envolvente (la colisión del dato). Origen en su centro (guía 2.4).
Objeto único `papas_fritas_cajita`. Tope de comida armada (600 tris). Sin colisión.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun  # noqa: E402
import cajita_papas as caj  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _papas as pp  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "papas_fritas_cajita"
FRITA = 3                       # después de rojo, amarillo y crema de la cajita
H = caj.H
LADO = 0.0095                   # el de papas_fritas.py
N_BASTONES = 18
R_BASTON = 0.0056               # medio grosor del bastón inclinado (ochavado + inclinación)
INCLINACION = (3.0, 18.0)       # grados
SEMILLA = 11


def seccion(lado, esc, lados):
    """Ochavado (8) de las papas fritas, o hexágono (6) del mismo grosor."""
    if lados == 8:
        return pp.seccion(lado, 0.0028, esc)
    r = lado / 2 * 1.08 * esc
    return [(r * math.cos(math.pi * k / 3), r * math.sin(math.pi * k / 3)) for k in range(6)]


def baston_parado(bm, pie, punta, lado, giro, afinar=0.85, lados=8):
    """Bastón recto de `pie` a `punta` (Godot, cajita con el piso en y = 0), sección que gira
    `giro` grados sobre su eje. Abajo abierto (adentro no se ve), arriba con tapa."""
    pie, punta = Vector(pie), Vector(punta)
    eje = (punta - pie).normalized()
    ref = Vector((1, 0, 0)) if abs(eje.x) < 0.9 else Vector((0, 0, 1))
    u = eje.cross(ref).normalized()
    w = eje.cross(u).normalized()
    rot = Matrix.Rotation(math.radians(giro), 3, eje)
    u, w = rot @ u, rot @ w
    baja = Vector((0, H / 2, 0))
    anillos = []
    for c, esc in ((pie, 1.0), (punta, afinar)):
        anillos.append([bm.verts.new(g2b(c - baja + u * a + w * b)) for a, b in seccion(lado, esc, lados)])
    caras = e2._unir(bm, anillos, FRITA, False, True)
    for f in caras:
        f.material_index = FRITA
    return caras


def adentro(x, y, z, r=R_BASTON):
    """¿Un bastón de radio r con su eje en (x, y, z) entra en el hueco de la cajita a esa
    altura? (rectángulo redondeado de la pared de adentro; arriba de la boca no hay pared)."""
    if y > caj.alto_boca(x, z) + 0.001:
        return True
    t = y / H
    hx = caj.ABAJO[0] + (caj.ARRIBA[0] - caj.ABAJO[0]) * t - caj.PARED - r
    hz = caj.ABAJO[1] + (caj.ARRIBA[1] - caj.ABAJO[1]) * t - caj.PARED - r
    if abs(x) > hx or abs(z) > hz:
        return False
    esq = max(caj.RADIO - r, 0.0)
    dx = max(abs(x) - (hx - esq), 0.0)
    dz = max(abs(z) - (hz - esq), 0.0)
    return dx * dx + dz * dz <= esq * esq + 1e-12


def sortear_bastones(rnd):
    """(pie, punta) de cada bastón: al azar, sin atravesar la cajita ni quedar encimados."""
    bastones = []
    while len(bastones) < N_BASTONES:
        for _ in range(4000):
            y0 = rnd.uniform(0.012, 0.05)
            pie = Vector((rnd.uniform(-0.03, 0.03), y0, rnd.uniform(-0.02, 0.02)))
            if not adentro(pie.x, pie.y, pie.z):
                continue
            incl = math.radians(rnd.uniform(*INCLINACION))
            # Hacia afuera (desde el centro) con un margen grande al azar.
            rumbo = math.atan2(pie.z, pie.x) + math.radians(rnd.uniform(-70, 70))
            d = Vector((math.sin(incl) * math.cos(rumbo), math.cos(incl), math.sin(incl) * math.sin(rumbo)))
            alto = H + rnd.uniform(0.012, 0.05)
            punta = pie + d * ((alto - y0) / d.y)
            if not all(adentro(*(pie + (punta - pie) * (k / 16)))
                       for k in range(17)):
                continue
            if any((pie - p).length < 0.0085 or (punta - q).length < 0.011 for p, q in bastones):
                continue
            bastones.append((pie, punta))
            break
        else:
            raise RuntimeError("no entran %d bastones en la cajita" % N_BASTONES)
    return bastones


def construir(nombre=ID):
    mats = caj.materiales() + comun.cargar_materiales("M_PapaFrita")
    rnd = random.Random(SEMILLA)
    bm = bmesh.new()
    caj.cuerpo(bm, piso_adentro=True)
    # Los más metidos (cerca del centro) van de 6 lados: casi no se ven y ahorran triángulos.
    bastones = sorted(sortear_bastones(rnd), key=lambda b: Vector((b[1].x, 0, b[1].z)).length)
    for i, (pie, punta) in enumerate(bastones):
        lados = 6 if i < N_BASTONES // 3 else 8
        baston_parado(bm, pie, punta, LADO, rnd.uniform(-25, 25), afinar=rnd.uniform(0.8, 0.95), lados=lados)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Centro de la caja envolvente en el origen (guía 2.4).
    mn = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
    mx = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
    bmesh.ops.translate(bm, vec=-(mn + mx) / 2, verts=bm.verts)
    obj = e2.objeto_en(nombre, bm, mats, (0, 0, 0), sombreado="duro")
    for p in obj.data.polygons:        # papas suaves (guía 3.4: comida), cartón duro
        if p.material_index == FRITA:
            p.use_smooth = True
    return obj


def medidas(obj):
    mn, mx = e2.limites_godot([obj])
    return tuple(round(c, 4) for c in (mx - mn))


def revisar(obj):
    res = comun.revisar(obj, pp.PRESUPUESTO_PORCION, medidas(obj), origen="centro")
    res = comun.chequeo_normales_cerrado(res, [obj])
    alto = medidas(obj)[1]
    res.append((alto > caj.H + 0.02, "Rebosa: %.3f m de alto, %.0f mm por arriba de la cajita (%.2f m); "
                                    "%d bastones parados y desordenados, ninguno atraviesa el cartón (sorteo contra el hueco "
                                    "de la cajita)" % (alto, 1000 * (alto - caj.H), caj.H, N_BASTONES)))
    return res


def escena_comparacion(obj):
    """Foto extra: la vacía (pack del depósito), la llena (para el cliente) y una porción."""
    import papas_fritas
    vacia = caj.construir("ref_cajita_vacia")
    porcion = papas_fritas.construir("ref_porcion")
    objs = []
    for o, x in ((vacia, 0.12), (obj, 0.0), (porcion, -0.12)):
        mn, mx = e2.limites_godot([o])
        o.location = g2b((x, (mx.y - mn.y) / 2, 0.0))
        objs.append(o)
    bpy.context.view_layer.update()
    return "Vacía (depósito), llena (cliente) y una porción · día", objs, objs, 1.35


def main():
    titulo = "papas_fritas_cajita · cajita rebosando de papas fritas (comida armada)"
    pp.main_comida(ID, construir, revisar, titulo, escena=escena_comparacion)


if __name__ == "__main__":
    main()
