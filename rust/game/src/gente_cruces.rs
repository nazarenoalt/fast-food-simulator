//! TASK-0509 · REQ-AMB-18: los peatones esperan en el cordón si viene un auto.
//! Submódulo de `gente`: ve los campos de `Gente`.

use super::Gente;

/// Estado propio de esta tarea.
#[derive(Default)]
pub(super) struct Estado {}

impl Gente {
    /// Cada cuadro, después de avisar vecinos.
    pub(super) fn cuadro_cruces(&mut self, _dt: f32) {}
}
