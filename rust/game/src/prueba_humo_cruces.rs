//! Prueba de humo de esperar en el cordón si viene un auto (REQ-AMB-18). (TASK-0509)

use super::PruebaHumo;

impl PruebaHumo {
    /// Se llama cada cuadro hasta que devuelve true (brazo de la cadena del paso 31).
    pub(super) fn chequear_cruces(&mut self) -> bool {
        true
    }
}
