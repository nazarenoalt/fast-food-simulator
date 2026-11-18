"""Modelo: chico / chica (id `persona_chico`).

Genera:
    arte/fuentes/personajes/persona_chico.blend
    godot/modelos/personajes/persona_chico.glb
    docs/arte/revisiones/persona_chico.jpg

Uso:
    python tools/blender/modelos/persona_chico.py [--sin-hoja]

Chico de 1,20 m (unos 7 años): cabeza más grande en proporción (casi 6 cabezas), piernas
más cortas, remera amarilla, bermuda de jean y zapatillas rojas. Camina a 1,1 m/s con pasos
más cortos.
Mismo esqueleto, superficies y nombres de animaciones que las otras personas: ver _persona.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _persona  # noqa: E402

ID = "persona_chico"
PRESUPUESTO = 2500  # guía 3.1 / lista de modelos
PARAMETROS = {   'altura': 1.2,
    'cabeza': 0.88,
    'ancho': 0.92,
    'grosor': 0.92,
    'hombros': 0.92,
    'cadera': 0.95,
    'cintura': 1.0,
    'pecho': 0.0,
    'panza': 0.2,
    'piernas': 0.96,
    'manga': 'corta',
    'pantalon': 'corto',
    'pelo': 'raya',
    'vel_caminar': 1.1,
    'periodo_caminar': 0.8,
    'vel_trotar': 2.6,
    'periodo_trotar': 0.6,
    'materiales': {   'piel': 'M_Piel4',
                      'pelo': 'M_PeloNegro',
                      'remera': 'M_Amarillo',
                      'pantalon': 'M_Jean',
                      'zapatillas': 'M_RojoAcento',
                      'detalles': 'M_PlasticoNegro'}}


def main():
    _persona.main(ID, PARAMETROS, PRESUPUESTO, "para la agenda jugar")


if __name__ == "__main__":
    main()
