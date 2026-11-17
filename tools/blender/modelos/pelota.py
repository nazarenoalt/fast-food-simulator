"""Modelo: pelota de fútbol (id `pelota`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/pelota.blend
    godot/modelos/plaza/pelota.glb
    docs/arte/revisiones/pelota.jpg

Uso:
    python tools/blender/modelos/pelota.py [--sin-hoja]

Forma: la pelota clásica de gajos: un icosaedro truncado (12 pentágonos negros de
M_PlasticoNegro y 20 hexágonos de M_BlancoCrema). Cada gajo se parte en triángulos desde
su centro, que se empuja hasta la esfera: así se ve redonda y los gajos se distinguen por
color, no por relieve. Sombreado suave, con arista marcada en el cambio de color.

Medidas (lista: Ø 0,22): 0,22 × 0,22 × 0,22 (la caja envolvente; el icosaedro está puesto con
sus ejes de simetría sobre X, Y y Z, así mide lo mismo en las tres direcciones).
Objeto con física (guía 6.1): origen en el centro, sin `-colonly` (la colisión la arma el
juego, una esfera de radio 0,11).

Objetos (hijo del Empty `pelota`): pelota_cuerpo.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "pelota"
PRESUPUESTO = 300   # lista de modelos
DIAMETRO = 0.22
BLANCO, NEGRO = 0, 1


def icosaedro():
    f = (1 + math.sqrt(5)) / 2
    vs = [Vector(v) for v in ((-1, f, 0), (1, f, 0), (-1, -f, 0), (1, -f, 0),
                              (0, -1, f), (0, 1, f), (0, -1, -f), (0, 1, -f),
                              (f, 0, -1), (f, 0, 1), (-f, 0, -1), (-f, 0, 1))]
    largo = (vs[0] - vs[1]).length
    vecinos = {i: [j for j in range(12) if j != i and abs((vs[i] - vs[j]).length - largo) < 1e-6]
               for i in range(12)}
    caras = sorted({tuple(sorted((i, j, k))) for i in range(12) for j in vecinos[i]
                    for k in vecinos[i] if j < k and k in vecinos[j]})
    return vs, vecinos, caras


def construir():
    blanco, negro = comun.cargar_materiales("M_BlancoCrema", "M_PlasticoNegro")
    vs, vecinos, caras = icosaedro()
    bm = bmesh.new()
    puntos = {}

    def punto(i, j):
        """Vértice del gajo sobre la arista i→j, a un tercio de i."""
        if (i, j) not in puntos:
            puntos[(i, j)] = bm.verts.new(vs[i] + (vs[j] - vs[i]) / 3)
        return puntos[(i, j)]

    gajos = []
    for i in range(12):   # pentágonos: los vecinos ordenados alrededor de i
        n = vs[i].normalized()
        u = (vs[vecinos[i][0]] - vs[i]).normalized()
        w = n.cross(u)
        orden = sorted(vecinos[i], key=lambda j: math.atan2((vs[j] - vs[i]).dot(w), (vs[j] - vs[i]).dot(u)))
        gajos.append(([punto(i, j) for j in orden], NEGRO))
    for a, b, c in caras:  # hexágonos
        gajos.append(([punto(a, b), punto(b, a), punto(b, c), punto(c, b), punto(c, a), punto(a, c)], BLANCO))
    for vertices, mat in gajos:
        centro = bm.verts.new(sum((v.co for v in vertices), Vector()) / len(vertices))
        for k in range(len(vertices)):
            f = bm.faces.new((vertices[k], vertices[(k + 1) % len(vertices)], centro))
            f.material_index = mat
    # Todo sobre la esfera, y a la medida (la caja envolvente justa).
    r = max(v.co.length for v in bm.verts)
    for v in bm.verts:
        v.co = v.co.normalized() * r
    ext = max(max(abs(v.co[k]) for v in bm.verts) for k in range(3))
    bmesh.ops.scale(bm, vec=Vector((1, 1, 1)) * (DIAMETRO / 2 / ext), verts=bm.verts)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [blanco, negro], sombreado="suave")
    raiz = piezas.raiz(ID, [cuerpo])
    return {"raiz": raiz, "cuerpo": cuerpo}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, (DIAMETRO,) * 3, origen="centro")
    m = mod["cuerpo"].data
    negros = sum(1 for p in m.polygons if p.material_index == NEGRO)
    blancos = sum(1 for p in m.polygons if p.material_index == BLANCO)
    rs = [v.co.length for v in m.vertices]
    res.append((negros == 60 and blancos == 120 and max(rs) - min(rs) < 1e-6,
                "12 pentágonos negros y 20 hexágonos blancos (%d + %d triángulos), todos los vértices "
                "sobre la esfera (r %.4f)" % (negros, blancos, max(rs))))
    sin_col = not any(o.name.endswith("-colonly") for o in bpy.data.objects)
    res.append((sin_col, "Con física: origen en el centro y sin -colonly (guía 6.1)"))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        # La pelota va apoyada en el piso para las fotos (el origen está en el centro).
        mod["cuerpo"].location.z = DIAMETRO / 2
        bpy.context.view_layer.update()  # si no, la primera foto encuadra la pelota en z = 0
        plaza.hoja(ID, "pelota · Ø 0,22 m · con física", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.35, 0, 0.1))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
