"""Modelo: borde de cantero, tramo de 2 m (id `cantero`).

Genera:
    arte/fuentes/plaza/cantero.blend
    godot/modelos/plaza/cantero.glb
    docs/arte/revisiones/cantero.jpg

Uso:
    python tools/blender/modelos/cantero.py [--sin-hoja]

Forma: cordoncito de piedra (M_Piedra) de 0,10 × 0,10 estirado 2 m sobre X, con las dos
aristas de arriba achaflanadas 2 cm (guía 3.3). Sin cara de abajo (apoya en el piso); las
puntas cerradas, para que se vean bien en las esquinas del cantero. Es simétrico: da lo mismo
de qué lado queda el pasto.

Medidas (lista-de-modelos): 2,00 × 0,10 × 0,10. Hoy el juego no tiene canteros, así que no
reemplaza nada. Sin colisión (10 cm: se pasa por arriba, como el cordón de hoy).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "cantero"
PRESUPUESTO = 50
LARGO, ALTO, ANCHO = 2.0, 0.10, 0.10
MEDIDAS = (LARGO, ALTO, ANCHO)
CHAFLAN = 0.02


def construir():
    (piedra,) = comun.cargar_materiales("M_Piedra")
    bm = bmesh.new()
    a = ANCHO / 2
    plaza.perfil_extruido(bm, [
        (-a, 0.0), (-a, ALTO - CHAFLAN), (-a + CHAFLAN, ALTO),
        (a - CHAFLAN, ALTO), (a, ALTO - CHAFLAN), (a, 0.0),
    ], LARGO)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [piedra])
    raiz = piezas.raiz(ID, [cuerpo])
    return raiz, cuerpo


def main():
    comun.escena_vacia()
    raiz, cuerpo = construir()
    revision = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [raiz, cuerpo])
    if "--sin-hoja" not in sys.argv:
        c = [cuerpo]
        plaza.hoja(ID, "cantero · tramo de 2,0 × 0,10 × 0,10 m · borde de piedra", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado (perfil) · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
        ], revision, persona_en=(0.6, 0, 0.4))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
