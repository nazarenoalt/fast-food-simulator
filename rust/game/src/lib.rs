//! Nodos de Godot del juego. Las reglas viven en `carrito_core`; acá solo se conectan
//! con la escena, la física y la pantalla.

use godot::prelude::*;

mod aderecera; // SPEC-012
mod bloque_stock; // SPEC-004
mod carrito; // SPEC-006
mod ciudad; // SPEC-013
mod comida; // SPEC-002/003/005
mod datos;
mod dia_noche; // SPEC-007
mod formas;
mod gente; // SPEC-009/013
mod hervidor; // SPEC-003
mod hud;
mod jugador; // SPEC-001/002
mod lugar_deposito; // SPEC-004/011
mod luz; // SPEC-006/007
mod negocio; // SPEC-010/011
mod nocturno;
mod palomas; // SPEC-013
mod paquete; // SPEC-011
mod peaton; // SPEC-013
mod plaza; // SPEC-008
mod prueba_humo;
mod sonido; // SPEC-024
mod tienda; // SPEC-011
mod transito; // SPEC-013
mod util;

struct CarritoExtension;

#[gdextension]
unsafe impl ExtensionLibrary for CarritoExtension {
    fn on_stage_deinit(stage: godot::init::InitStage) {
        // Soltar los materiales compartidos antes de que Godot cierre (si no, avisa pérdidas).
        if stage == godot::init::InitStage::MainLoop {
            nocturno::limpiar();
        }
    }
}
