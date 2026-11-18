"""Modelo: cordón de vereda, tramo de 2 m (id `cordon_vereda`, rust/game/src/plaza.rs).

Genera:
    arte/fuentes/plaza/cordon_vereda.blend
    godot/modelos/plaza/cordon_vereda.glb
    docs/arte/revisiones/cordon_vereda.jpg

Uso:
    python tools/blender/modelos/cordon_vereda.py [--sin-hoja]

Forma: un perfil de cordón estirado 2 m sobre X (M_Vereda), con la arista de arriba del lado
de la calle achaflanada 3 cm (la que pisan las ruedas y la que se ve desde la calle) y la del
lado de la vereda 2 cm (guía 3.3: 2–3 cm en mobiliario urbano). Sin cara de abajo (apoya en
el piso). Las puntas (±X) sí van cerradas: los tramos se ponen uno al lado del otro y en las
esquinas la punta se ve.

Orientación: la calle queda hacia −Z (como en plaza.rs, donde la calle está al norte, −Z, de
la vereda) y la vereda hacia +Z, el frente.

Medidas: 2,00 × 0,12 × 0,20. La lista-de-modelos dice 2,0 × 0,15 × 0,15, pero el juego hoy
dibuja el cordón como una caja de 0,12 de alto y 0,20 de ancho (plaza.rs, "Cordón de la
vereda"): se respeta lo que hay en el juego (guía 1, "si hoy algo mide 0,17 m, el modelo mide
0,17 m"). Hoy el cordón es más claro (0,75; 0,75; 0,72) que la vereda; acá usa M_Vereda.
Sin colisión: hoy el cordón es solo visual.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "cordon_vereda"
PRESUPUESTO = 50
LARGO, ALTO, ANCHO = 2.0, 0.12, 0.20
MEDIDAS = (LARGO, ALTO, ANCHO)
CHAFLAN_CALLE, CHAFLAN_VEREDA = 0.03, 0.02


def construir():
    (vereda,) = comun.cargar_materiales("M_Vereda")
    bm = bmesh.new()
    a = ANCHO / 2
    plaza.perfil_extruido(bm, [
        (-a, 0.0), (-a, ALTO - CHAFLAN_CALLE), (-a + CHAFLAN_CALLE, ALTO),     # lado calle (−Z)
        (a - CHAFLAN_VEREDA, ALTO), (a, ALTO - CHAFLAN_VEREDA), (a, 0.0),       # lado vereda (+Z)
    ], LARGO)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [vereda])
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
        plaza.hoja(ID, "cordon_vereda · tramo de 2,0 × 0,12 × 0,20 m · calle hacia −Z", [
            ("Frente (lado vereda) · día", c, "frente", "dia", True),
            ("Costado (perfil: calle a la derecha) · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
        ], revision, persona_en=(0.6, 0, 0.45))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
