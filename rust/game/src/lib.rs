//! Nodos de Godot del juego. Las reglas viven en `carrito_core`; acá solo se conectan
//! con la escena, la física y la pantalla.

use godot::prelude::*;

mod aderecera; // SPEC-012
mod armado; // SPEC-017
mod arranque; // SPEC-031 (panel "¿Con qué arrancás?")
mod bloque_stock; // SPEC-004
mod carrito; // SPEC-006
mod cartel; // SPEC-009 (cartel de cerrado)
mod ciudad; // SPEC-013
mod comida; // SPEC-002/003/005
mod datos;
mod dia_noche; // SPEC-007
mod feria; // SPEC-019 (puestos de la feria)
mod formas;
mod freidora; // SPEC-029
mod gente; // SPEC-009/013
mod heladera; // SPEC-016
mod hervidor; // SPEC-003
mod hud;
mod jugador; // SPEC-001/002
mod logo; // SPEC-028
mod lugar_deposito; // SPEC-004/011
mod luz; // SPEC-006/007
mod modelos; // SPEC-025
mod negocio; // SPEC-010/011
mod nocturno;
mod palomas; // SPEC-013
mod paquete; // SPEC-011
mod parrilla; // SPEC-015
mod peaton; // SPEC-013
mod plancha; // SPEC-014
mod plaza; // SPEC-008
mod preparar; // SPEC-029 (pelar y cortar)
mod prueba_humo;
mod puerta; // SPEC-006 (puerta de las bases)
mod rendimiento; // SPEC-032 (escena de medición)
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
            modelos::limpiar();
        }
    }
}
