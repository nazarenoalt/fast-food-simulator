"""Modelo: banqueta alta (id `banqueta`, lista de modelos, etapa 5).

Genera:
    arte/fuentes/accesorios/banqueta.blend
    godot/modelos/accesorios/banqueta.glb
    docs/arte/revisiones/banqueta.jpg

Uso:
    python tools/blender/modelos/banqueta.py [--sin-hoja]

Forma: banqueta de bar para que los clientes coman al lado del carrito. Asiento redondo de
Ø 0,35 con el canto redondeado, pintado del color del carrito (`pieza_pintura`,
M_PinturaCarrito: el juego lo tiñe igual que el cuerpo del carrito), sobre un plato de acero
y 4 patas de caño de acero abiertas hacia el piso, con regatones de goma y un aro apoyapié
a 0,26 m.
Medidas: Ø 0,35 × 0,75 (arriba del asiento a 0,75 m). Las patas apoyan dentro del círculo
del asiento (la huella no sale de Ø 0,35).
Origen: centro de la base, a nivel del piso.
Objetos (hijos del Empty `banqueta`): pieza_pintura (asiento), banqueta_cuerpo (acero y
goma) y `banqueta-colonly` (un cilindro del tamaño total).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "banqueta"
PRESUPUESTO = 400
RADIO, ALTO = 0.175, 0.75
MEDIDAS = (2 * RADIO, ALTO, 2 * RADIO)
ASIENTO_ABAJO = 0.705
PLATO = (0.115, 0.015)           # radio, espesor (debajo del asiento)
PATA_R, PATA_LADOS = 0.0115, 8   # caño de 23 mm (guía 3.2: < 1,5 cm → 8 lados)
PATA_ARRIBA_R = 0.085            # dónde se agarran las patas al plato
PATA_ABAJO_R = 0.150             # dónde apoyan (adentro del círculo del asiento)
REGATON = 0.03                   # alto de la goma del pie
ARO_Y, ARO_R = 0.26, 0.009       # aro apoyapié


def r_pata(y):
    """Radio (desde el eje) del centro de la pata a la altura y."""
    y1 = ASIENTO_ABAJO - PLATO[1]
    return PATA_ABAJO_R + (PATA_ARRIBA_R - PATA_ABAJO_R) * y / y1


def aro(bm, lados=6, tramos=8):
    """Aro apoyapié: octógono horizontal que pasa por el centro de las patas a ARO_Y, caño de
    `lados` lados. Cada anillo se arma con la vertical (Y) y la dirección radial, que en un
    aro horizontal nunca se alinean con el caño: así todos los anillos giran igual. (Con
    a5.tubo, que toma una referencia fija, los anillos de ±Z se aplastaban en un punto y los
    de al lado quedaban dados vuelta: eran las puntitas al lado de las patas.) En cada
    quiebre el anillo se estira 1/cos(22,5°) hacia afuera (inglete), para no afinarse."""
    ra = r_pata(ARO_Y)
    estirar = 1 / math.cos(math.pi / tramos)
    previas = set(bm.faces)
    anillos, eje = [], []
    for i in range(tramos):
        a = 2 * math.pi * i / tramos
        radial = (math.cos(a), 0.0, math.sin(a))
        c = (ra * radial[0], ARO_Y, ra * radial[2])
        eje.append(piezas.g2b(c))
        anillo = []
        for k in range(lados):
            t = 2 * math.pi * k / lados
            dy, dr = ARO_R * math.cos(t), ARO_R * math.sin(t) * estirar
            anillo.append(bm.verts.new(piezas.g2b((c[0] + dr * radial[0], c[1] + dy, c[2] + dr * radial[2]))))
        anillos.append(anillo)
    for a, b in zip(anillos, anillos[1:] + anillos[:1]):
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k])).material_index = 0
    a5._hacia_afuera([f for f in bm.faces if f not in previas], eje + eje[:1])


def construir():
    pintura, acero, goma = comun.cargar_materiales("M_PinturaCarrito", "M_Acero", "M_Goma")
    # Asiento: disco con el canto redondeado (16 lados, guía 3.2), la tapa de abajo se ve.
    bm = bmesh.new()
    perfil = [(RADIO - 0.010, ASIENTO_ABAJO), (RADIO, ASIENTO_ABAJO + 0.012),
              (RADIO, ALTO - 0.014), (RADIO - 0.012, ALTO)]
    plaza.torno(bm, perfil, 16, tapa_abajo=True, tapa_arriba=True)
    asiento = piezas.terminar("pieza_pintura", bm, [pintura])

    bm = bmesh.new()
    y1 = ASIENTO_ABAJO - PLATO[1]
    # Plato bajo el asiento (sin tapa de arriba: queda pegada al asiento).
    plaza.torno(bm, [(PLATO[0], y1), (PLATO[0], ASIENTO_ABAJO)], 12, mats=[0], tapa_abajo=True)
    # Patas en las diagonales: goma abajo, acero hasta el plato (anillos horizontales).
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pts = [(r_pata(y) * math.cos(a), y, r_pata(y) * math.sin(a)) for y in (0.0, REGATON, y1)]
        a5.poste(bm, pts, PATA_R, PATA_LADOS, mats=[1, 0])
    aro(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero, goma])
    a5.e2.suavizar_hasta(cuerpo, 46)   # patas y aro de 8 lados: redondos, no facetados

    col = a5.colision_cilindro(ID, RADIO, 0.0, ALTO)
    raiz = piezas.raiz(ID, [asiento, cuerpo, col])
    return raiz, asiento, cuerpo, col


def revisar(asiento, cuerpo, col):
    res = comun.revisar([asiento, cuerpo], PRESUPUESTO, MEDIDAS, origen="base")
    res = a5.chequeo_normales(res, [asiento, cuerpo])
    mn, mx = a5.limites([cuerpo])
    huella = max(math.hypot(v.x, v.z) for v in a5.e2.verts_godot(cuerpo) if v.y < 0.001)
    res.append((huella <= RADIO, "Las 4 patas apoyan adentro del asiento (huella hasta r = %.3f)" % huella))
    ma, xa = a5.limites([asiento])
    res.append((abs(xa.y - ALTO) < 0.001 and abs(ma.y - ASIENTO_ABAJO) < 0.001,
                "pieza_pintura (M_PinturaCarrito, sigue el color del carrito): asiento de %.3f a %.3f"
                % (ma.y, xa.y)))
    res.append(a5.chequeo_cilindro_colision(col, RADIO, 0.0, ALTO))
    return res


def hoja_revision(raiz, asiento, cuerpo, revision):
    comun.preparar_revision()
    solo = [asiento, cuerpo]
    carro, b = a5.carrito("barra_chica")
    # Dos banquetas copiadas al frente del carrito, donde los clientes comen.
    copias = []
    for i, (x, z) in enumerate(((0.55, 0.75), (-0.05, 0.8))):
        for o in solo:
            c = a5.e2.copiar(o, f"ref_{o.name}_{i}")
            c.location = piezas.g2b((x, 0, z))
            copias.append(c)
    persona = a5.persona()
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 bajo · día (aro apoyapié y regatones)", solo, "bajo", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Arriba · día", solo, "arriba", "dia"),
        ("Con la persona de 1,75 m · día", solo + [persona], "tres_cuartos", "dia", None,
         a5.mover_persona((0.45, 0, -0.1))),
        ("Al frente de la barra chica · 3/4 · día", carro + copias + [persona], "tres_cuartos", "dia",
         None, a5.mover_persona((1.15, 0, 0.75)), 1.05),
        ("Al frente de la barra chica · atardecer", carro + copias, "tres_cuartos", "atardecer", None,
         None, 1.05),
    ]
    a5.hoja(ID, "banqueta · Ø 0,35 × 0,75 m · accesorio (asiento del color del carrito)",
            pedidos, revision)


def main():
    comun.escena_vacia()
    raiz, asiento, cuerpo, col = construir()
    revision = revisar(asiento, cuerpo, col)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [raiz, asiento, cuerpo, col])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, asiento, cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
