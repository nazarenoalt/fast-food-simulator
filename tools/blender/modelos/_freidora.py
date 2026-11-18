"""Medidas y piezas compartidas por `freidora`, `freidora_doble` y `colador_freidora` (SPEC-026).

Así la cuba, el aceite y el colador encajan siempre. Todo en ejes de Godot (X derecha, Y
arriba, Z hacia el cliente), como piezas.py; origen de la freidora = centro de la base, a nivel
del mostrador (guía 2.4, accesorios).

Freidora eléctrica de mostrador, **angosta y profunda** (pedido: dos tienen que entrar en una
porción de mesada; la más chica es la del carro kiosco, 0,57 m entre anclajes):
    - Cuerpo de acero de planta redondeada (torno), 0,26 de ancho con el labio, sobre 4 patas
      negras. Arriba, un labio que sobresale 4 mm y la boca de la cuba, que baja hasta
      Y_FONDO (paredes en M_MetalOscuro, para que se lea la profundidad).
    - Cuba de 0,206 × 0,31 (X × Z) concéntrica con el cuerpo, corrida hacia el vendedor (−Z).
    - Aceite `pieza_aceite` (M_Aceite, transparente): llena la cuba hasta Y_ACEITE.
    - Cabezal de control del lado del cliente (+Z), más alto que la cuba y con el techo
      inclinado hacia atrás. En su cara que mira al vendedor (−Z), la perilla y la luz piloto
      (`pieza_piloto`, la del hervidor), como pide la guía 5.3. El mango del colador apunta al
      vendedor.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "cocina"
PRESUPUESTO = 1500           # equipos de cocina (guía 3.1)
ACERO, OSCURO, NEGRO = range(3)

# Cuba (interior) y cuerpo, concéntricos.
CUBA_HX, CUBA_HZ, CUBA_CZ = 0.103, 0.155, -0.055
METER = 0.023                # espesor de la pared (cuerpo − cuba)
CUERPO_HX, CUERPO_HZ = CUBA_HX + METER, CUBA_HZ + METER     # 0,126 × 0,178
LABIO = 0.004
RADIO = 0.024
Y_PIE, Y_BORDE, Y_FONDO, Y_ACEITE = 0.02, 0.24, 0.105, 0.19
# Cabezal de control (+Z).
CAB_Z0, CAB_Z1 = CUBA_CZ + CUERPO_HZ, 0.237                  # 0,123 → 0,237
Y_CAB, BAJA_CAB = 0.33, 0.035
Y_CONTROLES = 0.29
ANCHO = 2 * (CUERPO_HX + LABIO)                               # 0,26
PROFUNDIDAD = CAB_Z1 - (CUBA_CZ - CUERPO_HZ - LABIO)          # 0,474
ALTO = 0.328                 # Y_CAB menos los 2 mm que baja el bisel del techo inclinado

# Colador (canasto): mide lo que la colisión del dato; apoya en el fondo de la cuba.
CANASTO = (0.19, 0.095, 0.27)


def pos_colador(cx=0.0):
    """Centro del canasto del colador apoyado en la cuba de la unidad que está en x = cx."""
    return (cx, Y_FONDO + CANASTO[1] / 2 + 0.0005, CUBA_CZ)


def materiales():
    return comun.cargar_materiales("M_Acero", "M_MetalOscuro", "M_PlasticoNegro")


def unidad(bm, cx):
    """Cuerpo + cuba de una freidora centrada en x = cx (sin cabezal)."""
    perfil = [
        (0.006, Y_PIE),
        (0.0, Y_PIE + 0.008),
        (0.0, Y_BORDE - 0.012),
        (-LABIO, Y_BORDE - 0.006),       # labio que sobresale
        (-LABIO, Y_BORDE),
        (0.019, Y_BORDE),                # canto plano de arriba
        (METER, Y_BORDE - 0.004),
        (METER, Y_FONDO),                # pared de la cuba
    ]
    e2.torno_rr(bm, perfil, CUERPO_HX, CUERPO_HZ, RADIO, segs=2, centro=(cx, 0.0, CUBA_CZ),
                mats=[ACERO, ACERO, ACERO, ACERO, ACERO, OSCURO, OSCURO], tapa_ini=True,
                tapa_fin=True)
    # La tapa de abajo del cuerpo y el fondo de la cuba: el fondo, oscuro como las paredes.
    for x in (cx - 0.095, cx + 0.095):
        for z in (CUBA_CZ - 0.15, CUBA_CZ + 0.15):
            piezas.cilindro(bm, 0.012, Y_PIE + 0.002, (x, (Y_PIE + 0.002) / 2, z), lados=12,
                            mat=NEGRO, tapas=(False, False))


def cabezal(bm, ancho, controles_x):
    """Cabezal de control de `ancho`, con una perilla y un aro de piloto por unidad."""
    alto = Y_CAB - Y_PIE
    caras = piezas.caja(bm, (ancho, alto, CAB_Z1 - CAB_Z0), (0.0, Y_PIE + alto / 2, (CAB_Z0 + CAB_Z1) / 2),
                        mat=ACERO, bisel=0.006, sin_abajo=True)
    eq.inclinar_arriba(caras, Y_CAB - 0.02, CAB_Z0, CAB_Z1, BAJA_CAB)
    for x_perilla, x_piloto in controles_x:
        eq.perilla(bm, x_perilla, Y_CONTROLES, CAB_Z0, NEGRO)
        eq.aro_piloto(bm, x_piloto, Y_CONTROLES, CAB_Z0, ACERO)


def aceite(nombre, cx):
    """`pieza_aceite`: el aceite que llena la cuba (transparente). Origen en su cara de arriba."""
    m, = comun.cargar_materiales("M_Aceite")
    bm = bmesh.new()
    e2.torno_rr(bm, [(METER + 0.0005, Y_FONDO + 0.0005), (METER + 0.0005, Y_ACEITE)],
                CUERPO_HX, CUERPO_HZ, RADIO, segs=2, centro=(cx, 0.0, CUBA_CZ), mats=0,
                tapa_ini=True, tapa_fin=True)
    return e2.objeto_en(nombre, bm, [m], (cx, Y_ACEITE, CUBA_CZ), sombreado="duro")


def colision(nombre, cxs, ancho_cabezal):
    """Cuba hueca (para que el colador quede adentro) y cabezal macizo (guía 6.1)."""
    cajas = []
    h = Y_BORDE - Y_FONDO
    for cx in cxs:
        cajas += [
            ((2 * CUERPO_HX, Y_FONDO, 2 * CUERPO_HZ), (cx, Y_FONDO / 2, CUBA_CZ)),
            ((METER, h, 2 * CUERPO_HZ), (cx - CUERPO_HX + METER / 2, Y_FONDO + h / 2, CUBA_CZ)),
            ((METER, h, 2 * CUERPO_HZ), (cx + CUERPO_HX - METER / 2, Y_FONDO + h / 2, CUBA_CZ)),
            ((2 * CUBA_HX, h, METER), (cx, Y_FONDO + h / 2, CUBA_CZ - CUERPO_HZ + METER / 2)),
        ]
    alto = Y_CAB - BAJA_CAB
    cajas.append(((ancho_cabezal, alto, CAB_Z1 - CAB_Z0), (0.0, alto / 2, (CAB_Z0 + CAB_Z1) / 2)))
    return eq.colision_cajas(nombre, cajas)


def chequeo_cuba(colador_canasto=CANASTO):
    """La cuba deja entrar el canasto del colador con aire y el aceite lo tapa casi entero."""
    aire_x = CUBA_HX - colador_canasto[0] / 2
    aire_z = CUBA_HZ - colador_canasto[2] / 2
    arriba = Y_FONDO + colador_canasto[1]
    ok = aire_x >= 0.005 and aire_z >= 0.005 and Y_ACEITE < arriba < Y_BORDE
    return ok, ("Cuba %.3f × %.3f × %.3f m: entra el colador (%.3f × %.3f × %.3f) con %.0f y %.0f mm "
                "de aire; aceite a %.3f, el canasto asoma hasta %.3f" % (
                    2 * CUBA_HX, Y_BORDE - Y_FONDO, 2 * CUBA_HZ, *colador_canasto,
                    aire_x * 1000, aire_z * 1000, Y_ACEITE, arriba))


def hoja(id_, titulo, raiz, visibles, coladores, revision, segunda=None):
    """Hoja: frente, vendedor, arriba con el colador, 3/4 de día y de atardecer, y sobre la
    barra chica. `segunda` = piezas de otra freidora para mostrar que entran dos en una
    porción de mesada (la del kiosco: 0,57 m)."""
    comun.preparar_revision()
    con = visibles + coladores
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", visibles, "frente", "dia"),
        ("Lado del vendedor: perilla, piloto y mango del colador · día", con, "vendedor", "dia"),
        ("Arriba: cuba con aceite y colador · día", con, "arriba", "dia"),
        ("3/4 · día", con, "tres_cuartos", "dia"),
        ("3/4 · atardecer", con, "tres_cuartos", "atardecer"),
    ])
    barra = e2.barra_chica()
    ancla = (-0.4, 0.95, 0.0)
    mover = [raiz] + [c for c in coladores if c.parent is None]
    for o in mover:
        o.location += g2b(ancla)
    extra = []
    etiqueta = "Sobre la barra chica (mostrador_izq) · día"
    if segunda:
        for o in segunda:
            if o.parent is None:
                o.location += g2b((ancla[0] + ANCHO + 0.01, ancla[1], ancla[2]))
        extra = segunda
        etiqueta = "Dos en una porción de mesada (2 × %.2f m ≤ 0,57 m del kiosco) · día" % ANCHO
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([(etiqueta, con + extra + barra, "vendedor_alto", "dia", con + extra, 2.2)])
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


# ── Armado completo (freidora y freidora_doble) ────────────────────────

def construir(id_, cxs):
    """Una freidora con una unidad por cada x de `cxs` y un solo cabezal. Con una unidad las
    piezas se llaman pieza_aceite, pieza_piloto y punto_colador; con dos, _1 y _2."""
    acero, oscuro, negro = materiales()
    piloto_m, = comun.cargar_materiales("M_PilotoApagado")
    bm = bmesh.new()
    for cx in cxs:
        unidad(bm, cx)
    ancho_cab = max(cxs) - min(cxs) + ANCHO
    cabezal(bm, ancho_cab, [(cx - 0.04, cx + 0.045) for cx in cxs])
    cuerpo = piezas.terminar(f"{id_}_cuerpo", bm, [acero, oscuro, negro])
    e2.suavizar_hasta(cuerpo, 31)
    sufijos = [""] if len(cxs) == 1 else [f"_{i + 1}" for i in range(len(cxs))]
    pilotos = [eq.lente_piloto(cx + 0.045, Y_CONTROLES, CAB_Z0, piloto_m, nombre=f"pieza_piloto{s}")
               for cx, s in zip(cxs, sufijos)]
    aceites = [aceite(f"pieza_aceite{s}", cx) for cx, s in zip(cxs, sufijos)]
    puntos = [piezas.punto(f"punto_colador{s}", pos_colador(cx)) for cx, s in zip(cxs, sufijos)]
    col = colision(id_, cxs, ancho_cab)
    raiz = piezas.raiz(id_, [cuerpo] + pilotos + aceites + puntos + [col])
    return {"raiz": raiz, "cuerpo": cuerpo, "pilotos": pilotos, "aceites": aceites,
            "puntos": puntos, "col": col, "cxs": cxs, "ancho": ancho_cab}


def visibles(m):
    return [m["cuerpo"]] + m["pilotos"] + m["aceites"]


def revisar(m, medidas):
    vis = visibles(m)
    res = comun.revisar(vis, PRESUPUESTO, medidas, origen="base", max_materiales=6)
    res.insert(1, chequeo_cuba())
    ok_puntos = all((p.location - g2b(pos_colador(cx))).length < 1e-6 for p, cx in zip(m["puntos"], m["cxs"]))
    res.append((ok_puntos, "%s en el centro del canasto apoyado (lo usa Surtido en accesorios.ron)"
                % ", ".join(p.name for p in m["puntos"])))
    return res


def exportar(m):
    return [m["raiz"]] + visibles(m) + m["puntos"] + [m["col"]]


def coladores(m):
    """Coladores apoyados en cada cuba (solo para las fotos)."""
    import colador_freidora
    objs = []
    for cx in m["cxs"]:
        c = colador_freidora.construir()["obj"]
        c.location = g2b(pos_colador(cx))
        objs.append(c)
    return objs
