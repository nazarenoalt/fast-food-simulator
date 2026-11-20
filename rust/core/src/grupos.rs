//! SPEC-018 · Perfiles con comportamiento propio y grupos que caminan juntos
//! (REQ-RUT-05 a REQ-RUT-09). (TASK-0503)
//!
//! Acá va la geometría y las reglas (quién compone una familia, dónde se arma una ronda,
//! cómo caminan de a dos, cuándo alguien espera al grupo, a qué hora se van); `Gente` (Godot)
//! solo las usa para armar a la gente.

use std::f32::consts::{PI, TAU};

use crate::azar::Azar;
use crate::peatones::DISTANCIA_PERSONAL;
use crate::plaza::{self, TipoProp};
use crate::rutinas::Perfil;

/// REQ-RUT-05: a esta hora los oficinistas cortan lo que hacen y se van.
pub const HORA_SALIDA_OFICINISTAS: f32 = 14.5;
/// REQ-RUT-11: después de esta hora no hay chicos (y las familias que quedan se van).
pub const HORA_SIN_CHICOS: f32 = 21.0;
/// Antes de esta hora tampoco hay chicos (de madrugada).
pub const HORA_CON_CHICOS: f32 = 6.0;
/// REQ-RUT-06: altura de los chicos (m).
pub const ALTURA_CHICOS: [f32; 2] = [1.0, 1.3];
/// REQ-RUT-06: los chicos siguen a los adultos a menos de esto (m).
pub const DISTANCIA_CHICOS: f32 = 2.0;
/// REQ-RUT-06: con chicos, el grupo espera antes (así nadie queda a más de 2 m).
pub const UMBRAL_FAMILIA: f32 = 1.2;
/// REQ-RUT-08: si uno se adelanta más que esto (m) del último, espera.
pub const UMBRAL_GRUPO: f32 = 3.0;
/// REQ-RUT-08: de a dos, cada uno corrido esto (m) del centro del camino: entre los dos hay
/// 0,8 m, más que la distancia personal de REQ-AMB-13.
pub const LATERAL: f32 = 0.4;
/// REQ-RUT-08: la fila de atrás arranca esto (s) después (≈1 m a paso normal).
pub const DEMORA_FILA_S: f32 = 0.9;
/// REQ-RUT-06: vueltas que corren los chicos alrededor de la fuente (mínimo y máximo).
pub const VUELTAS: [usize; 2] = [1, 3];
/// REQ-RUT-06: radio de las vueltas (el borde de la fuente está a 3 m del centro).
pub const RADIO_VUELTAS: f32 = 3.6;
/// REQ-RUT-06: dónde esperan los adultos, junto al anillo que rodea la fuente.
pub const RADIO_ESPERA_FUENTE: f32 = 5.2;
/// REQ-RUT-06: los chicos corren a esta velocidad (m/s), más rápido que los adultos.
pub const VEL_CORRER: [f32; 2] = [2.0, 2.6];
/// REQ-RUT-07: separación entre dos vecinos de una ronda (m).
pub const SEPARACION_RONDA: f32 = 0.9;
/// REQ-RUT-07: la ronda se arma a esto (m) del farol, del lado opuesto al camino.
pub const CORRIMIENTO_FAROL: f32 = 1.3;
/// Separación entre dos personas sentadas en el mismo banco (m), REQ-AMB-13.
pub const SEPARACION_BANCO: f32 = 0.62;
/// En un banco entran 3 (mide 1,6 m); si son más, el resto se queda parado al lado.
pub const LUGARES_BANCO: usize = 3;

/// REQ-RUT-05 a REQ-RUT-09: perfiles que llegan en grupo o tienen comportamiento propio y
/// se arman en `grupos`. Corredor (trota), paseador (con perro), jubilado (lento, se sienta
/// largo) y trasnochado (pasea solo) se arman como paseantes comunes con su perfil.
pub fn arma_grupos(p: Perfil) -> bool {
    matches!(
        p,
        Perfil::Oficinista
            | Perfil::Familia
            | Perfil::Nocturno
            | Perfil::Pareja
            | Perfil::Adolescente
            | Perfil::AlTrabajo
    )
}

