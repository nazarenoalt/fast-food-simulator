"""Modelo: paloma de plaza (id `paloma`, lista-de-modelos, etapa 3 · Personajes; SPEC-013).

Genera:
    arte/fuentes/personajes/paloma.blend
    godot/modelos/personajes/paloma.glb
    docs/arte/revisiones/paloma.jpg

Uso:
    python tools/blender/modelos/paloma.py [--sin-hoja]

Qué hay hoy en el juego (rust/game/src/palomas.rs, REQ-AMB-10): 16 palomas que picotean en
los caminos y salen volando si el jugador se acerca a menos de 3,5 m. Cada una es un Node3D
con un cuerpo (esfera escalada 0,144 × 0,135 × 0,234 con el centro a 0,11), una cola (caja),
la cabeza (esfera de radio 0,045 + pico, colgada de un nodo en (0; 0,17; 0,08) que gira en X
para picotear) y dos alas (cajas de 0,16 × 0,11 abiertas hacia los costados, colgadas de
nodos en (±0,06; 0,14; 0) que giran en Z para aletear). No tiene patas: el cuerpo flota a 4 cm.

Forma: paloma bravía (la de plaza). Cuerpo de huevo con el pecho alto y lleno, el lomo que
baja hasta la cola (abanico chato con la franja oscura de la punta), cabeza chica y redonda
sobre un cuello grueso, pico corto, patas cortas rosadas con tres dedos adelante y uno atrás.
Alas plegadas sobre los costados, cruzándose sobre la cola, con una franja oscura y las
puntas oscuras. Lo que la hace reconocible de perfil: cabeza chica, pecho inflado y la línea
del lomo que baja derecha hasta la punta de la cola.

Colores (no hay grises de paloma en la paleta, se usan los más parecidos):
    M_Vereda (#7A7A78)      cuerpo y cola
    M_Piedra (#B2B2AD)      alas (más claras que el cuerpo, como en la bravía) y cera del pico
    M_MetalOscuro (#595961) cabeza y cuello (el metálico da un brillo, como el tornasolado
                            del cuello), franja de las alas y puntas, franja de la cola
    M_Terracota (#B4623E)   patas

Medidas: 0,12 × 0,19 × 0,29 (la lista dice ≈ 0,1 × 0,15 × 0,25, que es chica para una paloma
de verdad: 30–35 cm de largo; la de hoy en el juego mide 0,35 de largo y 0,215 de alto).
Origen: en el piso, entre las patas (las patas apoyan en Y = 0 y están centradas en X y Z; la
cola corre la caja envolvente hacia atrás: chequeo propio).

Objetos (hijos del Empty `paloma`), sin esqueleto, como hoy en el código:
    paloma_cuerpo     cuerpo, cola y patas.
    pieza_cabeza      cabeza, pico y cuello. Origen en la base del cuello (0; 0,122; 0,045):
                      girando en X (positivo = baja la cabeza) picotea. El cuello entra en el
                      cuerpo, así no se abre un hueco al girar.
    pieza_ala_izq     ala izquierda de la paloma (+X), origen en el hombro (+0,040; 0,125; 0,038).
    pieza_ala_der     ala derecha (−X), origen en (−0,040; 0,125; 0,038).
                      Plegadas a lo largo del cuerpo. Para volar: abrirlas girando en Y
                      (izq −80°, der +80°: la punta va hacia el costado) y aletear girando en Z
                      en ejes del cuerpo (después de abrir; ver el informe).
Sin colisión (hoy tampoco tiene).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _animales as an  # noqa: E402
import comun  # noqa: E402
from _animales import V  # noqa: E402

ID = "paloma"
PRESUPUESTO = 300  # lista de modelos
CUERPO, ALA, OSCURO, PATA = range(4)

# Cortes del cuerpo (planos z = cte), de adelante (pecho) hacia atrás (punta de la cola):
# (z, centro y, medio alto arriba, medio alto abajo, medio ancho)
CORTES = [
    (0.072, 0.112, 0.036, 0.034, 0.036),
    (0.048, 0.100, 0.050, 0.054, 0.052),
    (0.008, 0.091, 0.047, 0.050, 0.058),
    (-0.035, 0.088, 0.038, 0.036, 0.048),
    (-0.072, 0.086, 0.022, 0.018, 0.034),
    (-0.100, 0.082, 0.010, 0.007, 0.032),
    (-0.172, 0.063, 0.005, 0.004, 0.045),
]
PECHO = (0.0, 0.118, 0.090)        # punta del abanico de adelante del cuerpo
CUELLO = (0.0, 0.122, 0.045)       # pivote de pieza_cabeza
HOMBRO = (0.040, 0.125, 0.038)     # pivote de pieza_ala_izq (der: x negativa)
PATAS_X = 0.017


def corte_en(z):
    """Interpola el corte del cuerpo en z."""
    for a, b in zip(CORTES, CORTES[1:]):
        if b[0] <= z <= a[0]:
            t = (a[0] - z) / (a[0] - b[0])
            return tuple(x + (y - x) * t for x, y in zip(a, b))
    return CORTES[0] if z > CORTES[0][0] else CORTES[-1]


def superficie(z, ang, afuera=0.0):
    """Punto de la elipse del cuerpo en z, a `ang` grados del lomo (0 = arriba, 90 = costado,
    del lado +X), corrido `afuera` metros hacia afuera."""
    _, cy, up, dn, rx = corte_en(z)
    t = math.radians(ang)
    h = up if math.cos(t) >= 0 else dn
    x, y = rx * math.sin(t), h * math.cos(t)
    n = V(math.sin(t) / rx, math.cos(t) / h, 0).normalized()
    return V(x, cy + y, z) + n * afuera


def cuerpo(mats):
    bm = bmesh.new()
    anillos = [an.anillo((0, cy, z), (0, 0, 1), rx, up, lados=8, abajo=dn, corrido=0.25)
               for z, cy, up, dn, rx in CORTES]
    bandas = [CUERPO] * (len(CORTES) - 2) + [OSCURO]   # franja oscura en la punta de la cola
    an.lofteo(bm, anillos, bandas, punta_ini=PECHO)
    # Patas: tarso de 4 lados (8 mm) del vientre al tobillo y pie chato con 3 dedos adelante
    # y uno atrás (una sola pieza en abanico).
    for s in (-1, 1):
        x = s * PATAS_X
        an.tubo(bm, [(x, 0.052, -0.001), (x * 1.2, 0.010, -0.003)], [0.0042, 0.0038], 4, mats=PATA,
                fase=math.pi / 4)
        pie(bm, x * 1.2, s)
    return an.terminar(f"{ID}_cuerpo", bm, mats, angulo=42)


def pie(bm, x, s):
    """Pie chato (alto 8 mm) en el piso: palma y 4 dedos (3 adelante abiertos, 1 atrás)."""
    alto = 0.008
    puntas = [(x + s * 0.020, 0.021), (x + s * 0.004, 0.027), (x - s * 0.012, 0.019),
              (x - s * 0.004, -0.027)]
    centro = (x, -0.003)
    # Contorno: punta, entre-dedo, punta, ... alrededor del centro (en el plano XZ).
    contorno = []
    angs = [math.atan2(pz - centro[1], px - centro[0]) for px, pz in puntas]
    orden = sorted(range(4), key=lambda i: angs[i])
    for j, i in enumerate(orden):
        contorno.append(puntas[i])
        a0, a1 = angs[i], angs[orden[(j + 1) % 4]]
        if a1 <= a0:
            a1 += 2 * math.pi
        am = (a0 + a1) / 2
        contorno.append((centro[0] + 0.006 * math.cos(am), centro[1] + 0.006 * math.sin(am)))
    abajo = [bm.verts.new(an.g2b((px, 0.0, pz))) for px, pz in contorno]
    arriba = bm.verts.new(an.g2b((centro[0], alto, centro[1])))
    n = len(contorno)
    previas = set(bm.faces)
    for k in range(n):
        bm.faces.new((abajo[k], abajo[(k + 1) % n], arriba))
    bm.faces.new(list(reversed(abajo)))
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = PATA
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)


def cabeza(mats):
    bm = bmesh.new()
    # Cuello grueso (anillos horizontales), desde adentro del cuerpo hasta la cabeza.
    cuello = [
        an.anillo((0, 0.098, 0.040), (0, 1, 0), 0.036, 0.036, 6, arriba=(0, 0, 1)),
        an.anillo((0, 0.135, 0.054), (0, 1, 0), 0.030, 0.032, 6, arriba=(0, 0, 1)),
        an.anillo((0, 0.158, 0.064), (0, 1, 0), 0.021, 0.023, 6, arriba=(0, 0, 1)),
        an.anillo((0, 0.170, 0.070), (0, 1, 0), 0.015, 0.016, 6, arriba=(0, 0, 1)),
    ]
    an.lofteo(bm, cuello, OSCURO)
    # Cabeza chica y redonda (cortes z = cte); el abanico de adelante es el pico (cera clara).
    cab = [
        an.anillo((0, 0.172, 0.058), (0, 0, 1), 0.012, 0.012, 6, fase=math.pi / 6),
        an.anillo((0, 0.175, 0.068), (0, 0, 1), 0.018, 0.017, 6, fase=math.pi / 6),
        an.anillo((0, 0.175, 0.084), (0, 0, 1), 0.018, 0.016, 6, fase=math.pi / 6),
        an.anillo((0, 0.170, 0.097), (0, 0, 1), 0.010, 0.009, 6, fase=math.pi / 6),
    ]
    an.lofteo(bm, cab, OSCURO, punta_ini=(0, 0.174, 0.049), punta_fin=(0, 0.164, 0.116), mat_fin=ALA)
    return an.terminar("pieza_cabeza", bm, mats, origen=CUELLO, angulo=45)


def ala(mats, s):
    """Ala plegada sobre el costado s (+1 = izquierda de la paloma, +X). Corte triangular:
    borde de arriba apoyado en el cuerpo, panza hacia afuera, borde de abajo apoyado."""
    bm = bmesh.new()
    # (z, ángulo del borde de arriba, ángulo del borde de abajo, grosor)
    estaciones = [(0.048, 45, 95, 0.003), (0.010, 32, 102, 0.009), (-0.030, 22, 98, 0.009),
                  (-0.075, 12, 78, 0.006)]
    anillos = []
    for z, a_arr, a_ab, g in estaciones:
        medio = (a_arr + a_ab) / 2
        pts = [superficie(z, a_arr, -0.003), superficie(z, medio, g), superficie(z, a_ab, -0.003)]
        anillos.append([V(p.x * s, p.y, p.z) for p in pts])
    punta = V(0.010 * s, 0.094, -0.142)
    bandas = [ALA, OSCURO, ALA]                    # franja oscura a mitad del ala
    an.lofteo(bm, anillos, bandas, punta_fin=punta, mat_fin=OSCURO)
    nombre = "pieza_ala_izq" if s > 0 else "pieza_ala_der"
    return an.terminar(nombre, bm, mats, origen=(HOMBRO[0] * s, HOMBRO[1], HOMBRO[2]), angulo=45)


def construir():
    mats = comun.cargar_materiales("M_Vereda", "M_Piedra", "M_MetalOscuro", "M_Terracota")
    c = cuerpo(mats)
    cab = cabeza(mats)
    alas = [ala(mats, 1), ala(mats, -1)]
    r = an.raiz(ID, [c, cab] + alas)
    return {"raiz": r, "cuerpo": c, "cabeza": cab, "alas": alas}


def visibles(m):
    return [m["cuerpo"], m["cabeza"]] + m["alas"]


def revisar(m):
    mn, mx = an.limites(visibles(m))
    d = mx - mn
    medidas = (round(d.x, 3), round(d.y, 3), round(d.z, 3))
    res = comun.revisar(visibles(m), PRESUPUESTO, medidas, origen="base")
    res = an.reemplazar(res, "Medidas", abs(d.x - 0.12) < 0.006 and abs(d.y - 0.19) < 0.006
                        and abs(d.z - 0.29) < 0.006,
                        "Medidas %.3f × %.3f × %.3f m (≈ 0,12 × 0,19 × 0,29: paloma bravía; "
                        "la de hoy en el juego, 0,14 × 0,215 × 0,35)" % (d.x, d.y, d.z))
    ok, texto = an.chequeo_patas([m["cuerpo"]])
    res = an.reemplazar(res, "Origen", ok, texto)
    res.insert(1, an.chequeo_piezas([
        (m["cabeza"], CUELLO, "pieza_cabeza en la base del cuello"),
        (m["alas"][0], HOMBRO, "pieza_ala_izq en el hombro (+X)"),
        (m["alas"][1], (-HOMBRO[0], HOMBRO[1], HOMBRO[2]), "pieza_ala_der en el hombro (−X)"),
    ]))
    return res


def pose(m, picoteo=0.0, apertura=0.0, aleteo=0.0):
    """Pone una pose para las fotos (grados, en ejes de Godot; X de Godot = X de Blender,
    Y de Godot = Z de Blender, Z de Godot = −Y de Blender)."""
    from mathutils import Euler, Matrix

    def hacer():
        m["cabeza"].rotation_euler = (math.radians(picoteo), 0, 0)
        for o, s in zip(m["alas"], (1, -1)):
            # Primero abrir (Y de Godot), después aletear (Z de Godot, en ejes del cuerpo).
            abrir = Matrix.Rotation(math.radians(-apertura * s), 3, "Z")
            batir = Matrix.Rotation(math.radians(-aleteo * s), 3, "Y")   # Z Godot = −Y Blender
            o.rotation_euler = (batir @ abrir).to_euler()
        bpy.context.view_layer.update()
    return hacer


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    an.guardar_y_exportar(ID, [m["raiz"]] + visibles(m))
    if "--sin-hoja" not in sys.argv:
        v = visibles(m)
        quieta = pose(m)
        an.hoja(ID, "paloma · 0,12 × 0,19 × 0,29 m · picotea y sale volando (SPEC-013)", [
            ("Costado (silueta) · día", v, "costado", "dia", quieta),
            ("Frente · día", v, "frente", "dia", quieta),
            ("3/4 · día", v, "tres_cuartos", "dia", quieta),
            ("3/4 · atardecer", v, "tres_cuartos", "atardecer", quieta),
            ("Picoteando: pieza_cabeza girada 60° en X", v, "tres_cuartos", "dia", pose(m, picoteo=60)),
            ("Volando: alas abiertas 80° y batidas 25°", v, "tres_cuartos_atras", "dia",
             pose(m, apertura=80, aleteo=25)),
            ("Arriba · día", v, "arriba", "dia", quieta),
            ("Con la persona de 1,75 m · día", v + ["persona"], "tres_cuartos", "dia", quieta),
        ], revision, persona_en=(0.45, 0.0, -0.25))
        pose(m)()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
