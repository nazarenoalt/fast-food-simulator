//! SPEC-013 · Autos: recorrido de cada carril, frenado y renovación fuera de la vista.
//!
//! REQ-AMB-17: la calle sigue derecho frente a la plaza y en cada punta dobla hacia el sur
//! por una calle lateral que pasa detrás de los edificios de los costados. Los autos aparecen
//! y desaparecen al fondo de esas calles laterales, tapados por los edificios desde el
//! carrito. Cada carril es un recorrido abierto: el auto que llega al final vuelve a entrar
//! por el principio, como otro auto (otro color).

use crate::azar::Azar;
use crate::ciudad::SEMILLA_CIUDAD;
use crate::plaza;

/// REQ-AMB-08: mano derecha. Hacia el este (+X) por el carril sur, hacia el oeste por el
/// norte: `(z del carril frente a la plaza, sentido en x)`.
pub const CARRILES: [(f32, f32); 2] = [(-27.0, 1.0), (-31.0, -1.0)];
/// REQ-AMB-17: centro (|x|) de las calles laterales, detrás de las filas de edificios del
/// este y del oeste (que terminan a lo sumo en |x| = 45).
pub const X_CALLE_LATERAL: f32 = 50.0;
pub const ANCHO_CALLE_LATERAL: f32 = 8.0;
/// Hasta dónde (z) llegan los autos por las calles laterales: ahí aparecen y desaparecen.
pub const Z_FIN_LATERAL: f32 = 4.0;
/// Radio de la curva del carril de adentro (el de afuera es 4 m más abierto).
const RADIO_CURVA: f32 = 5.0;
const MEDIO_CARRIL: f32 = 1.7;
const MIRA_ADELANTE: f32 = 16.0;
/// Paso con el que se recorre el carril buscando obstáculos.
const PASO_MIRADA: f32 = 0.5;

#[derive(Debug, Clone, Copy, PartialEq)]
enum Tramo {
    Recta {
        desde: [f32; 2],
        hasta: [f32; 2],
    },
    /// `angulo` y `giro` en radianes, medidos en el plano (x, z).
    Arco {
        centro: [f32; 2],
        radio: f32,
        angulo: f32,
        giro: f32,
    },
}

impl Tramo {
    fn largo(&self) -> f32 {
        match *self {
            Tramo::Recta { desde, hasta } => (hasta[0] - desde[0]).hypot(hasta[1] - desde[1]),
            Tramo::Arco { radio, giro, .. } => radio * giro.abs(),
        }
    }

    /// Punto y dirección (unitaria) a `u` metros del comienzo del tramo.
    fn punto(&self, u: f32) -> ([f32; 2], [f32; 2]) {
        match *self {
            Tramo::Recta { desde, hasta } => {
                let l = self.largo().max(1e-6);
                let d = [(hasta[0] - desde[0]) / l, (hasta[1] - desde[1]) / l];
                ([desde[0] + d[0] * u, desde[1] + d[1] * u], d)
            }
            Tramo::Arco { centro, radio, angulo, giro } => {
                let a = angulo + giro.signum() * u / radio;
                let (s, c) = a.sin_cos();
                ([centro[0] + radio * c, centro[1] + radio * s], [-s * giro.signum(), c * giro.signum()])
            }
        }
    }
}

/// Camino que sigue un carril, de punta a punta, con curvas redondeadas.
#[derive(Debug, Clone, PartialEq)]
pub struct Recorrido {
    tramos: Vec<Tramo>,
    largo: f32,
}

fn normal(v: [f32; 2]) -> [f32; 2] {
    let l = v[0].hypot(v[1]).max(1e-6);
    [v[0] / l, v[1] / l]
}

