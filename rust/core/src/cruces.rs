//! SPEC-013 · Peatones que esperan en el cordón si viene un auto (REQ-AMB-18). (TASK-0509)
//!
//! REQ-AMB-18: un peatón que va a cruzar una calle (la principal o una lateral) espera en el
//! cordón si viene un auto a menos de 3 s de su paso, y cruza cuando pasó. Acá están las
//! calzadas en planta, por dónde cruza un camino y cuándo llega un auto a ese paso.

use crate::autos::{ANCHO_CALLE_LATERAL, Recorrido, X_CALLE_LATERAL, Z_FIN_LATERAL};
use crate::plaza;

/// REQ-AMB-18: si un auto llega al paso en menos de esto, el peatón espera.
pub const SEGUNDOS_AVISO: f32 = 3.0;
/// A cuánto del borde de la calzada (por su camino) se para a mirar.
pub const DISTANCIA_CORDON: f32 = 0.5;
/// Con mucho tránsito casi nunca hay 3 s libres: si ya esperó tanto, se conforma con un
/// hueco más corto (`AVISO_APURADO`), que alcanza para que el auto frene por él (REQ-AMB-08).
pub const ESPERA_MAXIMA: f32 = 10.0;
pub const AVISO_APURADO: f32 = 1.5;
/// Si esperó el doble y el paso sigue ocupado (un auto parado encima), cruza igual: que no
/// se trabe para siempre.
pub const ESPERA_TOPE: f32 = 2.0 * ESPERA_MAXIMA;
/// Medio largo del auto (4,1 m) y medio ancho (0,9 m) más el de una persona.
const MEDIO_LARGO_AUTO: f32 = 2.1;
const ALCANCE: f32 = 0.9 + 0.4;
/// Paso con el que se recorre el carril buscando el cruce.
const PASO: f32 = 0.25;
/// Largo mínimo dentro de la calzada para contar como cruce (no rozar una esquina).
const MINIMO_DENTRO: f32 = 0.05;

/// REQ-AMB-18: calzadas en planta, `[x_min, z_min, x_max, z_max]`: la calle principal (de
/// punta a punta del terreno) y las dos laterales (del cordón de la vereda del carrito hasta
/// donde se dibuja el asfalto).
pub fn calzadas() -> [[f32; 4]; 3] {
    let medio = plaza::TAMANO_TERRENO / 2.0;
    let z0 = plaza::Z_CALLE - plaza::ANCHO_CALLE / 2.0;
    let z1 = plaza::Z_CALLE + plaza::ANCHO_CALLE / 2.0;
    let x0 = X_CALLE_LATERAL - ANCHO_CALLE_LATERAL / 2.0;
    let x1 = X_CALLE_LATERAL + ANCHO_CALLE_LATERAL / 2.0;
    let fin = Z_FIN_LATERAL + 8.0;
    [[-medio, z0, medio, z1], [x0, z1, x1, fin], [-x1, z1, -x0, fin]]
}

/// ¿`p` está sobre una calzada (sin contar el borde)?
pub fn en_calzada(p: [f32; 2]) -> bool {
    calzadas().iter().any(|r| p[0] > r[0] && p[0] < r[2] && p[1] > r[1] && p[1] < r[3])
}

/// Parte del segmento `a`→`b` (en fracciones `t0..t1`) que cae en el rectángulo `r`.
fn recorte(a: [f32; 2], b: [f32; 2], r: [f32; 4]) -> Option<(f32, f32)> {
    let (mut t0, mut t1) = (0.0_f32, 1.0_f32);
    for eje in 0..2 {
        let d = b[eje] - a[eje];
        let (min, max) = (r[eje], r[eje + 2]);
        if d.abs() < 1e-6 {
            if a[eje] < min || a[eje] > max {
                return None;
            }
            continue;
        }
        let (mut u0, mut u1) = ((min - a[eje]) / d, (max - a[eje]) / d);
        if u0 > u1 {
            std::mem::swap(&mut u0, &mut u1);
        }
        t0 = t0.max(u0);
        t1 = t1.min(u1);
        if t0 > t1 {
            return None;
        }
    }
    Some((t0, t1))
}

