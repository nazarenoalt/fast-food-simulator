//! TASK-0504 · SPEC-030: clientes habituales. Submódulo de `gente`: ve los campos de `Gente`.

use carrito_core::clientes::{Evaluacion, ItemMenu, Pedido};

use super::{Gente, texto_pedido};

/// Estado propio de esta tarea (los habituales y su memoria).
#[derive(Default)]
pub(super) struct Estado {}

impl Gente {
    /// Cada cuadro: ¿llega algún habitual? (REQ-HAB-03)
    pub(super) fn cuadro_habituales(&mut self, _dt: f32) {}

    /// REQ-HAB-04: si el cliente `id` es habitual, su pedido.
    pub(super) fn pedido_habitual(&mut self, _id: u64, _menu: &[ItemMenu], _aderezos: &[String]) -> Option<Pedido> {
        None
    }

    /// REQ-CLI-05, REQ-HAB-05: el texto del globo del cliente `id`.
    pub(super) fn texto_globo(&self, _id: u64, p: &Pedido) -> String {
        texto_pedido(p)
    }

    /// El cliente `id` aceptó lo que le dieron (REQ-HAB-01, REQ-HAB-06).
    pub(super) fn al_atender(&mut self, _id: u64, _ev: &Evaluacion, _pedido: &Pedido) {}

    /// El cliente `id` se fue enojado (REQ-HAB-06).
    pub(super) fn al_perder(&mut self, _id: u64) {}
}