impl Recorrido {
    /// Polilínea `esquinas` (primera y última son las puntas) con cada esquina interior
    /// redondeada con su radio.
    fn por_esquinas(esquinas: &[[f32; 2]], radios: &[f32]) -> Self {
        let mut tramos = Vec::new();
        let mut actual = esquinas[0];
        for i in 1..esquinas.len() - 1 {
            let (p, c, q) = (esquinas[i - 1], esquinas[i], esquinas[i + 1]);
            let ent = normal([c[0] - p[0], c[1] - p[1]]);
            let sal = normal([q[0] - c[0], q[1] - c[1]]);
            let r = radios[i - 1];
            let theta = (ent[0] * sal[0] + ent[1] * sal[1]).clamp(-1.0, 1.0).acos();
            let t = r * (theta / 2.0).tan();
            let inicio = [c[0] - ent[0] * t, c[1] - ent[1] * t];
            let fin = [c[0] + sal[0] * t, c[1] + sal[1] * t];
            // El centro queda del lado hacia el que dobla.
            let mut n = [-ent[1], ent[0]];
            if n[0] * sal[0] + n[1] * sal[1] < 0.0 {
                n = [-n[0], -n[1]];
            }
            let centro = [inicio[0] + n[0] * r, inicio[1] + n[1] * r];
            let a0 = (inicio[1] - centro[1]).atan2(inicio[0] - centro[0]);
            let a1 = (fin[1] - centro[1]).atan2(fin[0] - centro[0]);
            let giro = (a1 - a0 + std::f32::consts::PI).rem_euclid(std::f32::consts::TAU) - std::f32::consts::PI;
            tramos.push(Tramo::Recta { desde: actual, hasta: inicio });
            tramos.push(Tramo::Arco { centro, radio: r, angulo: a0, giro });
            actual = fin;
        }
        tramos.push(Tramo::Recta { desde: actual, hasta: esquinas[esquinas.len() - 1] });
        let largo = tramos.iter().map(Tramo::largo).sum();
        Self { tramos, largo }
    }

    pub fn largo(&self) -> f32 {
        self.largo
    }

    /// Posición y dirección de marcha a `s` metros del comienzo (`s` da la vuelta).
    pub fn punto(&self, s: f32) -> ([f32; 2], [f32; 2]) {
        let mut u = s.rem_euclid(self.largo);
        for t in &self.tramos {
            let l = t.largo();
            if u <= l {
                return t.punto(u);
            }
            u -= l;
        }
        let t = self.tramos[self.tramos.len() - 1];
        t.punto(t.largo())
    }
}

/// REQ-AMB-08, REQ-AMB-17: recorrido del carril. Entra por la calle lateral de un costado,
/// cruza frente a la plaza y sale por la lateral del otro costado (mano derecha también en
/// las laterales: el carril de adentro de la curva es el más cercano a la plaza).
pub fn recorrido(carril: usize) -> Recorrido {
    let (z, sentido) = CARRILES[carril];
    let k = z - plaza::Z_CALLE; // +2 el de adentro (sur), -2 el de afuera
    let x = X_CALLE_LATERAL - k;
    let r = RADIO_CURVA + 2.0 - k;
    Recorrido::por_esquinas(
        &[[-sentido * x, Z_FIN_LATERAL], [-sentido * x, z], [sentido * x, z], [sentido * x, Z_FIN_LATERAL]],
        &[r, r],
    )
}

#[derive(Debug, Clone, PartialEq)]
pub struct AutoInicial {
    pub carril: usize,
    /// Metros recorridos desde la entrada del carril.
    pub s: f32,
    pub crucero: f32,
    pub color: [f32; 3],
}

pub const COLORES_AUTO: [[f32; 3]; 7] = [
    [0.8, 0.1, 0.1],
    [0.1, 0.2, 0.6],
    [0.9, 0.9, 0.9],
    [0.1, 0.1, 0.1],
    [0.6, 0.6, 0.62],
    [0.95, 0.8, 0.1],
    [0.2, 0.45, 0.3],
];

/// REQ-AMB-03: siempre los mismos autos al empezar.
pub fn autos_iniciales() -> Vec<AutoInicial> {
    let mut azar = Azar::new(SEMILLA_CIUDAD + 1);
    let mut v = Vec::new();
    for carril in 0..CARRILES.len() {
        let largo = recorrido(carril).largo();
        for i in 0..4 {
            v.push(AutoInicial {
                carril,
                s: i as f32 * largo / 4.0 + azar.rango(0.0, 15.0),
                crucero: azar.rango(8.0, 13.0),
                color: *azar.elegir(&COLORES_AUTO).unwrap(),
            });
        }
    }
    v
}

/// REQ-AMB-17: color del auto que vuelve a entrar; nunca el que tenía.
pub fn color_nuevo(azar: &mut Azar, anterior: [f32; 3]) -> [f32; 3] {
    let otros: Vec<_> = COLORES_AUTO.iter().filter(|c| **c != anterior).collect();
    **azar.elegir(&otros).unwrap()
}

/// REQ-AMB-17: avanza `ds` metros; si pasó el final del carril, vuelve a entrar por el
/// principio (fuera de la vista) y devuelve `true`.
pub fn avanzar(largo: f32, s: f32, ds: f32) -> (f32, bool) {
    let n = s + ds;
    if n >= largo { (n - largo, true) } else { (n, false) }
}

