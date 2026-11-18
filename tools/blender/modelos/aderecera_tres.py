"""Modelo: aderecera de tres pomos (id `aderecera_tres`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/aderecera_tres.blend
    godot/modelos/accesorios/aderecera_tres.glb
    docs/arte/revisiones/aderecera_tres.jpg

Uso:
    blender -b -P tools/blender/modelos/aderecera_tres.py
    python tools/blender/modelos/aderecera_tres.py

Forma: soporte de acero en "U" dada vuelta. Chapa de base de 0,30 × 0,015 × 0,10 (la `forma`
del dato, con bisel), dos laterales de chapa y, arriba, una bandeja con tres agujeros
redondos (12 lados) por donde pasan los pomos y que los mantiene parados. Adelante y atrás
queda abierto: el vendedor (−Z) ve el nivel de cada pomo y el cliente (+Z) ve los colores.

Solo el soporte: los tres pomos los arma aderecera.rs (modelo `pomo_aderezo`), parados
sobre la chapa (y = 0,015), en x = −0,09 / 0 / 0,09 (separacion 0,09 del dato) y z = −0,22.
Los agujeros tienen radio 0,031 (el pomo, 0,028) y la bandeja de arriba está a 0,079–0,085,
a la altura del cuerpo del pomo (no tapa el pico ni la tapa).

Origen: el del anclaje (mostrador_*), a nivel del mostrador. La chapa está corrida hacia el
vendedor, centrada en z = −0,22, igual que la `forma` de hoy. Por eso el chequeo de origen de
comun.revisar() (centro de la caja total) se reemplaza por uno propio: la base centrada en
(0, 0, −0,22) y apoyada en y = 0.

Objetos (hijos del Empty `aderecera_tres`):
- `aderecera_tres_cuerpo` (M_Acero).
- `aderecera_tres-colonly`: la chapa de base, 0,30 × 0,015 × 0,10 (la colisión de hoy). Los
  pomos tienen su propia colisión: la bandeja de arriba no colisiona para no tapárselos a la
  mira.
- `punto_pomo_1/2/3`: dónde se para cada pomo (de −X a +X, el orden de `tipos`).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "aderecera_tres"
FAMILIA = "accesorios"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)

# Datos (accesorios.ron + aderecera.rs)
ANCHO, ALTO_BASE, FONDO = 0.30, 0.015, 0.10
Z0 = -0.22
SEPARACION = 0.09
N_POMOS = 3
Y_POMO = 0.015

CHAPA = 0.006                      # espesor de laterales y bandeja (equipo: mín. 5 mm)
Y_BANDEJA = 0.079                  # abajo de la bandeja de arriba
ALTO = Y_BANDEJA + CHAPA           # 0,085
R_AGUJERO = 0.031
LADOS = 12
BISEL = 0.004                      # equipos de mostrador (guía 3.3)

MEDIDAS = (ANCHO, ALTO, FONDO)
POS_POMOS = [((i - (N_POMOS - 1) / 2) * SEPARACION, Y_POMO, Z0) for i in range(N_POMOS)]


def _rayo_rectangulo(a, x0, x1, z0, z1):
    """Punto donde el rayo desde (0,0) con ángulo a corta el rectángulo [x0,x1]×[z0,z1]."""
    c, s = math.cos(a), math.sin(a)
    ts = []
    if c > 1e-9:
        ts.append(x1 / c)
    if c < -1e-9:
        ts.append(x0 / c)
    if s > 1e-9:
        ts.append(z1 / s)
    if s < -1e-9:
        ts.append(z0 / s)
    t = min(ts)
    return (t * c, t * s)


def celda_agujereada(bm, cx, cz, x0, x1, z0, z1, y_abajo, y_arriba, r, lados):
    """Placa rectangular [cx+x0, cx+x1] × [cz+z0, cz+z1] con un agujero redondo en (cx, cz).
    Hace las caras de arriba y de abajo; las paredes se agregan después (bordes libres)."""
    angs = [2 * math.pi * k / lados for k in range(lados)]
    esquinas = [(x1, z1), (x0, z1), (x0, z0), (x1, z0)]
    ang_esq = [math.atan2(z, x) % (2 * math.pi) for x, z in esquinas]
    for y, arriba in ((y_arriba, True), (y_abajo, False)):
        adentro = [bm.verts.new(g2b((cx + r * math.cos(a), y, cz + r * math.sin(a)))) for a in angs]
        afuera = []
        for a in angs:
            px, pz = _rayo_rectangulo(a, x0, x1, z0, z1)
            afuera.append(bm.verts.new(g2b((cx + px, y, cz + pz))))
        for k in range(lados):
            a0 = angs[k]
            a1 = angs[(k + 1) % lados] if k + 1 < lados else 2 * math.pi
            medio = [bm.verts.new(g2b((cx + ex, y, cz + ez)))
                     for (ex, ez), ae in zip(esquinas, ang_esq) if a0 < ae < a1]
            poli = [adentro[k], afuera[k]] + medio + [afuera[(k + 1) % lados], adentro[(k + 1) % lados]]
            # g2b invierte el giro: visto desde arriba (Blender +Z) esta lista va en sentido
            # horario, así que para que la cara de arriba mire hacia arriba se da vuelta.
            bm.faces.new(list(reversed(poli)) if arriba else poli)


def paredes_de_bordes(bm, y_abajo, y_arriba):
    """Cierra los bordes libres de las caras de arriba con las de abajo (paredes verticales)."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.verts.ensure_lookup_table()
    za, zb = y_arriba, y_abajo  # Y de Godot = Z de Blender
    abajo = {(round(v.co.x, 6), round(v.co.y, 6)): v for v in bm.verts if abs(v.co.z - zb) < 1e-7}
    libres = [e for e in bm.edges if len(e.link_faces) == 1 and all(abs(v.co.z - za) < 1e-7 for v in e.verts)]
    for e in libres:
        f = e.link_faces[0]
        # Orden del borde según la cara de arriba, para que la pared quede para afuera.
        vs = list(f.verts)
        i = vs.index(e.verts[0])
        a, b = (e.verts[0], e.verts[1]) if vs[(i + 1) % len(vs)] == e.verts[1] else (e.verts[1], e.verts[0])
        a2 = abajo[(round(a.co.x, 6), round(a.co.y, 6))]
        b2 = abajo[(round(b.co.x, 6), round(b.co.y, 6))]
        bm.faces.new((b, a, a2, b2))