/// REQ-RUT-11: ¿puede haber chicos a esta hora (0–24)? No después de las 21 ni de madrugada.
pub fn hay_chicos(hora: f32) -> bool {
    (HORA_CON_CHICOS..HORA_SIN_CHICOS).contains(&hora.rem_euclid(24.0))
}

/// REQ-RUT-11: las familias que quedan se van cuando ya no puede haber chicos.
pub fn familias_se_van(hora: f32) -> bool {
    !hay_chicos(hora)
}

/// REQ-RUT-05: ¿ya es hora de que los oficinistas se vayan? (de 14:30 a medianoche).
pub fn oficinistas_se_van(hora: f32) -> bool {
    hora.rem_euclid(24.0) >= HORA_SALIDA_OFICINISTAS
}

/// REQ-RUT-06, REQ-RUT-11: cuántos adultos y cuántos chicos tiene una familia de `tamano`
/// (2–4): 1–2 adultos y 1–2 chicos. A la hora sin chicos llegan solo los adultos.
pub fn composicion_familia(azar: &mut Azar, tamano: usize, hora: f32) -> (usize, usize) {
    let tamano = tamano.clamp(2, 4);
    let (adultos, chicos) = match tamano {
        2 => (1, 1),
        3 => {
            if azar.chance(0.5) {
                (1, 2)
            } else {
                (2, 1)
            }
        }
        _ => (2, 2),
    };
    if hay_chicos(hora) { (adultos, chicos) } else { (adultos, 0) }
}

/// REQ-RUT-08: lugar de cada uno al caminar de a dos: (corrimiento lateral, fila). Si son
/// impares, el último va solo por el medio.
pub fn de_a_dos(n: usize) -> Vec<(f32, usize)> {
    (0..n)
        .map(|i| {
            let fila = i / 2;
            let lateral = if n % 2 == 1 && i == n - 1 {
                0.0
            } else if i % 2 == 0 {
                -LATERAL
            } else {
                LATERAL
            };
            (lateral, fila)
        })
        .collect()
}

/// REQ-RUT-08: la misma ruta corrida `lateral` metros hacia un costado (positivo: a la
/// izquierda de la marcha). En las esquinas se corre sobre la bisectriz, así dos personas
/// corridas a cada lado mantienen la distancia en toda la ruta.
pub fn correr_lateral(puntos: &[[f32; 2]], lateral: f32) -> Vec<[f32; 2]> {
    let normal = |a: [f32; 2], b: [f32; 2]| -> Option<[f32; 2]> {
        let (dx, dz) = (b[0] - a[0], b[1] - a[1]);
        let l = dx.hypot(dz);
        (l > 1e-4).then(|| [-dz / l, dx / l])
    };
    let n = puntos.len();
    (0..n)
        .map(|i| {
            let antes = if i > 0 { normal(puntos[i - 1], puntos[i]) } else { None };
            let despues = if i + 1 < n { normal(puntos[i], puntos[i + 1]) } else { None };
            let p = puntos[i];
            let offset = match (antes, despues) {
                (Some(a), Some(b)) => {
                    let s = [a[0] + b[0], a[1] + b[1]];
                    let l = s[0].hypot(s[1]);
                    if l < 1e-3 {
                        b
                    } else {
                        let m = [s[0] / l, s[1] / l];
                        // Inglete: en la esquina hay que correrse un poco más.
                        let c = (m[0] * a[0] + m[1] * a[1]).max(0.5);
                        [m[0] / c, m[1] / c]
                    }
                }
                (Some(a), None) | (None, Some(a)) => a,
                (None, None) => [0.0, 0.0],
            };
            [p[0] + offset[0] * lateral, p[1] + offset[1] * lateral]
        })
        .collect()
}

