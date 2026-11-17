"""Modelo: guirnalda de lamparitas (id `guirnalda_luces`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/guirnalda_luces_<tamaño>.blend
    godot/modelos/accesorios/guirnalda_luces_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/guirnalda_luces.jpg

Uso:
    python tools/blender/modelos/guirnalda_luces.py [--sin-hoja]

Forma: cable negro (6 lados, 4 mm de radio: la excepción de cables de la guía 2.2) que cuelga
en catenaria entre dos abrazaderas negras, con lamparitas tipo globo colgando de portalámparas
negros cada ≈ 18 cm (8 en el chico, 12 en el mediano, 18 en el grande). El cable se quiebra
apenas en cada lamparita, por el peso, como las de verdad.
Pensada para colgar entre los dos caños de adelante de cualquier techo de carrito (techo_plano,
techo_dos_aguas, techo_curvo, marquesina: todos tienen los caños en x = ±(ancho/2 − 0,03) y
z = profundidad/2 del carrito). Por eso tiene un tamaño por base, como los techos: el largo
lo da la distancia entre caños (1,54 / 2,34 / 3,34 m entre ejes). Las abrazaderas rodean el
caño (Ø 4 cm) a 2,08 m del piso, abajo del alero más bajo (2,12) y la lamparita más baja
queda a 1,80 m (pasa por arriba de la cabeza del cliente de 1,75).
Tamaño dinámico: una catenaria no se puede repetir de a tramos sin que se note; el script está
parametrizado por el largo (construir_largo), así que cualquier otro largo sale del mismo
código.

Medidas: largo = distancia entre caños + 2 × 0,028 (las abrazaderas) × 0,30 de alto × 0,056.
Origen: en el medio entre los ejes de los dos caños, a la altura del centro de las
abrazaderas (de donde cuelga; como el foco). En el carrito: (0, 2,08, profundidad/2).
Objetos (hijos del Empty `guirnalda_luces_<tamaño>`): guirnalda_luces_<tamaño>_cuerpo (cable,
portalámparas y abrazaderas, M_PlasticoNegro), pieza_lamparitas (M_LuzCalida: el juego las
prende de noche) y punto_luz (en el medio, a la altura de las lamparitas). Sin colisión
(cable colgado, como el foco).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _techo as t  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "guirnalda_luces"
PRESUPUESTO = 600            # lista (para 2,0 m); crece con el largo, como las rayas de los toldos
ALTO = 0.30
ALTURA_CARRITO = 2.08        # centro de las abrazaderas, medido desde el piso
CANO_R = t.CANO_R            # 0,02: caños de los techos
ABRAZADERA = (0.028, 0.0205, 0.03, 8)   # radio de afuera, de adentro, alto, lados
CABLE = (0.004, 6)
PASO = 0.18
PORTA = (0.011, 0.030, 6)    # radio, largo, lados
LAMPARITA = 0.028            # radio del globo (Ø 5,6 cm: se ve desde la fila)
FORMA = 1.4                  # parámetro de la catenaria (más chico = más "panza")
TAMANOS = t.TAMANOS


def catenaria(x, x0, flecha):
    g = (math.cosh(x / FORMA) - 1) / (math.cosh(x0 / FORMA) - 1)
    return -flecha * (1 - g)


def construir_largo(nombre, xp):
    """Guirnalda entre dos caños en x = ±xp (Godot, relativos al origen)."""
    negro, luz = comun.cargar_materiales("M_PlasticoNegro", "M_LuzCalida")
    ra, ri, ha, la = ABRAZADERA
    x0 = xp - ra + 0.004                         # el cable entra en la abrazadera
    largo = 2 * x0
    n = round(2 * xp / PASO) - 1
    xs = [-x0 + largo * (i + 1) / (n + 1) for i in range(n)]
    caida = PORTA[1] + 0.002 + 2 * LAMPARITA - 0.004     # del cable al fondo del globo
    abajo = -(ALTO - ha / 2)                     # lo más bajo, medido desde el origen
    g_max = max(1 - (math.cosh(x / FORMA) - 1) / (math.cosh(x0 / FORMA) - 1) for x in xs)
    flecha = (-abajo - caida) / g_max
    bm = bmesh.new()
    # Abrazaderas: anillo alrededor del caño (sin la cara de adentro: la tapa el caño).
    for sx in (-1, 1):
        c = (sx * xp, 0, 0)
        capas = [[bm.verts.new(g2b(p)) for p in a5.anillo_h((c[0], y, 0), r, la)]
                 for r, y in ((ri, -ha / 2), (ra, -ha / 2), (ra, ha / 2), (ri, ha / 2))]
        for a, b in zip(capas, capas[1:]):
            for k in range(la):
                bm.faces.new((a[k], a[(k + 1) % la], b[(k + 1) % la], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:                           # recalc no sabe con anillos abiertos
        f.normal_update()
        c = f.calc_center_median()
        eje = Vector((math.copysign(xp, c.x), 0, c.z))
        radial = c - eje
        if abs(f.normal.z) < 0.5 and f.normal.dot(radial) < 0:
            f.normal_flip()
        elif abs(f.normal.z) >= 0.5 and f.normal.z * c.z < 0:
            f.normal_flip()
    # Cable: un vértice en cada lamparita (se quiebra apenas por el peso).
    pts = [(x, catenaria(x, x0, flecha), 0) for x in [-x0] + xs + [x0]]
    a5.tubo(bm, pts, CABLE[0], CABLE[1])
    # Portalámparas: cilindros abiertos (arriba entra en el cable, abajo lo tapa el globo).
    bmb = bmesh.new()
    centros = []
    for x in xs:
        y = catenaria(x, x0, flecha)
        piezas.cilindro(bm, PORTA[0], PORTA[1] + 0.002, (x, y - (PORTA[1] + 0.002) / 2, 0),
                        lados=PORTA[2], tapas=(False, False))
        cy = y - PORTA[1] - 0.002 - LAMPARITA + 0.004
        piezas.esfera(bmb, LAMPARITA, (x, cy, 0), lados=6)
        centros.append(cy)
    cuerpo = piezas.terminar(f"{nombre}_cuerpo", bm, [negro])
    a5.e2.suavizar_hasta(cuerpo, 61)               # cable y portalámparas de 6 lados: redondos
    lamparitas = piezas.terminar("pieza_lamparitas", bmb, [luz], sombreado="suave")
    p_luz = piezas.punto("punto_luz", (0, catenaria(0, x0, flecha) - PORTA[1] - LAMPARITA, 0))
    raiz = piezas.raiz(nombre, [cuerpo, lamparitas, p_luz])
    return {"raiz": raiz, "cuerpo": cuerpo, "lamparitas": lamparitas, "punto_luz": p_luz,
            "n": n, "flecha": flecha, "xp": xp, "ancho": 2 * (xp + ra),
            "exportar": [raiz, cuerpo, lamparitas, p_luz]}


def construir(tam):
    b = t.base(tam)
    m = construir_largo(f"{ID}_{tam}", b.w / 2 - 0.03)     # = _techo.geometria_techo().xp
    m["base"] = b
    m["presup"] = max(PRESUPUESTO, int(round(PRESUPUESTO * m["ancho"] / 2.0, -1)))
    return m


def revisar(m):
    vis = [m["cuerpo"], m["lamparitas"]]
    medidas = (m["ancho"], ALTO, 2 * ABRAZADERA[0])
    res = comun.revisar(vis, m["presup"], medidas, origen="base")
    res = a5.chequeo_normales(res, vis)
    mn, mx = a5.limites(vis)
    ha = ABRAZADERA[2]
    ok = abs(mx.y - ha / 2) < 0.002 and abs(mn.x + mx.x) < 0.002 and abs(mn.z + mx.z) < 0.002
    res = a5.reemplazar(res, "Origen", ok, "Origen entre los ejes de los caños (x = ±%.2f), a la "
                        "altura del centro de las abrazaderas (tope en y = %.3f)" % (m["xp"], mx.y))
    b = m["base"]
    res.append((ALTURA_CARRITO + mn.y >= 1.79,
                "En el carrito: abrazaderas a %.2f m (abajo del alero más bajo, 2,12); la lamparita "
                "más baja a %.2f m" % (ALTURA_CARRITO, ALTURA_CARRITO + mn.y)))
    res.append((8 <= m["n"] if b.id == "barra_chica" else True,
                "%d lamparitas en pieza_lamparitas (M_LuzCalida) cada %.2f m, flecha del cable %.2f m"
                % (m["n"], 2 * m["xp"] / (m["n"] + 1), m["flecha"])))
    d = m["punto_luz"].matrix_world.translation
    res.append((abs(d.x) < 1e-4 and abs(d.y) < 1e-4, "punto_luz en el medio, a la altura de las "
                "lamparitas (y = %.3f)" % d.z))
    return res


def hoja():
    import techo_curvo
    import techo_dos_aguas
    import techo_plano
    comun.escena_vacia()
    comun.preparar_revision()
    techos = {"chico": techo_plano, "mediano": techo_dos_aguas, "grande": techo_curvo}
    esc = {}
    x = 0.0
    for tam, id_base in TAMANOS:
        b = t.leer_base(id_base)
        x += b.w / 2 + 0.25
        carro, _ = a5.carrito(id_base, x)
        tm = techos[tam].construir(tam)
        tm["raiz"].location = Vector((x, 0, 0)) + g2b(b.anclajes["techo"])
        m = construir(tam)
        a5.poner(m["raiz"], (0, ALTURA_CARRITO, b.p / 2), x)
        esc[tam] = {"todo": carro + tm["visibles"] + [m["cuerpo"], m["lamparitas"]], "x": x, "b": b,
                    "m": m, "techo": tm}
        x += b.w / 2 + 0.6
    # Para el detalle: un cubito invisible en la abrazadera izquierda del chico.
    ch = esc["chico"]
    bpy.ops.mesh.primitive_cube_add(size=0.34)
    cubo = bpy.context.active_object
    cubo.location = Vector((ch["x"], 0, 0)) + g2b((-ch["m"]["xp"] + 0.16, ALTURA_CARRITO - 0.12,
                                                   ch["b"].p / 2))
    cubo.hide_render = True
    persona = a5.persona()
    b = ch["b"]
    tres = [o for e in esc.values() for o in e["todo"]]
    solo_ch = [ch["m"]["cuerpo"], ch["m"]["lamparitas"]]
    pedidos = [
        ("Los tres tamaños, con techo plano / dos aguas / curvo · frente · día", tres, "frente", "dia"),
        ("Tamaño chico, sola · frente · día", solo_ch, "frente", "dia"),
        ("Chico en la barra chica con techo_plano · frente", ch["todo"] + [persona], "frente", "dia",
         None, a5.mover_persona((b.w / 2 + 0.5, 0, 0.3), ch["x"]), 1.05),
        ("Chico · 3/4 · día", ch["todo"], "tres_cuartos", "dia"),
        ("Chico · costado · cliente de 1,75 m en el mostrador", ch["todo"] + [persona], "costado", "dia",
         None, a5.mover_persona((0.0, 0, b.p / 2 + 0.3), ch["x"]), 1.05),
        ("Detalle: abrazadera en el caño y portalámparas", ch["todo"], "bajo", "dia", [cubo], None, 1.0),
        ("Chico · 3/4 · atardecer (las lamparitas brillan)", ch["todo"], "tres_cuartos", "atardecer"),
        ("Mediano con techo_dos_aguas · 3/4 · día", esc["mediano"]["todo"], "tres_cuartos", "dia"),
        ("Grande con techo_curvo · 3/4 · atardecer", esc["grande"]["todo"], "tres_cuartos", "atardecer"),
    ]
    return pedidos


def main():
    por_tamano = []
    ok = True
    for tam, _ in TAMANOS:
        comun.escena_vacia()
        m = construir(tam)
        bpy.context.view_layer.update()
        res = [(o, t.coma(x)) for o, x in revisar(m)]
        nombre = f"{ID}_{tam}"
        ok &= comun.imprimir_revision(nombre, res)
        a5.guardar_y_exportar(nombre, m["exportar"])
        por_tamano.append((tam, res))
    if "--sin-hoja" not in sys.argv:
        revision = t.juntar_revisiones(por_tamano)
        pedidos = hoja()
        a5.hoja(ID, "guirnalda_luces · chico / mediano / grande · entre los caños de adelante de "
                "un techo · 0,30 de alto", pedidos, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
