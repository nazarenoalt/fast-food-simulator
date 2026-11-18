//! SPEC-006 · Puerta del carrito: estado y animación (sin Godot).

/// Segundos que tarda en abrirse o cerrarse del todo. REQ-CAR-12
pub const SEGUNDOS_GIRO: f32 = 1.0;

#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct EstadoPuerta {
    /// Hacia dónde va: `true` = abrirse.
    pub abierta: bool,
    /// 0 = cerrada del todo, 1 = abierta del todo.
    pub progreso: f32,
}

impl EstadoPuerta {
    /// REQ-CAR-12: cambia hacia dónde va (desde donde esté, sin saltos).
    pub fn alternar(&mut self) {
        self.abierta = !self.abierta;
    }

    /// REQ-CAR-12
    pub fn paso(&mut self, dt: f32) {
        let d = dt / SEGUNDOS_GIRO;
        self.progreso = if self.abierta { (self.progreso + d).min(1.0) } else { (self.progreso - d).max(0.0) };
    }

    pub fn en_movimiento(&self) -> bool {
        if self.abierta { self.progreso < 1.0 } else { self.progreso > 0.0 }
    }

    /// Ángulo actual (grados) para una puerta que abre `apertura` grados; arranca y frena suave.
    pub fn angulo(&self, apertura: f32) -> f32 {
        let t = self.progreso;
        apertura * t * t * (3.0 - 2.0 * t)
    }

    /// Texto del cartel de acción.
    pub fn cartel(&self) -> &'static str {
        if self.abierta { "[E] Cerrar puerta" } else { "[E] Abrir puerta" }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_car_12_arranca_cerrada() {
        let p = EstadoPuerta::default();
        assert!(!p.abierta && p.progreso == 0.0 && p.angulo(100.0) == 0.0);
    }

    #[test]
    fn req_car_12_se_abre_en_un_segundo_hasta_el_angulo() {
        let mut p = EstadoPuerta::default();
        p.alternar();
        p.paso(0.5);
        assert!(p.en_movimiento());
        let medio = p.angulo(100.0);
        assert!((medio - 50.0).abs() < 1e-3, "a mitad de camino, mitad del ángulo");
        p.paso(0.6);
        assert_eq!(p.progreso, 1.0);
        assert!((p.angulo(100.0) - 100.0).abs() < 1e-3);
        assert!(!p.en_movimiento(), "abierta y quieta");
    }

    #[test]
    fn req_car_12_se_cierra_y_conserva_el_estado() {
        let mut p = EstadoPuerta::default();
        p.alternar();
        p.paso(2.0);
        p.paso(5.0);
        assert_eq!(p.progreso, 1.0, "sigue abierta mientras nadie la cierre");
        p.alternar();
        assert_eq!(p.cartel(), "[E] Abrir puerta");
        p.paso(2.0);
        assert_eq!(p.progreso, 0.0);
    }

    #[test]
    fn req_car_12_cambiar_de_idea_a_mitad_de_camino_no_salta() {
        let mut p = EstadoPuerta::default();
        p.alternar();
        p.paso(0.4);
        let antes = p.angulo(90.0);
        p.alternar();
        assert_eq!(p.angulo(90.0), antes);
        p.paso(0.1);
        assert!(p.angulo(90.0) < antes);
    }
}
