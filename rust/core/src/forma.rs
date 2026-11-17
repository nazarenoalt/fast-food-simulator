//! Piezas visuales simples (caja, cilindro, esfera, cono, cápsula).
//! Se usan para productos y accesorios hasta tener modelos de Blender.

use serde::Deserialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
pub enum TipoPieza {
    /// medidas = (ancho, alto, profundidad)
    Caja,
    /// medidas = (radio, alto, _)
    Cilindro,
    /// medidas = (radio, _, _)
    Esfera,
    /// medidas = (radio de abajo, alto, _)
    Cono,
    /// medidas = (radio, alto total, _)
    Capsula,
}

fn uno() -> [f32; 3] {
    [1.0, 1.0, 1.0]
}
fn opaco() -> f32 {
    1.0
}
fn si() -> bool {
    true
}

/// Una pieza: forma + medidas + posición/giro (grados) relativos + color.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Pieza {
    pub tipo: TipoPieza,
    pub medidas: [f32; 3],
    #[serde(default)]
    pub pos: [f32; 3],
    #[serde(default)]
    pub rot: [f32; 3],
    #[serde(default = "uno")]
    pub escala: [f32; 3],
    pub color: [f32; 3],
    /// 1 = opaco, menos = transparente.
    #[serde(default = "opaco")]
    pub alfa: f32,
    #[serde(default)]
    pub metal: bool,
    /// Brillo propio (para focos, pilotos).
    #[serde(default)]
    pub emision: f32,
    /// Si la pieza tiene colisión (por defecto sí).
    #[serde(default = "si")]
    pub colision: bool,
    /// Si el color de esta pieza lo da el estado de cocción (ej. la salchicha del pancho).
    #[serde(default)]
    pub tinte_coccion: bool,
}
