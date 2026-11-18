//! SPEC-006 · Puerta de una base de carrito: se abre y se cierra con E (REQ-CAR-13).
//! Sin Godot: el nodo (`rust/game/src/puerta.rs`) solo gira la pieza con este ángulo.

/// Segundos que tarda en abrirse o cerrarse del todo. REQ-CAR-13
pub const DURACION: f32 = 0.5;

/// Estado de la puerta: hacia dónde va y en qué ángulo está (grados, giro en Y; positivo
/// abre hacia afuera).
#[derive(Debug, Clone, PartialEq)]
pub struct Puerta {
    /// Ángulo de apertura completa (`puerta` del `.ron` de la base). REQ-CAR-11
    pub apertura: f32,
    abierta: bool,
    angulo: f32,
}

impl Puerta {
    /// REQ-CAR-11: arranca abierta del todo o cerrada (`puerta_abierta`).
    pub fn nueva(apertura: f32, abierta: bool) -> Self {
        Self { apertura, abierta, angulo: if abierta { apertura } else { 0.0 } }
    }

    pub fn abierta(&self) -> bool {
        self.abierta
    }

    pub fn angulo(&self) -> f32 {
        self.angulo
    }

    /// REQ-CAR-13: E la abre si está cerrada (o cerrándose) y la cierra si está abierta.
    pub fn alternar(&mut self) {
        self.abierta = !self.abierta;
    }

    /// Avanza la animación: gira hacia el ángulo final a velocidad constante (todo el recorrido
    /// en DURACION segundos). Devuelve si se movió.
    pub fn paso(&mut self, dt: f32) -> bool {
        let objetivo = if self.abierta { self.apertura } else { 0.0 };
        let falta = objetivo - self.angulo;
        if falta == 0.0 {
            return false;
        }
        let max = self.apertura.abs() / DURACION * dt;
        self.angulo = if falta.abs() <= max { objetivo } else { self.angulo + max * falta.signum() };
        true
    }

    /// Texto del cartel al mirarla. REQ-CAR-13
    pub fn cartel(&self) -> &'static str {
        if self.abierta { "[E] Cerrar puerta" } else { "[E] Abrir puerta" }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_car_11_arranca_abierta_o_cerrada() {
        let k = Puerta::nueva(100.0, true);
        assert!(k.abierta() && k.angulo() == 100.0);
        let g = Puerta::nueva(105.0, false);
        assert!(!g.abierta() && g.angulo() == 0.0);
    }

    #[test]
    fn req_car_13_e_abre_y_cierra_en_medio_segundo() {
        let mut p = Puerta::nueva(105.0, false);
        p.alternar();
        assert!(p.abierta());
        // A la mitad del tiempo, a mitad de camino.
        for _ in 0..15 {
            p.paso(1.0 / 60.0);
        }
        assert!((p.angulo() - 52.5).abs() < 0.01, "{}", p.angulo());
        for _ in 0..15 {
            p.paso(1.0 / 60.0);
        }
        assert!((p.angulo() - 105.0).abs() < 1e-3);
        assert!(!p.paso(1.0 / 60.0), "llegó: no se mueve más");
        assert_eq!(p.cartel(), "[E] Cerrar puerta");
        // Otra vez E: vuelve a 0.
        p.alternar();
        for _ in 0..31 {
            p.paso(1.0 / 60.0);
        }
        assert_eq!(p.angulo(), 0.0);
        assert_eq!(p.cartel(), "[E] Abrir puerta");
    }

    #[test]
    fn req_car_13_suena_la_puerta_del_carrito_no_la_de_la_heladera() {
        let ruta = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data/sonidos.ron");
        let sonidos = crate::sonido::cargar(&std::fs::read_to_string(ruta).unwrap()).unwrap();
        let def = |id: &str| sonidos.iter().find(|s| s.id == id).unwrap_or_else(|| panic!("falta {id}"));
        let carrito = def(crate::sonido::ids::CARRITO_PUERTA);
        let heladera = def(crate::sonido::ids::HELADERA_PUERTA);
        assert!(carrito.espacial, "sale de la puerta");
        assert!(
            carrito.archivos.iter().all(|a| !heladera.archivos.contains(a)),
            "no reusa los archivos de la heladera"
        );
    }

    #[test]
    fn req_car_13_bases_con_puerta() {
        let cat = crate::datos::tests::catalogo_real();
        let base = |id: &str| cat.bases.iter().find(|b| b.id == id).unwrap();
        let g = base("carro_grande");
        assert!(g.puerta.is_some_and(|a| a > 90.0 && a <= 120.0) && !g.puerta_abierta, "el carro grande: cerrada");
        assert!(base("carro_kiosco").puerta_abierta, "el kiosco arranca abierto (CA-CAR-03)");
    }

    #[test]
    fn req_car_13_cambiar_de_idea_a_mitad_de_camino() {
        let mut p = Puerta::nueva(100.0, false);
        p.alternar();
        p.paso(0.1);
        let a = p.angulo();
        p.alternar();
        p.paso(0.05);
        assert!(p.angulo() < a && p.angulo() > 0.0, "vuelve desde donde estaba");
    }
}
