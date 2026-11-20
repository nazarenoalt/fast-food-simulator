//! SPEC-003 · Agua del hervidor (fuente de calor).

use crate::TEMP_AMBIENTE;

/// Temperatura máxima del agua encendida (°C).
pub const TEMP_MAX_AGUA: f32 = 95.0;
/// Subida por segundo encendido (°C/s).
pub const SUBIDA_POR_SEGUNDO: f32 = 1.5;
/// Qué tan rápido se enfría apagado (1/s).
pub const K_ENFRIADO: f32 = 0.004;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct AguaHervidor {
    pub temp: f32,
    pub encendido: bool,
}

impl Default for AguaHervidor {
    fn default() -> Self {
        // REQ-COC-07: arranca a temperatura ambiente, apagado.
        Self { temp: TEMP_AMBIENTE, encendido: false }
    }
}

impl AguaHervidor {
    /// REQ-COC-09
    pub fn alternar(&mut self) {
        self.encendido = !self.encendido;
    }

    /// REQ-COC-07
    pub fn paso(&mut self, dt: f32) {
        if self.encendido {
            self.temp = (self.temp + SUBIDA_POR_SEGUNDO * dt).min(TEMP_MAX_AGUA);
        } else {
            self.temp += (TEMP_AMBIENTE - self.temp) * (K_ENFRIADO * dt).min(1.0);
        }
    }
}

/// Espacio libre entre alimentos flotando y contra las paredes (m). REQ-COC-10
const HOLGURA: f32 = 0.01;
/// Altura del agua, como parte del alto interior de la cuba. REQ-COC-08
pub const NIVEL_AGUA: f32 = 0.7;

/// REQ-COC-08: altura de la superficie del agua sobre el piso de una cuba de `interior`.
pub fn altura_superficie(interior: [f32; 3]) -> f32 {
    interior[1] * NIVEL_AGUA
}

/// REQ-COC-08, REQ-COC-10 (TASK-0262): los lugares donde flota algo de `largo` × `grosor` en
/// una cuba de `interior` (ancho X, alto Y, fondo Z): acostado a lo largo de X, en filas a lo
/// ancho de la cuba, en **una sola capa** con el centro a la altura de la superficie.
/// Posiciones del centro relativas al centro del piso de la cuba, en orden de llenado.
pub fn lugares_superficie(interior: [f32; 3], largo: f32, grosor: f32) -> Vec<[f32; 3]> {
    let [w, _, d] = interior;
    let paso_x = largo + HOLGURA;
    let paso_z = grosor + HOLGURA;
    let cols = ((w - HOLGURA) / paso_x).floor().max(0.0) as u32;
    let filas = ((d - HOLGURA) / paso_z).floor().max(0.0) as u32;
    let y = altura_superficie(interior);
    (0..cols * filas)
        .map(|i| {
            let (fila, col) = (i / cols, i % cols);
            [(col as f32 - (cols as f32 - 1.0) / 2.0) * paso_x, y, (fila as f32 - (filas as f32 - 1.0) / 2.0) * paso_z]
        })
        .collect()
}

/// REQ-COC-08: cuántos de `largo` × `grosor` entran flotando (una sola capa).
pub fn capacidad(interior: [f32; 3], largo: f32, grosor: f32) -> usize {
    lugares_superficie(interior, largo, grosor).len()
}

