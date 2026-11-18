"""Modelo: cajita rebosando de papas fritas (id `papas_fritas_cajita`, productos.ron, REQ-PAP-02).

Genera:
    arte/fuentes/comida/papas_fritas_cajita.blend
    godot/modelos/comida/papas_fritas_cajita.glb
    docs/arte/revisiones/papas_fritas_cajita.jpg

Uso:
    python tools/blender/modelos/papas_fritas_cajita.py [--sin-hoja]

Forma: la misma cajita de `cajita_papas.py` (sin el piso de adentro, que no se ve) con 16
bastones fritos **parados** que desbordan por arriba de la boca curva, en tres filas: los de
atrás más altos y abiertos hacia atrás, los del medio, y los de adelante más cortos y volcados
hacia el cliente por donde la boca baja, como sale servida. Cada bastón es el ochavado de las
papas fritas (`_papas.seccion`, 8 lados, M_PapaFrita), recto pero algo torcido y con la punta
un poco más fina; abajo quedan abiertos porque los tapa el **colchón** de papas (una tapa
abombada de M_PapaFrita a la altura de la boca, que hace que entre los bastones se vea dorado y
no el cartón de adentro). Sombreado suave en las papas, duro en el cartón.

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
Y_ABAJO = 0.02 - H / 2          # donde empiezan los bastones (tapado por el colchón)
# Filas: (z del pie, z en la boca, xs en la boca, alto de la punta sobre el borde de atrás). Cada
# bastón va del pie (adentro, abajo) a su punto en la boca y sigue derecho: se abren en abanico
# desde adentro sin atravesar las paredes (la boca mide ≈ 0,078 × 0,045 a esa altura).
Y_BOCA = H / 2 - 0.02
FILAS = [
    (-0.008, -0.016, (-0.030, -0.018, -0.006, 0.006, 0.018, 0.030), 0.040),
    (0.000, 0.000, (-0.024, -0.012, 0.000, 0.012, 0.024), 0.032),
    (0.008, 0.016, (-0.024, -0.012, 0.000, 0.012, 0.024), 0.020),
]
SEMILLA = 7


def baston_parado(bm, pie, punta, lado, giro, afinar=0.85):
    """Bastón recto de `pie` a `punta` (Godot), sección ochavada que gira `giro` grados sobre
    su eje. Abajo abierto (lo tapa el colchón), arriba con tapa."""
    pie, punta = Vector(pie), Vector(punta)
    eje = (punta - pie).normalized()
    ref = Vector((1, 0, 0)) if abs(eje.x) < 0.9 else Vector((0, 0, 1))
    u = eje.cross(ref).normalized()
    w = eje.cross(u).normalized()
    rot = Matrix.Rotation(math.radians(giro), 3, eje)
    u, w = rot @ u, rot @ w
    anillos = []
    for c, esc in ((pie, 1.0), (punta, afinar)):
        anillos.append([bm.verts.new(g2b(c + u * a + w * b)) for a, b in pp.seccion(lado, 0.0028, esc)])
    caras = e2._unir(bm, anillos, FRITA, False, True)
    for f in caras:
        f.material_index = FRITA
    return caras


def colchon(bm):
    """Tapa abombada de papas a la altura de la boca (más alta atrás, más baja adelante, donde
    la boca baja), sobre el contorno de adentro de la cajita."""
    vs = []
    for x, z in caj.contorno(H - 0.02, caj.PARED):
        y = H - 0.022 - 0.01 * max(0.0, z) / caj.ARRIBA[1]
        vs.append(bm.verts.new(g2b((x, y - H / 2, z))))
    centro = bm.verts.new(g2b((0.0, H - 0.012 - H / 2, -0.003)))
    caras = [bm.faces.new((centro, vs[k], vs[(k + 1) % len(vs)])) for k in range(len(vs))]
    for f in caras:
        f.material_index = FRITA
    return caras


def construir(nombre=ID):
    mats = caj.materiales() + comun.cargar_materiales("M_PapaFrita")
    rnd = random.Random(SEMILLA)
    bm = bmesh.new()
    caj.cuerpo(bm, piso_adentro=False)
    papas = colchon(bm)
    for z_pie, z_boca, xs, alto in FILAS:
        for x in xs:
            pie = Vector((0.75 * x + rnd.uniform(-0.002, 0.002), Y_ABAJO, z_pie))
            boca = Vector((x, Y_BOCA, z_boca + rnd.uniform(-0.0015, 0.0015)))
            d = (boca - pie).normalized()
            largo = (H / 2 + alto + rnd.uniform(-0.006, 0.006) - Y_ABAJO) / d.y
            papas += baston_parado(bm, pie, pie + d * largo, LADO, rnd.uniform(-25, 25),
                                   afinar=rnd.uniform(0.8, 0.95))
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
                                    "16 bastones parados" % (alto, 1000 * (alto - caj.H), caj.H)))
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
