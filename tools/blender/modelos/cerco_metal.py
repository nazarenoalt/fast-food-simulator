"""Modelo: cerco de metal (id `cerco_metal`, lista de modelos, etapa 5).

Genera:
    arte/fuentes/accesorios/cerco_metal.blend
    godot/modelos/accesorios/cerco_metal.glb
    docs/arte/revisiones/cerco_metal.jpg

Uso:
    python tools/blender/modelos/cerco_metal.py [--sin-hoja]

Forma: variante de hierro del cerco_bajo (mismo largo, 2,46 m, y mismo anclaje `frente`),
como las rejas de plaza: 2 postes de caño cuadrado de 4 cm con un capitel y una punta de pirámide arriba,
2 planchuelas horizontales (abajo a 0,10–0,13 m y arriba a 0,76–0,79 m) y 18 barrotes
cuadrados de 14 mm cada ≈ 12,5 cm que pasan la planchuela de arriba y terminan en punta de
lanza. Todo en M_Hierro.
Medidas: 2,46 × 0,90 × 0,05 (lista). Postes en x = ±1,205 (los capiteles de 5 cm llegan a
±1,23, como los postes del cerco_bajo).
Origen: centro de la base, a nivel del piso (= anclaje `frente`, como el cerco_bajo).
Objetos (hijos del Empty `cerco_metal`): cerco_metal_cuerpo y `cerco_metal-colonly` (una
caja del tamaño total).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "cerco_metal"
PRESUPUESTO = 600
MEDIDAS = (2.46, 0.9, 0.05)
POSTE_X, POSTE = 1.205, 0.04
POSTE_ARRIBA = 0.83
CAPITEL = (0.05, 0.02)              # lado, alto
PLANCHUELAS = ((0.10, 0.13), (0.76, 0.79))
PLANCHUELA_P = 0.02                 # profundidad
BARROTE = 0.014
BARROTES = 18
BARROTE_ARRIBA = 0.82               # donde arranca la lanza
LANZA = (0.024, 0.045)              # ancho de la base, alto


def lanza(bm, x, y, mat=0):
    """Punta de lanza: rombo achatado (base cuadrada girada 45°) con punta arriba y abajo."""
    w, h = LANZA[0] / 2, LANZA[1]
    yb = y + h * 0.3
    base = [bm.verts.new(g2b(p)) for p in ((x + w, yb, 0), (x, yb, w * 0.5), (x - w, yb, 0), (x, yb, -w * 0.5))]
    arriba = bm.verts.new(g2b((x, y + h, 0)))
    abajo = bm.verts.new(g2b((x, y, 0)))
    for k in range(4):
        a, b = base[k], base[(k + 1) % 4]
        bm.faces.new((a, b, arriba)).material_index = mat
        bm.faces.new((b, a, abajo)).material_index = mat


def construir():
    (hierro,) = comun.cargar_materiales("M_Hierro")
    bm = bmesh.new()
    xi = POSTE_X - POSTE / 2                                  # cara de adentro de los postes
    for sx in (-1, 1):
        x = sx * POSTE_X
        piezas.caja(bm, (POSTE, POSTE_ARRIBA, POSTE), (x, POSTE_ARRIBA / 2, 0), bisel=0.006,
                    sin_abajo=True)
        caras = piezas.caja(bm, (CAPITEL[0], CAPITEL[1], CAPITEL[0]),
                            (x, POSTE_ARRIBA + CAPITEL[1] / 2, 0), bisel=0.005)
        for f in caras:
            f.normal_update()
        arriba = max(caras, key=lambda f: f.normal.z)
        punta = MEDIDAS[1] - POSTE_ARRIBA - CAPITEL[1]
        bmesh.ops.poke(bm, faces=[arriba], offset=punta, use_relative_offset=False)
    for y0, y1 in PLANCHUELAS:
        caras = piezas.caja(bm, (2 * xi, y1 - y0, PLANCHUELA_P), (0, (y0 + y1) / 2, 0), bisel=0.004)
        tapas = []
        for f in caras:
            f.normal_update()
            if abs(f.normal.x) > 0.999:
                tapas.append(f)                                # pegadas a los postes (guía 3.6)
        bmesh.ops.delete(bm, geom=tapas, context="FACES")
    paso = 2 * xi / (BARROTES + 1)
    ya = PLANCHUELAS[0][1]
    for i in range(BARROTES):
        x = -xi + paso * (i + 1)
        caras = piezas.caja(bm, (BARROTE, BARROTE_ARRIBA - ya, BARROTE), (x, (ya + BARROTE_ARRIBA) / 2, 0))
        borrar = []
        for f in caras:
            f.normal_update()
            if abs(f.normal.z) > 0.999:          # tapas: sobre la planchuela y bajo la lanza
                borrar.append(f)
        bmesh.ops.delete(bm, geom=borrar, context="FACES")
        lanza(bm, x, BARROTE_ARRIBA - 0.012)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [hierro])
    col = piezas.colision_caja(ID, MEDIDAS, (0, MEDIDAS[1] / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


def revisar(cuerpo):
    res = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    res = a5.chequeo_normales(res, [cuerpo])
    xi = POSTE_X - POSTE / 2
    res.append((True, "%d barrotes de %d mm cada %.3f m con punta de lanza; planchuelas a %s m"
                % (BARROTES, BARROTE * 1000, 2 * xi / (BARROTES + 1),
                   " y ".join("%.2f–%.2f" % p for p in PLANCHUELAS))))
    return res


def hoja_revision(cuerpo, revision):
    import cerco_bajo
    comun.preparar_revision()
    solo = [cuerpo]
    carro, b = a5.carrito("barra_chica")
    copia = a5.e2.copiar(cuerpo, "ref_cerco")
    copia.location = g2b(b.anclajes["frente"])
    _, bajo, _ = cerco_bajo.construir()
    bajo.parent = None
    bajo.location = g2b((0, 0, -0.6))
    persona = a5.persona()
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado de cerca · día", solo, "costado", "dia", None, None, 3.0),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Detalle: poste, planchuelas y lanzas · día", solo, "bajo", "dia",
         None, None, 0.45),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Con la persona y el cerco_bajo atrás · día", solo + [bajo, persona], "tres_cuartos", "dia",
         None, a5.mover_persona((0.6, 0, 0.5))),
        ("En el anclaje `frente` de la barra chica · día", carro + [copia, persona], "tres_cuartos",
         "dia", None, a5.mover_persona((0.3, 0, 1.0)), 1.05),
        ("Ídem · de costado: queda 5 cm abajo del mostrador", carro + [copia, persona], "costado",
         "dia", None, None, 1.1),
        ("Ídem · atardecer", carro + [copia], "tres_cuartos", "atardecer", None, None, 1.05),
    ]
    a5.hoja(ID, "cerco_metal · 2,46 × 0,90 × 0,05 m · accesorio (anclaje frente)", pedidos, revision)


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = revisar(cuerpo)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [raiz, cuerpo, col])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
