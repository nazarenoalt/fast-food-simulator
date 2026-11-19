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

/// Espacio libre entre alimentos volcados y contra las paredes (m). REQ-COC-10
const HOLGURA_VOLCADO: f32 = 0.01;

/// REQ-COC-10: dónde va cada uno de `n` alimentos volcados en una cuba de `interior`
/// (ancho X, alto Y, fondo Z): acostados a lo largo de X, en filas a lo ancho de la cuba y en
/// capas si no entran. Posiciones del centro relativas al centro del piso de la cuba.
pub fn acomodar_volcado(n: u32, interior: [f32; 3], largo: f32, grosor: f32) -> Vec<[f32; 3]> {
    let [w, _, d] = interior;
    let paso_x = largo + HOLGURA_VOLCADO;
    let paso_z = grosor + HOLGURA_VOLCADO;
    let cols = ((w - HOLGURA_VOLCADO) / paso_x).floor().max(1.0) as u32;
    let filas = ((d - HOLGURA_VOLCADO) / paso_z).floor().max(1.0) as u32;
    let por_capa = cols * filas;
    (0..n)
        .map(|i| {
            let capa = i / por_capa;
            let resto = i % por_capa;
            let (fila, col) = (resto / cols, resto % cols);
            [
                (col as f32 - (cols as f32 - 1.0) / 2.0) * paso_x,
                grosor / 2.0 + HOLGURA_VOLCADO + capa as f32 * (grosor + HOLGURA_VOLCADO),
                (fila as f32 - (filas as f32 - 1.0) / 2.0) * paso_z,
            ]
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_coc_10_doce_salchichas_entran_acostadas_en_el_hervidor_chico() {
        let interior = [0.36, 0.18, 0.26];
        let p = acomodar_volcado(12, interior, 0.15 + 0.022, 0.022);
        assert_eq!(p.len(), 12);
        for [x, y, z] in &p {
            assert!(x.abs() + 0.086 <= 0.18 && z.abs() + 0.011 <= 0.13, "adentro de la cuba: {x} {z}");
            assert!(*y < 0.18 * 0.7, "bajo el agua: {y}");
        }
        for (i, a) in p.iter().enumerate() {
            for b in &p[i + 1..] {
                let lejos = (a[0] - b[0]).abs() >= 0.17 || (a[2] - b[2]).abs() >= 0.022 || (a[1] - b[1]).abs() >= 0.022;
                assert!(lejos, "no se pisan: {a:?} {b:?}");
            }
        }
    }

    #[test]
    fn req_coc_10_si_no_entran_van_en_capas() {
        let p = acomodar_volcado(5, [0.2, 0.2, 0.05], 0.15, 0.02);
        // Entra 1 columna × 2 filas por capa: la quinta va en la tercera capa.
        assert!(p[4][1] > p[2][1] && p[2][1] > p[0][1]);
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
