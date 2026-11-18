"""Modelo: feta de queso (id `feta_queso`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/feta_queso.blend
    godot/modelos/comida/feta_queso.glb
    docs/arte/revisiones/feta_queso.jpg

Uso:
    blender -b -P tools/blender/modelos/feta_queso.py
    python tools/blender/modelos/feta_queso.py

Forma: feta cuadrada de 0,09 × 0,003 × 0,09 (lista de modelos), M_Amarillo, sin bisel.
Las dos versiones de la lista ("esquinas caídas al derretirse") son la MISMA malla:
- La base es la feta plana (la que mide 0,09 × 0,003 × 0,09).
- Una forma clave (shape key → blend shape `derretida` en Godot) baja las cuatro esquinas
  9 mm y las mete un poco hacia el centro, como cuando el queso se derrite sobre el
  medallón. El juego puede pasar de una a otra (0 → 1) mientras se derrite.
El centro de la feta es un octógono plano que llega hasta r = 0,053 (el borde de arriba del
medallón): de ahí para afuera solo caen las cuatro puntas, así la feta derretida se apoya
arriba de la carne sin atravesarla. En cada esquina la cara de arriba y la de abajo se
juntan en un vértice (la punta se afina, como el queso derretido), y así entra en 36
triángulos (presupuesto 40).
Sombreado: suave en las caras de arriba y abajo (también donde caen las puntas) y canto
marcado, como una feta cortada (si no, la luz mezcla la cara con el canto en las puntas).
En la hamburguesa armada va la versión derretida ya aplicada, como `pieza_queso`.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "feta_queso"
LADO, ALTO = 0.09, c4.ALTO_QUESO
MEDIDAS = (LADO, ALTO, LADO)
PRESUPUESTO = 40
M, H = LADO / 2, ALTO / 2
R_PLANO = 0.053                       # hasta acá la feta queda plana (borde del medallón)
E = math.sqrt(R_PLANO ** 2 - M ** 2)  # donde el borde cruza ese radio (0,028)
CAIDA = 0.009                         # cuánto bajan las puntas, desde la cara de arriba
METER = 0.95                          # las puntas derretidas se acercan un poco al centro


def esquina(sx, sz, derretida):
    """Punta de la feta (Godot) para `derretida` de 0 (plana) a 1."""
    f = 1 + (METER - 1) * derretida
    return (sx * M * f, (H - CAIDA) * derretida, sz * M * f)


def construir(nombre=ID, derretida=0.0, forma_clave=True):
    """derretida = cuánto se aplica en la malla (0 plana, 1 derretida). forma_clave = agrega
    la forma clave `derretida` (para el .glb de la feta suelta)."""
    (material,) = comun.cargar_materiales("M_Amarillo")
    bm = bmesh.new()
    arriba, abajo, puntas = [], [], []
    # Alrededor, desde +X hacia +Z: E antes de la esquina, la esquina, E después.
    for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        if sx * sz > 0:
            pa, pb = (sx * M, sz * E), (sx * E, sz * M)
        else:
            pa, pb = (sx * E, sz * M), (sx * M, sz * E)
        for (x, z) in (pa, pb):
            arriba.append(bm.verts.new(g2b((x, H, z))))
            abajo.append(bm.verts.new(g2b((x, -H, z))))
        puntas.append(bm.verts.new(g2b(esquina(sx, sz, derretida))))
    n = len(arriba)  # 8: dos por esquina (a, b)
    bm.faces.new(arriba)
    bm.faces.new(list(reversed(abajo)))
    for i in range(4):
        a, b, p = 2 * i, 2 * i + 1, puntas[i]
        bm.faces.new((arriba[a], p, arriba[b]))          # punta, arriba
        bm.faces.new((abajo[b], p, abajo[a]))            # punta, abajo
        bm.faces.new((arriba[a], abajo[a], p))           # costados de la punta
        bm.faces.new((arriba[b], p, abajo[b]))
        sig = (b + 1) % n                                # canto recto hasta la otra esquina
        bm.faces.new((arriba[b], abajo[b], abajo[sig], arriba[sig]))
    # Canto marcado (es una feta cortada); la caída de las puntas, suave.
    obj = e2.objeto_en(nombre, bm, [material], (0, 0, 0), sombreado="duro")
    e2.suavizar_hasta(obj, 55)
    if forma_clave:
        obj.shape_key_add(name="Basis")
        clave = obj.shape_key_add(name="derretida")
        for v in obj.data.vertices:
            x, y = v.co.x, v.co.y
            if abs(abs(x) - M) < 1e-6 and abs(abs(y) - M) < 1e-6:
                p = g2b(esquina(math.copysign(1, x), -math.copysign(1, y), 1.0))
                clave.data[v.index].co = p
        obj.data.shape_keys.use_relative = True
        clave.value = 0.0
        obj.active_shape_key_index = 0
    return obj


def chequeo_forma_clave(obj):
    claves = obj.data.shape_keys
    ok = claves is not None and "derretida" in claves.key_blocks
    if ok:
        k = claves.key_blocks["derretida"]
        bajan = sum(1 for a, b in zip(obj.data.vertices, k.data) if (a.co - b.co).length > 1e-6)
        ok = bajan == 4
    return ok, "Forma clave `derretida` (blend shape): mueve solo las 4 puntas"


def hoja_revision(queso, revision):
    comun.preparar_revision()
    queso.location.z = H
    derr = construir("ref_derretida", derretida=1.0, forma_clave=False)
    import medallon
    carne = medallon.construir("ref_medallon")
    carne.data.materials[0] = c4.material_ref("carne_cocida", c4.COCCION_CARNE[1][1])
    carne.location = (0.35, 0, c4.ALTO_CARNE / 2)
    derr.location = (0.35, 0, c4.ALTO_CARNE + H)
    derr.rotation_euler = (0, 0, math.radians(20))
    ref = c4.pan_de_escala(0.0, -0.11)
    solo = [queso]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("Arriba · día", solo, "arriba", "dia"),
        ("3/4 · día (plana)", solo, "tres_cuartos", "dia"),
        ("Derretida sobre el medallón (cocido) · día", [derr, carne], "tres_cuartos", "dia"),
        ("Derretida · costado bajo · atardecer", [derr, carne], "bajo", "atardecer"),
        ("Al lado de un pan de pancho · día", [queso, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · 0,09 × 0,003 × 0,09 m · forma clave `derretida`", cuadros, revision)


def main():
    comun.escena_vacia()
    queso = construir()
    revision = comun.revisar(queso, PRESUPUESTO, MEDIDAS, origen="centro")
    revision.insert(1, chequeo_forma_clave(queso))
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [queso])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(queso, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
