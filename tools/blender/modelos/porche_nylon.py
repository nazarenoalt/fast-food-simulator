"""Modelo: porche de nylon (id `porche_nylon`, familia `accesorios`; sin `.ron` todavía).

Genera:
    arte/fuentes/accesorios/porche_nylon.blend
    godot/modelos/accesorios/porche_nylon.glb
    docs/arte/revisiones/porche_nylon.jpg

Uso:
    python tools/blender/modelos/porche_nylon.py [--sin-hoja]

El cerramiento de nylon transparente que se arma al costado de los carros de chorizos de
esquina: un "porche" donde los clientes se paran a comer. Va aparte del carro (se pone y se
saca) y se engancha en el anclaje propuesto `lateral_der` del `carro_kiosco` (la punta +X), pero
no depende de esa base: es una estructura parada sola.

Forma (ejes de Godot, el porche crece hacia +X desde la cara del carro):
    - Marco de caño azul (M_AzulAcento, Ø 4 cm, 12 lados): 5 parantes (dos contra el carro, en
      x 0,05; dos en la punta, en x 1,78; uno en el medio de la punta, que hace de marco de la
      entrada), las vigas del techo, y travesaños a 0,10 y 1,00 m en los paños cerrados.
      Pies de acero.
    - Paños de nylon transparente (`M_BolsaPlastica`: con `M_PlasticoClaro` casi no se veía el
      paño): adelante (+Z) y atrás (−Z) enteros y en la punta solo la mitad +Z; la otra mitad de
      la punta queda abierta como entrada. Van como objeto aparte (`porche_nylon_panos`), para
      que la transparencia quede solo ahí.
    - Techito de lona (M_Lona) con caída hacia afuera (de 2,13 contra el carro a 1,99), en
      voladizo 0,32 m más allá de la punta y con un faldón corto. Contra el carro queda abajo del
      alero del carro_kiosco (2,15).
    - Barra para comer de acero contra el nylon de adelante, a 1,05 m (el alto del mostrador),
      apoyada en los parantes y en una pata en el medio.

Medidas: 2,10 × 2,13 × 1,84 (largo X con el voladizo; alto; fondo Z del techo). Los parantes,
1,73 × 1,70. Origen: el punto de enganche, en la cara del carro (x 0), centrado en Z, a nivel
del piso (no es el centro de la caja: el porche crece hacia +X).

Presupuesto: 2.000 (accesorio grande). Materiales (4): M_AzulAcento, M_Acero, M_Lona,
M_BolsaPlastica.
Objetos (hijos del Empty `porche_nylon`): porche_nylon_marco (caños, pies, barra, techito),
porche_nylon_panos (nylon) y `porche_nylon-colonly` (parantes, paños y barra; la entrada libre).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _plaza as plaza  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "porche_nylon"
FAMILIA = "accesorios"
PRESUPUESTO = 2000
AZUL, ACERO, LONA = range(3)
R_CANO, LADOS = 0.02, 12
X_IN, X_OUT, X_VOLADIZO = 0.05, 1.78, 2.10
ZP = 0.85                                   # parantes en z ±0,85 (el fondo del carro)
Z_TECHO = 0.92
Y_TECHO_IN, Y_TECHO_OUT = 2.12, 1.986       # arriba de las vigas, contra el carro y en el voladizo
LONA_E = 0.012
MEDIDAS = (X_VOLADIZO, Y_TECHO_IN + LONA_E, 2 * Z_TECHO)
Y_BARRA = 1.05


def y_techo(x):
    """Abajo de la lona (= arriba de las vigas) en x."""
    return Y_TECHO_IN + (Y_TECHO_OUT - Y_TECHO_IN) * x / X_VOLADIZO


def caño(bm, a, b, radio=R_CANO, mat=AZUL):
    plaza.caño(bm, a, b, radio, LADOS, mat=mat)


def construir():
    azul, acero, lona, nylon = comun.cargar_materiales("M_AzulAcento", "M_Acero", "M_Lona", "M_BolsaPlastica")
    bm = bmesh.new()
    yv = lambda x: y_techo(x) - R_CANO          # noqa: E731  (eje de las vigas)
    parantes = [(X_IN, -ZP), (X_IN, ZP), (X_OUT, -ZP), (X_OUT, ZP), (X_OUT, 0.0)]
    for x, z in parantes:
        caño(bm, (x, 0.012, z), (x, yv(x) - R_CANO + 0.002, z))
        piezas.caja(bm, (0.09, 0.012, 0.09), (x, 0.006, z), mat=ACERO, bisel=0.003)
    # Vigas del techo: a lo largo (z ±0,85, en voladizo hasta la punta) y de lado a lado.
    for z in (-ZP, ZP):
        caño(bm, (X_IN - R_CANO, yv(X_IN - R_CANO), z), (X_VOLADIZO - 0.03, yv(X_VOLADIZO - 0.03), z))
    for x in (X_IN, X_OUT, X_VOLADIZO - 0.03):
        caño(bm, (x, yv(x) - 0.001, -ZP - R_CANO), (x, yv(x) - 0.001, ZP + R_CANO))
    # Travesaños de los paños cerrados (adelante, atrás y la mitad +Z de la punta).
    for y in (0.10, 1.00):
        for z in (-ZP, ZP):
            caño(bm, (X_IN + R_CANO - 0.002, y, z), (X_OUT - R_CANO + 0.002, y, z))
        caño(bm, (X_OUT, y, R_CANO - 0.002), (X_OUT, y, ZP - R_CANO + 0.002))
    # Barra para comer contra el nylon de adelante, con una pata en el medio.
    zb0, zb1 = 0.58, ZP - R_CANO + 0.004
    piezas.caja(bm, (X_OUT - X_IN - 2 * R_CANO + 0.006, 0.025, zb1 - zb0), ((X_IN + X_OUT) / 2, Y_BARRA - 0.0125,
                (zb0 + zb1) / 2), mat=ACERO, bisel=0.006)
    xm = (X_IN + X_OUT) / 2
    caño(bm, (xm, 0.012, 0.74), (xm, Y_BARRA - 0.024, 0.74), radio=0.016, mat=ACERO)
    piezas.caja(bm, (0.08, 0.012, 0.08), (xm, 0.006, 0.74), mat=ACERO, bisel=0.003)
    # Techito de lona con caída hacia afuera y faldón en la punta.
    ang = math.degrees(math.atan2(Y_TECHO_IN - Y_TECHO_OUT, X_VOLADIZO))
    yc = y_techo(X_VOLADIZO / 2) + LONA_E / 2 / math.cos(math.radians(ang))
    piezas.caja(bm, (X_VOLADIZO / math.cos(math.radians(ang)), LONA_E, 2 * Z_TECHO), (X_VOLADIZO / 2, yc, 0),
                mat=LONA, rot=(0, 0, -ang))
    piezas.caja(bm, (LONA_E, 0.10, 2 * Z_TECHO), (X_VOLADIZO - LONA_E / 2, Y_TECHO_OUT - 0.05 + 0.002, 0), mat=LONA)
    marco = piezas.terminar(f"{ID}_marco", bm, [azul, acero, lona])

    # Paños de nylon (1 cm), por adentro de los caños, con el borde de arriba inclinado.
    bn = bmesh.new()

    def paño(x0, x1, z0, z1):
        """Paño vertical de (x0, z0) a (x1, z1) (en planta), del piso a las vigas."""
        e = 0.005
        vs = []
        for x, z in ((x0, z0), (x1, z1)):
            for y in (0.04, y_techo(x) - 2 * R_CANO - 0.01):
                for s in (-1, 1):
                    dz, dx = (s * e, 0) if z0 == z1 else (0, s * e)
                    vs.append(bn.verts.new(g2b((x + dx, y, z + dz))))
        a = vs[:4]
        b = vs[4:]
        # a/b: (abajo −e, abajo +e, arriba −e, arriba +e)
        caras = [(a[0], a[2], a[3], a[1]), (b[0], b[1], b[3], b[2]), (a[0], a[1], b[1], b[0]),
                 (a[2], b[2], b[3], a[3]), (a[0], b[0], b[2], a[2]), (a[1], a[3], b[3], b[1])]
        nuevas = [bn.faces.new(c) for c in caras]
        bmesh.ops.recalc_face_normals(bn, faces=nuevas)

    zn = ZP - R_CANO - 0.007
    paño(X_IN + R_CANO, X_OUT - R_CANO, zn, zn)
    paño(X_IN + R_CANO, X_OUT - R_CANO, -zn, -zn)
    xn = X_OUT - R_CANO - 0.007
    paño(xn, xn, R_CANO, ZP - R_CANO)
    panos = piezas.terminar(f"{ID}_panos", bn, [nylon])

    cajas = [((0.04, 2.0, 0.04), (x, 1.0, z), (0, 0, 0)) for x, z in parantes]
    cajas += [((X_OUT - X_IN, 1.95, 0.02), ((X_IN + X_OUT) / 2, 1.0, s * zn), (0, 0, 0)) for s in (-1, 1)]
    cajas += [((0.02, 1.95, ZP), (xn, 1.0, ZP / 2), (0, 0, 0)),
              ((X_OUT - X_IN, 0.025, zb1 - zb0), (xm, Y_BARRA - 0.0125, (zb0 + zb1) / 2), (0, 0, 0))]
    col = comun.colision_cajas(ID, cajas)
    raiz = piezas.raiz(ID, [marco, panos, col])
    return {"raiz": raiz, "marco": marco, "panos": panos, "visibles": [marco, panos], "colisiones": [col]}


def revisar(m):
    res = comun.revisar(m["visibles"], PRESUPUESTO, MEDIDAS, origen="base")
    bpy.context.view_layer.update()
    mn, mx = comun._limites(m["visibles"])
    ok = abs(mn.x) < 0.002 and abs(mn.z) < 0.002 and abs(mn.y + mx.y) < 0.002
    return comun.reemplazar_linea(res, "Origen", ok, "Origen en el punto de enganche: x = 0 en la cara del carro "
                                  "(de %.3f a %.3f), centrado en Z, y = 0 en el piso" % (mn.x, mx.x))


def hoja_revision(m, revision):
    import carro_kiosco as k
    import _rodante as r
    import tempfile
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = g2b((1.0, 0, 0.45))
    persona.rotation_euler.z = math.radians(-90)
    kio = k.construir()
    for o in [kio["raiz"]] + kio["colisiones"]:
        o.hide_render = True
    m["raiz"].location = g2b(k.ANCLAJES[6][1])
    dx = k.ANCLAJES[6][1][0]
    bpy.context.view_layer.update()
    solo = m["visibles"]
    con = m["visibles"] + kio["visibles"] + [persona]
    persona2 = persona.copy()
    bpy.context.scene.collection.objects.link(persona2)
    persona2.location = g2b((dx + 1.3, 0, 0.2))
    persona2.rotation_euler.z = math.radians(-90)
    persona.location = g2b((dx + 0.6, 0, 0.55))
    con.append(persona2)
    vistas = [
        ("Frente (+Z) · día", solo, "dia", ((dx + 1.05, 1.1, 30), (dx + 1.05, 1.1, 0), 50, 3.4)),
        ("Costado: la punta, con la entrada · día", solo, "dia", ((dx + 30, 1.1, 0), (dx, 1.1, 0), 50, 3.4)),
        ("3/4 · día", solo, "dia", ((dx + 4.6, 2.6, 4.2), (dx + 1.0, 1.0, 0), 35, None)),
        ("3/4 · atardecer", solo, "atardecer", ((dx - 1.6, 2.6, 4.6), (dx + 1.0, 1.0, 0), 35, None)),
        ("En el carro_kiosco, con clientes de 1,75 m · día", con, "dia",
         ((dx + 5.2, 2.4, 4.4), (dx - 0.4, 1.2, 0), 30, None)),
        ("En el carro_kiosco, desde la entrada · día", con, "dia",
         ((dx + 4.2, 1.7, -3.6), (dx - 0.2, 1.2, 0.2), 30, None)),
    ]
    tmp = Path(tempfile.mkdtemp())
    todos = {o for v in vistas for o in v[1]}
    cuadros = []
    for etiqueta, objs, luz, (pos, mira, lente, orto) in vistas:
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        r.camara(pos, mira, lente, orto)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    comun.componer_hoja("porche_nylon · 2,10 × 2,13 × 1,84 m · accesorio: nylon y caño azul (lateral_der)", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([m["raiz"]] + m["visibles"] + m["colisiones"], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
