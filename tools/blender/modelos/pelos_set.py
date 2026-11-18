"""Modelo: set de peinados (id `pelos_set`).

Genera:
    arte/fuentes/personajes/pelos_set.blend
    godot/modelos/personajes/pelos_set.glb
    docs/arte/revisiones/pelos_set.jpg

Uso:
    python tools/blender/modelos/pelos_set.py [--sin-hoja]

Ocho peinados intercambiables, cada uno un objeto `pelo_<nombre>` de una sola superficie
(el juego le pone el color de pelo: M_PeloNegro/Castano/Rubio/Canoso):
    corto, rapado, raya (con flequillo de costado), largo (hasta los hombros), colita,
    rodete, rulos, pelado (pelado arriba, pelo a los costados y atrás).
Construcción (_persona.pelo): un casco que copia la forma de la cabeza (rayos desde el centro
de la cabeza contra la malla de la cabeza de escala 1), con grosor que va de "arriba" al
"borde", una línea de pelo que baja a los costados y en la nuca, patillas, algo de
irregularidad y sombreado facetado (se lee como mechones y no como gorro). En el borde el
casco se mete adentro de la cabeza y se cierra: volumen cerrado, normales hacia afuera.

Cómo se engancha: el origen de cada peinado es la base del cráneo, que es la cabeza del hueso
Head de una cabeza de escala 1. En cada persona hay un `punto_pelo` (hijo del hueso Head, en
ese punto, ya escalado por la cabeza de la variante): el peinado va como hijo de punto_pelo con
transformación identidad. En el .glb todos los peinados están en el origen, sin giro ni escala.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

import _persona  # noqa: E402
import comun  # noqa: E402
import persona_adulto_a  # noqa: E402

ID = "pelos_set"
PRESUPUESTO = 300   # por peinado (lista de modelos)
COLORES = {
    "corto": "M_PeloCastano", "rapado": "M_PeloNegro", "raya": "M_PeloCastano", "largo": "M_PeloNegro",
    "colita": "M_PeloRubio", "rodete": "M_PeloCastano", "rulos": "M_PeloNegro", "pelado": "M_PeloCanoso",
}


def construir():
    pelos = []
    for estilo in _persona.ESTILOS_PELO:
        mat = comun.cargar_materiales(COLORES[estilo])[0]
        pelos.append(_persona.pelo(estilo, mat))
    return pelos


def revisar(pelos):
    res = []
    tris = {p.name: comun.contar_triangulos(p) for p in pelos}
    res.append((all(t <= PRESUPUESTO for t in tris.values()),
                "Triángulos por peinado (máx. %d): " % PRESUPUESTO + ", ".join(
                    f"{n.removeprefix('pelo_')} {t}" for n, t in tris.items())))
    limpio = all(p.rotation_euler.to_quaternion().angle < 1e-5 and all(abs(s - 1) < 1e-5 for s in p.scale)
                 and p.location.length < 1e-6 for p in pelos)
    res.append((limpio, "Todos en el origen (base del cráneo), rotación 0 y escala 1"))
    validos = comun.paleta()
    nombres = [p.data.materials[0].name for p in pelos]
    res.append((all(n in validos for n in nombres) and all(len(p.data.materials) == 1 for p in pelos),
                "Una superficie por peinado, de la paleta (Pelo…): el juego le cambia el color"))
    malas = abiertas = 0
    for p in pelos:
        a, b = _persona._componentes_bien(p)
        malas += a
        abiertas += b
    res.append((malas == 0 and abiertas == 0,
                f"Piezas cerradas con normales hacia afuera ({malas} mal, {abiertas} abiertas)"))
    return res


def hoja(pelos, revision):
    """Cada peinado puesto en la cabeza de persona_adulto_a (sin animar)."""
    import tempfile
    from mathutils import Vector as V
    R = _persona.construir("persona_adulto_a", persona_adulto_a.PARAMETROS)
    R["pelo"].hide_render = True
    comun.preparar_revision()
    _persona.poner_pose(R["arm"], _persona.Pose(R["esq"]))
    copias = []
    for p in pelos:
        c = p.copy()
        bpy.context.scene.collection.objects.link(c)
        c.parent = R["punto"]
        c.matrix_parent_inverse.identity()
        copias.append(c)
    p.hide_render = True
    for p in pelos:
        p.hide_render = True
    tmp = Path(tempfile.mkdtemp())
    cuadros = []
    pedidos = [(c, "3/4", V((0.65, -1.3, 0.25))) for c in copias]
    atras = {"largo", "colita", "rodete", "pelado"}
    pedidos += [(c, "de atrás", V((-0.8, 1.3, 0.3))) for c in copias if c.name.split(".")[0].removeprefix("pelo_") in atras]
    for c, vista, d in pedidos:
        for o in copias:
            o.hide_render = o is not c
        comun.poner_luz("dia")
        _persona._encuadre_cara(R, d)
        nombre = c.name.split(".")[0]
        cuadros.append((f"{nombre} · {vista} ({COLORES[nombre.removeprefix('pelo_')].removeprefix('M_')})",
                        comun.render(tmp / f"{len(cuadros)}.png")))
    comun.componer_hoja("pelos_set · 8 peinados · ≤300 tris c/u · hijos de punto_pelo (hueso Head)",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg", columnas=4)


def main():
    comun.escena_vacia()
    pelos = construir()
    revision = revisar(pelos)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{_persona.FAMILIA}/{ID}.blend")
    comun.exportar_glb(pelos, comun.RAIZ / f"godot/modelos/{_persona.FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja(pelos, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
