"""Modelo: fachada con negocio en planta baja (id `fachada_casa_b`, familia `ciudad`).

Genera:
    arte/fuentes/ciudad/fachada_casa_b.blend
    godot/modelos/ciudad/fachada_casa_b.glb
    docs/arte/revisiones/fachada_casa_b.jpg

Uso:
    python tools/blender/modelos/fachada_casa_b.py [--sin-hoja]

Casa de dos plantas con un local (almacén, kiosco) en planta baja: es el edificio con
`toldo` de ciudad.rs, en el ancho de referencia de 9 m. Ver _fachada.py para los módulos,
los vidrios y el origen.

Planta baja: puerta de hierro y vidrio a los pisos de arriba en la columna 0 (la puerta del
código) y el local con las medidas del código: vano de x −2,1 a 3,9 (ancho − 3 m, corrido
0,9 a la derecha), de 0 a 2,6 m y 0,2 de hondo. Adentro, la vidriera: dos paños fijos sobre
un zócalo de hierro (de 0,4 a 2,6, como la del código) y la puerta del local en el medio,
con parantes y travesaño de hierro. Delante, la cortina metálica en sus guías, con el
cajón arriba, y el toldo rayado inclinado 18° (6,6 × 1,3 m, como el del código).

Objetos especiales (además de los de _fachada.py):
    - pieza_vidriera: los vidrios del local (M_LuzCalida, emisión): hoy el código hace que
      la vidriera brille de noche (nocturno::material).
    - pieza_cortina: la cortina metálica BAJA (M_Piedra, chapa ondulada con su zócalo). El
      origen está arriba, en el cajón (x 0,9; y 2,6): el juego la sube escalándola en Y
      (escala 0,04 = levantada, 1 = cerrada). En las fotos de día está levantada.
    - pieza_toldo: lona en 20 rayas (superficie 0 = M_AzulAcento, 1 = M_BlancoCrema) y dos
      brazos de hierro. Origen en la línea donde se agarra a la pared (x 0,9; y 3,15). El
      juego le pone el color del toldo a las dos superficies (lisa) o a una (rayada).

Materiales: muro M_Terracota (el juego lo cambia), molduras y rayas M_BlancoCrema, zócalo,
cajón y cortina M_Piedra, puertas, herrería y vidrios oscuros M_Hierro, toldo
M_AzulAcento, vidrios que se prenden y vidriera M_LuzCalida.

Medidas: 9,00 × 6,95 × 1,49 (lista ≈ 9 × 7 × 1). Adelante manda el toldo (1,26 m).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _fachada as fa  # noqa: E402
from _fachada import CLARO, HIERRO, MURO, OSCURO, PROF  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

TOLDO, LUZ = 3, 5   # índices propios: el lugar de la carpintería lo ocupa el toldo
P = {
    "id": "fachada_casa_b",
    "materiales": ("M_Terracota", "M_BlancoCrema", "M_Piedra", "M_AzulAcento", "M_Hierro", "M_LuzCalida"),
    "pisos": 2,
    "luz": [True, False, False, True],
}
MEDIDAS = (9.0, 6.95, 1.486)
PUERTA = (1.2, 2.6)
# Local (ciudad.rs: vidriera de ancho − 3, corrida 0,9; toldo de ancho_vid + 0,6 a 18°).
LOCAL = (-2.1, 3.9, 0.0, 2.6)
LOCAL_HONDO = 0.2
X_LOCAL = 0.9
PUERTA_LOCAL = (0.3, 1.5)
ZOCALO_VIDRIERA = 0.4
CORTINA_Z = -0.07                # plano de la cortina (adentro del vano, delante de la vidriera)
TOLDO_ANCHO, TOLDO_LARGO, TOLDO_GIRO = 6.6, 1.3, 18.0
TOLDO_ARRIBA = 2.95 + TOLDO_LARGO / 2 * math.sin(math.radians(TOLDO_GIRO))   # 3,15
FALDON = 0.25
LONA = 0.02


def local(f, bm, zf):
    """Vidriera, puerta del local y herrería (en el fondo del vano)."""
    xa, xb, ya, yb = LOCAL
    pa, pb = PUERTA_LOCAL
    zb = zf + 0.025
    bv = bmesh.new()
    for x0, x1, y0 in ((xa, pa, ZOCALO_VIDRIERA), (pa, pb, 0.0), (pb, xb, ZOCALO_VIDRIERA)):
        ciudad.rectangulo(bv, x0, x1, y0, yb, zf)
        if y0 > 0:
            ciudad.rectangulo(bm, x0, x1, 0.0, y0, zf, HIERRO)
            ciudad.barra(bm, (x0, y0, zb), (x1, y0, zb), 0.05, HIERRO)
    for x in (xa + 0.025, pa, pb, xb - 0.025):
        ciudad.barra(bm, (x, 0.0, zb), (x, yb, zb), 0.05, HIERRO)
    ciudad.barra(bm, (xa, 2.25, zb), (xb, 2.25, zb), 0.05, HIERRO)
    ciudad.barra(bm, (pa, 1.0, zb), (pb, 1.0, zb), 0.04, HIERRO)   # manija / travesaño de la puerta
    vidriera = ciudad.terminar("pieza_vidriera", bv, [f.mats[LUZ]])
    f.objetos.append(vidriera)
    # Guías de la cortina y cajón.
    for x in (xa + 0.04, xb - 0.04):
        ciudad.caja_frente(bm, (0.08, yb, 0.08), (x, yb / 2, CORTINA_Z), HIERRO, sin_abajo=True,
                           sin_arriba=True)
    ciudad.caja_frente(bm, (xb - xa + 0.3, 0.3, 0.08), (X_LOCAL, yb + 0.15, 0.04), OSCURO, fa.BISEL_FINO)


def cortina(f):
    """Cortina metálica baja: chapa ondulada (paso 0,1) con zócalo, en el plano CORTINA_Z."""
    xa, xb, _, yb = LOCAL
    paso, onda = 0.1, 0.02
    n = int(round((yb - 0.06) / paso))
    perfil = [(0.0, 0.0)]
    for k in range(n):
        perfil += [(onda, -(k + 0.5) * paso), (0.0, -(k + 1) * paso)]
    perfil += [(0.03, -n * paso), (0.03, -yb), (-0.03, -yb), (-0.03, -n * paso), (-0.01, -n * paso),
               (-0.01, 0.0)]
    perfil = [(z + CORTINA_Z, y + yb) for z, y in perfil]
    bm = bmesh.new()
    ciudad.perfil_segmentado(bm, perfil, [xa + 0.04, xb - 0.04], [0])
    o = ciudad.terminar_en("pieza_cortina", bm, [f.mats[OSCURO]], origen=(X_LOCAL, yb, CORTINA_Z))
    f.objetos.append(o)
    return o


def toldo(f):
    """Toldo de lona rayada: paño inclinado y faldón, con dos brazos de hierro."""
    a = math.radians(TOLDO_GIRO)
    zf, yf = TOLDO_LARGO * math.cos(a), TOLDO_ARRIBA - TOLDO_LARGO * math.sin(a)
    t = LONA
    perfil = [(0.0, TOLDO_ARRIBA), (zf, yf), (zf, yf - FALDON), (zf - t, yf - FALDON),
              (zf - t, yf - t / math.cos(a) + t * math.tan(a)), (0.0, TOLDO_ARRIBA - t / math.cos(a))]
    rayas = 20
    xs = [X_LOCAL - TOLDO_ANCHO / 2 + TOLDO_ANCHO * k / rayas for k in range(rayas + 1)]
    bm = bmesh.new()
    ciudad.perfil_segmentado(bm, perfil, xs, [k % 2 for k in range(rayas)])
    for s in (-1, 1):  # brazos: de la pared, 0,45 más abajo, a la punta del paño
        x = X_LOCAL + s * (TOLDO_ANCHO / 2 - 0.3)
        plaza_caño(bm, (x, TOLDO_ARRIBA - 0.75, 0.0), (x, yf - 0.03, zf - 0.03), 0.02, 2)
    o = ciudad.terminar_en("pieza_toldo", bm, [f.mats[TOLDO], f.mats[CLARO], f.mats[HIERRO]],
                           origen=(X_LOCAL, TOLDO_ARRIBA, 0.0))
    f.objetos.append(o)
    return o


def plaza_caño(bm, a, b, r, mat):
    import _plaza as plaza
    plaza.caño(bm, a, b, r, 6, mat)


def planta_baja(f):
    bm = bmesh.new()
    xp = fa.col_x(0)
    vanos = [(xp - PUERTA[0] / 2, xp + PUERTA[0] / 2, 0.0, PUERTA[1]), (*LOCAL, LOCAL_HONDO)]
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PB, vanos, PROF, MURO,
                                   espesor=fa.ESPESOR)
    fa.puerta_hierro(bm, f, xp, PUERTA[0], PUERTA[1], fondos[0][4])
    local(f, bm, fondos[1][4])
    xa, xb = vanos[0][0] - 0.16, vanos[0][1] + 0.16
    fa.zocalo(bm, [(-fa.ANCHO / 2, xa), (xb, LOCAL[0]), (LOCAL[1], fa.ANCHO / 2)])
    fa.moldura_pb(bm)
    f.objeto("pieza_planta_baja", bm, modulo=True)


def piso(bm, f, n):
    vanos = [(fa.col_x(c) - 0.55, fa.col_x(c) + 0.55, *fa.ventana_y()) for c in range(fa.COLUMNAS)]
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PISO, vanos, PROF, MURO,
                                   espesor=fa.ESPESOR)
    for xa, xb, ya, yb, zf in fondos:
        fa.molduras_ventana(bm, (xa + xb) / 2, ya, yb)
    return fondos


def construir():
    f = fa.Fachada(P)
    planta_baja(f)
    f.cortina = cortina(f)
    f.toldo = toldo(f)
    f.pisos(piso)
    f.cornisa(fa.cornisa_casa)
    f.terminar_vidrios()
    f.colision()
    f.raiz()
    return f


def main():
    comun.escena_vacia()
    f = construir()

    def subir_cortina():
        f.cortina.scale.z = 0.04
        bpy.context.view_layer.update()

    def bajar_cortina():
        f.cortina.scale.z = 1.0
        bpy.context.view_layer.update()

    pb = [o for o in f.objetos if o.name in ("pieza_planta_baja", "pieza_toldo")]
    fa.main(f, MEDIDAS, ciudad.m("fachada_casa_b · 9 × 6.95 × 1.49 m · casa con local (vidriera, "
                                 "cortina, toldo) · fachada"),
            extra_fotos=[("Cortina baja · atardecer", f.objetos, "tres_cuartos", "atardecer", False, pb)],
            antes_fotos=subir_cortina, entre_fotos={5: bajar_cortina})


if __name__ == "__main__":
    main()