/// REQ-RUT-08: si `yo` (que camina hacia `dir`, largo 1) se adelantó más de `umbral` metros
/// de alguien del grupo que viene atrás, a quién tiene que esperar (el más rezagado).
pub fn a_quien_esperar(yo: [f32; 2], dir: [f32; 2], otros: &[[f32; 2]], umbral: f32) -> Option<usize> {
    otros
        .iter()
        .enumerate()
        .filter_map(|(i, o)| {
            let d = [yo[0] - o[0], yo[1] - o[1]];
            let atras = d[0] * dir[0] + d[1] * dir[1] > 0.0;
            let dist = d[0].hypot(d[1]);
            (atras && dist > umbral).then_some((i, dist))
        })
        .max_by(|a, b| a.1.total_cmp(&b.1))
        .map(|(i, _)| i)
}

/// REQ-RUT-07: radio de una ronda de `n` personas, con `SEPARACION_RONDA` entre vecinos.
pub fn radio_ronda(n: usize) -> f32 {
    let n = n.max(2) as f32;
    (SEPARACION_RONDA / (2.0 * (PI / n).sin())).max(0.45)
}

/// REQ-RUT-07: dónde se para cada uno de una ronda de `n` alrededor de `centro` (todos miran
/// al centro). `giro` (radianes) rota la ronda entera.
pub fn ronda(centro: [f32; 2], n: usize, giro: f32) -> Vec<[f32; 2]> {
    let r = radio_ronda(n);
    (0..n)
        .map(|i| {
            let a = giro + i as f32 * TAU / n as f32;
            [centro[0] + r * a.cos(), centro[1] + r * a.sin()]
        })
        .collect()
}

/// Dónde está la fuente (SPEC-008).
pub fn fuente() -> [f32; 2] {
    plaza::distribucion().iter().find(|p| p.tipo == TipoProp::Fuente).map(|p| [p.x, p.z]).unwrap_or([0.0, 0.0])
}

/// REQ-RUT-07: centros posibles para las rondas nocturnas: junto a cada farol de la plaza (los
/// cuatro del anillo de la fuente y los de los caminos), corridos del lado opuesto al camino.
pub fn lugares_ronda() -> Vec<[f32; 2]> {
    let medio = plaza::LADO_PLAZA / 2.0;
    let f = fuente();
    plaza::distribucion()
        .iter()
        .filter(|p| p.tipo == TipoProp::Farol && p.x.abs() < medio && p.z.abs() < medio)
        .map(|p| {
            let (x, z) = (p.x - f[0], p.z - f[1]);
            let dir = if (x.abs() - z.abs()).abs() < 0.5 {
                let l = x.hypot(z);
                [x / l, z / l]
            } else if z.abs() < x.abs() {
                [0.0, z.signum()]
            } else {
                [x.signum(), 0.0]
            };
            [p.x + dir[0] * CORRIMIENTO_FAROL, p.z + dir[1] * CORRIMIENTO_FAROL]
        })
        .collect()
}

/// REQ-RUT-06: dónde esperan los adultos junto a la fuente, mirando hacia ella. `angulo` en
/// radianes alrededor de la fuente.
pub fn espera_fuente(angulo: f32) -> [f32; 2] {
    let f = fuente();
    [f[0] + RADIO_ESPERA_FUENTE * angulo.cos(), f[1] + RADIO_ESPERA_FUENTE * angulo.sin()]
}

/// REQ-RUT-06: un ángulo para esperar junto a la fuente lejos de los caminos en cruz y de los
/// faroles del anillo (que están a 0°, 90°... y a 45°, 135°...).
pub fn angulo_espera(azar: &mut Azar) -> f32 {
    let cuarto = azar.entero(4) as f32 * PI / 2.0;
    let base = if azar.chance(0.5) { PI / 8.0 } else { 3.0 * PI / 8.0 };
    cuarto + base + azar.rango(-0.06, 0.06)
}

/// REQ-RUT-06: los puntos de `vueltas` vueltas alrededor de la fuente, empezando y terminando
/// en `angulo` (radianes), en sentido antihorario.
pub fn vueltas_fuente(angulo: f32, vueltas: usize) -> Vec<[f32; 2]> {
    let f = fuente();
    let por_vuelta = 16;
    (0..=vueltas * por_vuelta)
        .map(|i| {
            let a = angulo + i as f32 * TAU / por_vuelta as f32;
            [f[0] + RADIO_VUELTAS * a.cos(), f[1] + RADIO_VUELTAS * a.sin()]
        })
        .collect()
}

