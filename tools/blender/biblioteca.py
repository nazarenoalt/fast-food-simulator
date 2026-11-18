"""Crea la biblioteca de arte (guía de modelado, sección 9):

- arte/biblioteca/materiales.blend: todos los materiales de la paleta (tools/arte/paleta.json),
  marcados como assets para usarlos desde el Asset Browser de Blender.
- arte/biblioteca/referencias.blend: silueta humana de 1,75 m, mostrador de 0,95 m, piso,
  y la luz de día y de atardecer del juego.

Uso (cualquiera de las dos):
    blender -b -P tools/blender/biblioteca.py
    python tools/blender/biblioteca.py        # con el paquete bpy instalado
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix  # noqa: E402

import comun  # noqa: E402


def materiales():
    comun.escena_vacia()
    for nombre, m in comun.paleta().items():
        mat = comun.crear_material(
            nombre, m["hex"], m.get("metalico", 0.0), m.get("rugosidad", 0.7),
            m.get("alfa", 1.0), m.get("emision", 0.0),
        )
        mat.use_fake_user = True  # que se guarde aunque ningún objeto lo use
        try:
            mat.asset_mark()
        except (AttributeError, RuntimeError):
            pass
    comun.guardar_blend(comun.MATERIALES_BLEND)


def _caja(bm, medidas, centro):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(centro) @ Matrix.Diagonal((*medidas, 1)))


def _cilindro(bm, radio, alto, centro, lados=12):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=radio, radius2=radio,
                          depth=alto, matrix=Matrix.Translation(centro))


def _persona(material):
    """Maniquí low poly de 1,75 m (REQ-JUG-05), parado en el origen, mirando a −Y."""
    bm = bmesh.new()
    for x in (-0.09, 0.09):
        _cilindro(bm, 0.065, 0.82, (x, 0, 0.41))          # piernas
        _cilindro(bm, 0.045, 0.62, (x * 2.6, 0, 1.13))    # brazos
    _caja(bm, (0.38, 0.22, 0.58), (0, 0, 1.13))           # torso
    _cilindro(bm, 0.05, 0.08, (0, 0, 1.45))               # cuello
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.115,
                              matrix=Matrix.Translation((0, 0, 1.635)))  # cabeza: tope a 1,75
    _caja(bm, (0.06, 0.04, 0.03), (0, -0.115, 1.65))      # nariz: marca el frente
    for f in bm.faces:
        f.smooth = False
    return comun.objeto_desde_bmesh("ref_persona_1,75m", bm, [material])


def _cielo(nombre, luz):
    mundo = bpy.data.worlds.new(nombre)
    if mundo.node_tree is None:  # Blender < 5 necesita activar los nodos
        mundo.use_nodes = True
    nodos = mundo.node_tree.nodes
    enlaces = mundo.node_tree.links
    fondo = next(n for n in nodos if n.type == "BACKGROUND")
    coord = nodos.new("ShaderNodeTexCoord")
    separar = nodos.new("ShaderNodeSeparateXYZ")
    rampa = nodos.new("ShaderNodeValToRGB")
    enlaces.new(coord.outputs["Generated"], separar.inputs[0])
    enlaces.new(separar.outputs["Z"], rampa.inputs["Fac"])
    enlaces.new(rampa.outputs["Color"], fondo.inputs["Color"])
    # Z va de −1 (abajo) a 1 (arriba): el horizonte es 0 → posición 0,5 de la rampa.
    rampa.color_ramp.elements[0].position = 0.5
    rampa.color_ramp.elements[0].color = comun.hex_a_lineal(luz["cielo_horizonte"])
    rampa.color_ramp.elements[1].position = 0.85
    rampa.color_ramp.elements[1].color = comun.hex_a_lineal(luz["cielo_arriba"])
    fondo.inputs["Strength"].default_value = luz["cielo_fuerza"]
    mundo.use_fake_user = True
    return mundo


def _sol(nombre, luz, coleccion):
    datos = bpy.data.lights.new(nombre, "SUN")
    datos.color = comun.hex_a_lineal(luz["sol_color"])[:3]
    datos.energy = luz["sol_fuerza"]
    datos.angle = math.radians(1.5)
    sol = bpy.data.objects.new(nombre, datos)
    sol.rotation_euler = (math.radians(90 - luz["sol_altura"]), 0, math.radians(luz["sol_rumbo"]))
    coleccion.objects.link(sol)
    return sol


def referencias():
    escena = comun.escena_vacia()
    vereda, acero, pintura, gris = comun.cargar_materiales(
        "M_Vereda", "M_Acero", "M_PinturaCarrito", "M_Piedra")
    col = bpy.data.collections.new(comun.COLECCION_REFERENCIAS)
    escena.collection.children.link(col)

    def mover_a_col(obj):
        for c in obj.users_collection:
            c.objects.unlink(obj)
        col.objects.link(obj)
        return obj

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=10.0)
    mover_a_col(comun.objeto_desde_bmesh("ref_piso", bm, [vereda]))

    persona = mover_a_col(_persona(gris))
    persona.location = (-1.2, 0.6, 0)

    bm = bmesh.new()
    _caja(bm, (1.6, 0.7, 0.91), (0, 0, 0.455))     # cuerpo de la barra chica
    _caja(bm, (1.64, 0.76, 0.04), (0, 0.02, 0.93))  # mesada a 0,95 m
    mostrador = mover_a_col(comun.objeto_desde_bmesh("ref_mostrador_0,95m", bm, [pintura, acero]))
    for p in mostrador.data.polygons:
        p.material_index = 1 if p.center.z > 0.905 else 0
    mostrador.location = (1.6, 0.8, 0)

    for modo, luz in comun.LUCES.items():
        _sol(f"sol_{modo}", luz, col)
        _cielo(f"cielo_{modo}", luz)
    escena.world = bpy.data.worlds["cielo_dia"]
    comun.guardar_blend(comun.REFERENCIAS_BLEND)


if __name__ == "__main__":
    materiales()
    referencias()
