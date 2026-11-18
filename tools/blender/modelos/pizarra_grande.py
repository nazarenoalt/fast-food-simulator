"""Modelo: pizarra de menú grande (id `pizarra_grande`, lista de modelos, etapa 5).

Genera:
    arte/fuentes/accesorios/pizarra_grande.blend
    godot/modelos/accesorios/pizarra_grande.glb
    docs/arte/revisiones/pizarra_grande.jpg

Uso:
    python tools/blender/modelos/pizarra_grande.py [--sin-hoja]

Forma: pizarra de caballete (la "pizarra de vereda" de los bares y carritos), parada en el
piso al lado del carrito: dos hojas de 0,60 × 0,91 con marco de madera (M_Madera, moldura de
4 cm y 2,5 cm de espesor) abiertas 12° cada una, unidas arriba por dos bisagras y abajo por
dos cadenitas (M_Hierro) que no las dejan abrirse más. Las dos pizarras van **en blanco**
(guía 4.5, como pizarra_precios): `pieza_pizarra` (la de adelante, +Z) y `pieza_pizarra_2`
(la de atrás, −Z), cada una con su cara de afuera mapeada (UV de 0 a 1, derecha para el que
la mira), para que el juego escriba el menú.
Medidas: 0,60 × 0,90 de frente (lista ≈ 0,6 × 0,9). La lista dice 0,05 de fondo: es la
pizarra cerrada; abierta, para que se pare sola, ocupa 0,43 de fondo.
Origen: centro de la base, a nivel del piso.
Objetos (hijos del Empty `pizarra_grande`): pizarra_grande_cuerpo (marcos, bisagras y
cadenitas), pieza_pizarra, pieza_pizarra_2 y `pizarra_grande-colonly` (una caja inclinada por
hoja).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
from pizarra_precios import girar_x, mapear_cara  # noqa: E402

ID = "pizarra_grande"
PRESUPUESTO = 400
ANCHO, ALTO = 0.60, 0.90
ANGULO = 12.0                    # cada hoja, desde la vertical
ESPESOR, MOLDURA = 0.025, 0.04
HUNDIDA = 0.004                  # la pizarra queda 4 mm detrás del frente del marco
CADENA_Y, CADENA_X = 0.30, 0.28
BISAGRA_X = 0.20


def largo_hoja():
    """Largo de cada hoja para que el caballete abierto mida ALTO."""
    a = math.radians(ANGULO)
    return (ALTO + 0.002 - ESPESOR * math.sin(a)) / math.cos(a)   # + lo que se come el bisel


def hoja(bm, bm_piz, L):
    """Una hoja parada (frente en z = 0, base en y = 0), inclinada hacia atrás sobre su canto
    de abajo atrás y corrida para que el canto de arriba atrás quede en z = 0."""
    previas, previas_p = set(bm.faces), set(bm_piz.faces)
    a5.marco(bm, ANCHO, L, ESPESOR, MOLDURA, mat=0, bisel=0.004)
    piz = (ANCHO - 2 * MOLDURA, L - 2 * MOLDURA, ESPESOR - HUNDIDA)
    caras = piezas.caja(bm_piz, piz, (0, L / 2, -HUNDIDA - piz[2] / 2), mat=0)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)     # −Y Blender = +Z Godot
    giro = Matrix.Rotation(math.radians(-ANGULO), 3, "X")
    mapear_cara(bm_piz, frente, Vector((1, 0, 0)), giro @ Vector((0, 0, 1)))
    dz = ESPESOR + L * math.sin(math.radians(ANGULO))
    for b, prev in ((bm, previas), (bm_piz, previas_p)):
        vs = list({v for f in b.faces if f not in prev for v in f.verts})
        bmesh.ops.rotate(b, verts=vs, cent=g2b((0, 0, -ESPESOR)), matrix=giro)
        bmesh.ops.translate(b, verts=vs, vec=g2b((0, 0, dz)))
        yield vs


def colision_hoja(L, signo):
    """(medidas, centro, rot) de la caja de una hoja (signo +1 adelante, −1 atrás)."""
    c = girar_x((0, L / 2, ESPESOR / 2), -ANGULO)           # relativo al canto de abajo atrás
    z = c[2] + L * math.sin(math.radians(ANGULO))          # + corrimiento de hoja()
    return ((ANCHO, L, ESPESOR), (0, c[1], signo * z), (-signo * ANGULO, 0, 0))


def construir():
    madera, pizarra, hierro = comun.cargar_materiales("M_Madera", "M_Pizarra", "M_Hierro")
    L = largo_hoja()
    bm, bm_p1, bm_p2 = bmesh.new(), bmesh.new(), bmesh.new()
    list(hoja(bm, bm_p1, L))
    # La hoja de atrás: la misma, girada 180° sobre el eje vertical.
    atras = list(hoja(bm, bm_p2, L))
    media_vuelta = Matrix.Rotation(math.pi, 3, "Z")
    bmesh.ops.rotate(bm, verts=atras[0], matrix=media_vuelta)
    bmesh.ops.rotate(bm_p2, verts=list(bm_p2.verts), matrix=media_vuelta)
    # Bisagras arriba, en la unión de las dos hojas.
    a = math.radians(ANGULO)
    y_union = L * math.cos(a)
    for sx in (-1, 1):
        piezas.cilindro(bm, 0.007, 0.05, (sx * BISAGRA_X, y_union - 0.012, 0), eje="x", lados=6, mat=1)
    # Cadenitas: de la espalda de una hoja a la otra, con un poco de panza.
    z_esp = L * math.sin(a) * (1 - CADENA_Y / y_union) + 0.003
    for sx in (-1, 1):
        x = sx * CADENA_X
        a5.tubo(bm, [(x, CADENA_Y, z_esp), (x, CADENA_Y - 0.025, 0), (x, CADENA_Y, -z_esp)], 0.004, 6, mat=1)
    # Apoyo justo en el piso (el bisel del canto deja el marco 1 mm en el aire).
    abajo = min(v.co.z for v in bm.verts)
    for b in (bm, bm_p1, bm_p2):
        bmesh.ops.translate(b, verts=b.verts, vec=Vector((0, 0, -abajo)))
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [madera, hierro])
    a5.e2.suavizar_hasta(cuerpo, 61)          # cadenitas y bisagras de 6 lados
    p1 = piezas.terminar("pieza_pizarra", bm_p1, [pizarra])
    p2 = piezas.terminar("pieza_pizarra_2", bm_p2, [pizarra])
    col = plaza.colision_cajas(ID, [colision_hoja(L, s) for s in (1, -1)])
    raiz = piezas.raiz(ID, [cuerpo, p1, p2, col])
    return raiz, cuerpo, p1, p2, col


def revisar(cuerpo, p1, p2):
    vis = [cuerpo, p1, p2]
    mn, mx = a5.limites(vis)
    fondo = mx.z - mn.z
    res = comun.revisar(vis, PRESUPUESTO, (ANCHO, ALTO, fondo), origen="base")
    res = a5.reemplazar(res, "Medidas", res[0][0], res[0][1] + " · de fondo, abierta (la lista "
                        "da 0,05: la pizarra cerrada)")
    res = a5.chequeo_normales(res, vis)
    uv_ok = all(o.data.uv_layers and any(
        max(o.data.uv_layers[0].data[i].uv.x for i in p.loop_indices) > 0.99 for p in o.data.polygons)
        for o in (p1, p2))
    res.append((uv_ok, "pieza_pizarra (+Z) y pieza_pizarra_2 (−Z) en blanco, con la cara de afuera "
                       "mapeada (UV de 0 a 1) para que el juego escriba"))
    return res


def hoja_revision(cuerpo, p1, p2, revision):
    comun.preparar_revision()
    solo = [cuerpo, p1, p2]
    carro, b = a5.carrito("barra_chica")
    copias = [a5.e2.copiar(o, f"ref_{o.name}") for o in solo]
    for c in copias:
        c.location = g2b((1.25, 0, 0.55))
        c.rotation_euler.z = math.radians(-25)
    persona = a5.persona()
    escena = carro + copias + [persona]
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado: abierta 12° por hoja, cadenitas · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 desde atrás (pieza_pizarra_2) · día", solo, "vendedor", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Con la persona de 1,75 m · día", solo + [persona], "tres_cuartos", "dia", None,
         a5.mover_persona((0.6, 0, -0.1))),
        ("Al lado de la barra chica · día", escena, "tres_cuartos", "dia", None,
         a5.mover_persona((0.3, 0, 1.05)), 1.0),
        ("Ídem · a la altura de los ojos", escena[:-1], "bajo", "dia", None, None, 1.0),
        ("Ídem · atardecer", escena[:-1], "tres_cuartos", "atardecer", None, None, 1.0),
    ]
    a5.hoja(ID, "pizarra_grande · 0,60 × 0,90 m (0,43 de fondo, abierta) · caballete, pizarras en "
            "blanco", pedidos, revision)


def main():
    comun.escena_vacia()
    raiz, cuerpo, p1, p2, col = construir()
    bpy.context.view_layer.update()
    revision = revisar(cuerpo, p1, p2)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [raiz, cuerpo, p1, p2, col], uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, p1, p2, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
