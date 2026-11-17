"""Modelo: arbusto (id `arbusto`), para los canteros.

Genera:
    arte/fuentes/plaza/arbusto.blend
    godot/modelos/plaza/arbusto.glb
    docs/arte/revisiones/arbusto.jpg

Uso:
    python tools/blender/modelos/arbusto.py [--sin-hoja]

Forma: como la copa de los árboles (_arbol.py), en chico: 3 bollos irregulares facetados
(envolvente convexa de puntos sobre un elipsoide con ruido), cada uno con uno de los tres
verdes (M_Hojas1/2/3) y un 15 % de caras de otro, sombreado plano. Los bollos se aplastan
contra el piso (abajo planos) y la cara de abajo se borra (apoya en la tierra, guía 3.6).
Semilla fija: siempre da el mismo arbusto.

Medidas decididas: 1,00 de ancho (X) × 0,80 de alto (lista ≈ 1,0 × 0,8); la profundidad (Z)
sale de la forma. Se ajusta escalando al final, como la copa de los árboles.
Origen: centro de la base (la caja envolvente se centra en X y Z), a nivel del piso.
Sin colisión: hoy el juego no tiene arbustos, y una planta baja no hace falta que choque.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _arbol  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "arbusto"
PRESUPUESTO = 300
ANCHO, ALTO = 1.0, 0.8
SEMILLA = 512
PISO = 0.08   # los puntos más bajos se aplastan acá: los tres bollos apoyan en el piso
# centro (Godot), radios (x, y, z), puntos, verde (1, 2 o 3)
BOLLOS = [
    ((0.0, 0.34, 0.02), (0.42, 0.42, 0.4), 26, 2),
    ((-0.27, 0.24, 0.12), (0.3, 0.27, 0.3), 20, 1),
    ((0.27, 0.22, -0.1), (0.3, 0.26, 0.3), 20, 3),
]


def construir():
    rng = random.Random(SEMILLA)
    mats = comun.cargar_materiales("M_Hojas1", "M_Hojas2", "M_Hojas3")
    bm = bmesh.new()
    for centro, radios, puntos, verde in BOLLOS:
        m = verde - 1
        _arbol.bollo(bm, rng, centro, radios, puntos, m, [o for o in (0, 1, 2) if o != m],
                     aplastar=0.8, piso=PISO)
    # Ajuste de medidas: ancho X y alto justos, caja centrada en X y Z.
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]   # Blender Y = −Z de Godot
    zs = [v.co.z for v in bm.verts]
    s = ANCHO / (max(xs) - min(xs))
    sy = ALTO / (max(zs) - PISO)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    for v in bm.verts:
        v.co.x = (v.co.x - cx) * s
        v.co.y = (v.co.y - cy) * s
        v.co.z = (v.co.z - PISO) * sy
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats, sombreado="plano")
    raiz = piezas.raiz(ID, [cuerpo])
    return raiz, cuerpo


def revisar(cuerpo):
    mn, mx = plaza.limites([cuerpo])
    prof = mx.z - mn.z
    res = comun.revisar(cuerpo, PRESUPUESTO, (ANCHO, ALTO, prof), origen="base")
    res = plaza.reemplazar(res, "Medidas", res[0][0],
                           "Medidas: ancho X %.3f, alto %.3f, profundidad Z %.3f m (decididas: "
                           "%.2f × %.2f; lista ≈ 1,0 × 0,8)" % (mx.x - mn.x, mx.y - mn.y, prof,
                                                                ANCHO, ALTO))
    partes = _arbol._componentes(cuerpo)
    caras = [len(c) for c in partes]
    pol = cuerpo.data.polygons
    pisos = [min(cuerpo.data.vertices[i].co.z for f in c for i in pol[f].vertices) for c in partes]
    res.append((all(abs(z) < 1e-4 for z in pisos), "Los %d bollos apoyan en el piso" % len(partes)))
    res.append((all(30 <= n <= 80 for n in caras),
                "%d bollos de %s caras (como las copas: 30 a 80)" % (len(caras), ", ".join(map(str, caras)))))
    return res


def main():
    comun.escena_vacia()
    raiz, cuerpo = construir()
    revision = revisar(cuerpo)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [raiz, cuerpo])
    if "--sin-hoja" not in sys.argv:
        c = [cuerpo]
        plaza.hoja(ID, "arbusto · 1,0 × 0,8 m · para canteros", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.9, 0, 0.5))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
