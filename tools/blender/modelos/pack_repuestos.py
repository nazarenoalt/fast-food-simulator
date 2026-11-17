"""Modelo: pack de 2 repuestos de aderezo (id `pack_repuestos`, el empaque de `pack_mostaza`,
`pack_ketchup` y `pack_mayonesa` de godot/data/bloques.ron).

Genera:
    arte/fuentes/stock/pack_repuestos.blend
    godot/modelos/stock/pack_repuestos.glb
    docs/arte/revisiones/pack_repuestos.jpg

Uso:
    blender -b -P tools/blender/modelos/pack_repuestos.py
    python tools/blender/modelos/pack_repuestos.py

Forma: solo el paquete (los 2 repuestos los pone el código, REQ-DEP-03, con el modelo
`repuesto_aderezo`). Bandeja de cartón de esquinas redondeadas, paredes apenas abiertas y
una pestaña arriba; y un film termocontraíble transparente que sale de la pestaña, abraza
las dos botellas (de costado tiene forma de "estadio": dos medias vueltas unidas) y se
cierra arriba sobre las tapas. El film es M_PlasticoClaro (alfa 0,15), no M_BolsaPlastica:
con el blanco de la bolsa los repuestos se veían desteñidos.

Un solo modelo para los tres packs: los tres bloques tienen la misma grilla, separación y
`color_empaque` (el cartón); lo que cambia es el color de los repuestos de adentro.

Medidas (bloques.ron): grilla 2 × 1 × 1, separación 0,09 × 0,19 × 0,09 → tamaño 0,18 × 0,19
× 0,09; el paquete de hoy (bloque_stock.rs, Bandeja) suma 4 mm de cada lado y el film llega
a 0,194. Afuera: 0,188 × 0,194 × 0,098. Adentro de la bandeja entran las dos botellas
(Ø 0,078, en x = ±0,045).
Cambio respecto de hoy: la pared de la bandeja mide 0,05 (hoy 0,45 del alto = 0,0855): con
la de hoy la bandeja tapaba la mitad de las botellas y no se veía la etiqueta.
Origen: centro de la base, a nivel de apoyo (las botellas arrancan en y = 0; quedan 3 mm
metidas en el fondo de cartón, que no se ve).

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready y
Paquete::ready), como en la bolsa de panes y la bandeja de salchichas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pack_repuestos"
FAMILIA = "stock"
PRESUPUESTO = 400  # empaques y bloques de stock (guía 3.1)

GRILLA = (2, 1, 1)
SEPARACION = (0.09, 0.19, 0.09)
TAMANO = (GRILLA[0] * SEPARACION[0], GRILLA[2] * SEPARACION[1], GRILLA[1] * SEPARACION[2])
E = 0.004                                   # lo que suma el paquete de hoy de cada lado
MEDIO_X, MEDIO_Z = TAMANO[0] / 2 + E, TAMANO[2] / 2 + E   # 0,094 × 0,049
RADIO = 0.010
ALTO_BANDEJA = 0.05
ALTO_FILM = TAMANO[1] + 0.004               # 0,194

MEDIDAS = (2 * MEDIO_X, ALTO_FILM, 2 * MEDIO_Z)

# Bandeja: (meter, y), por afuera de abajo hacia arriba, la pestaña y por adentro hasta el
# fondo (que se cierra). Pared de cartón de 3–4 mm.
PERFIL_BANDEJA = [
    (0.0040, 0.0),
    (0.0015, ALTO_BANDEJA - 0.004),
    (0.0, ALTO_BANDEJA - 0.003),
    (0.0, ALTO_BANDEJA),
    (0.0035, ALTO_BANDEJA),
    (0.0050, ALTO_BANDEJA - 0.004),
    (0.0065, 0.003),
]
# Film: (meter, y, radio de esquina). Sale de la pestaña, se hace "estadio" alrededor de las
# botellas (radio = media profundidad: cada punta es media vuelta alrededor de una botella)
# y se cierra arriba de las tapas.
_ESTADIO = MEDIO_Z - 0.004
PERFIL_FILM = [
    (0.0015, ALTO_BANDEJA + 0.0005, RADIO),
    (0.0030, 0.066, 0.030),
    (0.0040, 0.140, _ESTADIO),
    (0.0120, 0.172, MEDIO_Z - 0.012),
    (0.0250, 0.1895, MEDIO_Z - 0.025),
    (0.0290, ALTO_FILM, MEDIO_Z - 0.029),
]


def suavizar_material(obj, indice):
    """Sombreado suave en las caras de un material (el film es como una tela, guía 3.4)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for e in bm.edges:
        if all(f.material_index == indice for f in e.link_faces):
            e.smooth = True
    bm.to_mesh(obj.data)
    bm.free()


