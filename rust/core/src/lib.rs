//! Reglas del juego, sin Godot. Todo lo de acá se puede probar con `cargo test`.
//!
//! Cada módulo implementa una spec de `docs/specs/`.

pub mod aderezos; // SPEC-012
pub mod armado; // SPEC-005
pub mod azar; // números al azar con semilla
pub mod caminos; // SPEC-013 (red de peatones)
pub mod carrito; // SPEC-006
pub mod ciudad; // SPEC-013
pub mod clientes; // SPEC-009
pub mod coccion; // SPEC-003
pub mod datos; // carga de archivos .ron
pub mod deposito; // SPEC-004
pub mod economia; // SPEC-010
pub mod forma; // piezas visuales simples (compartido)
pub mod hervidor; // SPEC-003 (fuente de calor)
pub mod peatones; // SPEC-013
pub mod plaza; // SPEC-008
pub mod proveedor; // SPEC-011
pub mod reloj; // SPEC-007

/// Temperatura ambiente en °C.
pub const TEMP_AMBIENTE: f32 = 20.0;