/// REQ-COC-08, REQ-COC-10: los lugares de la superficie que quedan libres, sabiendo dónde
/// flota lo que ya está en el agua (`ocupados`, posiciones relativas al centro del piso; solo
/// cuentan X y Z). Cada cosa en el agua ocupa el lugar libre más cercano, aunque se haya
/// corrido un poco. Vacío = hervidor lleno.
pub fn lugares_libres(interior: [f32; 3], largo: f32, grosor: f32, ocupados: &[[f32; 3]]) -> Vec<[f32; 3]> {
    let mut libres = lugares_superficie(interior, largo, grosor);
    for o in ocupados {
        let distancia = |l: &[f32; 3]| (l[0] - o[0]).powi(2) + (l[2] - o[2]).powi(2);
        let cercano =
            libres.iter().enumerate().min_by(|(_, a), (_, b)| distancia(a).total_cmp(&distancia(b))).map(|(i, _)| i);
        match cercano {
            Some(i) => {
                libres.remove(i);
            }
            None => break,
        }
    }
    libres
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Hervidor chico (godot/data/accesorios.ron) y salchicha (cápsula de 0,15 × 0,022).
    const CHICO: [f32; 3] = [0.36, 0.18, 0.26];
    const LARGO: f32 = 0.15;
    const GROSOR: f32 = 0.022;

    #[test]
    fn req_coc_08_entran_14_salchichas_en_una_capa_en_el_hervidor_chico() {
        assert_eq!(capacidad(CHICO, LARGO, GROSOR), 14);
        let p = lugares_superficie(CHICO, LARGO, GROSOR);
        for [x, y, z] in &p {
            assert!(x.abs() + LARGO / 2.0 <= 0.18 && z.abs() + GROSOR / 2.0 <= 0.13, "adentro de la cuba: {x} {z}");
            // Una sola capa, con el centro en la superficie (no en el fondo).
            assert!((y - 0.18 * NIVEL_AGUA).abs() < 1e-6, "en la superficie: {y}");
        }
        for (i, a) in p.iter().enumerate() {
            for b in &p[i + 1..] {
                let lejos = (a[0] - b[0]).abs() >= LARGO || (a[2] - b[2]).abs() >= GROSOR;
                assert!(lejos, "no se pisan: {a:?} {b:?}");
            }
        }
    }

    #[test]
    fn req_coc_10_lugares_libres_descuenta_los_ocupados() {
        let todos = lugares_superficie(CHICO, LARGO, GROSOR);
        assert_eq!(lugares_libres(CHICO, LARGO, GROSOR, &[]), todos);
        // Una salchicha corrida un poco del primer lugar ocupa ese lugar.
        let corrida = [todos[0][0] + 0.01, 0.0, todos[0][2] - 0.004];
        let libres = lugares_libres(CHICO, LARGO, GROSOR, &[corrida]);
        assert_eq!(libres.len(), 13);
        assert!(!libres.contains(&todos[0]));
        // Con las 14 adentro, está lleno (vacío); con más, también.
        assert!(lugares_libres(CHICO, LARGO, GROSOR, &todos).is_empty());
        let mut de_mas = todos.clone();
        de_mas.push([0.0; 3]);
        assert!(lugares_libres(CHICO, LARGO, GROSOR, &de_mas).is_empty());
    }

    #[test]
    fn req_coc_08_si_no_entra_ni_una_no_hay_lugares() {
        assert_eq!(capacidad([0.1, 0.1, 0.1], LARGO, GROSOR), 0);
        assert!(lugares_libres([0.1, 0.1, 0.1], LARGO, GROSOR, &[]).is_empty());
    }

    #[test]
    fn req_coc_07_sube_1_5_por_segundo_hasta_95() {
        let mut a = AguaHervidor::default();
        assert_eq!(a.temp, 20.0);
        a.alternar();
        a.paso(10.0);
        assert!((a.temp - 35.0).abs() < 1e-4);
        for _ in 0..100 {
            a.paso(1.0);
        }
        assert_eq!(a.temp, 95.0);
    }

    #[test]
    fn req_coc_07_apagado_se_enfria_gradualmente() {
        let mut a = AguaHervidor { temp: 95.0, encendido: false };
        a.paso(1.0);
        assert!(a.temp < 95.0 && a.temp > 90.0);
        for _ in 0..10_000 {
            a.paso(1.0);
        }
        assert!((a.temp - 20.0).abs() < 0.5);
    }

    #[test]
    fn req_coc_09_alternar() {
        let mut a = AguaHervidor::default();
        a.alternar();
        assert!(a.encendido);
        a.alternar();
        assert!(!a.encendido);
    }
}
