# Scripts de Blender

Generan la biblioteca de arte y los modelos 3D siguiendo la
[guía de modelado](../../docs/arte/guia-modelado-3d.md). Cada modelo hecho por código es un
script en `modelos/`: si hay que cambiar algo, se cambia el script y se vuelve a correr.

## Cómo correrlos

**Con Blender instalado** (4.2 o más nuevo):

```bash
blender -b -P tools/blender/biblioteca.py
```

```bash
blender -b -P tools/blender/modelos/pan_pancho.py
```

**Sin Blender**, con el paquete `bpy` de Python (Blender como librería; necesita Python 3.13):

```bash
python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy pillow
```

```bash
.venv-blender/bin/python tools/blender/biblioteca.py
```

```bash
.venv-blender/bin/python tools/blender/modelos/pan_pancho.py
```

La hoja de revisión necesita `pillow`. Con el Blender normal no viene: se generan los
renders pero no la hoja. Para saltearla, agregá `--sin-hoja` al final del comando.

## Qué hay

| Archivo | Qué hace |
|---|---|
| `biblioteca.py` | Crea `arte/biblioteca/materiales.blend` (la paleta, desde `tools/arte/paleta.json`) y `arte/biblioteca/referencias.blend` (silueta de 1,75 m, mostrador de 0,95 m, piso, sol y cielo de día y de atardecer). **Correrlo primero** y cada vez que cambie la paleta. |
| `comun.py` | Funciones compartidas: cargar materiales de la biblioteca, revisión automática (guía 8.2), exportar `.glb` (guía 7.3), renders y hoja de revisión (guía 8.1). |
| `piezas.py` | Piezas básicas para objetos duros (caja con bisel, cilindro, esfera, colisión `-colonly`, Empties `punto_`), con medidas y posiciones en ejes de Godot, como en los `.ron`. |
| `modelos/<id>.py` | Un script por modelo. Genera `arte/fuentes/<familia>/<id>.blend`, `godot/modelos/<familia>/<id>.glb` y `docs/arte/revisiones/<id>.jpg`. Termina con error si el modelo no cumple la guía. |

## Modelar a mano

Si un modelo se hace a mano en Blender en vez de por código:

1. Abrí `arte/biblioteca/referencias.blend` para tener la escala a mano.
2. Traé los materiales desde `arte/biblioteca/materiales.blend` (*File → Append → Material*,
   o desde el *Asset Browser*). No crees materiales nuevos.
3. Guardá en `arte/fuentes/<familia>/<id>.blend` y exportá con las opciones de la guía (7.3).
4. Para la revisión automática, se puede llamar a `comun.revisar()` desde la consola de
   Python de Blender.
