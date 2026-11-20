//! Reglas del juego, sin Godot. Todo lo de acá se puede probar con `cargo test`.
//!
//! Cada módulo implementa una spec de `docs/specs/`.

pub mod aderezos; // SPEC-012
pub mod agarre; // SPEC-002
pub mod ampliaciones; // SPEC-027
pub mod armado; // SPEC-005
pub mod autos; // SPEC-013 (autos de la calle)
pub mod azar; // números al azar con semilla
pub mod caminos; // SPEC-013 (red de peatones)
pub mod carrito; // SPEC-006
pub mod ciudad; // SPEC-013
pub mod clientes; // SPEC-009
pub mod coccion; // SPEC-003
pub mod cruces; // SPEC-013 (cruzar la calle)
pub mod datos; // carga de archivos .ron
pub mod deposito; // SPEC-004
pub mod economia; // SPEC-010
pub mod eventos; // SPEC-019
pub mod forma; // piezas visuales simples (compartido)
pub mod freidora; // SPEC-029 (aceite, colador y freír)
pub mod grupos; // SPEC-018 (perfiles y grupos)
pub mod habituales; // SPEC-030
pub mod heladera; // SPEC-016
pub mod hervidor; // SPEC-003 (fuente de calor)
pub mod lados; // SPEC-014 (cocción por lados)
pub mod logo; // SPEC-028
pub mod modelos; // SPEC-025
pub mod papas; // SPEC-026
pub mod parrilla; // SPEC-015 (carbón)
pub mod peatones; // SPEC-013
pub mod plancha; // SPEC-014 (fuente de calor)
pub mod plaza; // SPEC-008
pub mod preparar; // SPEC-029 (pelar y cortar)
pub mod proveedor; // SPEC-011
pub mod puerta; // SPEC-006 (puerta de las bases)
pub mod reloj; // SPEC-007
pub mod rutinas; // SPEC-018 (agenda)
pub mod sonido; // SPEC-024
pub mod tienda; // SPEC-017
pub mod tostado; // SPEC-015 (pan tostado)
pub mod vestimenta; // SPEC-018 (ropa y actividades por hora)

/// Temperatura ambiente en °C.
pub const TEMP_AMBIENTE: f32 = 20.0;