def construir():
    (acero,) = comun.cargar_materiales("M_Acero")
    bm = bmesh.new()

    # Bandeja de arriba con los tres agujeros (se arma aparte y se suma).
    bb = bmesh.new()
    medio_ancho, medio_fondo = ANCHO / 2, FONDO / 2
    for i, (px, _, _) in enumerate(POS_POMOS):
        x0 = -medio_ancho - px if i == 0 else -SEPARACION / 2
        x1 = medio_ancho - px if i == N_POMOS - 1 else SEPARACION / 2
        celda_agujereada(bb, px, Z0, x0, x1, -medio_fondo, medio_fondo, Y_BANDEJA, ALTO, R_AGUJERO, LADOS)
    paredes_de_bordes(bb, Y_BANDEJA, ALTO)
    malla = bpy.data.meshes.new("tmp_bandeja")
    bb.to_mesh(malla)
    bb.free()
    bm.from_mesh(malla)
    bpy.data.meshes.remove(malla)
    for f in bm.faces:
        f.material_index = 0

    # Chapa de base (la `forma` del dato), con bisel. Sin cara de abajo (apoya).
    piezas.caja(bm, (ANCHO, ALTO_BASE, FONDO), (0, ALTO_BASE / 2, Z0), bisel=BISEL, sin_abajo=True)

    # Laterales: de la base a la bandeja, metidos 1 mm en cada una para que no quede luz.
    alto_lat = Y_BANDEJA - ALTO_BASE + 0.002
    for s in (-1, 1):
        c = piezas.caja(bm, (CHAPA, alto_lat, FONDO - 0.012),
                        (s * (medio_ancho - CHAPA / 2 - 0.002), ALTO_BASE - 0.001 + alto_lat / 2, Z0),
                        bisel=0.002)
        e2.borrar_caras(bm, c, (0, 1, 0))
        e2.borrar_caras(bm, c, (0, -1, 0))

    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero])
    col = piezas.colision_caja(ID, (ANCHO, ALTO_BASE, FONDO), (0, ALTO_BASE / 2, Z0))
    puntos = [piezas.punto(f"punto_pomo_{i + 1}", p, tam=0.02) for i, p in enumerate(POS_POMOS)]
    raiz = piezas.raiz(ID, [cuerpo, col] + puntos)
    return raiz, cuerpo, col, puntos


