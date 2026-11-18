"""Modelo: moneda (id `moneda`, etapa 2; no está en el juego: la plata es solo el número del
HUD).

Genera:
    arte/fuentes/accesorios/moneda.blend
    godot/modelos/accesorios/moneda.glb
    docs/arte/revisiones/moneda.jpg

Uso:
    python tools/blender/modelos/moneda.py [--sin-hoja]

Forma: disco de 12 lados (lista de modelos) de Ø 0,024 × 0,003, de M_Acero, sin bisel (un
bisel de 1 segmento pasaría el presupuesto; con el canto de 12 caras ya se lee redonda).
Diseño inventado: liso, sin cara ni números (detalle fino, guía 3.5).

Presupuesto: la lista pide 40, pero un prisma cerrado de 12 lados tiene como mínimo 44
triángulos (24 del canto + 10 por tapa). Se deja en 44 y se avisa en el informe.

Familia `accesorios`, como la caja de dinero. Objeto que se agarra: origen en el centro, sin
colisión (si el juego le pone física, la arma el dato, guía 6.1).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "moneda"
FAMILIA = "accesorios"
RADIO, ALTO = 0.012, 0.003
MEDIDAS = (2 * RADIO, ALTO, 2 * RADIO)
PRESUPUESTO = 44   # lista: 40 (ver docstring)


def construir(nombre=ID):
    (acero,) = comun.cargar_materiales("M_Acero")
    bm = bmesh.new()
    # radio_a_caras: así mide Ø 0,024 de cara a cara (la caja envolvente sale justa).
    piezas.cilindro(bm, RADIO, ALTO, (0, 0, 0), eje="y", lados=12, radio_a_caras=True)
    obj = piezas.terminar(nombre, bm, [acero])
    e2.suavizar_hasta(obj, 35)   # canto suave (12 lados doblan 30°), tapas marcadas
    return obj


def medidas_reales(obj):
    mn, mx = e2.limites_godot([obj])
    return tuple(round(v, 4) for v in (mx - mn))


def hoja_revision(moneda, revision):
    import _comida4 as c4
    comun.preparar_revision()
    moneda.location.z = ALTO / 2
    pila = []
    for i in range(4):
        c = e2.copiar(moneda, f"ref_pila_{i}")
        c.location = (0.04, 0.01, ALTO / 2 + i * (ALTO + 0.0003))
        c.rotation_euler.z = i * 0.3
        pila.append(c)
    pan = c4.pan_de_escala(0.0, -0.06)
    pan.hide_render = False
    solo = [moneda]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", solo, 1.4),
        ("Arriba: 12 lados · día", solo, "arriba", "dia", solo, 1.3),
        ("3/4 · día", solo, "tres_cuartos", "dia", solo, 1.6),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", solo, 1.6),
        ("Una pila de monedas · día", [moneda] + pila, "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [moneda, pan] + pila, "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(f"{ID} · Ø 0,024 × 0,003 m · 12 lados · acero", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    moneda = construir()
    revision = comun.revisar(moneda, PRESUPUESTO, MEDIDAS, origen="centro", tolerancia=1e-4)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([moneda], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(moneda, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
