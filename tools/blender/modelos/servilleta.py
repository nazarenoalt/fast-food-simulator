"""Modelo: servilleta de papel (id `servilleta`, etapa 2; no está en el juego: SPEC-009 entrega
en la bandeja).

Genera:
    arte/fuentes/comida/servilleta.blend
    godot/modelos/comida/servilleta.glb
    docs/arte/revisiones/servilleta.jpg

Uso:
    python tools/blender/modelos/servilleta.py [--sin-hoja]

Forma: servilleta de bar doblada en cuatro y después en diagonal, de 0,15 × 0,003 × 0,15
(lista de modelos), M_BlancoCrema, sin bisel (papel, guía 3.3). Arriba se ve el triángulo
de la última capa: la mitad del cuadrado (de la esquina −X+Z a la +X−Z, del lado +X+Z) queda
a 3 mm y la otra mitad, 1,5 mm más abajo, con el escalón del doblez sobre la diagonal. Así se
lee como servilleta doblada y no como una baldosa. 16 triángulos (presupuesto 20).

Objeto que se agarra: origen en el centro, sin colisión (guía 6.1).
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
import _comida4 as c4  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "servilleta"
FAMILIA = "comida"
MEDIDAS = (0.15, 0.003, 0.15)
PRESUPUESTO = 20
ESCALON = 0.0015


def construir(nombre=ID):
    (papel,) = comun.cargar_materiales("M_BlancoCrema")
    w, h = MEDIDAS[0] / 2, MEDIDAS[1] / 2
    bajo = h - ESCALON
    bm = bmesh.new()

    def v(x, y, z):
        return bm.verts.new(g2b((x, y, z)))
    # Esquinas (x, z): A −X+Z, B +X+Z, C +X−Z, D −X−Z. Diagonal del doblez: A–C.
    A, B, C, D = (-w, w), (w, w), (w, -w), (-w, -w)
    Ab, Bb, Cb, Db = (v(x, -h, z) for x, z in (A, B, C, D))
    Ah, Bh, Ch = (v(x, h, z) for x, z in (A, B, C))
    Al, Cl, Dl = (v(x, bajo, z) for x, z in (A, C, D))
    caras = [
        (Ah, Bh, Ch), (Al, Cl, Dl),          # capa de arriba (triángulo) y capa de abajo
        (Al, Ah, Ch, Cl),                    # escalón del doblez
        (Ab, Db, Cb, Bb),                    # abajo
        (Al, Ab, Bb), (Al, Bb, Bh), (Al, Bh, Ah),   # canto A–B (alto, con el escalón en A)
        (Cl, Ch, Bh), (Cl, Bh, Bb), (Cl, Bb, Cb),   # canto B–C (alto, con el escalón en C)
        (Cb, Db, Dl, Cl), (Db, Ab, Al, Dl),  # cantos bajos
    ]
    for c in caras:
        bm.faces.new(c)
    return piezas.terminar(nombre, bm, [papel])


def hoja_revision(serv, revision):
    comun.preparar_revision()
    serv.location.z = MEDIDAS[1] / 2
    otra = e2.copiar(serv, "ref_servilleta_2")
    otra.location = (0.02, 0.015, MEDIDAS[1] * 1.5 + 0.0002)
    otra.rotation_euler.z = 0.35
    pan = c4.pan_de_escala(0.03, -0.13)
    pan.hide_render = False
    solo = [serv]
    cuadros = e2.sacar_fotos([
        ("Arriba: el triángulo del doblez · día", solo, "arriba", "dia", solo, 1.15),
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("3/4 · día", solo, "tres_cuartos", "dia", solo, 1.2),
        ("Bajo: el escalón del doblez · día", solo, "bajo", "dia", solo, 1.1),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", solo, 1.2),
        ("Dos servilletas y un pan de pancho · día", [serv, otra, pan], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(f"{ID} · 0,15 × 0,003 × 0,15 m · doblada en triángulo", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    serv = construir()
    revision = comun.revisar(serv, PRESUPUESTO, MEDIDAS, origen="centro", tolerancia=1e-4)
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [serv])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(serv, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
