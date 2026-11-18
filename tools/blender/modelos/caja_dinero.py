"""Modelo: caja de dinero (id `caja_dinero`, etapa 2; no está en el juego: la plata es solo el
número del HUD).

Genera:
    arte/fuentes/accesorios/caja_dinero.blend
    godot/modelos/accesorios/caja_dinero.glb
    docs/arte/revisiones/caja_dinero.jpg

Uso:
    python tools/blender/modelos/caja_dinero.py [--sin-hoja]

Forma: caja de caudales chica de chapa pintada (M_MetalOscuro), como las de los kioscos: cuerpo
de 0,30 × 0,064 × 0,25 hueco por dentro, tapa de 2,3 cm con bisagras atrás (+Z, del lado del
cliente) y manija rebatible acostada arriba (barra de acero con puño negro). Del lado del
vendedor (−Z), la cerradura (chapita de acero con la ranura de la llave) y la pestaña de la
tapa. Adentro, la bandeja negra de plástico: una fila de 4 cajitas para monedas del lado del
vendedor y, atrás, dos lugares para billetes.

Medidas (lista ≈ 0,30 × 0,10 × 0,25): 0,30 × 0,10 × 0,262 (la cerradura sale 4 mm adelante y
las bisagras 7,5 mm atrás del cuerpo de 0,25). Arriba de todo, el puño de la manija (0,10).

Objetos (hijos del Empty `caja_dinero`; origen = centro de la base, a nivel del mostrador):
    caja_dinero_cuerpo  cuerpo, cerradura y bandeja (MetalOscuro, Acero, PlasticoNegro).
    pieza_tapa          tapa, bisagras, pestaña y manija (MetalOscuro, Acero, PlasticoNegro).
                        **Origen en el eje de las bisagras** (0; 0,0645; 0,127), eje X: el juego
                        la abre girándola en X (rotation.x positivo abre; abierta ≈ 100°).
    caja_dinero-colonly piso y 4 paredes del cuerpo (cajas): lo de adentro queda libre.
    caja_dinero_tapa-colonly  la tapa, hija de `pieza_tapa` (la sigue al abrir, guía v1.5).

Chequeo de origen propio: la cerradura y las bisagras corren la caja total 1,5 mm; se mide el
cuerpo (0,30 × 0,25) centrado en el origen.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _plaza as plaza  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "caja_dinero"
FAMILIA = "accesorios"
PRESUPUESTO = 500
OSCURO, ACERO, NEGRO = range(3)

W, D = 0.30, 0.25
Y_CUERPO = 0.064            # arriba del cuerpo
Y_TAPA = (0.0645, 0.0875)   # tapa (abajo, arriba)
PARED, PISO = 0.006, 0.014  # paredes y piso de adentro
BISEL = 0.006               # equipos de mostrador (guía 3.3: 4-6 mm)
BISAGRA = (0.0645, D / 2 + 0.002, 0.005)   # eje (y, z) y radio
R_PUNO, Y_MANIJA = 0.0062, 0.0938
MEDIDAS = (W, 0.100, 0.262)


def cuerpo(mats):
    bm = bmesh.new()
    caras = piezas.caja(bm, (W, Y_CUERPO, D), (0, Y_CUERPO / 2, 0), mat=OSCURO, bisel=BISEL, sin_abajo=True)
    arriba = [f for f in caras if f.is_valid and f.normal.z > 0.999 and
              all(abs(v.co.z - Y_CUERPO) < 1e-6 for v in f.verts)]
    bmesh.ops.inset_region(bm, faces=arriba, thickness=PARED, depth=0.0)
    ext = bmesh.ops.extrude_face_region(bm, geom=arriba)
    nuevos = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, -(Y_CUERPO - PISO)), verts=nuevos)
    bmesh.ops.delete(bm, geom=arriba, context="FACES")
    nuevos_set = set(nuevos)
    piso = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMFace) and set(g.verts) <= nuevos_set]
    for f in piso:
        f.material_index = NEGRO
    # Bandeja negra: tabiques sobre el piso (no se ve la cara de abajo).
    ix = W / 2 - BISEL - PARED          # medio ancho de adentro
    iz = D / 2 - BISEL - PARED
    alto = 0.042
    yc = PISO + alto / 2
    z_div = -0.035
    piezas.caja(bm, (2 * ix, alto, 0.006), (0, yc, z_div), mat=NEGRO, sin_abajo=True)
    for x in (-ix / 2, 0.0, ix / 2):
        largo = z_div - 0.003 + iz
        piezas.caja(bm, (0.006, alto, largo), (x, yc, -iz + largo / 2), mat=NEGRO, sin_abajo=True)
    largo = iz - z_div - 0.003
    piezas.caja(bm, (0.006, alto, largo), (0, yc, z_div + 0.003 + largo / 2), mat=NEGRO, sin_abajo=True)
    # Cerradura (lado del vendedor): chapita y ranura.
    piezas.caja(bm, (0.04, 0.022, 0.003), (0, 0.048, -D / 2 - 0.0015), mat=ACERO)
    piezas.caja(bm, (0.004, 0.011, 0.002), (0, 0.048, -D / 2 - 0.004), mat=NEGRO)
    return piezas.terminar(f"{ID}_cuerpo", bm, mats)


def tapa(mats):
    bm = bmesh.new()
    y0, y1 = Y_TAPA
    piezas.caja(bm, (W, y1 - y0, D), (0, (y0 + y1) / 2, 0), mat=OSCURO, bisel=BISEL)
    # Pestaña de la tapa, sobre la cerradura (lado del vendedor).
    piezas.caja(bm, (0.03, 0.014, 0.003), (0, y0 - 0.002, -D / 2 - 0.0015), mat=ACERO)
    # Bisagras (atrás, +Z): dos caños sobre el eje.
    yb, zb, rb = BISAGRA
    for sx in (-1, 1):
        piezas.cilindro(bm, rb, 0.05, (sx * 0.09, yb, zb), eje="x", lados=8, mat=ACERO, radio_a_caras=True)
    # Manija rebatible acostada: pivotes, patas, barra y puño.
    xp, zp, zm = 0.075, 0.02, -0.03
    for sx in (-1, 1):
        piezas.caja(bm, (0.016, 0.01, 0.018), (sx * xp, y1 + 0.005, zp), mat=ACERO, sin_abajo=True)
        piezas.cilindro(bm, 0.004, zp - zm + 0.004, (sx * xp, Y_MANIJA, (zp + zm - 0.004) / 2), eje="z",
                        lados=8, mat=ACERO, radio_a_caras=True)
    piezas.cilindro(bm, 0.004, 2 * xp + 0.008, (0, Y_MANIJA, zm), eje="x", lados=8, mat=ACERO,
                    radio_a_caras=True)
    piezas.cilindro(bm, R_PUNO, 0.09, (0, Y_MANIJA, zm), eje="x", lados=8, mat=NEGRO, radio_a_caras=True)
    return e2.objeto_en("pieza_tapa", bm, mats, (0, yb, zb))


def construir():
    mats = comun.cargar_materiales("M_MetalOscuro", "M_Acero", "M_PlasticoNegro")
    c = cuerpo(mats)
    t = tapa(mats)
    e2.suavizar_hasta(t, 50)   # caños de 8 lados redondos
    # Colisión: piso y paredes (lo de adentro queda libre); la tapa, hija de su pieza.
    h = Y_CUERPO
    col = plaza.colision_cajas(ID, [
        ((W, PISO, D), (0, PISO / 2, 0), (0, 0, 0)),
        ((W, h, PARED + BISEL), (0, h / 2, D / 2 - (PARED + BISEL) / 2), (0, 0, 0)),
        ((W, h, PARED + BISEL), (0, h / 2, -D / 2 + (PARED + BISEL) / 2), (0, 0, 0)),
        ((PARED + BISEL, h, D), (W / 2 - (PARED + BISEL) / 2, h / 2, 0), (0, 0, 0)),
        ((PARED + BISEL, h, D), (-W / 2 + (PARED + BISEL) / 2, h / 2, 0), (0, 0, 0)),
    ])
    y0, y1 = Y_TAPA
    col_t = piezas.colision_caja(f"{ID}_tapa", (W, y1 - y0, D), (0, (y0 + y1) / 2, 0))
    col_t.parent = t
    col_t.location = -t.location   # malla en el mundo, relativa al eje
    col_t.matrix_parent_inverse.identity()
    raiz = piezas.raiz(ID, [c, t, col])
    return raiz, c, t, col, col_t


def chequeo_origen(c):
    vs = [v for v in e2.verts_godot(c) if abs(v.z) <= D / 2 + 1e-6]
    mn_x, mx_x = min(v.x for v in vs), max(v.x for v in vs)
    mn_z, mx_z = min(v.z for v in vs), max(v.z for v in vs)
    piso = min(v.y for v in vs)
    ok = abs(mn_x + mx_x) < 1e-4 and abs(mn_z + mx_z) < 1e-4 and abs(piso) < 1e-6
    return ok, "Origen en el centro de la base del cuerpo (%.2f × %.2f), a nivel del mostrador" % (
        mx_x - mn_x, mx_z - mn_z)


def chequeo_tapa(t, col_t):
    bpy.context.view_layer.update()
    eje = e2.verts_godot(t)
    yb, zb, _ = BISAGRA
    o = t.matrix_world.translation
    ok = abs(o.z - yb) < 1e-6 and abs(-o.y - zb) < 1e-6 and col_t.parent == t
    mn, mx = e2.limites_godot([col_t])
    ok = ok and abs(mn.y - Y_TAPA[0]) < 1e-5 and abs(mx.y - Y_TAPA[1]) < 1e-5 and len(eje) > 0
    return ok, "pieza_tapa con el origen en el eje de las bisagras (y %.4f, z %.3f); su colisión es hija" % (
        yb, zb)


def revisar(c, t, col_t):
    res = comun.revisar([c, t], PRESUPUESTO, MEDIDAS, origen="base")
    res = plaza.reemplazar(res, "Origen", *chequeo_origen(c))
    res.insert(1, chequeo_tapa(t, col_t))
    return res


def hoja_revision(c, t, revision):
    import _comida4 as c4
    import moneda
    import billete
    comun.preparar_revision()
    abierta = e2.copiar(t, "ref_tapa_abierta")
    abierta.rotation_euler.x = math.radians(100)
    plata = []
    for i, (x, z) in enumerate(((-0.103, -0.08), (-0.034, -0.08), (0.034, -0.085), (0.103, -0.075))):
        for k in range(2 + i % 2):
            mo = moneda.construir(f"ref_moneda_{i}_{k}")
            mo.location = g2b((x + 0.004 * k, PISO + moneda.ALTO / 2 + k * (moneda.ALTO + 0.0003), z))
            plata.append(mo)
    for i, (x, mat) in enumerate(((-0.065, "M_TelaVerde"), (0.065, "M_TelaBordo"))):
        for k in range(3):
            b = billete.construir(f"ref_billete_{i}_{k}")
            b.data.materials[0] = comun.cargar_materiales(mat)[0]
            b.scale.x = 0.92   # solo en la foto: el lugar mide 0,145 (doblados en la vida real)
            b.rotation_euler.z = math.radians(90 + 4 * (k - 1))
            b.location = g2b((x, PISO + 0.001 + k * 0.0021, 0.04))
            plata.append(b)
    pan = c4.pan_de_escala(0.27, 0.0)
    pan.hide_render = False
    cerrada, abierta_v = [c, t], [c, abierta] + plata
    cuadros = e2.sacar_fotos([
        ("Cerrada · 3/4 lado del vendedor (cerradura) · día", cerrada, "vendedor", "dia"),
        ("Cerrada · frente (cliente: bisagras) · día", cerrada, "frente", "dia"),
        ("Cerrada · costado · día", cerrada, "costado", "dia"),
        ("Abierta (100°), con monedas y billetes · día", abierta_v, "vendedor_alto", "dia"),
        ("Abierta · 3/4 · atardecer", abierta_v, "vendedor", "atardecer"),
        ("Al lado de un pan de pancho · día", cerrada + [pan], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(f"{ID} · 0,30 × 0,10 × 0,26 m · accesorio (tapa con bisagra)", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    raiz, c, t, col, col_t = construir()
    revision = revisar(c, t, col_t)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, c, t, col, col_t], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(c, t, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
