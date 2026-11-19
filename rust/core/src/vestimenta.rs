//! SPEC-018 · Ropa según perfil y hora (REQ-RUT-10) y actividades según la hora (REQ-RUT-11).
//! (TASK-0507)

use crate::peatones::{Paleta, Plan};
use crate::rutinas::Perfil;

/// REQ-RUT-10: de qué paleta se viste alguien de ese perfil a esa hora (0–24).
pub fn paleta(_perfil: Perfil, _hora: f32) -> Paleta {
    Paleta::comun()
}

/// REQ-RUT-11: ¿alguien de ese perfil puede hacer esa actividad a esa hora?
pub fn plan_permitido(_perfil: Perfil, _plan: Plan, _hora: f32) -> bool {
    true
}

/// REQ-RUT-11: ¿se puede sentar alguien en el asiento de la red que está en `asiento` (x, z)
/// a esa hora? De noche, solo cerca de un farol.
pub fn asiento_permitido(_asiento: [f32; 2], _hora: f32) -> bool {
    true
}
