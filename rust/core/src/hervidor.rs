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

#[cfg(test)]
mod tests {
    use super::*;

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