def construir():
    m_carton, m_film = comun.cargar_materiales("M_Carton", "M_PlasticoClaro")
    bm = bmesh.new()
    e2.torno_rr(bm, PERFIL_BANDEJA, MEDIO_X, MEDIO_Z, RADIO, segs=3, mats=0, tapa_fin=True)
    e2.torno_rr(bm, PERFIL_FILM, MEDIO_X, MEDIO_Z, RADIO, segs=3, mats=1, tapa_fin=True)
    obj = piezas.terminar(ID, bm, [m_carton, m_film], sombreado="duro")
    suavizar_material(obj, 1)
    e2.suavizar_hasta(obj, 31)
    return obj


def posiciones_unidades():
    """Lo mismo que DefBloque::posicion_unidad (rust/core/src/deposito.rs), en Godot."""
    cols, filas, capas = GRILLA
    sx, sy, sz = SEPARACION
    for i in range(cols * filas * capas):
        capa, resto = divmod(i, cols * filas)
        fila, col = divmod(resto, cols)
        yield ((col - (cols - 1) / 2) * sx, capa * sy + sy / 2, ((filas - 1) / 2 - fila) * sz)


def chequeo_lugar(obj):
    """Las botellas (Ø 0,078) entran adentro de la bandeja y del film."""
    vs = e2.verts_godot(obj)
    fondo = [v for v in vs if abs(v.y - 0.003) < 1e-5]
    ok = min(MEDIO_X - abs(v.x) for v in fondo) >= 0 and \
        max(abs(v.x) for v in fondo) >= 0.045 + 0.039 and max(abs(v.z) for v in fondo) >= 0.039
    return ok, "Adentro entran las 2 botellas (x = ±0,045, Ø 0,078); film hasta 0,194"


def hoja_revision(pack, revision):
    import repuesto_aderezo as rep
    comun.preparar_revision()
    e2.sin_cara_de_atras(pack)
    mats = e2.materiales_aderezo()
    llenos, centro = [], []
    for j, (nombre, _) in enumerate(e2.ADEREZOS):
        dx = (j - 1) * 0.22
        p = pack if j == 1 else e2.copiar(pack, f"ref_pack_{nombre}")
        p.location.x = dx
        este = [p]
        for pos in posiciones_unidades():
            raiz, cuerpo, resto = rep.construir()
            cuerpo.data.materials[0] = mats[nombre]
            raiz.location = piezas.g2b(pos) + Vector((dx, 0, 0))
            este += [cuerpo, resto]
        llenos += este
        if j == 1:
            centro = este
    cuadros = e2.sacar_fotos([
        ("Frente (cliente) con 2 repuestos de ketchup · día", centro, "frente", "dia"),
        ("Costado · día", centro, "costado", "dia"),
        ("3/4 · día", centro, "tres_cuartos", "dia"),
        ("3/4 · atardecer", centro, "tres_cuartos", "atardecer"),
        ("Los tres packs · día", llenos, "tres_cuartos", "dia"),
        ("Solo (lo que exporta el .glb) · día", [pack], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(
        f"{ID} · 0,188 × 0,194 × 0,098 m · un empaque para los tres packs",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    pack = construir()
    revision = comun.revisar(pack, PRESUPUESTO, MEDIDAS, origen="base")
    revision.insert(1, chequeo_lugar(pack))
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([pack], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pack, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
