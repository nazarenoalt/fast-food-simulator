//! Prueba de humo de la etapa 2.5 · agente A: REQ-CLI-01 (menú), REQ-CLI-06, REQ-ARR-05, REQ-EVE-09, REQ-EVE-10, REQ-PAR-02, REQ-PAR-05. (TASK-0250)

use super::PruebaHumo;

impl PruebaHumo {
    /// Se llama cada cuadro hasta que devuelve true. Usá self.fase5, self.cuadro5 y
    /// self.notas5 (se reinician al pasar al brazo siguiente). Si cambiás día u hora,
    /// guardalos y devolvelos al terminar.
    /// BASE-ETAPA-2.5: lo llena el agente A.
    pub(super) fn chequear_balance(&mut self) -> bool {
        true
    }
}
