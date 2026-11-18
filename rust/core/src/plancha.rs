//! SPEC-014 · Plancha (fuente de calor).

use crate::TEMP_AMBIENTE;

/// Temperatura máxima de la plancha encendida (°C). REQ-PLA-02
pub const TEMP_MAX: f32 = 220.0;
/// Subida por segundo encendida (°C/s). REQ-PLA-02
pub const SUBIDA_POR_SEGUNDO: f32 = 4.0;
/// Qué tan rápido se enfría apagada (1/s). REQ-PLA-02
pub const K_ENFRIADO: f32 = 0.004;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Plancha {
    pub temp: f32,
    pub encendida: bool,
}

impl Default for Plancha {
    fn default() -> Self {
        Self { temp: TEMP_AMBIENTE, encendida: false }
    }
}

impl Plancha {
    /// REQ-PLA-01
    pub fn alternar(&mut self) {
        self.encendida = !self.encendida;
    }

    /// REQ-PLA-02
    pub fn paso(&mut self, dt: f32) {
        if self.encendida {
            self.temp = (self.temp + SUBIDA_POR_SEGUNDO * dt).min(TEMP_MAX);
        } else {
            self.temp += (TEMP_AMBIENTE - self.temp) * (K_ENFRIADO * dt).min(1.0);
        }
    }
}

/// REQ-PLA-03: temperaturas de entorno `(lado de abajo, lado de arriba)` de un alimento.
/// Solo el lado que toca la plancha toma su temperatura; el de arriba toma la del ambiente.
pub fn entorno_por_lados(plancha: Option<f32>) -> (f32, f32) {
    (plancha.unwrap_or(TEMP_AMBIENTE), TEMP_AMBIENTE)
}

/// REQ-PLA-07: qué lado (0 o 1) mira hacia abajo, según cuánto apunta hacia arriba el eje
/// del alimento (componente vertical del eje Y del objeto). El lado 0 es el de abajo en reposo.
pub fn lado_abajo(eje_y_vertical: f32) -> usize {
    if eje_y_vertical >= 0.0 { 0 } else { 1 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_pla_01_se_enciende_y_apaga() {
        let mut p = Plancha::default();
        assert!(!p.encendida);
        p.alternar();
        assert!(p.encendida);
        p.alternar();
        assert!(!p.encendida);
    }

    #[test]
    fn req_pla_02_sube_4_por_segundo_hasta_220() {
        let mut p = Plancha::default();
        p.alternar();
        p.paso(10.0);
        assert!((p.temp - 60.0).abs() < 1e-4);
        for _ in 0..100 {
            p.paso(1.0);
        }
        assert_eq!(p.temp, 220.0);
    }

    #[test]
    fn req_pla_02_apagada_se_enfria_hacia_el_ambiente() {
        let mut p = Plancha { temp: 220.0, encendida: false };
        p.paso(1.0);
        assert!(p.temp < 220.0 && p.temp > 215.0);
        for _ in 0..10_000 {
            p.paso(1.0);
        }
        assert!((p.temp - 20.0).abs() < 0.5);
    }

    #[test]
    fn req_pla_03_solo_el_lado_de_abajo_toma_la_temperatura() {
        assert_eq!(entorno_por_lados(Some(200.0)), (200.0, 20.0));
        assert_eq!(entorno_por_lados(None), (20.0, 20.0));
    }

    #[test]
    fn req_pla_07_el_lado_de_abajo_sale_de_la_orientacion() {
        assert_eq!(lado_abajo(1.0), 0);
        assert_eq!(lado_abajo(-1.0), 1);
    }
}
