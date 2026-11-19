//! TASK-0505 · SPEC-019: feria y partido. Submódulo de `gente`: ve los campos de `Gente`
//! (`self.dia`, `self.hora` y `self.modificador` ya están al día en cada cuadro).

use carrito_core::peatones::Apariencia;
use carrito_core::rutinas::Perfil;

use super::Gente;

/// Estado propio de esta tarea (aviso del día, puestos, vendedores...).
#[derive(Default)]
pub(super) struct Estado {}

impl Gente {
    /// Cada cuadro: aviso del día, puestos de la feria, festejo...
    pub(super) fn cuadro_eventos(&mut self, _dt: f32) {}

    /// REQ-EVE-07: retoca la apariencia de alguien que llega (camiseta).
    pub(super) fn retocar_por_evento(&mut self, _ap: &mut Apariencia, _perfil: Perfil) {}
}