def chequeo_origen(cuerpo):
    mn, mx = e2.limites_godot([cuerpo])
    cx, cz = (mn.x + mx.x) / 2, (mn.z + mx.z) / 2
    ok = abs(cx) < 1e-4 and abs(cz - Z0) < 1e-4 and abs(mn.y) < 1e-4
    return ok, "Origen en el anclaje: base centrada en (0, 0, −0,22) como la forma del dato, a nivel del mostrador"


def chequeo_agujeros(cuerpo):
    """Los agujeros están donde aderecera.rs pone los pomos y les dejan lugar."""
    vs = [v for v in e2.verts_godot(cuerpo) if v.y > Y_BANDEJA - 1e-5]
    ok = True
    for px, _, pz in POS_POMOS:
        cerca = [v for v in vs if math.hypot(v.x - px, v.z - pz) < R_AGUJERO + 1e-4]
        if not cerca:
            ok = False
            continue
        rmin = min(math.hypot(v.x - px, v.z - pz) for v in cerca) * math.cos(math.pi / LADOS)
        ok = ok and rmin > 0.028 + 0.001
    return ok, "Agujeros en x = −0,09 / 0 / 0,09, z = −0,22, con lugar para el pomo (radio 0,028)"


def revisar(cuerpo):
    res = comun.revisar([cuerpo], PRESUPUESTO, MEDIDAS, origen="base")
    res = [chequeo_origen(cuerpo) if t.startswith("Origen") else (ok, t) for ok, t in res]
    res.insert(1, chequeo_agujeros(cuerpo))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def pomos_de_referencia(desplazamiento):
    """Los tres pomos (modelo pomo_aderezo) parados en la aderecera, con su color."""
    import pomo_aderezo
    raiz, envase, tapa, relleno, col = pomo_aderezo.construir()
    bpy.data.objects.remove(col)
    e2.sin_cara_de_atras(envase)
    mats = e2.materiales_aderezo()
    objs = []
    for (nombre, _), pos, nivel in zip(e2.ADEREZOS, POS_POMOS, (1.0, 0.7, 0.4)):
        base = g2b(pos) + desplazamiento
        for o, mat in ((envase, None), (tapa, mats[nombre]), (relleno, mats[nombre])):
            c = e2.copiar(o, f"ref_{o.name}_{nombre}", mat)
            c.parent = None
            c.location = base + Vector((0, 0, o.location.z))
            if o is relleno:
                c.scale.z = nivel
            objs.append(c)
    for o in (envase, tapa, relleno, raiz):
        bpy.data.objects.remove(o)
    return objs


def hoja_revision(raiz, cuerpo, revision):
    comun.preparar_revision()
    solo = [cuerpo]
    pomos = pomos_de_referencia(Vector((0, 0, 0)))
    con = solo + pomos
    cuadros = e2.sacar_fotos([
        ("Frente (cliente) · día", solo, "frente", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Con los tres pomos, 3/4 · día", con, "tres_cuartos", "dia"),
        ("Con los pomos, desde el vendedor · día", con, "vendedor", "dia"),
        ("Con los pomos, 3/4 · atardecer", con, "tres_cuartos", "atardecer"),
    ])
    # Sobre la barra chica, en mostrador_der (0,4; 0,95; 0), como en carrito_jugador.ron.
    for o in solo + pomos:
        o.hide_render = False
    barra = e2.barra_chica()
    ancla = g2b((0.4, 0.95, 0.0))
    for o in solo + pomos:
        o.location += ancla
    import pan_pancho
    pan = pan_pancho.construir("ref_pan")
    pan.location = g2b((0.1, 0.95 + 0.0225, -0.15))
    cuadros += e2.sacar_fotos([
        ("En la barra chica (mostrador_der), lado del vendedor", con + barra + [pan], "vendedor_alto", "dia",
         con, 2.2),
    ])
    comun.componer_hoja(
        f"{ID} · 0,30 × 0,085 × 0,10 m · soporte de acero (los pomos los pone el juego)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col, puntos = construir()
    revision = revisar(cuerpo)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col] + puntos, comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
