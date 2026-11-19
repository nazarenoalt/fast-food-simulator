//! TASK-0503 · SPEC-018: perfiles con comportamiento propio y grupos que caminan juntos
//! (REQ-RUT-05 a REQ-RUT-09). Submódulo de `gente`: ve los campos de `Gente`.

use carrito_core::rutinas::Perfil;

use super::Gente;

/// Estado propio de esta tarea (grupos armados, a quién sigue cada chico, etc.).
#[derive(Default)]
pub(super) struct Estado {}

impl Gente {
    /// Si `perfil` llega en grupo o tiene un comportamiento propio, arma a la gente acá y
    /// devuelve `true`; si no, `Gente` lo arma como un paseante común.
    pub(super) fn planear_grupo(&mut self, _perfil: Perfil, _desde_salida: bool) -> bool {
        false
    }

    /// Cada cuadro: mantener los grupos juntos, chicos cerca de los adultos, oficinistas
    /// que se van a las 14:30...
    pub(super) fn cuadro_grupos(&mut self, _dt: f32) {}
}