/// REQ-RUT-06: cuánto tardan los chicos en dar `vueltas` vueltas a `vel` m/s (s), más lo que
/// tardan en ir y volver de los adultos. Es lo que esperan los adultos.
pub fn tiempo_vueltas(vueltas: usize, vel: f32) -> f32 {
    let ida_y_vuelta = 2.0 * (RADIO_ESPERA_FUENTE - RADIO_VUELTAS) + 2.0;
    (vueltas as f32 * TAU * RADIO_VUELTAS + ida_y_vuelta) / vel.max(0.1) + 2.0
}

/// REQ-RUT-05, REQ-RUT-06, REQ-RUT-09: dónde se sienta cada uno de un grupo de `n` en el banco
/// cuyo asiento está en `asiento` y mira hacia `rot_y` (grados): uno al lado del otro, a lo
/// largo del banco. Entran `LUGARES_BANCO`; el resto queda parado al costado del banco.
/// Devuelve (posición, sentado).
pub fn lugares_banco(asiento: [f32; 2], rot_y: f32, n: usize) -> Vec<([f32; 2], bool)> {
    let (s, c) = rot_y.to_radians().sin_cos();
    let a_lo_largo = [c, -s];
    let adelante = [s, c];
    let sentados = n.min(LUGARES_BANCO);
    let mut v: Vec<([f32; 2], bool)> = (0..sentados)
        .map(|k| {
            let d = (k as f32 - (sentados as f32 - 1.0) / 2.0) * SEPARACION_BANCO;
            ([asiento[0] + a_lo_largo[0] * d, asiento[1] + a_lo_largo[1] * d], true)
        })
        .collect();
    for k in sentados..n {
        // Parados delante del banco, a un costado.
        let d = 1.1 + (k - sentados) as f32 * 0.7;
        let p =
            [asiento[0] + a_lo_largo[0] * d + adelante[0] * 0.5, asiento[1] + a_lo_largo[1] * d + adelante[1] * 0.5];
        v.push((p, false));
    }
    v
}

/// REQ-RUT-06: velocidad de los chicos cuando caminan con la familia: si se quedaron atrás
/// (más de `UMBRAL_FAMILIA` del adulto más cercano), apuran el paso.
pub fn vel_chico(vel_adultos: f32, dist_adulto: f32) -> f32 {
    if dist_adulto > UMBRAL_FAMILIA * 0.8 { vel_adultos * 1.35 } else { vel_adultos }
}