fn interpolar(a: [f32; 2], b: [f32; 2], t: f32) -> [f32; 2] {
    [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
}

fn distancia(a: [f32; 2], b: [f32; 2]) -> f32 {
    (a[0] - b[0]).hypot(a[1] - b[1])
}

/// Distancia de `p` a la polilínea `puntos`.
fn distancia_a_polilinea(p: [f32; 2], puntos: &[[f32; 2]]) -> f32 {
    if puntos.len() == 1 {
        return distancia(p, puntos[0]);
    }
    puntos
        .windows(2)
        .map(|w| {
            let (a, b) = (w[0], w[1]);
            let ab = [b[0] - a[0], b[1] - a[1]];
            let l2 = (ab[0] * ab[0] + ab[1] * ab[1]).max(1e-9);
            let t = (((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / l2).clamp(0.0, 1.0);
            distancia(p, interpolar(a, b, t))
        })
        .fold(f32::INFINITY, f32::min)
}

/// Por dónde cruza un camino una calzada. REQ-AMB-18
#[derive(Debug, Clone, PartialEq)]
pub struct Cruce {
    /// Punto del borde donde baja a la calzada.
    pub cordon: [f32; 2],
    /// Punto del otro borde donde sube.
    pub salida: [f32; 2],
    /// Lo que camina sobre la calzada, de `cordon` a `salida`.
    pub puntos: Vec<[f32; 2]>,
    /// Lo que le falta caminar (por su camino) hasta el cordón.
    pub distancia: f32,
}

impl Cruce {
    /// ¿Ya llegó al cordón (y tiene que mirar si viene un auto)?
    pub fn en_el_cordon(&self) -> bool {
        self.distancia <= DISTANCIA_CORDON
    }
}

/// REQ-AMB-18: primer cruce de calzada de la polilínea `ruta` (el primer punto es donde está
/// el peatón). `None` si no cruza ninguna calle o si ya está sobre la calzada (cruzando).
pub fn cruce(ruta: &[[f32; 2]]) -> Option<Cruce> {
    if ruta.len() < 2 || en_calzada(ruta[0]) {
        return None;
    }
    let calzadas = calzadas();
    let mut recorrido = 0.0;
    for i in 0..ruta.len() - 1 {
        let (a, b) = (ruta[i], ruta[i + 1]);
        let largo = distancia(a, b);
        let entrada = calzadas
            .iter()
            .filter_map(|&r| recorte(a, b, r))
            // Que de verdad baje a la calzada: ni rozar una esquina ni caminar por el borde.
            .filter(|&(t0, t1)| (t1 - t0) * largo > MINIMO_DENTRO && en_calzada(interpolar(a, b, (t0 + t1) / 2.0)))
            .map(|(t0, _)| t0)
            .reduce(f32::min);
        let Some(t0) = entrada else {
            recorrido += largo;
            continue;
        };
        let cordon = interpolar(a, b, t0);
        let mut puntos = vec![cordon];
        let (mut tramo, mut t) = (i, t0);
        loop {
            let (a, b) = (ruta[tramo], ruta[tramo + 1]);
            // Se avanza mientras siga sobre alguna calzada (pasando de una a otra si se tocan).
            loop {
                let mas_lejos = calzadas
                    .iter()
                    .filter_map(|&r| recorte(a, b, r))
                    .filter(|&(u0, u1)| u0 <= t + 1e-4 && u1 > t + 1e-6)
                    .map(|(_, u1)| u1)
                    .reduce(f32::max);
                match mas_lejos {
                    Some(u) => t = u,
                    None => break,
                }
            }
            if t < 1.0 - 1e-6 || tramo + 2 >= ruta.len() {
                let salida = interpolar(a, b, t.min(1.0));
                puntos.push(salida);
                return Some(Cruce { cordon, salida, puntos, distancia: recorrido + t0 * largo });
            }
            puntos.push(b);
            tramo += 1;
            t = 0.0;
        }
    }
    None
}

/// REQ-AMB-18: en cuántos segundos llega al paso un auto que va a `v` m/s y está a `s` m del
/// comienzo de su carril `rec`. `Some(0.0)` si ya está encima; `None` si ya pasó, si está
/// parado lejos o si tarda más de `SEGUNDOS_AVISO`.
pub fn tiempo_hasta_el_paso(rec: &Recorrido, s: f32, v: f32, cruce: &Cruce) -> Option<f32> {
    let toca = |u: f32| distancia_a_polilinea(rec.punto(s + u).0, &cruce.puntos) < ALCANCE;
    let mut u = -MEDIO_LARGO_AUTO;
    while u <= MEDIO_LARGO_AUTO {
        if toca(u) {
            return Some(0.0);
        }
        u += PASO;
    }
    if v < 0.1 {
        return None;
    }
    let limite = MEDIO_LARGO_AUTO + v * SEGUNDOS_AVISO;
    while u <= limite {
        if toca(u) {
            return Some((u - MEDIO_LARGO_AUTO) / v);
        }
        u += PASO;
    }
    None
}

/// REQ-AMB-18: ¿viene un auto a menos de 3 s del paso (o ya está encima)?
pub fn viene_auto(rec: &Recorrido, s: f32, v: f32, cruce: &Cruce) -> bool {
    viene_auto_antes(rec, s, v, cruce, SEGUNDOS_AVISO)
}

/// ¿Viene un auto a menos de `segundos` del paso (o ya está encima)?
pub fn viene_auto_antes(rec: &Recorrido, s: f32, v: f32, cruce: &Cruce, segundos: f32) -> bool {
    tiempo_hasta_el_paso(rec, s, v, cruce).is_some_and(|t| t < segundos.min(SEGUNDOS_AVISO))
}

/// REQ-AMB-18: cuánto margen pide quien lleva `esperado` segundos en el cordón: 3 s; si ya
/// esperó `ESPERA_MAXIMA`, un hueco más corto; y pasado `ESPERA_TOPE`, ninguno (ver `espera`).
pub fn margen_pedido(esperado: f32) -> f32 {
    if esperado < ESPERA_MAXIMA {
        SEGUNDOS_AVISO
    } else if esperado < ESPERA_TOPE {
        AVISO_APURADO
    } else {
        0.0
    }
}

/// Por debajo de esta velocidad (m/s) un auto cuenta como parado.
const PARADO: f32 = 0.5;

/// REQ-AMB-18: ¿quien lleva `esperado` segundos en el cordón tiene que seguir esperando por el
/// auto del carril `rec` (en `s`, a `v` m/s)? Pasado `ESPERA_TOPE` ya no espera a un auto
/// parado en el paso (que no se trabe), pero nunca se cruza delante de uno andando que llega
/// en menos de `AVISO_APURADO`.
pub fn espera(rec: &Recorrido, s: f32, v: f32, cruce: &Cruce, esperado: f32) -> bool {
    if esperado < ESPERA_TOPE {
        viene_auto_antes(rec, s, v, cruce, margen_pedido(esperado))
    } else {
        v >= PARADO && viene_auto_antes(rec, s, v, cruce, AVISO_APURADO)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::autos::recorrido;
    use crate::caminos::{self, Z_VEREDA_PEATONES};
    use crate::ciudad::{SENDAS, Z_VEREDA_ENFRENTE};

    fn cerca(a: [f32; 2], b: [f32; 2]) -> bool {
        distancia(a, b) < 0.01
    }

    /// `s` del carril en el que el auto está en `p` (el punto más cercano del recorrido).
    fn s_en(rec: &Recorrido, p: [f32; 2]) -> f32 {
        let n = (rec.largo() / 0.05) as usize;
        (0..n)
            .map(|i| i as f32 * 0.05)
            .min_by(|&a, &b| distancia(rec.punto(a).0, p).total_cmp(&distancia(rec.punto(b).0, p)))
            .unwrap()
    }

    #[test]
    fn req_amb_18_cruce_de_la_principal_por_la_senda() {
        let x = SENDAS[1];
        // De la vereda del carrito a la de enfrente: baja en el cordón sur y sube en el norte.
        let c = cruce(&[[x, Z_VEREDA_PEATONES], [x, Z_VEREDA_ENFRENTE]]).unwrap();
        assert!(cerca(c.cordon, [x, -25.0]) && cerca(c.salida, [x, -33.0]), "{c:?}");
        assert!((c.distancia - 3.6).abs() < 0.01 && !c.en_el_cordon());
        // Al revés, el cordón es el del norte; y parado a 0,3 m ya está en el cordón.
        let c = cruce(&[[x, -33.3], [x, Z_VEREDA_PEATONES]]).unwrap();
        assert!(cerca(c.cordon, [x, -33.0]) && cerca(c.salida, [x, -25.0]) && c.en_el_cordon(), "{c:?}");
        // El cruce puede estar más adelante en la ruta.
        let c = cruce(&[[0.0, Z_VEREDA_PEATONES], [x, Z_VEREDA_PEATONES], [x, Z_VEREDA_ENFRENTE]]).unwrap();
        assert!(cerca(c.cordon, [x, -25.0]) && (c.distancia - 28.6).abs() < 0.01, "{c:?}");
    }

    #[test]
    fn req_amb_18_cruce_de_una_lateral() {
        // El camino a la salida del este cruza la lateral: baja en x = 46, pasa por el medio
        // y sube del otro lado, en diagonal.
        let ruta = [[42.0, Z_VEREDA_PEATONES], [50.0, Z_VEREDA_PEATONES], [55.0, -15.0], [59.5, -5.0]];
        let c = cruce(&ruta).unwrap();
        assert!(cerca(c.cordon, [46.0, Z_VEREDA_PEATONES]), "{c:?}");
        assert!((c.salida[0] - 54.0).abs() < 0.01 && c.salida[1] > Z_VEREDA_PEATONES, "{c:?}");
        assert_eq!(c.puntos.len(), 3);
        // Del oeste, viniendo desde la salida.
        let ruta = [[-55.0, -15.0], [-50.0, Z_VEREDA_PEATONES], [-42.0, Z_VEREDA_PEATONES]];
        let c = cruce(&ruta).unwrap();
        assert!((c.cordon[0] + 54.0).abs() < 0.01 && cerca(c.salida, [-46.0, Z_VEREDA_PEATONES]), "{c:?}");
    }

    #[test]
    fn req_amb_18_tramo_que_no_cruza() {
        // Por la vereda, por la plaza o ya sobre la calzada (cruzando): nada.
        assert_eq!(cruce(&[[0.0, Z_VEREDA_PEATONES], [8.0, Z_VEREDA_PEATONES]]), None);
        assert_eq!(cruce(&[[0.0, 0.0], [0.0, -20.5], [17.0, -21.4]]), None);
        assert_eq!(cruce(&[[25.0, -29.0], [25.0, Z_VEREDA_ENFRENTE]]), None);
        assert_eq!(cruce(&[[25.0, -21.0]]), None);
        // Caminar justo por el borde no es cruzar.
        assert_eq!(cruce(&[[0.0, -25.0], [10.0, -25.0]]), None);
    }

    #[test]
    fn req_amb_18_la_red_cruza_solo_por_las_sendas_y_las_laterales() {
        let r = caminos::red();
        let (mut principal, mut laterales) = (0, 0);
        for (a, vecinos) in r.vecinos.iter().enumerate() {
            for &b in vecinos {
                let (p, q) = (r.pos[a], r.pos[b]);
                let Some(c) = cruce(&[p, q]) else { continue };
                if c.cordon[1] <= -25.0 + 0.01 && c.cordon[1] >= -33.0 - 0.01 && c.cordon[0].abs() < 40.0 {
                    assert!(
                        SENDAS.contains(&p[0]) && p[0] == q[0],
                        "cruza la principal fuera de la senda: {p:?} → {q:?}"
                    );
                    principal += 1;
                } else {
                    assert!((c.cordon[0].abs() - X_CALLE_LATERAL).abs() <= ANCHO_CALLE_LATERAL / 2.0 + 0.01, "{c:?}");
                    laterales += 1;
                }
            }
        }
        // Dos sendas en los dos sentidos; en las laterales se entra desde la vereda o desde
        // el camino a la salida (que arranca sobre la calzada: ese tramo ya está cruzando).
        assert_eq!(principal, 4);
        assert!(laterales >= 2, "{laterales}");
    }

    #[test]
    fn req_amb_18_espera_si_viene_un_auto_a_menos_de_3_s() {
        let x = SENDAS[1];
        let c = cruce(&[[x, -24.7], [x, Z_VEREDA_ENFRENTE]]).unwrap();
        // Carril hacia el este (z = -27): el auto está a `d` m antes de la senda.
        let rec = recorrido(0);
        let s0 = s_en(&rec, [x, -27.0]);
        // Lejos (a 40 m, a 10 m/s): más de 3 s, cruza.
        assert!(!viene_auto(&rec, s0 - 40.0, 10.0, &c));
        // A 20 m: llega en menos de 3 s, espera.
        let t = tiempo_hasta_el_paso(&rec, s0 - 20.0, 10.0, &c).unwrap();
        assert!(t > 1.0 && t < 2.0, "{t}");
        assert!(viene_auto(&rec, s0 - 20.0, 10.0, &c));
        // Encima del paso, aunque esté parado: espera.
        assert_eq!(tiempo_hasta_el_paso(&rec, s0 + 1.0, 0.0, &c), Some(0.0));
        // Ya pasó: cruza.
        assert!(!viene_auto(&rec, s0 + 5.0, 10.0, &c));
        // Parado lejos (frenó por otro): cruza.
        assert!(!viene_auto(&rec, s0 - 10.0, 0.0, &c));
        // Despacio: tarda más de 3 s, cruza.
        assert!(!viene_auto(&rec, s0 - 20.0, 4.0, &c));
        // El carril de enfrente (hacia el oeste) también cuenta.
        let rec1 = recorrido(1);
        let s1 = s_en(&rec1, [x, -31.0]);
        assert!(viene_auto(&rec1, s1 - 15.0, 10.0, &c));
        assert!(!viene_auto(&rec1, s1 + 5.0, 10.0, &c));
    }

    #[test]
    fn req_amb_18_no_se_traba_para_siempre() {
        let x = SENDAS[1];
        let c = cruce(&[[x, -24.7], [x, Z_VEREDA_ENFRENTE]]).unwrap();
        let rec = recorrido(0);
        let s0 = s_en(&rec, [x, -27.0]);
        // Un auto a unos 2 s: al principio espera; después de mucho esperar ya no (un hueco de
        // 2 s alcanza para que el auto frene), pero sí si el auto está por llegar.
        assert_eq!(margen_pedido(0.0), SEGUNDOS_AVISO);
        let apurado = margen_pedido(ESPERA_MAXIMA);
        assert!(apurado < 2.0 && apurado > 1.0);
        assert!(viene_auto_antes(&rec, s0 - 24.0, 10.0, &c, margen_pedido(0.0)));
        assert!(!viene_auto_antes(&rec, s0 - 24.0, 10.0, &c, apurado));
        assert!(viene_auto_antes(&rec, s0 - 10.0, 10.0, &c, apurado));
        // Con un auto parado encima del paso, al final cruza igual.
        assert!(viene_auto_antes(&rec, s0, 0.0, &c, apurado));
        assert!(!viene_auto_antes(&rec, s0, 0.0, &c, margen_pedido(ESPERA_TOPE)));
        assert!(!espera(&rec, s0, 0.0, &c, ESPERA_TOPE));
        assert!(espera(&rec, s0, 0.0, &c, ESPERA_TOPE - 1.0));
    }

    #[test]
    fn req_amb_18_a_los_20_s_no_cruza_delante_de_un_auto_andando() {
        let x = SENDAS[1];
        let c = cruce(&[[x, -24.7], [x, Z_VEREDA_ENFRENTE]]).unwrap();
        let rec = recorrido(0);
        let s0 = s_en(&rec, [x, -27.0]);
        // Un auto a 10 m/s a ~1 s del paso, o ya encima andando: sigue esperando aunque esperó 20 s.
        assert!(espera(&rec, s0 - 10.0, 10.0, &c, ESPERA_TOPE + 5.0));
        assert!(espera(&rec, s0, 8.0, &c, ESPERA_TOPE + 5.0));
        // Uno a ~2,4 s: ya cruza (el auto frena, REQ-AMB-08).
        assert!(!espera(&rec, s0 - 24.0, 10.0, &c, ESPERA_TOPE + 5.0));
    }

    #[test]
    fn req_amb_18_en_la_lateral_cuenta_el_auto_que_dobla() {
        let ruta = [[42.0, Z_VEREDA_PEATONES], [50.0, Z_VEREDA_PEATONES], [55.0, -15.0]];
        let c = cruce(&[[45.7, Z_VEREDA_PEATONES], ruta[1], ruta[2]]).unwrap();
        assert!(c.en_el_cordon());
        // El que sube por la lateral (carril hacia el oeste, x = 52) a 20 m: espera.
        let rec1 = recorrido(1);
        let s = s_en(&rec1, [52.0, Z_VEREDA_PEATONES + 20.0]);
        assert!(viene_auto(&rec1, s, 10.0, &c));
        assert!(!viene_auto(&rec1, s, 3.0, &c), "despacio no llega en 3 s");
        // El que viene por la principal y dobla hacia el sur (x = 48): todavía no apunta al
        // paso, pero llega en menos de 3 s siguiendo la curva.
        let rec0 = recorrido(0);
        let s = s_en(&rec0, [37.0, -27.0]);
        let t = tiempo_hasta_el_paso(&rec0, s, 10.0, &c).unwrap();
        assert!(t > 0.5 && t < SEGUNDOS_AVISO, "{t}");
        // Cuando ya bajó por la lateral, pasó.
        let s = s_en(&rec0, [48.0, -12.0]);
        assert!(!viene_auto(&rec0, s, 10.0, &c));
    }
}
