//! Nodos de Godot del juego. Las reglas viven en `carrito_core`; acá solo se conectan
//! con la escena, la física y la pantalla.

use godot::prelude::*;

mod bloque_stock; // SPEC-004
mod carrito; // SPEC-006
mod comida; // SPEC-002/003/005
mod datos;
mod dia_noche; // SPEC-007
mod formas;
mod hervidor; // SPEC-003
mod hud;
mod jugador; // SPEC-001/002
mod luz; // SPEC-006/007
mod plaza; // SPEC-008
mod prueba_humo;

struct CarritoExtension;

#[gdextension]
unsafe impl ExtensionLibrary for CarritoExtension {}