/// Distancia a un obstáculo (`obj` = (x, z)) que está adelante en el carril, si hay. REQ-AMB-08
pub fn distancia_adelante(rec: &Recorrido, s: f32, obj: [f32; 2]) -> Option<f32> {
    let mut d = 0.0;
    while d < MIRA_ADELANTE {
        let (p, dir) = rec.punto(s + d);
        let v = [obj[0] - p[0], obj[1] - p[1]];
        let a_lo_largo = v[0] * dir[0] + v[1] * dir[1];
        let al_costado = (v[0] * dir[1] - v[1] * dir[0]).abs();
        if a_lo_largo.abs() <= PASO_MIRADA / 2.0 && al_costado <= MEDIO_CARRIL {
            let total = d + a_lo_largo;
            return (0.0..MIRA_ADELANTE).contains(&total).then_some(total);
        }
        d += PASO_MIRADA;
    }
    None
}

/// Distancia al auto de adelante en el mismo carril (`s_otro`), si está cerca. REQ-AMB-08
pub fn distancia_al_de_adelante(largo: f32, s: f32, s_otro: f32) -> Option<f32> {
    let d = (s_otro - s).rem_euclid(largo);
    (d > 0.0 && d < MIRA_ADELANTE).then_some(d)
}

/// REQ-AMB-08: frena en forma gradual; parado si el obstáculo está a menos de 5 m.
pub fn velocidad_deseada(crucero: f32, obstaculo: Option<f32>) -> f32 {
    match obstaculo {
        None => crucero,
        Some(d) if d < 5.0 => 0.0,
        Some(d) => crucero * ((d - 5.0) / (MIRA_ADELANTE - 5.0)).min(1.0),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::caminos::{self, PUNTO_CARRITO};
    use crate::ciudad;

    /// Puntos del carril cada medio metro, con la dirección de marcha.
    fn muestras(rec: &Recorrido) -> Vec<(f32, [f32; 2], [f32; 2])> {
        let n = (rec.largo() / 0.5) as usize;
        (0..=n)
            .map(|i| {
                let s = rec.largo() * i as f32 / n as f32;
                let (p, d) = rec.punto(s.min(rec.largo() - 1e-3));
                (s, p, d)
            })
            .collect()
    }

    #[test]
    fn req_amb_03_autos_repetibles() {
        assert_eq!(autos_iniciales(), autos_iniciales());
    }

    #[test]
    fn req_amb_08_mano_derecha_y_frenado() {
        // El carril hacia el este está al sur (más cerca de la plaza).
        let este = CARRILES.iter().find(|c| c.1 > 0.0).unwrap();
        let oeste = CARRILES.iter().find(|c| c.1 < 0.0).unwrap();
        assert!(este.0 > oeste.0);
        for (z, _) in CARRILES {
            assert!((z - plaza::Z_CALLE).abs() < plaza::ANCHO_CALLE / 2.0);
        }
        // Mano derecha en todo el recorrido (también en las curvas y las laterales): el
        // carril contrario siempre queda a la izquierda.
        for c in 0..2 {
            let otro = muestras(&recorrido(1 - c));
            for (_, p, d) in muestras(&recorrido(c)) {
                let q = otro
                    .iter()
                    .map(|o| o.1)
                    .min_by(|a, b| (a[0] - p[0]).hypot(a[1] - p[1]).total_cmp(&(b[0] - p[0]).hypot(b[1] - p[1])));
                let q = q.unwrap();
                let derecha = [-d[1], d[0]];
                let lado = (q[0] - p[0]) * derecha[0] + (q[1] - p[1]) * derecha[1];
                assert!(lado < -2.0, "carril {c} en {p:?}: el contrario no queda a la izquierda");
            }
        }
        // Frente a la plaza circulan por su carril, en su sentido.
        let rec = recorrido(0);
        let s0 = muestras(&rec).iter().find(|m| m.1[0].abs() < 0.3).unwrap().0;
        let (p, d) = rec.punto(s0);
        assert!((p[1] - -27.0).abs() < 0.01 && d[0] > 0.99, "{p:?} {d:?}");
        assert_eq!(rec.punto(s0 + 10.0).0[0].round(), (p[0] + 10.0).round());
        // Obstáculos: adelante en el carril sí; atrás o en el otro carril no.
        let d = distancia_adelante(&rec, s0, [p[0] + 10.0, -27.0]).unwrap();
        assert!((d - 10.0).abs() < 0.05, "{d}");
        assert_eq!(distancia_adelante(&rec, s0, [p[0] - 10.0, -27.0]), None, "atrás no cuenta");
        assert_eq!(distancia_adelante(&rec, s0, [p[0] + 10.0, -31.0]), None, "otro carril");
        // También en la curva: alguien parado en la lateral frena al que dobla.
        let rec1 = recorrido(1);
        let s1 = muestras(&rec1).iter().find(|m| m.1[0].abs() < 0.3).unwrap().0;
        let (p1, _) = rec1.punto(s1 + 60.0);
        let d = distancia_adelante(&rec1, s1 + 50.0, p1).unwrap();
        assert!((d - 10.0).abs() < 0.3, "{d}");
        // Autos del mismo carril, también cuando el de adelante ya volvió a entrar.
        let l = rec.largo();
        assert_eq!(distancia_al_de_adelante(l, 10.0, 18.0), Some(8.0));
        assert_eq!(distancia_al_de_adelante(l, 18.0, 10.0), None);
        assert!((distancia_al_de_adelante(l, l - 2.0, 3.0).unwrap() - 5.0).abs() < 0.01);
        assert_eq!(velocidad_deseada(10.0, None), 10.0);
        assert_eq!(velocidad_deseada(10.0, Some(3.0)), 0.0);
        let v = velocidad_deseada(10.0, Some(10.0));
        assert!(v > 0.0 && v < 10.0);
        let vel: Vec<_> = autos_iniciales().iter().map(|a| (a.crucero * 10.0) as i32).collect();
        assert!(vel.iter().any(|v| *v != vel[0]), "velocidades distintas");
    }

    #[test]
    fn req_amb_08_17_recorrido_continuo_sin_pisar_edificios() {
        let e = ciudad::edificios();
        let medio = plaza::TAMANO_TERRENO / 2.0;
        for c in 0..2 {
            let m = muestras(&recorrido(c));
            for w in m.windows(2) {
                let (a, b) = (w[0].1, w[1].1);
                assert!((a[0] - b[0]).hypot(a[1] - b[1]) < 0.6, "salto entre {a:?} y {b:?}");
            }
            for (_, p, _) in &m {
                assert!(p[0].abs() < medio - 2.0 && p[1].abs() < medio, "{p:?} fuera del terreno");
                // Con el ancho del auto (0,9 m a cada lado) y algo de aire.
                for b in &e {
                    let [x0, z0, x1, z1] = b.planta();
                    let dentro = p[0] > x0 - 1.5 && p[0] < x1 + 1.5 && p[1] > z0 - 1.5 && p[1] < z1 + 1.5;
                    assert!(!dentro, "carril {c} pasa por un edificio en {p:?}");
                }
            }
        }
    }

    #[test]
    fn req_amb_17_entran_y_salen_tapados_desde_el_carrito() {
        let e = ciudad::edificios();
        for c in 0..2 {
            let rec = recorrido(c);
            let l = rec.largo();
            // Los primeros y los últimos 6 m del carril, con el largo (±2,1 m) y el ancho
            // (±0,9 m) del auto: ni la trompa ni la cola se ven desde el mostrador.
            let mut puntos = Vec::new();
            for k in 0..=24 {
                let u = k as f32 * 0.25;
                for s in [u, l - u] {
                    let (p, d) = rec.punto(s.min(l - 1e-3));
                    for (a, b) in [(-2.1, -0.9), (-2.1, 0.9), (2.1, -0.9), (2.1, 0.9)] {
                        puntos.push([p[0] + d[0] * a - d[1] * b, p[1] + d[1] * a + d[0] * b]);
                    }
                }
            }
            for punto in puntos {
                for ojo in caminos::ojos_carrito() {
                    assert!(caminos::tapado(ojo, punto, &e), "carril {c}: se ve {punto:?} desde {ojo:?}");
                }
            }
            // En cambio, frente al carrito sí se ven pasar.
            let frente = muestras(&rec).into_iter().find(|m| m.1[0].abs() < 0.3).unwrap().1;
            assert!(!caminos::tapado(PUNTO_CARRITO, frente, &e));
        }
    }

    #[test]
    fn req_amb_17_vuelve_a_entrar_otro_auto() {
        let l = recorrido(0).largo();
        assert_eq!(avanzar(l, 10.0, 0.5), (10.5, false));
        let (s, vuelta) = avanzar(l, l - 0.2, 0.5);
        assert!(vuelta && (s - 0.3).abs() < 1e-3, "{s}");
        // Otro color, nunca el mismo que tenía, y con variedad.
        let mut azar = Azar::new(7);
        for anterior in COLORES_AUTO {
            let nuevos: std::collections::HashSet<_> =
                (0..60).map(|_| color_nuevo(&mut azar, anterior).map(|x| (x * 100.0) as i32)).collect();
            assert!(!nuevos.contains(&anterior.map(|x| (x * 100.0) as i32)), "repite {anterior:?}");
            assert!(nuevos.len() >= 4, "poca variedad: {nuevos:?}");
        }
    }
}