/// REQ-AMB-13: ¿todos los puntos están a más de la distancia personal entre sí?
pub fn sin_chocarse(puntos: &[[f32; 2]]) -> bool {
    puntos
        .iter()
        .enumerate()
        .all(|(i, a)| puntos.iter().skip(i + 1).all(|b| (a[0] - b[0]).hypot(a[1] - b[1]) >= DISTANCIA_PERSONAL))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::peatones::Plan;
    use crate::rutinas::tests::plaza_real;

    fn dist(a: [f32; 2], b: [f32; 2]) -> f32 {
        (a[0] - b[0]).hypot(a[1] - b[1])
    }

    #[test]
    fn req_rut_05_oficinistas_rapidos_de_a_1_a_3_y_se_van_a_las_14_30() {
        let a = plaza_real().agenda;
        let mut azar = Azar::new(3);
        for _ in 0..50 {
            let v = a.velocidad(&mut azar, Perfil::Oficinista);
            assert!((1.4..=1.7).contains(&v), "{v}");
            let g = a.tamano_grupo(&mut azar, Perfil::Oficinista);
            assert!((1..=3).contains(&g), "{g}");
            let plan = a.sortear_plan(&mut azar, Perfil::Oficinista);
            assert!(matches!(plan, Plan::Sentarse | Plan::Pasear), "se sientan o cruzan: {plan:?}");
        }
        assert!(!oficinistas_se_van(13.0));
        assert!(!oficinistas_se_van(14.49));
        assert!(oficinistas_se_van(14.5));
        assert!(oficinistas_se_van(14.75));
        assert!(arma_grupos(Perfil::Oficinista));
    }

    #[test]
    fn req_rut_05_sentados_juntos_en_el_banco() {
        // Banco que mira a +Z (rot 0): se sientan a lo largo de X, a 0,6 m.
        let l = lugares_banco([7.0, -2.48], 0.0, 3);
        assert_eq!(l.len(), 3);
        assert!(l.iter().all(|(_, sentado)| *sentado));
        assert!(l.iter().all(|(p, _)| (p[1] + 2.48).abs() < 1e-4 && (p[0] - 7.0).abs() <= 0.63));
        assert!(sin_chocarse(&l.iter().map(|x| x.0).collect::<Vec<_>>()));
        // Una familia de 4: tres sentados y uno parado al lado, sin chocarse.
        let l = lugares_banco([2.48, 7.0], -90.0, 4);
        assert_eq!(l.iter().filter(|x| x.1).count(), 3);
        assert!(sin_chocarse(&l.iter().map(|x| x.0).collect::<Vec<_>>()));
    }

    #[test]
    fn req_rut_06_familia_de_1_a_2_adultos_y_1_a_2_chicos() {
        let mut azar = Azar::new(9);
        let a = plaza_real().agenda;
        for _ in 0..100 {
            let t = a.tamano_grupo(&mut azar, Perfil::Familia);
            assert!((2..=4).contains(&t), "{t}");
            let (ad, ch) = composicion_familia(&mut azar, t, 17.0);
            assert_eq!(ad + ch, t);
            assert!((1..=2).contains(&ad) && (1..=2).contains(&ch), "{ad} adultos, {ch} chicos");
        }
        const { assert!(ALTURA_CHICOS[0] >= 1.0 && ALTURA_CHICOS[1] <= 1.3) };
        // Un chico atrasado apura el paso; uno al lado del adulto va a su ritmo.
        assert!(vel_chico(1.0, 1.8) > 1.0);
        assert_eq!(vel_chico(1.0, 0.8), 1.0);
        // Con el umbral de la familia nadie queda a más de 2 m.
        const { assert!(UMBRAL_FAMILIA < DISTANCIA_CHICOS) };
    }

    #[test]
    fn req_rut_06_vueltas_alrededor_de_la_fuente() {
        let f = fuente();
        for vueltas in VUELTAS[0]..=VUELTAS[1] {
            let p = vueltas_fuente(0.4, vueltas);
            assert_eq!(p.len(), vueltas * 16 + 1);
            // Por fuera del borde (3 m) y por dentro de donde esperan los adultos.
            assert!(p.iter().all(|q| (3.3..RADIO_ESPERA_FUENTE).contains(&dist(*q, f))));
            // Empieza y termina en el mismo lugar.
            assert!(dist(p[0], *p.last().unwrap()) < 1e-3);
            // Recorre vueltas × 2πr.
            let largo: f32 = p.windows(2).map(|w| dist(w[0], w[1])).sum();
            let esperado = vueltas as f32 * TAU * RADIO_VUELTAS;
            assert!((largo - esperado).abs() < esperado * 0.03, "{largo} vs {esperado}");
        }
        // Los chicos corren más rápido que los adultos de la familia.
        let a = plaza_real().agenda;
        assert!(VEL_CORRER[0] > a.def(Perfil::Familia).velocidad[1]);
        // Los adultos esperan lo que tardan los chicos.
        assert!(tiempo_vueltas(3, 2.0) > tiempo_vueltas(1, 2.0));
        assert!(tiempo_vueltas(1, 2.0) > TAU * RADIO_VUELTAS / 2.0);
    }

    #[test]
    fn req_rut_06_los_adultos_esperan_lejos_de_los_caminos_y_faroles() {
        let mut azar = Azar::new(2);
        let faroles: Vec<[f32; 2]> =
            plaza::distribucion().iter().filter(|p| p.tipo != TipoProp::Arbol).map(|p| [p.x, p.z]).collect();
        for _ in 0..100 {
            let p = espera_fuente(angulo_espera(&mut azar));
            assert!((dist(p, fuente()) - RADIO_ESPERA_FUENTE).abs() < 1e-3);
            assert!(p[0].abs() > 1.5 && p[1].abs() > 1.5, "en el camino: {p:?}");
            for f in &faroles[1..] {
                assert!(dist(p, *f) > 1.0, "{p:?} pegado a {f:?}");
            }
        }
    }

    #[test]
    fn req_rut_11_despues_de_las_21_no_hay_chicos() {
        assert!(hay_chicos(17.0));
        assert!(hay_chicos(20.9));
        assert!(!hay_chicos(21.0));
        assert!(!hay_chicos(23.5));
        assert!(!hay_chicos(2.0));
        assert!(familias_se_van(21.5));
        assert!(!familias_se_van(18.0));
        // Una familia que llega tarde (por un evento) viene sin chicos.
        let mut azar = Azar::new(1);
        for t in 2..=4 {
            let (ad, ch) = composicion_familia(&mut azar, t, 22.0);
            assert_eq!(ch, 0);
            assert!(ad >= 1);
        }
    }

    #[test]
    fn req_rut_07_ronda_mirando_al_centro_sin_chocarse() {
        for n in 3..=4 {
            let c = [10.0, 3.1];
            let r = ronda(c, n, 0.3);
            assert_eq!(r.len(), n);
            assert!(sin_chocarse(&r), "{r:?}");
            // Todos a la misma distancia del centro, y cerca (es una ronda, no un círculo grande).
            let d0 = dist(r[0], c);
            assert!(r.iter().all(|p| (dist(*p, c) - d0).abs() < 1e-4));
            assert!(d0 < 0.8);
        }
        let a = plaza_real().agenda;
        let mut azar = Azar::new(6);
        for _ in 0..30 {
            let g = a.tamano_grupo(&mut azar, Perfil::Nocturno);
            assert!((3..=4).contains(&g));
            let s = a.quieto(&mut azar, Perfil::Nocturno);
            assert!((30.0..=90.0).contains(&s), "30–90 min de juego: {s}");
        }
    }

    #[test]
    fn req_rut_07_rondas_cerca_de_la_fuente_o_de_un_farol() {
        let lugares = lugares_ronda();
        assert!(lugares.len() >= 8);
        let props = plaza::distribucion();
        let faroles: Vec<[f32; 2]> = props.iter().filter(|p| p.tipo == TipoProp::Farol).map(|p| [p.x, p.z]).collect();
        let r = radio_ronda(4);
        for c in &lugares {
            let al_farol = faroles.iter().map(|f| dist(*c, *f)).fold(f32::INFINITY, f32::min);
            assert!(al_farol < 2.0 && al_farol > r + 0.3, "{c:?} a {al_farol} m del farol");
            // Ninguno de la ronda queda sobre los caminos en cruz ni sobre el anillo de la fuente.
            for p in ronda(*c, 4, 0.0) {
                assert!(p[0].abs() > 1.5 + 0.2 && p[1].abs() > 1.5 + 0.2, "{p:?} en el camino");
                assert!(dist(p, fuente()) > 4.5 + 0.6, "{p:?} sobre el anillo");
                for q in props.iter().filter(|q| q.tipo != TipoProp::Fuente) {
                    assert!(dist(p, [q.x, q.z]) > 0.5, "{p:?} encima de {q:?}");
                }
            }
        }
    }

    #[test]
    fn req_rut_08_de_a_dos_por_la_misma_ruta() {
        assert_eq!(de_a_dos(2), vec![(-LATERAL, 0), (LATERAL, 0)]);
        assert_eq!(de_a_dos(3), vec![(-LATERAL, 0), (LATERAL, 0), (0.0, 1)]);
        assert_eq!(de_a_dos(4).iter().filter(|x| x.1 == 1).count(), 2);
        // Una ruta con esquina: los dos corridos quedan siempre a más de 0,6 m (REQ-AMB-13).
        let ruta = [[0.0, 0.0], [10.0, 0.0], [10.0, 8.0], [3.0, 15.0]];
        let a = correr_lateral(&ruta, -LATERAL);
        let b = correr_lateral(&ruta, LATERAL);
        assert_eq!(a.len(), ruta.len());
        for i in 0..ruta.len() {
            let d = dist(a[i], b[i]);
            assert!((DISTANCIA_PERSONAL..1.5).contains(&d), "punto {i}: {d}");
        }
        // En los tramos rectos, corrido exactamente LATERAL.
        assert!((a[0][1].abs() - LATERAL).abs() < 1e-4);
        // Sin corrimiento, la misma ruta.
        assert_eq!(correr_lateral(&ruta, 0.0), ruta.to_vec());
    }

    #[test]
    fn req_rut_08_si_uno_se_adelanta_mas_de_3_m_espera() {
        let dir = [1.0, 0.0];
        // El de atrás a 2 m: sigue.
        assert_eq!(a_quien_esperar([5.0, 0.0], dir, &[[3.0, 0.4]], UMBRAL_GRUPO), None);
        // A 3,5 m: espera al más rezagado.
        assert_eq!(a_quien_esperar([5.0, 0.0], dir, &[[3.0, 0.4], [1.5, 0.0]], UMBRAL_GRUPO), Some(1));
        // El que está adelante no hace esperar a nadie (el que espera es el de adelante).
        assert_eq!(a_quien_esperar([1.0, 0.0], dir, &[[5.0, 0.0]], UMBRAL_GRUPO), None);
    }

    #[test]
    fn req_rut_09_los_demas_perfiles() {
        let a = plaza_real().agenda;
        let mut azar = Azar::new(8);
        for _ in 0..40 {
            assert_eq!(a.sortear_plan(&mut azar, Perfil::Corredor), Plan::Trotar);
            assert_eq!(a.sortear_plan(&mut azar, Perfil::Paseador), Plan::PasearPerro);
            assert_eq!(a.sortear_plan(&mut azar, Perfil::AlTrabajo), Plan::Pasear);
            assert_eq!(a.sortear_plan(&mut azar, Perfil::Trasnochado), Plan::Pasear);
            let v = a.velocidad(&mut azar, Perfil::Jubilado);
            assert!((0.8..=1.1).contains(&v), "jubilado lento: {v}");
            let s = a.quieto(&mut azar, Perfil::Jubilado);
            assert!((40.0..=120.0).contains(&s), "jubilado sentado: {s}");
            assert_eq!(a.tamano_grupo(&mut azar, Perfil::Pareja), 2);
            let g = a.tamano_grupo(&mut azar, Perfil::Adolescente);
            assert!((2..=3).contains(&g));
            assert_eq!(a.tamano_grupo(&mut azar, Perfil::Trasnochado), 1);
            assert_eq!(a.tamano_grupo(&mut azar, Perfil::AlTrabajo), 1);
        }
        // Pareja y adolescentes pasean, se sientan y (los adolescentes) charlan.
        let planes = |p| a.def(p).planes.iter().map(|x| x.0).collect::<Vec<_>>();
        assert!(planes(Perfil::Pareja).contains(&Plan::Sentarse) && planes(Perfil::Pareja).contains(&Plan::Pasear));
        assert!(planes(Perfil::Adolescente).contains(&Plan::Charlar));
        // Quién se arma acá y quién como paseante común.
        for p in [Perfil::Pareja, Perfil::Adolescente, Perfil::AlTrabajo, Perfil::Nocturno, Perfil::Familia] {
            assert!(arma_grupos(p), "{p:?}");
        }
        for p in [Perfil::Corredor, Perfil::Paseador, Perfil::Jubilado, Perfil::Trasnochado, Perfil::Paseante] {
            assert!(!arma_grupos(p), "{p:?}");
        }
    }
}
