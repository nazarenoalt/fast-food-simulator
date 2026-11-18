"""Modelo: accesorios para variar las personas (id `accesorios_persona`).

Genera:
    arte/fuentes/personajes/accesorios_persona.blend
    godot/modelos/personajes/accesorios_persona.glb
    docs/arte/revisiones/accesorios_persona.jpg

Uso:
    python tools/blender/modelos/accesorios_persona.py [--sin-hoja]

Nueve accesorios, cada uno un objeto `acc_<nombre>` (≤ 300 tris) con el origen en su punto de
enganche, sin giro ni escala (como pelos_set.glb con los peinados):

    objeto                enganche        superficies (0 = color principal que el juego puede cambiar)
    acc_gorra             punto_pelo      0 copa y visera · 1 abajo de la visera y botón
    acc_gorro_lana        punto_pelo      0 gorro y doblez · 1 pompón
    acc_anteojos_sol      punto_pelo      0 armazón y cristales oscuros opacos (no se cambia)
    acc_anteojos_lectura  punto_pelo      0 armazón (sin cristales: no hay transparencias)
    acc_mochila           punto_espalda*  0 cuerpo · 1 tiras y bolsillo
    acc_bolso_cruzado     punto_pecho*    0 bolso y tapa · 1 correa y broche
    acc_bolsa_mandados    punto_mano_d    0 bolsa y manijas · 1 pan · 2 verdura
    acc_termo             punto_mano_i*   0 cuerpo · 1 tapón, pico y manija
    acc_mate              punto_mano_d    0 calabaza · 1 virola y bombilla · 2 yerba

Puntos de enganche (* = todavía no están en las personas; ver propuesta en el informe):
    punto_pelo     (ya existe) hijo del hueso Head, en la base del cráneo, con la escala de la
                   cabeza. Los accesorios de cabeza se arman sobre la cabeza de escala 1 y van
                   como hijos con transformación identidad: calzan en las 4 variantes.
    punto_mano_d   (ya existe) hijo de RightHand, en la palma, alineado con el mundo en reposo.
    punto_mano_i   hijo de LeftHand: el espejo de punto_mano_d (x → −x), alineado con el mundo
                   en reposo. Los objetos de mano son simétricos en x: sirven en cualquier mano.
    punto_espalda  hijo de UpperChest, en la cabeza del hueso, derecho como punto_pelo (sigue la
                   postura de la persona mayor), con escala k = cuerpo de la variante respecto
                   del adulto A: k = (altura − 0,235 × cabeza) / 1,515.
    punto_pecho    ídem, hijo de Chest, pero con escala (k × ancho × cintura, k, k): así la
                   correa pasa entre el brazo y la cintura en las 4 variantes.
En Godot, sin tocar las personas: BoneAttachment3D del hueso y un Node3D hijo con esa escala
(UpperChest/Chest) — el reposo de esos huesos en el .glb es la identidad salvo la postura —,
o para punto_mano_i un Node3D en la posición de punto_mano_d con x cambiada de signo.

Uso en las animaciones: todos se revisan en quieto, caminar y sentado. Sentado, los de mano
(bolsa, termo, mate) van apoyados en el banco. La bolsa y el termo no son para el chico (le
llegan al piso). Con gorra o gorro, los peinados colita y rodete se cambian por largo y rulos por
corto (la cola, el rodete y los rulos atravesarían la tela). El mate va derecho con la mano
colgando; en `comer` la mano gira ~130° entre "adelante" y "a la boca" (pensado para el pancho):
para tomar mate haría falta una animación propia.

Cómo se ajustan: los de cabeza se calculan contra la cabeza (con orejas) y la unión de los
peinados con los que se pueden usar (rayos desde el centro de la cabeza); la mochila y el bolso
contra la envolvente del torso de las 4 variantes en reposo, quieto, caminar y sentado (rayos
contra la malla deformada, en el espacio del punto de enganche y dividido por k). La revisión
pone todos los accesorios en las 4 variantes y en varias poses de cada animación y mide si algún
vértice del accesorio queda adentro del cuerpo o del pelo, o al revés (pieza por pieza, por
paridad de rayos).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import _persona  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
import persona_adulto_a  # noqa: E402
import persona_adulto_b  # noqa: E402
import persona_chico  # noqa: E402
import persona_mayor  # noqa: E402

ID = "accesorios_persona"
FAMILIA = _persona.FAMILIA
PRESUPUESTO = 300            # por accesorio (lista de modelos)
V = Vector
VARIANTES = [("persona_adulto_a", persona_adulto_a.PARAMETROS), ("persona_adulto_b", persona_adulto_b.PARAMETROS),
             ("persona_mayor", persona_mayor.PARAMETROS), ("persona_chico", persona_chico.PARAMETROS)]
CORTO = {"persona_adulto_a": "adulto A", "persona_adulto_b": "adulto B", "persona_mayor": "mayor",
         "persona_chico": "chico"}
CENTRO = V((0, 0.004, 0.118))     # centro de la cabeza (desde el mentón), el mismo de _persona.pelo
NUCA = _persona.NUCA_REL          # punto_pelo respecto del mentón (cabeza de escala 1)
TOL = 0.002                       # cuánto puede meterse algo adentro de otra cosa (m)

# nombre: enganche, materiales por superficie, qué es cada superficie, índice del color principal.
ACC = {
    "gorra": dict(punto="punto_pelo", mats=["M_AzulAcento", "M_TelaGris"],
                  sup=["copa y visera", "abajo de la visera y botón"], principal=0),
    "gorro_lana": dict(punto="punto_pelo", mats=["M_TelaBordo", "M_BlancoCrema"],
                       sup=["gorro y doblez", "pompón"], principal=0),
    "anteojos_sol": dict(punto="punto_pelo", mats=["M_PlasticoNegro"],
                         sup=["armazón y cristales oscuros"], principal=None),
    "anteojos_lectura": dict(punto="punto_pelo", mats=["M_PlasticoNegro"], sup=["armazón"], principal=0),
    "mochila": dict(punto="punto_espalda", mats=["M_TelaVerde", "M_PlasticoNegro"],
                    sup=["cuerpo", "tiras y bolsillo"], principal=0),
    "bolso_cruzado": dict(punto="punto_pecho", mats=["M_TelaBordo", "M_Tronco"],
                          sup=["bolso y tapa", "correa y broche"], principal=0),
    "bolsa_mandados": dict(punto="punto_mano_d", mats=["M_BlancoCrema", "M_PanCorteza", "M_Lechuga"],
                           sup=["bolsa y manijas", "pan", "verdura"], principal=0, sin=["persona_chico"]),
    "termo": dict(punto="punto_mano_i", mats=["M_Acero", "M_PlasticoNegro"],
                  sup=["cuerpo", "tapón, pico y manija"], principal=0, sin=["persona_chico"]),
    "mate": dict(punto="punto_mano_d", mats=["M_Madera", "M_Acero", "M_Chimichurri"],
                 sup=["calabaza", "virola y bombilla", "yerba"], principal=0),
}
DE_MANO = {"bolsa_mandados", "termo", "mate"}
HUESO_PUNTO = {"punto_espalda": "UpperChest", "punto_pecho": "Chest"}


# ── Malla ──────────────────────────────────────────────────────────────

class Pieza:
    """bmesh en ejes de Blender (la persona mira a −Y; su izquierda es +X)."""

    def __init__(self):
        self.bm = bmesh.new()

    def loft(self, anillos, mats, ini=None, fin=None, mat_tapas=None):
        """anillos: [[Vector]] (mismo n). mats: material por banda (lista o entero).
        ini/fin: None (abierto), "plana" o un punto (abanico)."""
        bm = self.bm
        n = len(anillos[0])
        mat = (lambda b: mats) if isinstance(mats, int) else (lambda b: mats[b])
        vs = [[bm.verts.new(p) for p in a] for a in anillos]
        caras = []
        for b, (a1, a2) in enumerate(zip(vs, vs[1:])):
            for k in range(n):
                f = bm.faces.new((a1[k], a1[(k + 1) % n], a2[(k + 1) % n], a2[k]))
                f.material_index = mat(b)
                caras.append(f)
        for tapa, fila, mt in ((ini, vs[0], mat(0)), (fin, vs[-1], mat(len(vs) - 2))):
            mt = mat_tapas if mat_tapas is not None else mt
            if tapa is None:
                continue
            if isinstance(tapa, str):
                f = bm.faces.new(fila)
                f.material_index = mt
                caras.append(f)
            else:
                c = bm.verts.new(tapa)
                for k in range(n):
                    f = bm.faces.new((fila[k], fila[(k + 1) % n], c))
                    f.material_index = mt
                    caras.append(f)
        # Normales hacia afuera según el volumen con signo de la pieza cerrada.
        vol = 0.0
        for f in caras:
            v = [x.co for x in f.verts]
            for i in range(1, len(v) - 1):
                vol += v[0].dot(v[i].cross(v[i + 1])) / 6
        if vol < 0:
            for f in caras:
                f.normal_flip()
        return caras

    def cinta(self, pts, normales, ancho, grosor, mat):
        """Tira de sección rectangular por una polilínea; `normales` = hacia afuera (grosor)."""
        anillos = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            n = V(normales[i])
            n = (n - t * n.dot(t)).normalized()
            b = t.cross(n).normalized()
            anillos.append([p + b * s1 * ancho / 2 + n * s2 * grosor / 2
                            for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        return self.loft(anillos, mat, "plana", "plana")

    def tubo(self, pts, radio, lados, mat, ref=V((1, 0, 0)), radios=None):
        """Tubo redondo por una polilínea (marco que se transporta, sin retorcerse)."""
        anillos = []
        u = None
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            u = (ref if u is None else u)
            u = (u - t * u.dot(t)).normalized()
            w = t.cross(u)
            r = radios[i] if radios else radio
            anillos.append([p + (u * math.cos(a) + w * math.sin(a)) * r
                            for a in (math.pi / lados + 2 * math.pi * k / lados for k in range(lados))])
        return self.loft(anillos, mat, "plana", "plana")

    def esfera(self, centro, radio, lados, mat, escala=(1, 1, 1)):
        bm = self.bm
        previas = set(bm.faces)
        res = bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=lados // 2, radius=radio)
        bmesh.ops.scale(bm, vec=V(escala), verts=res["verts"])
        bmesh.ops.translate(bm, vec=centro, verts=res["verts"])
        for f in bm.faces:
            if f not in previas:
                f.material_index = mat

    def terminar(self, nombre, materiales, sombreado="duro", mover=V()):
        if mover.length:
            bmesh.ops.translate(self.bm, vec=mover, verts=self.bm.verts)
        return piezas.terminar(f"acc_{nombre}", self.bm, materiales, sombreado)


def anillo_rect(cx, cy, z, hx, hy, ch, giro=0.0):
    """Rectángulo de 8 puntos con las esquinas ochavadas (ch), en el plano horizontal z."""
    pts = [(hx, -hy + ch), (hx, hy - ch), (hx - ch, hy), (-hx + ch, hy), (-hx, hy - ch), (-hx, -hy + ch),
           (-hx + ch, -hy), (hx - ch, -hy)]
    c, s = math.cos(giro), math.sin(giro)
    return [V((cx + x * c - y * s, cy + x * s + y * c, z)) for x, y in pts]


# ── Cabeza y peinados (para ajustar los accesorios de cabeza) ──────────

def malla_cabeza():
    """Cabeza de escala 1 con orejas (desde el mentón): verts y polígonos."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in a] for a in _persona.anillos_cabeza(1.0, V())]
    n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    for punta, fila in ((V((0, -0.070, -0.004)), vs[0]), (V((0, 0.006, 0.235)), vs[-1])):
        c = bm.verts.new(punta)
        for k in range(n):
            bm.faces.new((fila[k], fila[(k + 1) % n], c))
    for lado in (1, -1):       # orejas, como _persona.cabeza()
        c = V((lado * 0.074, 0.008, 0.105))
        d = V((lado, 0.25, 0)).normalized()
        a1 = _persona.anillo_eje(c, d, 0.022, 0.013, 6, ref=_persona.ARRIBA)
        a2 = _persona.anillo_eje(c + d * 0.011, d, 0.019, 0.011, 6, ref=_persona.ARRIBA)
        f1 = [bm.verts.new(p) for p in a1]
        f2 = [bm.verts.new(p) for p in a2]
        for k in range(6):
            bm.faces.new((f1[k], f1[(k + 1) % 6], f2[(k + 1) % 6], f2[k]))
        bm.faces.new(f1)
        bm.faces.new(list(reversed(f2)))
    bm.verts.index_update()
    verts = [v.co.copy() for v in bm.verts]
    polys = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, polys


