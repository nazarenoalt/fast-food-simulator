"""Modelo: bandeja de entrega del carrito (id `bandeja_entrega`, la que arma carrito.rs en
el punto `entrega` de cada base, REQ-CLI-07).

Genera:
    arte/fuentes/carritos/bandeja_entrega.blend
    godot/modelos/carritos/bandeja_entrega.glb
    docs/arte/revisiones/bandeja_entrega.jpg

Uso:
    blender -b -P tools/blender/modelos/bandeja_entrega.py
    python tools/blender/modelos/bandeja_entrega.py

Forma: bandeja de plástico roja de patio de comidas: esquinas redondeadas, borde en las
cuatro puntas, paredes abiertas hacia afuera y un reborde redondeado arriba. El fondo de
adentro es plano (ahí se apoya la comida que se entrega).

Medidas = lo que arma hoy carrito.rs (construir_bandeja): fondo de 0,30 × 0,22 y bordes de
2 cm de alto y 8 mm de espesor en z = ±0,11 → caja 0,30 × 0,02 × 0,228. Hoy hay borde solo
adelante y atrás; el modelo lo tiene en las cuatro puntas (una bandeja de verdad), dentro de
la misma caja. La zona de entrega del código (0,30 × 0,14 × 0,22, desde y = 0) no cambia.
Color: M_RojoAcento (hoy (0,8; 0,12; 0,1), casi igual).
Origen: centro de la base, a nivel del mostrador = el punto `entrega` del .ron de la base.
Abajo queda abierta (apoya en la mesada, guía 3.6).

Objetos (hijos del Empty `bandeja_entrega`):
- `bandeja_entrega_cuerpo` (M_RojoAcento).
- `bandeja_entrega-colonly`: el fondo (0,30 × 0,004 × 0,228). Hoy la bandeja no tiene
  colisión y la comida se hunde 8 mm en el dibujo; con esta queda apoyada sobre el fondo. Los
  bordes no colisionan, para que la comida no se trabe al dejarla.
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
from piezas import g2b  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "bandeja_entrega"
FAMILIA = "carritos"
PRESUPUESTO = 400  # objeto chico de mostrador (entre empaques 400 y utensilios 500)

ANCHO, ALTO, FONDO = 0.30, 0.02, 0.228
MEDIO_X, MEDIO_Z = ANCHO / 2, FONDO / 2
RADIO = 0.025
PISO = 0.004
MEDIDAS = (ANCHO, ALTO, FONDO)

# (meter, y): por afuera de abajo hacia arriba, el reborde y por adentro hasta el fondo.
PERFIL = [
    (0.010, 0.0),
    (0.003, 0.0165),
    (0.0, 0.0185),
    (0.0015, ALTO),
    (0.0065, ALTO),
    (0.0080, 0.0185),
    (0.0160, PISO + 0.0005),
    (0.0185, PISO),
]


def construir():
    (rojo,) = comun.cargar_materiales("M_RojoAcento")
    bm = bmesh.new()
    e2.torno_rr(bm, PERFIL, MEDIO_X, MEDIO_Z, RADIO, segs=3, mats=0, tapa_fin=True)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [rojo])
    col = piezas.colision_caja(ID, (ANCHO, PISO, FONDO), (0, PISO / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


# ── Hoja de revisión ───────────────────────────────────────────────────

def hoja_revision(raiz, cuerpo, revision):
    comun.preparar_revision()
    import pancho
    p_raiz, pan, salchicha = pancho.construir()
    p_raiz.location = g2b((-0.03, PISO + 0.0225, 0.02))
    p_raiz.rotation_euler.z = 0.3
    con = [cuerpo, pan, salchicha]
    solo = [cuerpo]
    cuadros = e2.sacar_fotos([
        ("Frente (cliente) · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Con un pancho para entregar · día", con, "tres_cuartos", "dia"),
        ("3/4 · atardecer", con, "tres_cuartos", "atardecer"),
    ])
    # Sobre la barra chica, en `entrega` (0,5; 0,95; 0,2), vista del cliente.
    for o in con:
        o.hide_render = False
    barra = e2.barra_chica()
    raiz.location = g2b((0.5, 0.95, 0.2))
    p_raiz.location += g2b((0.5, 0.95, 0.2))
    cuadros += e2.sacar_fotos([
        ("En la barra chica (punto entrega) · día", con + barra, "tres_cuartos", "dia", con, 3.0),
    ])
    comun.componer_hoja(
        f"{ID} · 0,30 × 0,02 × 0,228 m · bandeja de entrega del carrito",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = comun.revisar([cuerpo], PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
