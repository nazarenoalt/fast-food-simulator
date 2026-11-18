"""Modelo: hervidor baño maría chico (id `hervidor_chico`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/cocina/hervidor_chico.blend
    godot/modelos/cocina/hervidor_chico.glb
    docs/arte/revisiones/hervidor_chico.jpg

Uso:
    blender -b -P tools/blender/modelos/hervidor_chico.py
    python tools/blender/modelos/hervidor_chico.py

Forma: batea abierta de acero con esquinas redondeadas y un reborde (pestaña) de 1 cm
alrededor de la boca, manijas laterales negras y, del lado del vendedor (−Z de Godot,
+Y de Blender), un frente de controles con la perilla negra (en −X, como hervidor.rs) y la
luz piloto (en +X).

Coincide con lo que arma hoy rust/game/src/hervidor.rs, que sigue creando la física:
- Interior (la batea): EXACTO 0,36 × 0,18 × 0,26 (`interior` de accesorios.ron). El piso de
  adentro está a 0,012 del apoyo (ESPESOR) y las paredes llegan a 0,192.
- Paredes de 0,012 (las mismas que las cajas de colisión del código), así lo que se ve
  coincide con lo que choca.
- Perilla en x = −w/4 y piloto en x = +w/4, a 0,55 del alto.

Objetos (todos hijos del Empty `hervidor_chico`, que es el origen = centro de la base, a
nivel del mostrador, como el anclaje `mostrador_*`):
- `hervidor_chico_cuerpo`: batea, frente de controles, manijas y perilla (Acero, PlasticoNegro).
- `pieza_agua` (M_Agua): el agua, al 70 % del alto interior (NIVEL_AGUA de hervidor.rs).
  Su origen está en el centro del piso de la batea: si el código quiere subir o bajar el
  nivel, le cambia la escala en Y. Es 1 mm más chica que la batea para no pelearse con las
  paredes (parpadeo).
- `pieza_piloto` (M_PilotoApagado): la lente de la luz piloto; el juego la enciende.
- `punto_interior`: Empty en el centro del piso de la batea (0, 0,012, 0). Ahí arranca el
  volumen que calienta (la zona de agua del código).

Sin colisión `-colonly`: la batea la arma hervidor.rs con 5 cajas a partir de `interior`
(una caja simple acá llenaría la batea y la comida no podría entrar).

Qué se mide en la revisión: el total (con perilla y manijas) en el chequeo de medidas, y
aparte un chequeo propio de la batea (paredes de adentro, piso y boca). El chequeo de
origen de comun.revisar() mide el centro de la caja que envuelve todo, que se corre hacia
el vendedor por la perilla y el frente de controles; se reemplaza por uno propio: la batea
centrada en el origen y la base a nivel del piso.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "hervidor_chico"
FAMILIA = "cocina"
PRESUPUESTO = 1500  # equipos de cocina (guía 3.1)

# Datos (accesorios.ron + hervidor.rs)
INTERIOR = (0.36, 0.18, 0.26)
ESPESOR = 0.012
NIVEL_AGUA = 0.7
W, H, D = INTERIOR
A, B = W / 2, D / 2                 # medio ancho / media profundidad de la batea
PISO = ESPESOR                      # piso de adentro
BOCA = PISO + H                     # alto de las paredes (0,192)
ALTO_AGUA = H * NIVEL_AGUA

RADIO_ESQUINA = 0.015               # esquinas de adentro redondeadas (4 segmentos: se ven lisas)
PESTANA = 0.022                     # cuánto sale el reborde desde la pared de adentro
Y_CONTROLES = (H + ESPESOR) * 0.55  # alto de perilla y piloto (hervidor.rs)
Z_PARED_ATRAS = -(B + ESPESOR)      # cara de afuera de la pared del vendedor
FRENTE_CONTROLES = 0.02             # cuánto sobresale el frente de controles
Z_CONTROLES = Z_PARED_ATRAS - FRENTE_CONTROLES

# Perfil de la pared: (cuánto se aleja de la pared de adentro, alto), desde el apoyo de
# afuera, subiendo por el reborde y bajando por adentro hasta el piso.
PERFIL = [
    (ESPESOR - 0.004, 0.0),
    (ESPESOR, 0.004),
    (ESPESOR, 0.172),
    (PESTANA, 0.177),
    (PESTANA, 0.188),
    (PESTANA - 0.004, BOCA),
    (0.003, BOCA),
    (0.0, BOCA - 0.003),
    (0.0, PISO),
]

PERILLA_X, PILOTO_X = -W / 4, W / 4
MANIJA_X = A + ESPESOR
LARGO_PERILLA = 0.018

MEDIDAS = (
    2 * (MANIJA_X + 0.034),                                       # de manija a manija
    BOCA,
    (B + PESTANA) + (-Z_CONTROLES + 0.004 + LARGO_PERILLA + 0.008),  # del reborde a la aleta de la perilla
)


# ── Piezas propias ─────────────────────────────────────────────────────

def anillo(desvio, y, a=A, b=B, r=RADIO_ESQUINA, segmentos=4):
    """Rectángulo de esquinas redondeadas (Godot, plano XZ a la altura y), corrido `desvio`
    hacia afuera. Arranca en +X y gira de +X a +Z."""
    pts = []
    esquinas = [(a - r, b - r, 0), (-(a - r), b - r, 90), (-(a - r), -(b - r), 180), (a - r, -(b - r), 270)]
    for cx, cz, ang0 in esquinas:
        for s in range(segmentos + 1):
            t = math.radians(ang0 + 90 * s / segmentos)
            pts.append((cx + (r + desvio) * math.cos(t), y, cz + (r + desvio) * math.sin(t)))
    return pts


def barrido(bm, perfil, mat=0, tapa_ini=False, tapa_fin=False, **kw):
    """Une anillos del perfil [(desvio, y)] con caras. Tapas opcionales en los extremos."""
    previas = set(bm.faces)
    anillos = [[bm.verts.new(g2b(p)) for p in anillo(o, y, **kw)] for o, y in perfil]
    n = len(anillos[0])
    for r1, r2 in zip(anillos, anillos[1:]):
        for k in range(n):
            bm.faces.new((r1[k], r1[(k + 1) % n], r2[(k + 1) % n], r2[k]))
    if tapa_ini:
        bm.faces.new(list(reversed(anillos[0])))
    if tapa_fin:
        bm.faces.new(anillos[-1])
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def borrar_caras(bm, caras, normal_godot):
    """Borra las caras (de una pieza recién hecha) que miran hacia normal_godot: las que
    quedan pegadas a otra pieza y nunca se ven (guía 3.6)."""
    n = g2b(normal_godot)
    fuera = []
    for f in caras:
        f.normal_update()
        if f.normal.dot(n) > 0.999:
            fuera.append(f)
    bmesh.ops.delete(bm, geom=fuera, context="FACES")


def objeto_en(nombre, bm, materiales, origen_godot):
    """Termina el bmesh y deja el origen del objeto en origen_godot (sin mover la malla)."""
    bmesh.ops.translate(bm, vec=-g2b(origen_godot), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, materiales)
    obj.location = g2b(origen_godot)
    return obj


# ── Modelo ─────────────────────────────────────────────────────────────

def construir():
    acero, negro, piloto_mat, agua_mat = comun.cargar_materiales(
        "M_Acero", "M_PlasticoNegro", "M_PilotoApagado", "M_Agua")

    bm = bmesh.new()
    # Batea: sin la cara de abajo (apoya en el mostrador), con el piso de adentro.
    barrido(bm, PERFIL, mat=0, tapa_fin=True)

    # Frente de controles del lado del vendedor (−Z), debajo del reborde.
    caras = piezas.caja(bm, (0.30, 0.13, FRENTE_CONTROLES + 0.004),
                        (0, 0.095, Z_PARED_ATRAS - FRENTE_CONTROLES / 2 + 0.002), mat=0, bisel=0.005)
    borrar_caras(bm, caras, (0, 0, 1))

    # Perilla (negra): base, cuerpo un poco cónico y una aleta para agarrarla.
    zp = Z_CONTROLES
    piezas.cilindro(bm, 0.022, 0.004, (PERILLA_X, Y_CONTROLES, zp - 0.002), eje="z", lados=12, mat=1,
                    tapas=(True, False))
    piezas.cilindro(bm, 0.016, LARGO_PERILLA, (PERILLA_X, Y_CONTROLES, zp - 0.004 - LARGO_PERILLA / 2),
                    eje="z", lados=12, mat=1, radio_arriba=0.019, tapas=(True, False))
    piezas.caja(bm, (0.008, 0.036, 0.012), (PERILLA_X, Y_CONTROLES, zp - 0.004 - LARGO_PERILLA - 0.002),
                mat=1, bisel=0.002)
    # Aro de acero de la luz piloto (la lente es `pieza_piloto`, aparte).
    piezas.cilindro(bm, 0.013, 0.006, (PILOTO_X, Y_CONTROLES, zp - 0.003), eje="z", lados=12, mat=0,
                    tapas=(True, False))

    # Manijas laterales: dos soportes de acero y una barra negra, debajo del reborde.
    for lado in (-1, 1):
        for zs in (-0.05, 0.05):
            c = piezas.caja(bm, (0.026, 0.02, 0.016), (lado * (MANIJA_X + 0.011), 0.152, zs), mat=0, bisel=0.004)
            borrar_caras(bm, c, (-lado, 0, 0))
        piezas.caja(bm, (0.018, 0.024, 0.13), (lado * (MANIJA_X + 0.025), 0.152, 0), mat=1, bisel=0.006)

    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero, negro])

    # Agua: misma forma que la batea, 1 mm más chica, hasta el 70 % del alto.
    bm = bmesh.new()
    barrido(bm, [(-0.001, PISO + 0.001), (-0.001, PISO + ALTO_AGUA)], tapa_ini=True, tapa_fin=True)
    agua = objeto_en("pieza_agua", bm, [agua_mat], (0, PISO, 0))

    # Lente de la luz piloto: media esfera achatada que asoma del aro.
    bm = bmesh.new()
    zl = zp - 0.006
    caras = piezas.esfera(bm, 0.009, (0, 0, 0), lados=12, escala=(1, 1, 0.6))
    borrar = [f for f in caras if all(v.co.y < 1e-6 for v in f.verts)]  # mitad de atrás (Blender −Y)
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    abiertos = [e for e in bm.edges if len(e.link_faces) == 1]
    bmesh.ops.edgeloop_fill(bm, edges=abiertos)
    for f in bm.faces:
        f.material_index = 0
    piezas.mover(bm, list(bm.faces), (PILOTO_X, Y_CONTROLES, zl))
    piloto = objeto_en("pieza_piloto", bm, [piloto_mat], (PILOTO_X, Y_CONTROLES, zl))

    interior = piezas.punto("punto_interior", (0, PISO, 0))
    raiz = piezas.raiz(ID, [cuerpo, agua, piloto, interior])
    return raiz, cuerpo, agua, piloto, interior


# ── Chequeos propios ───────────────────────────────────────────────────

def _verts_godot(obj):
    m = obj.matrix_world
    return [Vector(((m @ v.co).x, (m @ v.co).z, -(m @ v.co).y)) for v in obj.data.vertices]


def _verts_batea(vs):
    """Vértices de las paredes de adentro y del piso de la batea."""
    return [v for v in vs if abs(v.x) <= A + 1e-5 and abs(v.z) <= B + 1e-5 and v.y >= PISO - 1e-5]


def chequeo_batea(cuerpo, agua):
    """La batea mide exacto `interior` y el agua llega al 70 %."""
    vs = _verts_godot(cuerpo)
    adentro = _verts_batea(vs)
    ancho = max(v.x for v in adentro) - min(v.x for v in adentro)
    prof = max(v.z for v in adentro) - min(v.z for v in adentro)
    piso = min(v.y for v in adentro)
    boca = max(v.y for v in vs)
    alto = boca - piso
    nivel = max(v.y for v in _verts_godot(agua))
    ok = (abs(ancho - W) < 1e-4 and abs(prof - D) < 1e-4 and abs(alto - H) < 1e-4
          and abs(piso - PISO) < 1e-4 and abs(nivel - (PISO + ALTO_AGUA)) < 1e-4)
    return ok, ("Batea %.3f × %.3f × %.3f m, piso a %.3f (dato %.2f × %.2f × %.2f, piso %.3f); "
                "agua hasta %.3f (70 %%)" % (ancho, alto, prof, piso, W, H, D, PISO, nivel))


def chequeo_origen(cuerpo):
    vs = _verts_godot(cuerpo)
    adentro = _verts_batea(vs)
    cx = (max(v.x for v in adentro) + min(v.x for v in adentro)) / 2
    cz = (max(v.z for v in adentro) + min(v.z for v in adentro)) / 2
    base = min(v.y for v in vs)
    ok = abs(cx) < 1e-4 and abs(cz) < 1e-4 and abs(base) < 1e-4
    return ok, "Origen en el centro de la batea, a nivel del mostrador (la perilla corre la caja total)"


def revisar(cuerpo, agua, piloto):
    res = comun.revisar([cuerpo, agua, piloto], PRESUPUESTO, MEDIDAS, origen="base", max_materiales=6)
    res = [chequeo_origen(cuerpo) if t.startswith("Origen") else (ok, t) for ok, t in res]
    res.insert(1, chequeo_batea(cuerpo, agua))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def hoja_revision(raiz, piezas_vis, revision):
    comun.preparar_revision()
    mostrador = bpy.data.objects["ref_mostrador_0,95m"]
    cuadros = comun.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas_vis, "frente", "dia", True),
        ("Lado del vendedor: perilla y piloto · día", piezas_vis, "tres_cuartos_atras", "dia", False),
        ("3/4 · día", piezas_vis, "tres_cuartos", "dia", False),
        ("Arriba: batea y agua · día", piezas_vis, "arriba", "dia", True),
        ("3/4 · atardecer", piezas_vis, "tres_cuartos", "atardecer", False),
    ])
    # Última: sobre el mostrador de 0,95 m, en el lugar de `mostrador_izq` (x = −0,4).
    raiz.location = mostrador.location + Vector((-0.4, 0, 0.95))
    cuadros += comun.sacar_fotos([
        ("Sobre el mostrador (mostrador_izq) · día", piezas_vis + [mostrador], "tres_cuartos_atras", "dia", False),
    ])
    comun.componer_hoja(
        "hervidor_chico · batea 0,36 × 0,18 × 0,26 m · equipo de cocina",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def _vista_desde_atras():
    """comun.encuadrar no tiene vista desde el vendedor: se agrega una 3/4 desde +Y de
    Blender (−Z de Godot), sin tocar comun.py."""
    original = comun.encuadrar

    def encuadrar(objetos, vista, margen=1.25, de_cerca=False):
        if vista != "tres_cuartos_atras":
            return original(objetos, vista, margen, de_cerca)
        original(objetos, "tres_cuartos", margen, de_cerca)
        cam = bpy.context.scene.camera
        esquinas = [o.matrix_world @ Vector(c) for o in objetos for c in o.bound_box]
        centro = (Vector(map(min, *esquinas)) + Vector(map(max, *esquinas))) / 2
        rel = cam.location - centro
        cam.location = centro + Vector((-rel.x * 0.8, -rel.y, rel.z))
        cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()

    comun.encuadrar = encuadrar


def main():
    comun.escena_vacia()
    raiz, cuerpo, agua, piloto, interior = construir()
    revision = revisar(cuerpo, agua, piloto)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, agua, piloto, interior], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        _vista_desde_atras()
        hoja_revision(raiz, [cuerpo, agua, piloto], revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