def mallas_pelo():
    """{estilo: [(verts, polys) por pieza]} en coordenadas del mentón."""
    m = comun.cargar_materiales("M_PeloNegro")[0]
    res = {}
    for estilo in _persona.ESTILOS_PELO:
        o = _persona.pelo(estilo, m, nombre=f"_tmp_{estilo}")
        res[estilo] = componentes(o, [v.co + NUCA for v in o.data.vertices])
        bpy.data.objects.remove(o)
    return res


def componentes(obj, verts):
    """Piezas sueltas de una malla: [(verts, polys)] con índices locales."""
    me = obj.data
    padre = list(range(len(me.vertices)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    for p in me.polygons:
        vs = list(p.vertices)
        for v in vs[1:]:
            a, b = raiz(vs[0]), raiz(v)
            if a != b:
                padre[a] = b
    grupos = {}
    for p in me.polygons:
        grupos.setdefault(raiz(p.vertices[0]), []).append(list(p.vertices))
    out = []
    for polys in grupos.values():
        idx = sorted({i for p in polys for i in p})
        loc = {i: k for k, i in enumerate(idx)}
        out.append(([V(verts[i]) for i in idx], [[loc[i] for i in p] for p in polys], idx))
    return [(v, p) for v, p, _ in out]


def bvh(verts, polys):
    return BVHTree.FromPolygons([V(v) for v in verts], polys, all_triangles=False)


def distancia_afuera(bvhs, origen, d, lejos=0.6):
    """Primer choque viniendo desde lejos por d hacia el origen: distancia al origen (la
    superficie más de afuera entre todas las mallas), o None."""
    mejor = None
    for b in bvhs:
        hit = b.ray_cast(origen + d * lejos, -d, lejos)
        if hit[0] is not None:
            r = (hit[0] - origen).dot(d)
            mejor = r if mejor is None else max(mejor, r)
    return mejor


def direccion(phi, a):
    """Desde arriba (phi = 0) hacia abajo; a = 0 adelante (−Y), π/2 a la izquierda (+X)."""
    return V((math.sin(phi) * math.sin(a), -math.sin(phi) * math.cos(a), math.cos(phi)))


class EnvCabeza:
    """Radio (desde CENTRO) de la cabeza y de los peinados con los que se usa un gorro."""

    def __init__(self, cabeza, pelos, estilos):
        self.cab = bvh(*cabeza)
        self.todos = [self.cab]
        for e in estilos:
            piezas_ = pelos[e]
            if e in ("colita", "rodete"):      # solo el casco: la cola y el rodete quedan afuera
                piezas_ = [max(piezas_, key=lambda c: len(c[0]))]
            self.todos += [bvh(v, p) for v, p in piezas_]

    def radio(self, phi, a, cono=0.12, tope=0.06):
        """Máximo en un conito alrededor de la dirección (para que entre vértices no asome)."""
        r = 0.0
        for dp in (-cono, 0, cono):
            for da in (-cono, 0, cono):
                d = direccion(max(0.0, phi + dp), a + da)
                rc = distancia_afuera([self.cab], CENTRO, d) or 0.0
                rt = distancia_afuera(self.todos, CENTRO, d) or rc
                r = max(r, min(rt, rc + tope))
        return r


def suavizar_circular(vals):
    n = len(vals)
    return [max(vals[i], (vals[i - 1] + vals[(i + 1) % n]) / 2) for i in range(n)]


def limite_por_azimut(frente, lados, atras):
    def lim(a):
        f = (math.cos(a) + 1) / 2
        if f > 0.5:
            t = (f - 0.5) * 2
            return lados * (1 - t) + frente * t
        t = (0.5 - f) * 2
        return lados * (1 - t) + atras * t
    return lim


def cascara(p, env, lim, filas_ext, filas_int, NA, margen, grosor, mat, extra=lambda f, a: 0.0,
            capa=lambda f, a: 0.0):
    """Gorro como cáscara cerrada: superficie de afuera (filas_ext, fracciones del límite, de
    arriba hacia el borde), borde y superficie de adentro (filas_int, del borde hacia arriba).
    extra(f, a): cuánto se levanta todo (forma del gorro); capa(f, a): grosor de más afuera."""
    radios = {}

    def r_base(f, i):
        if (f, i) not in radios:
            a = 2 * math.pi * i / NA
            radios[(f, i)] = env.radio(lim(a) * f, a, cono=0.2)
        return radios[(f, i)]

    def anillo(f, afuera, capa_f=None):
        rs = suavizar_circular([r_base(f, i) for i in range(NA)])
        pts = []
        for i in range(NA):
            a = 2 * math.pi * i / NA
            r = rs[i] + margen + extra(f, a) + (grosor + (capa(f, a) if capa_f is None else capa_f(f, a))
                                                 if afuera else 0.0)
            pts.append(CENTRO + direccion(lim(a) * f, a) * r)
        return pts
    ext = []
    for f in filas_ext:
        if isinstance(f, tuple):          # (fracción, sin capa): escalón (doblez del gorro)
            ext.append(anillo(f[0], True, capa_f=lambda f_, a: 0.0))
        else:
            ext.append(anillo(f, True))
    inn = [anillo(f, False) for f in filas_int]
    r_arriba = env.radio(0.0, 0.0, cono=0.2)
    apex_ext = CENTRO + V((0, 0, r_arriba + margen + grosor + extra(0.0, 0.0)))
    apex_int = CENTRO + V((0, 0, r_arriba + margen + extra(0.0, 0.0)))
    p.loft(ext + inn, mat, ini=apex_ext, fin=apex_int)
    return ext, apex_ext


# ── Accesorios de cabeza (coordenadas desde el mentón; al final se pasan a punto_pelo) ──

def gorra(env, mats):
    p = Pieza()
    NA = 12
    lim = limite_por_azimut(1.12, 1.45, 1.72)
    alto_frente = lambda f, a: 0.010 * max(0.0, math.cos(a)) * (1 - f) ** 0.7 * min(1.0, f * 4)  # noqa: E731
    ext, apex = cascara(p, env, lim, [0.3, 0.6, 0.85, 1.0], [1.0, 0.66, 0.33], NA, 0.0045, 0.006, 0, extra=alto_frente)
    # Visera: sale del borde de adelante, horizontal y apenas caída, curvada de lado a lado.
    cols = 7
    a_max = math.radians(64)
    raiz, mitad, punta = [], [], []
    for k in range(cols):
        a = -a_max + 2 * a_max * k / (cols - 1)
        phi = lim(a)
        r = env.radio(phi, a, cono=0.2) + 0.0045 + 0.006 + alto_frente(1.0, a)
        base = CENTRO + direccion(phi, a) * r + V((0, 0, 0.002))
        afuera = V((math.sin(a), -math.cos(a), 0))
        u = abs(a) / a_max
        largo = 0.074 * (1 - u ** 2.2) ** 0.6 + 0.010
        caida = math.tan(math.radians(12))
        arco = 0.012 * u ** 2
        raiz.append(base - afuera * 0.010)
        mitad.append(base + afuera * largo * 0.5 + V((0, 0, -largo * 0.5 * caida - arco * 0.4)))
        punta.append(base + afuera * largo + V((0, 0, -largo * caida - arco)))
    e = 0.005
    arriba = [raiz, mitad, punta]
    bm = p.bm
    va = [[bm.verts.new(q) for q in fila] for fila in arriba]
    vb = [[bm.verts.new(q - V((0, 0, e))) for q in fila] for fila in arriba]
    caras = []
    for j in range(2):
        for k in range(cols - 1):
            f = bm.faces.new((va[j][k], va[j][k + 1], va[j + 1][k + 1], va[j + 1][k]))
            f.material_index = 0
            g = bm.faces.new((vb[j][k], vb[j + 1][k], vb[j + 1][k + 1], vb[j][k + 1]))
            g.material_index = 1
            caras += [f, g]
    for k in range(cols - 1):       # borde de la punta y de la raíz
        caras.append(bm.faces.new((va[2][k], va[2][k + 1], vb[2][k + 1], vb[2][k])))
        caras.append(bm.faces.new((va[0][k + 1], va[0][k], vb[0][k], vb[0][k + 1])))
    for k, sentido in ((0, 1), (cols - 1, -1)):
        for j in range(2):
            q = (va[j][k], va[j + 1][k], vb[j + 1][k], vb[j][k])
            caras.append(bm.faces.new(q if sentido > 0 else tuple(reversed(q))))
    for f in caras[4 * (cols - 1):]:
        f.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=caras)
    # Botón arriba.
    c = apex + V((0, 0, -0.002))
    p.loft([[c + V((0.009 * math.cos(t), 0.009 * math.sin(t), 0)) for t in (math.pi / 6 + k * math.pi / 3 for k in range(6))],
            [c + V((0.008 * math.cos(t), 0.008 * math.sin(t), 0.006)) for t in (math.pi / 6 + k * math.pi / 3 for k in range(6))]],
           1, "plana", "plana")
    return p.terminar("gorra", mats, mover=-NUCA)


def gorro_lana(env, mats):
    p = Pieza()
    NA = 12
    lim = limite_por_azimut(1.22, 1.80, 1.84)
    alto = lambda f, a: 0.016 * (1 - f) ** 1.5   # noqa: E731  (un poco suelto arriba)
    doblez = lambda f, a: 0.007 if f > 0.80 else 0.0   # noqa: E731
    ext, apex = cascara(p, env, lim, [0.18, 0.42, 0.64, (0.82,), 0.82, 1.0], [1.0, 0.66, 0.33], NA, 0.003, 0.007, 0,
                        extra=alto, capa=doblez)
    p.esfera(apex + V((0, 0.003, 0.016)), 0.030, 8, 1, escala=(1, 1, 0.85))
    return p.terminar("gorro_lana", mats, mover=-NUCA)


def _lente(cx, cz, ancho_arriba, ancho_abajo, alto, y, giro):
    """Contorno de 8 puntos de un cristal (en el plano XZ, girado para seguir la cara)."""
    a, b, h = ancho_arriba / 2, ancho_abajo / 2, alto / 2
    pts = [(-a, h * 0.85), (-a * 0.8, h), (a * 0.8, h), (a, h * 0.85), (b, -h * 0.55), (b * 0.75, -h),
           (-b * 0.75, -h), (-b, -h * 0.55)]
    c, s = math.cos(giro), math.sin(giro)
    return [V((cx + x * c, y + x * s, cz + z)) for x, z in pts]


def _patillas(p, inicio_z, inicio_x, mat):
    for lado in (1, -1):
        pts = [V((lado * inicio_x, -0.101, inicio_z)), V((lado * 0.080, -0.091, inicio_z + 0.002)),
               V((lado * 0.085, -0.040, 0.133)), V((lado * 0.085, 0.010, 0.135)), V((lado * 0.080, 0.030, 0.118))]
        nor = [V((0, 0, 1))] * len(pts)
        p.cinta(pts, nor, 0.0035, 0.006, mat)


def anteojos_sol(mats):
    p = Pieza()
    for lado in (1, -1):
        cx = lado * 0.034
        frente = _lente(cx, 0.118, 0.052, 0.044, 0.036, -0.106, lado * math.radians(10))
        atras = [q + V((0, 0.004, 0)) for q in frente]
        p.loft([frente, atras], 0, "plana", "plana")
    # Puente y patillas.
    p.cinta([V((-0.012, -0.1045, 0.127)), V((0, -0.1055, 0.128)), V((0.012, -0.1045, 0.127))],
            [V((0, 0, 1))] * 3, 0.005, 0.005, 0)
    _patillas(p, 0.129, 0.058, 0)
    return p.terminar("anteojos_sol", mats, mover=-NUCA)


def anteojos_lectura(mats):
    p = Pieza()
    for lado in (1, -1):
        cx = lado * 0.031
        giro = lado * math.radians(8)
        adentro = _lente(cx, 0.104, 0.042, 0.040, 0.021, -0.104, giro)
        afuera = _lente(cx, 0.104, 0.050, 0.048, 0.029, -0.104, giro)
        prof = V((0, 0.004, 0))
        p.loft([afuera, adentro, [q + prof for q in adentro], [q + prof for q in afuera]], 0, None, None)
        # El loft queda cerrado como anillo: se unen la última y la primera fila.
        bm = p.bm
        bm.verts.ensure_lookup_table()
        n = 8
        fila0 = list(bm.verts)[-4 * n:-3 * n]
        fila3 = list(bm.verts)[-n:]
        for k in range(n):
            bm.faces.new((fila3[k], fila3[(k + 1) % n], fila0[(k + 1) % n], fila0[k]))
    p.cinta([V((-0.010, -0.1015, 0.110)), V((0, -0.1030, 0.112)), V((0.010, -0.1015, 0.110))],
            [V((0, 0, 1))] * 3, 0.0035, 0.004, 0)
    _patillas(p, 0.112, 0.054, 0)
    bmesh.ops.recalc_face_normals(p.bm, faces=p.bm.faces)
    return p.terminar("anteojos_lectura", mats, mover=-NUCA)


# ── Mochila y bolso (espacio del punto, dividido por k) ───────────────

def mochila(env, mats):
    p = Pieza()
    xs = [0.15, 0.075, 0.0, -0.075, -0.15]
    filas = [(-0.25, 0.135, 0.10), (-0.225, 0.15, 0.13), (-0.06, 0.15, 0.15), (0.075, 0.145, 0.135),
             (0.125, 0.12, 0.09)]
    sep = 0.007
    anillos = []
    for z, hx, prof in filas:
        frente = []
        for x in xs:
            xx = x * hx / 0.15
            y = max(distancia_afuera(env, V((xx + dx, 0, z + dz)), V((0, 1, 0))) or 0.0
                    for dx in (-0.03, 0, 0.03) for dz in (-0.03, 0, 0.03))
            frente.append(V((xx, y + sep, z)))
        yf = max(q.y for q in frente)
        atras = [V((q.x * 0.94, yf + prof * f, z)) for q, f in zip(reversed(frente), (0.72, 0.95, 1.0, 0.95, 0.72))]
        anillos.append(frente + atras)
    top = anillos[-1]
    apex = sum(top, V()) / len(top) + V((0, 0, 0.022))
    p.loft(anillos, 0, ini="plana", fin=apex)
    # Bolsillo de adelante (en la cara de atrás de la mochila).
    yb = [max(q.y for q in a) for a in anillos]
    bol = []
    for z, yz in ((-0.205, (yb[1] + yb[2]) / 2 - 0.004), (-0.075, yb[2] - 0.004)):
        bol.append([V((-0.10, yz - 0.03, z)), V((-0.10, yz + 0.022, z)), V((-0.075, yz + 0.038, z)),
                    V((0.075, yz + 0.038, z)), V((0.10, yz + 0.022, z)), V((0.10, yz - 0.03, z))])
    p.loft(bol, 1, "plana", "plana")
    # Tiras: por arriba del hombro y hasta el pecho, siguiendo la envolvente.
    for lado in (1, -1):
        x = lado * 0.110
        C = V((x, 0.0, 0.03))
        pts, nor = [], []
        for th in (15, 45, 70, 90, 110, 135, 160, 182, 200):
            d = V((0, math.cos(math.radians(th)), math.sin(math.radians(th))))
            r = max(distancia_afuera(env, C + V((dx, 0, 0)), dd) or 0.0
                    for dx in (-0.019, 0, 0.019)
                    for dd in (d, V((0, math.cos(math.radians(th + 6)), math.sin(math.radians(th + 6)))),
                               V((0, math.cos(math.radians(th - 6)), math.sin(math.radians(th - 6))))))
            pts.append(C + d * (r + 0.004 + 0.004))
            nor.append(d)
        p.cinta(pts, nor, 0.040, 0.008, 1)
    return p.terminar("mochila", mats)


def bolso_cruzado(env, mats):
    p = Pieza()
    xl, xr = 0.05, -0.11
    sep = 0.006
    prof = 0.055
    anillos = []
    filas = [-0.158, -0.146, -0.023, -0.008]
    for z in filas:
        yb = min(-(distancia_afuera(env, V((x, 0, z + dz)), V((0, -1, 0))) or 0.0)
                 for x in (xl + 0.01, (xl + xr) / 2, xr - 0.01, xr + 0.03) for dz in (-0.02, 0, 0.02)) - sep
        ch = 0.012
        cx, hx = (xl + xr) / 2, (xl - xr) / 2
        anillos.append(anillo_rect(cx, yb - prof / 2, z, hx - (0.004 if z in (filas[0], filas[-1]) else 0),
                                   prof / 2 - (0.004 if z in (filas[0], filas[-1]) else 0), ch))
    p.loft(anillos, 0, "plana", "plana")
    # Tapa: placa delante, de arriba hasta un poco más abajo de la mitad.
    yf = [min(q.y for q in a) for a in anillos]
    tapa = []
    for z, y in ((-0.003, yf[3]), (-0.081, (yf[2] * 0.6 + yf[1] * 0.4))):
        tapa.append([V((xl + 0.003, y + 0.003, z)), V((xl + 0.003, y - 0.004, z)), V((xr - 0.003, y - 0.004, z)),
                     V((xr - 0.003, y + 0.003, z))])
    p.loft(tapa, 0, "plana", "plana")
    cxm = (xl + xr) / 2
    ym = tapa[1][1].y
    p.loft([anillo_rect(cxm, ym - 0.002, -0.083, 0.012, 0.004, 0.003),
            anillo_rect(cxm, ym - 0.002, -0.063, 0.012, 0.004, 0.003)], 1, "plana", "plana")
    # Correa: de la esquina izquierda del bolso, por el pecho, sobre el hombro izquierdo, por
    # la espalda en diagonal, alrededor del costado derecho y a la esquina derecha del bolso.
    guias = []        # (origen afuera, destino adentro) del rayo
    for x, z in ((0.045, 0.01), (0.065, 0.075), (0.085, 0.14), (0.103, 0.20)):
        guias.append((V((x, -0.6, z)), V((x, 0, z))))
    C = V((0.120, 0.0, 0.21))
    for th in (160, 130, 105, 80, 55, 25):
        d = V((0, math.cos(math.radians(th)), math.sin(math.radians(th))))
        guias.append((C + d * 0.6, C))
    for x, z in ((0.090, 0.15), (0.040, 0.09), (-0.020, 0.03), (-0.072, -0.025)):
        guias.append((V((x, 0.6, z)), V((x, 0, z))))
    A = V((0, 0, -0.050))
    for d in ((-0.55, 0.83), (-0.85, 0.52), (-1.0, 0.08), (-0.95, -0.32)):
        dd = V((d[0], d[1], 0)).normalized()
        guias.append((A + dd * 0.6, A))
    pts, nor = [V((xl - 0.010, yf[3] + prof * 0.5, -0.023))], [V((0, -1, 0))]
    for o, t in guias:
        d = (o - t).normalized()
        lado = d.cross(V((0, 0, 1))) if abs(d.z) < 0.9 else V((1, 0, 0))
        lado = lado.normalized() * 0.014
        r = max(distancia_afuera(env, t + e, d, (o - t).length) or 0.0 for e in (V(), lado, -lado))
        pts.append(t + d * (r + 0.004 + 0.003))
        nor.append(d)
    pts.append(V((xr + 0.010, yf[3] + prof * 0.5, -0.023)))
    nor.append(V((-0.3, -0.95, 0)))
    p.cinta(pts, nor, 0.030, 0.006, 1)
    return p.terminar("bolso_cruzado", mats)


# ── De mano (origen en la palma; la mano cuelga: dedos hacia −Z) ───────

def bolsa_mandados(mats):
    p = Pieza()
    filas = [(-0.48, 0.040, 0.130), (-0.465, 0.048, 0.140), (-0.32, 0.046, 0.148), (-0.20, 0.032, 0.150)]
    anillos = [anillo_rect(0, 0, z, hx, hy, 0.016) for z, hx, hy in filas]
    p.loft(anillos, 0, "plana", "plana")
    # Pan francés (flauta) asomando adelante, verdura atrás.
    d = V((0, -0.42, 1)).normalized()
    c = V((0.008, -0.075, -0.17))
    perfil = [(-0.16, 0.0), (-0.15, 0.016), (-0.12, 0.024), (0.12, 0.024), (0.15, 0.016)]
    an = [[c + d * t + q for q in (_persona.anillo_eje(V(), d, r, r * 0.9, 6, ref=V((1, 0, 0))))] for t, r in perfil[1:]]
    p.loft(an, 1, ini=c + d * -0.16, fin=c + d * 0.165)
    for lado, inc in ((1, 0.32), (-1, 0.42)):
        e = V((lado * 0.15, inc, 1)).normalized()
        base = V((lado * 0.012, 0.075, -0.24))
        perf = [(0.0, 0.010, 0.006), (0.09, 0.030, 0.008), (0.17, 0.024, 0.006)]
        an = []
        for t, ancho, gro in perf:
            q = base + e * t
            u = V((0, 1, 0)).cross(e).normalized() if abs(e.y) < 0.9 else V((1, 0, 0))
            w = e.cross(u).normalized()
            an.append([q + u * ancho, q + w * gro, q - u * ancho, q - w * gro])
        p.loft(an, 2, ini=base - e * 0.01, fin=base + e * 0.23)
    # Manijas: de cada lado de la boca de la bolsa hasta el puño.
    for lado in (1, -1):
        pts = [V((lado * 0.026, -0.10, -0.205)), V((lado * 0.022, -0.075, -0.13)), V((lado * 0.010, -0.032, -0.03)),
               V((lado * 0.010, 0.032, -0.03)), V((lado * 0.022, 0.075, -0.13)), V((lado * 0.026, 0.10, -0.205))]
        nor = [V((lado, 0, 0))] * len(pts)
        p.cinta(pts, nor, 0.022, 0.004, 0)
    return p.terminar("bolsa_mandados", mats)


def termo(mats):
    p = Pieza()
    L = 12
    k = 1 / math.cos(math.pi / L)    # radio medido en las caras planas (guía 3.2)

    def ring(z, r, lados=L):
        return [V((r * k * math.cos(math.pi / lados + 2 * math.pi * i / lados),
                   r * k * math.sin(math.pi / lados + 2 * math.pi * i / lados), z)) for i in range(lados)]
    p.loft([ring(-0.44, 0.042), ring(-0.432, 0.045), ring(-0.195, 0.045), ring(-0.175, 0.040)], 0, "plana", "plana")
    p.loft([ring(-0.182, 0.0425), ring(-0.130, 0.0405)], 1, "plana", "plana")
    # Pico cebador adelante, arriba del tapón.
    p.loft([[V((0, -0.022, -0.131)) + q for q in ring(0, 0.010, 6)],
            [V((0, -0.026, -0.112)) + q for q in ring(0, 0.008, 6)]], 1, "plana", "plana")
    # Manija arriba: arco de adelante hacia atrás que pasa por el puño.
    pts = [V((0.028, 0, -0.155)), V((0.034, 0, -0.105)), V((0.018, 0, -0.030)), V((-0.018, 0, -0.030)),
           V((-0.034, 0, -0.105)), V((-0.028, 0, -0.155))]
    pts = [V((0, q.x, q.z)) for q in pts]      # el arco va de adelante hacia atrás (eje Y)
    p.tubo(pts, 0.0055, 6, 1)
    return p.terminar("termo", mats)


def mate(mats):
    p = Pieza()
    L = 10
    perfil = [(0.000, 0.020), (0.008, 0.030), (0.030, 0.037), (0.055, 0.034), (0.074, 0.027), (0.082, 0.026)]
    c = V((0.0, -0.030, -0.135))

    def ring(z, r, lados=L, cx=0.0, cy=0.0):
        return [c + V((cx + r * math.cos(2 * math.pi * i / lados), cy + r * math.sin(2 * math.pi * i / lados), z))
                for i in range(lados)]
    p.loft([ring(z, r) for z, r in perfil], 0, ini=c + V((0, 0, -0.002)), fin="plana")
    # Virola de metal y yerba adentro.
    p.loft([ring(0.078, 0.0285), ring(0.090, 0.0285), ring(0.090, 0.0225), ring(0.082, 0.0225)], 1, None, None)
    bm = p.bm
    fila0 = list(bm.verts)[-4 * L:-3 * L]
    fila3 = list(bm.verts)[-L:]
    for kk in range(L):
        bm.faces.new((fila3[kk], fila3[(kk + 1) % L], fila0[(kk + 1) % L], fila0[kk]))
    p.loft([ring(0.080, 0.0235, 8), ring(0.087, 0.0235, 8)], 2, "plana", "plana")
    # Bombilla: sale de la yerba, inclinada, con la punta doblada.
    b0 = c + V((0.004, 0.006, 0.070))
    b1 = c + V((0.016, 0.022, 0.150))
    b2 = c + V((0.020, 0.030, 0.165))
    p.tubo([b0, b1, b2], 0.003, 6, 1)
    bmesh.ops.recalc_face_normals(p.bm, faces=p.bm.faces)
    return p.terminar("mate", mats)


# ── Personas y puntos de enganche ──────────────────────────────────────

def escala_punto(nombre, P, M):
    """Escala de punto_espalda (k) y de punto_pecho (k, con el ancho de la cintura en x: así
    la correa del bolso pasa entre el brazo y la cintura en todas las variantes)."""
    k = M["k"]
    if nombre == "punto_pecho":
        return (k * P.get("ancho", 1.0) * P.get("cintura", 1.0), k, k)
    return (k, k, k)


def poner_puntos(R):
    """Crea en la persona los puntos propuestos (punto_espalda, punto_pecho, punto_mano_i),
    con la misma receta que punto_pelo. Devuelve {nombre: objeto} con los 5 puntos."""
    arm, esq, M = R["arm"], R["esq"], R["M"]
    _persona.poner_pose(arm, _persona.Pose(esq))
    pts = {"punto_pelo": R["punto"], "punto_mano_d": R["mano"]}
    if R.get("extra"):  # las personas ya traen los puntos (_persona.puntos_extra)
        pts.update(R["extra"])
        bpy.context.view_layer.update()
        return pts
    for nombre, hueso in HUESO_PUNTO.items():
        e = bpy.data.objects.new(nombre, None)
        e.empty_display_size = 0.05
        bpy.context.scene.collection.objects.link(e)
        e.parent = arm
        e.parent_type = "BONE"
        e.parent_bone = hueso
        bpy.context.view_layer.update()
        base = esq.rot(hueso) @ Quaternion(V((1, 0, 0)), math.radians(90)).inverted()
        sx, sy, sz = escala_punto(nombre, R["P"], M)
        e.matrix_world = (Matrix.Translation(esq.rest[hueso].translation) @ base.to_matrix().to_4x4() @
                          Matrix.Diagonal((sx, sy, sz, 1.0)))
        pts[nombre] = e
    e = bpy.data.objects.new("punto_mano_i", None)
    e.empty_display_size = 0.04
    bpy.context.scene.collection.objects.link(e)
    e.parent = arm
    e.parent_type = "BONE"
    e.parent_bone = "LeftHand"
    bpy.context.view_layer.update()
    d = R["mano"].matrix_world.translation
    e.matrix_world = Matrix.Translation(V((-d.x, d.y, d.z)))
    pts["punto_mano_i"] = e
    bpy.context.view_layer.update()
    return pts


def construir_persona(id_, P):
    R = _persona.construir(id_, P)
    R["id"] = id_
    R["P"] = P
    R["puntos"] = poner_puntos(R)
    R["funs"] = {n: f for n, a, c, f in R["acciones"]}
    # Hueso dominante de cada vértice y piezas del cuerpo.
    cuerpo = R["cuerpo"]
    grupos = {g.index: g.name for g in cuerpo.vertex_groups}
    R["dominante"] = [grupos[max(v.groups, key=lambda g: g.weight).group] for v in cuerpo.data.vertices]
    return R


def poses_muestra(R):
    """(etiqueta, función t → Pose, lista de t) de las animaciones principales."""
    per = R["caminar"].T
    return [("quieto", R["funs"]["quieto"], [0.0, 1.0, 2.0, 3.0]),
            ("caminar", R["funs"]["caminar"], [per * i / 8 for i in range(8)]),
            ("sentado", R["funs"]["sentado"], [0.0, 1.5, 2.7, 4.5])]


def malla_mundo(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    mw = obj.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return vs


TORSO = {"Hips", "Spine", "Chest", "UpperChest", "Neck", "LeftShoulder", "RightShoulder"}


def envolventes(variantes):
    """BVH del torso (sin brazos, piernas ni cabeza) de cada variante y pose, en el espacio de
    punto_espalda y de punto_pecho (dividido por k)."""
    env = {"punto_espalda": [], "punto_pecho": []}
    for id_, P in variantes:
        R = construir_persona(id_, P)
        cuerpo = R["cuerpo"]
        dom = R["dominante"]
        polys = [list(p.vertices) for p in cuerpo.data.polygons if any(dom[i] in TORSO for i in p.vertices)]
        poses = [_persona.Pose(R["esq"])]
        for _, f, ts in poses_muestra(R):
            poses += [f(R["esq"], t) for t in ts]
        for pose in poses:
            _persona.poner_pose(R["arm"], pose)
            vs = malla_mundo(cuerpo)
            for nombre in env:
                inv = R["puntos"][nombre].matrix_world.inverted()
                env[nombre].append(bvh([inv @ v for v in vs], polys))
    return env


# ── Revisión ───────────────────────────────────────────────────────────

class Solidos:
    """Piezas cerradas (en el mundo) para preguntar si un punto está adentro."""

    def __init__(self, piezas_):
        self.p = []
        for vs, polys, nombre in piezas_:
            if not polys:
                continue
            mn = V(map(min, *vs))
            mx = V(map(max, *vs))
            self.p.append((bvh(vs, polys), mn, mx, nombre))

    def adentro(self, q, excluir=()):
        """Mayor profundidad a la que q está adentro de alguna pieza (0 si afuera)."""
        return self.adentro_donde(q, excluir)[0]

    def adentro_donde(self, q, excluir=()):
        peor, donde = 0.0, None
        d = V((0.123, 0.311, 0.942)).normalized()
        for b, mn, mx, nombre in self.p:
            if nombre in excluir:
                continue
            if not (mn.x - 1e-4 <= q.x <= mx.x + 1e-4 and mn.y - 1e-4 <= q.y <= mx.y + 1e-4 and
                    mn.z - 1e-4 <= q.z <= mx.z + 1e-4):
                continue
            cruces, o = 0, q.copy()
            for _ in range(40):
                hit = b.ray_cast(o, d)
                if hit[0] is None:
                    break
                cruces += 1
                o = hit[0] + d * 1e-6
            if cruces % 2 == 1:
                prof = b.find_nearest(q)[3]
                if prof > peor:
                    peor, donde = prof, nombre
        return peor, donde


def piezas_cuerpo(R, vs):
    """Piezas del cuerpo deformado, cada una con el nombre de su hueso dominante."""
    cuerpo = R["cuerpo"]
    dom = R["dominante"]
    me = cuerpo.data
    padre = list(range(len(me.vertices)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    for p in me.polygons:
        for v in p.vertices[1:]:
            a, b = raiz(p.vertices[0]), raiz(v)
            if a != b:
                padre[a] = b
    grupos = {}
    for p in me.polygons:
        grupos.setdefault(raiz(p.vertices[0]), []).append(list(p.vertices))
    out = []
    for polys in grupos.values():
        idx = sorted({i for p in polys for i in p})
        loc = {i: k for k, i in enumerate(idx)}
        cuenta = {}
        for i in idx:
            cuenta[dom[i]] = cuenta.get(dom[i], 0) + 1
        out.append(([vs[i] for i in idx], [[loc[i] for i in p] for p in polys], max(cuenta, key=cuenta.get)))
    return out


def poner_accesorios(R, objetos):
    """Copias de los accesorios como hijas de los puntos de la persona (identidad)."""
    copias = {}
    for o in objetos:
        nombre = o.name.removeprefix("acc_")
        c = o.copy()
        c.name = f"{o.name}·{R['id']}"
        bpy.context.scene.collection.objects.link(c)
        c.parent = R["puntos"][ACC[nombre]["punto"]]
        c.matrix_parent_inverse = Matrix()
        c.matrix_basis = Matrix()
        copias[nombre] = c
    bpy.context.view_layer.update()
    return copias


def chequeo_choques(R, copias):
    """{accesorio: [(pose, profundidad máx.)]} para las poses donde algo se mete > TOL."""
    malas = {n: [] for n in copias}
    muestras = []
    for etiqueta, f, ts in poses_muestra(R):
        muestras += [(f"{etiqueta} {t:.2f}s", etiqueta, f(R["esq"], t)) for t in ts]
    for etiqueta, tipo, pose in muestras:
        _persona.poner_pose(R["arm"], pose)
        vs = malla_mundo(R["cuerpo"])
        cuerpo = piezas_cuerpo(R, vs)
        pel = R["pelo"]
        pel_vs = [pel.matrix_world @ v.co for v in pel.data.vertices]
        solidos = Solidos(cuerpo + [(v, p, "pelo") for v, p in componentes(pel, pel_vs)])
        for nombre, c in copias.items():
            if R["id"] in ACC[nombre].get("sin", ()):
                continue           # no es para esta variante (al chico le arrastra por el piso)
            de_mano = nombre in DE_MANO
            if tipo == "sentado" and de_mano:
                continue           # sentado: la bolsa, el termo y el mate van apoyados en el banco
            excluir = set()
            if de_mano:
                excluir = {"RightHand"} if ACC[nombre]["punto"] == "punto_mano_d" else {"LeftHand"}
            if nombre.startswith("anteojos"):
                excluir = {"pelo"}      # las patillas pasan por debajo del pelo (como en la realidad)
            mw = c.matrix_world
            acc_vs = [mw @ v.co for v in c.data.vertices]
            peor, donde = max((solidos.adentro_donde(q, excluir) for q in acc_vs), key=lambda x: x[0])
            # Al revés: el cuerpo (y el pelo) adentro del accesorio.
            acc_sol = Solidos([(v, p, "acc") for v, p in componentes(c, acc_vs)])
            for v_, p_, nombre_p in solidos_lista(cuerpo, pel, pel_vs):
                if nombre_p in excluir:
                    continue
                for q in v_:
                    pr = acc_sol.adentro(q)
                    if pr > peor:
                        peor, donde = pr, nombre_p + " (adentro del acc.)"
            if peor > TOL:
                malas[nombre].append((f"{etiqueta} [{donde}]", peor))
    return malas


def solidos_lista(cuerpo, pel, pel_vs):
    return cuerpo + [(v, p, "pelo") for v, p in componentes(pel, pel_vs)]


def chequeo_pelos(objetos, pelos):
    """Peinados con gorra y gorro: cuánto pelo asoma atravesando el gorro (en el espacio del
    mentón, cabeza de escala 1). Devuelve {gorro: {estilo: profundidad máx.}}."""
    res = {}
    for o in objetos:
        nombre = o.name.removeprefix("acc_")
        if nombre not in ("gorra", "gorro_lana"):
            continue
        vs = [v.co + NUCA for v in o.data.vertices]
        comps = componentes(o, vs)
        sol = Solidos([(v, p, "acc") for v, p in comps])
        hat_bvh = [bvh(v, p) for v, p in comps]
        copa = bvh(*max(comps, key=lambda c: len(c[0])))
        res[nombre] = {}
        for estilo, piezas_ in pelos.items():
            peor = 0.0
            pel_sol = Solidos([(v, p, "pelo") for v, p in piezas_])
            for q in vs:                       # el gorro adentro del pelo
                peor = max(peor, pel_sol.adentro(q))
            for v_, p_ in piezas_:             # el pelo adentro de la tela, o afuera del gorro
                for q in v_:
                    peor = max(peor, sol.adentro(q))
                    d = q - CENTRO
                    r = d.length
                    d.normalize()
                    rg = distancia_afuera(hat_bvh, CENTRO, d)
                    if rg is None:
                        continue
                    # ¿La copa tapa esa dirección? Si el pelo queda más afuera, asoma.
                    hit = copa.ray_cast(CENTRO, d)
                    if hit[0] is not None and r > rg:
                        peor = max(peor, r - rg)
            res[nombre][estilo] = peor
    return res


def revisar(objetos):
    res = []
    tris = {o.name.removeprefix("acc_"): comun.contar_triangulos(o) for o in objetos}
    res.append((all(t <= PRESUPUESTO for t in tris.values()),
                "Triángulos por accesorio (máx. %d): " % PRESUPUESTO + ", ".join(f"{n} {t}" for n, t in tris.items())))
    limpio = all(o.rotation_euler.to_quaternion().angle < 1e-6 and all(abs(s - 1) < 1e-6 for s in o.scale)
                 and o.location.length < 1e-9 for o in objetos)
    res.append((limpio, "Todos con el origen en su punto de enganche (0, 0, 0), rotación 0 y escala 1"))
    validos = comun.paleta()
    ok_mat = True
    for o in objetos:
        nombres = [m.name for m in o.data.materials]
        usados = {p.material_index for p in o.data.polygons}
        ok_mat &= all(n in validos for n in nombres) and len(nombres) <= 4 and usados == set(range(len(nombres)))
    res.append((ok_mat, "Materiales de la paleta, máx. 4 por accesorio y todos se usan; sin transparencias"))
    malas = abiertas = sueltos = dobles = 0
    for o in objetos:
        a, b = _persona._componentes_bien(o)
        malas += a
        abiertas += b
        bm = bmesh.new()
        bm.from_mesh(o.data)
        sueltos += sum(1 for v in bm.verts if not v.link_faces)
        antes = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        dobles += antes - len(bm.verts)
        bm.free()
    res.append((malas == 0 and abiertas == 0 and sueltos == 0 and dobles == 0,
                f"Piezas cerradas con normales hacia afuera ({malas} mal, {abiertas} abiertas); "
                f"sin vértices sueltos ({sueltos}) ni duplicados ({dobles})"))
    return res, tris


def main():
    # 1) Envolventes del torso de las 4 variantes (en una escena aparte).
    comun.escena_vacia()
    env = envolventes(VARIANTES)
    comun.escena_vacia()
    # 2) Accesorios.
    cabeza = malla_cabeza()
    pelos = mallas_pelo()
    con_gorro = ["corto", "rapado", "raya", "largo", "colita", "rodete", "pelado"]
    env_gorra = EnvCabeza(cabeza, pelos, con_gorro)
    mats = {n: comun.cargar_materiales(*a["mats"]) for n, a in ACC.items()}
    objetos = [
        gorra(env_gorra, mats["gorra"]),
        gorro_lana(env_gorra, mats["gorro_lana"]),
        anteojos_sol(mats["anteojos_sol"]),
        anteojos_lectura(mats["anteojos_lectura"]),
        mochila(env["punto_espalda"], mats["mochila"]),
        bolso_cruzado(env["punto_pecho"], mats["bolso_cruzado"]),
        bolsa_mandados(mats["bolsa_mandados"]),
        termo(mats["termo"]),
        mate(mats["mate"]),
    ]
    revision, tris = revisar(objetos)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    glb = comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb"
    comun.exportar_glb(objetos, glb)
    j = _persona.leer_glb(glb)
    en_glb = sorted(n["name"] for n in j["nodes"])
    revision.append((en_glb == sorted(o.name for o in objetos), f".glb: {len(en_glb)} objetos acc_… en el origen"))
    # 3) Puestos en las 4 variantes: choques con el cuerpo y el pelo.
    personas = {}
    for id_, P in VARIANTES:
        R = construir_persona(id_, P)
        R["copias"] = poner_accesorios(R, objetos)
        personas[id_] = R
    malas = {n.removeprefix("acc_"): {} for n in (o.name for o in objetos)}
    for id_, R in personas.items():
        for nombre, lista in chequeo_choques(R, R["copias"]).items():
            if lista:
                malas[nombre][id_] = lista
    for nombre, por_var in malas.items():
        for id_, lista in por_var.items():
            print(f"  choque {nombre} en {id_}: " + ", ".join(f"{e} ({p * 1000:.0f} mm)" for e, p in lista))
    ok_choques = all(not v for v in malas.values())
    texto = ", ".join(f"{n} " + ("ok" if not v else "✘ " + "/".join(CORTO[i] for i in v)) for n, v in malas.items())
    revision.append((ok_choques, "Sin meterse en el cuerpo ni en el pelo (4 variantes × quieto, caminar, sentado; "
                                 f"los de mano sin sentado, sin chico la bolsa y el termo): {texto}"))
    compat = chequeo_pelos(objetos, pelos)
    sin_gorro = {"colita": "largo", "rodete": "largo", "rulos": "corto"}
    for gor, d in compat.items():
        bien = [e for e, p in d.items() if p <= TOL]
        mal = [f"{e} {p * 1000:.0f} mm" for e, p in d.items() if p > TOL]
        print(f"  {gor}: bien con {bien}; asoma {mal}")
        revision.append((all(e in sin_gorro or d[e] <= TOL for e in d),
                         f"{gor} sobre los peinados: bien con {', '.join(bien)}"
                         + (f" · atraviesan {', '.join(mal)}: con gorro el juego pone "
                            + ", ".join(f"{a}→{b}" for a, b in sin_gorro.items()) if mal else "")))
    escalas = []
    for id_, R in personas.items():
        ex, _, ez = escala_punto("punto_pecho", R["P"], R["M"])
        escalas.append(f"{CORTO[id_]} {ez:.3f} (pecho x {ex:.3f})".replace(".", ","))
    revision.append((True, "Escala k de punto_espalda y punto_pecho: " + ", ".join(escalas)))
    ok = comun.imprimir_revision(ID, revision)
    if "--sin-hoja" not in sys.argv:
        hoja(objetos, personas, revision, tris)
    if not ok:
        sys.exit(1)


# ── Hoja de revisión ───────────────────────────────────────────────────

def hoja(objetos, personas, revision, tris):
    """Cada accesorio solo y puesto en las variantes (quieto, caminando, sentado)."""
    import tempfile
    import _plaza as plaza
    rapido = "--rapido" in sys.argv
    comun.preparar_revision()
    if rapido:
        bpy.context.scene.cycles.samples = 12
    banco = _persona._importar_banco()
    por_nombre = {o.name.removeprefix("acc_"): o for o in objetos}
    todos = set(banco) | set(objetos)
    for R in personas.values():
        todos |= {R["cuerpo"], R["pelo"]} | set(R["copias"].values())
        R["arm"].hide_render = True

    def fila(nombres, paso):
        """Copias de los accesorios en fila (para la foto de solos)."""
        cs = []
        for k, n in enumerate(nombres):
            c = por_nombre[n].copy()
            bpy.context.scene.collection.objects.link(c)
            zmin = min(v.co.z for v in c.data.vertices)
            c.location = (paso * (k - (len(nombres) - 1) / 2), 0, -zmin)   # apoyado en el piso
            cs.append(c)
            todos.add(c)
        return cs
    en_banco = []
    for n, x in (("termo", 0.42), ("mate", 0.31)):       # apoyados en el asiento, al lado
        c = por_nombre[n].copy()
        bpy.context.scene.collection.objects.link(c)
        c.location = (x, 0.06, 0.45 - min(v.co.z for v in c.data.vertices))
        en_banco.append(c)
        todos.add(c)
    for o in objetos:
        o.hide_render = True

    def tris_de(*ns):
        return " · ".join(f"{n} {tris[n]}" for n in ns)

    solos = [
        (f"gorra y gorro de lana ({tris_de('gorra', 'gorro_lana')} tris)", fila(["gorra", "gorro_lana"], 0.30),
         V((0.9, -1.3, 0.6))),
        (f"anteojos de sol y de lectura ({tris_de('anteojos_sol', 'anteojos_lectura')})",
         fila(["anteojos_sol", "anteojos_lectura"], 0.22), V((0.5, -1.3, 0.35))),
        (f"mochila ({tris['mochila']} tris) · de atrás", fila(["mochila"], 0), V((-0.9, 1.3, 0.5))),
        (f"bolso cruzado ({tris['bolso_cruzado']} tris)", fila(["bolso_cruzado"], 0), V((0.9, -1.3, 0.5))),
        (f"bolsa de mandados ({tris['bolsa_mandados']} tris)", fila(["bolsa_mandados"], 0), V((1.0, -1.3, 0.45))),
        (f"termo y mate ({tris_de('termo', 'mate')} tris)", fila(["termo", "mate"], 0.16), V((0.9, -1.3, 0.5))),
    ]
    A, B, Mm, C = (personas[i] for i in ("persona_adulto_a", "persona_adulto_b", "persona_mayor", "persona_chico"))

    def yo(R, *ns):
        return [R["cuerpo"], R["pelo"]] + [R["copias"][n] for n in ns]

    def pose(R, anim, t):
        return lambda: _persona.poner_pose(R["arm"], R["funs"][anim](R["esq"], t))
    perA, perB, perM, perC = (R["caminar"].T for R in (A, B, Mm, C))
    puestos = [
        ("adulto A quieto: gorra, anteojos de sol, mochila, bolsa", yo(A, "gorra", "anteojos_sol", "mochila",
         "bolsa_mandados"), pose(A, "quieto", 0.0), "tres_cuartos", "dia"),
        ("adulto A caminando, de atrás", yo(A, "gorra", "anteojos_sol", "mochila", "bolsa_mandados"),
         pose(A, "caminar", perA * 0.3), "tres_cuartos_atras", "dia"),
        ("adulto B caminando: gorro, bolso, termo y mate", yo(B, "gorro_lana", "bolso_cruzado", "termo", "mate"),
         pose(B, "caminar", perB * 0.55), "tres_cuartos", "dia"),
        ("adulto B quieto, de frente · atardecer", yo(B, "gorro_lana", "bolso_cruzado", "anteojos_sol"),
         pose(B, "quieto", 1.0), "frente", "atardecer"),
        ("mayor sentado: termo y mate en el banco", yo(Mm, "anteojos_lectura", "gorra", "bolso_cruzado") + banco + en_banco,
         pose(Mm, "sentado", 2.0), "tres_cuartos", "dia"),
        ("mayor caminando: gorro, mochila, termo", yo(Mm, "gorro_lana", "mochila", "termo", "anteojos_lectura"),
         pose(Mm, "caminar", perM * 0.1), "costado_p", "dia"),
        ("chico caminando: gorra y mochila", yo(C, "gorra", "mochila"), pose(C, "caminar", perC * 0.3),
         "tres_cuartos", "dia"),
        ("chico sentado: gorro y bolso", yo(C, "gorro_lana", "bolso_cruzado") + banco, pose(C, "sentado", 2.0),
         "tres_cuartos", "atardecer"),
        ("adulto B caminando: termo y mate, de cerca", yo(B, "termo", "mate", "bolso_cruzado"),
         pose(B, "caminar", perB * 0.3), ("manos", B), "dia"),
        ("mayor quieto: bolso cruzado sobre la panza", yo(Mm, "bolso_cruzado", "anteojos_lectura", "gorro_lana"),
         pose(Mm, "quieto", 2.0), "cerca", "dia"),
        ("cara: gorra y anteojos de sol", yo(A, "gorra", "anteojos_sol"), pose(A, "quieto", 0.0), ("cara", A), "dia"),
        ("cara: mayor con anteojos de lectura", yo(Mm, "anteojos_lectura"), pose(Mm, "quieto", 0.0), ("cara", Mm), "dia"),
        ("cara: gorro de lana sobre pelo largo", yo(B, "gorro_lana"), pose(B, "quieto", 0.0), ("cara", B), "atardecer"),
        ("adulto B de atrás: gorra sobre el pelo largo, mochila", yo(B, "gorra", "mochila"), pose(B, "quieto", 0.0),
         "atras_cerca", "dia"),
    ]
    tmp = Path(tempfile.mkdtemp())
    cuadros = []
    for etiqueta, objs, d in solos:
        for o in todos:
            o.hide_render = o not in objs
        comun.poner_luz("dia")
        plaza.PERSPECTIVAS["_tmp"] = d
        plaza.encuadre_ajustado(objs, "_tmp", margen=1.15)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    for etiqueta, objs, poner, vista, luz in puestos:
        poner()
        for o in todos:
            o.hide_render = o not in objs
        comun.poner_luz(luz)
        if vista == "frente":
            comun.encuadrar(objs, vista, margen=1.08, de_cerca=True)
        elif vista == "costado_p":
            _persona._encuadre(objs, V((1, -0.15, 0.12)))
        elif vista == "atras_cerca":
            _persona._encuadre(objs, V((-0.8, 1.3, 0.35)), solo_arriba=True)
        elif vista == "cerca":
            _persona._encuadre(objs, V((0.9, -1.3, 0.35)), solo_arriba=True)
        elif isinstance(vista, tuple) and vista[0] == "manos":
            import _plaza as plaza_
            Rm = vista[1]
            c = (Rm["puntos"]["punto_mano_d"].matrix_world.translation +
                 Rm["puntos"]["punto_mano_i"].matrix_world.translation) / 2
            caja = _persona._caja(c + V((0, 0, -0.12)), (0.30, 0.30, 0.30))
            plaza_.PERSPECTIVAS["_tmp"] = V((0.9, -1.3, 0.25))
            plaza_.encuadre_ajustado([caja], "_tmp", margen=1.0)
        elif isinstance(vista, tuple):
            _persona._encuadre_cara(vista[1], V((0.55, -1.3, 0.18)) if vista[0] == "cara" else V((-0.7, 1.2, 0.3)))
        else:
            plaza.encuadre_ajustado(objs, vista)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    destino = comun.RAIZ / (f".hoja_rapida_{ID}.jpg" if rapido else f"docs/arte/revisiones/{ID}.jpg")
    comun.componer_hoja(f"{ID} · 9 accesorios · ≤300 tris c/u · enganchados a huesos y puntos de las personas",
                        cuadros, revision, destino, columnas=4)
    if rapido:   # prueba: la hoja va a la carpeta temporal del sistema, no a docs/
        import shutil
        final = Path(tempfile.gettempdir()) / f"hoja_rapida_{ID}.jpg"
        shutil.move(destino, final)
        print(f"Hoja rápida: {final}")


if __name__ == "__main__":
    main()
