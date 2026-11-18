"""Modelo: persona mayor (id `persona_mayor`).

Genera:
    arte/fuentes/personajes/persona_mayor.blend
    godot/modelos/personajes/persona_mayor.glb
    docs/arte/revisiones/persona_mayor.jpg

Uso:
    python tools/blender/modelos/persona_mayor.py [--sin-hoja]

Persona mayor de 1,65 m (parada derecha; encorvada mide un poco menos): columna y cuello hacia
adelante en la pose de descanso (así toda animación la conserva), algo de panza, camisa de
manga larga, pantalón gris, zapatos marrones y pelado con pelo canoso a los costados. Camina
más despacio (1,0 m/s).
Mismo esqueleto, superficies y nombres de animaciones que las otras personas: ver _persona.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _persona  # noqa: E402

ID = "persona_mayor"
PRESUPUESTO = 3000  # guía 3.1 / lista de modelos
PARAMETROS = {   'altura': 1.65,
    'cabeza': 0.98,
    'ancho': 1.0,
    'grosor': 0.98,
    'hombros': 0.95,
    'cadera': 1.02,
    'cintura': 1.08,
    'pecho': 0.0,
    'panza': 0.7,
    'postura': 1.0,
    'manga': 'larga',
    'pantalon': 'largo',
    'pelo': 'pelado',
    'vel_caminar': 1.0,
    'periodo_caminar': 1.1,
    'vel_trotar': 2.2,
    'periodo_trotar': 0.8,
    'materiales': {   'piel': 'M_Piel1',
                      'pelo': 'M_PeloCanoso',
                      'remera': 'M_TelaBeige',
                      'pantalon': 'M_TelaGris',
                      'zapatillas': 'M_Tronco',
                      'detalles': 'M_PlasticoNegro'}}


def main():
    _persona.main(ID, PARAMETROS, PRESUPUESTO, "apenas encorvada")


if __name__ == "__main__":
    main()
