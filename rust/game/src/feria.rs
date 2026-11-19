//! REQ-EVE-05 · Los puestos de la feria: piezas simples con colisión. Dónde van y cuándo
//! están lo decide `carrito_core::eventos` (y `Gente`, que los arma y los saca).

use carrito_core::eventos::{self, Puesto};
use carrito_core::forma::{Pieza, TipoPieza};
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::formas;

pub const GRUPO: &str = "feria_puestos";

const MADERA: [f32; 3] = [0.55, 0.38, 0.22];
const TABLA: [f32; 3] = [0.78, 0.66, 0.48];
const PALO: [f32; 3] = [0.35, 0.3, 0.27];
const BLANCO: [f32; 3] = [0.95, 0.93, 0.88];
/// Lo que hay a la venta: frascos, frutas, artesanías (colores sueltos).
const MERCADERIA: [[f32; 3]; 5] =
    [[0.85, 0.3, 0.2], [0.95, 0.8, 0.3], [0.4, 0.65, 0.3], [0.55, 0.35, 0.6], [0.9, 0.6, 0.4]];

fn solida(tipo: TipoPieza, medidas: [f32; 3], pos: [f32; 3], c: [f32; 3]) -> Pieza {
    Pieza { colision: true, ..formas::pieza(tipo, medidas, pos, c) }
}

/// Las piezas de un puesto, en su espacio local (frente hacia +Z, piso en y = 0).
fn piezas(p: &Puesto, i: usize) -> Vec<Pieza> {
    let (a, f) = (eventos::ANCHO_PUESTO, eventos::FONDO_PUESTO);
    let alto = 2.25;
    let mut v = vec![
        // Mostrador al frente (con colisión) y su tabla.
        solida(TipoPieza::Caja, [a - 0.1, 0.92, 0.55], [0.0, 0.46, f / 2.0 - 0.3], MADERA),
        formas::pieza(TipoPieza::Caja, [a, 0.05, 0.65], [0.0, 0.945, f / 2.0 - 0.3], TABLA),
    ];
    // Cuatro palos (con colisión); los de atrás, más altos, por la caída del toldo.
    for sx in [-1.0_f32, 1.0] {
        for sz in [-1.0_f32, 1.0] {
            let h = if sz < 0.0 { alto + 0.2 } else { alto };
            let pos = [sx * (a / 2.0 - 0.05), h / 2.0, sz * (f / 2.0 - 0.05)];
            v.push(solida(TipoPieza::Cilindro, [0.04, h, 0.0], pos, PALO));
        }
    }
    // Toldo a rayas, un poco inclinado hacia adelante, y el faldón del frente.
    let rayas = 6;
    let ancho_raya = (a + 0.2) / rayas as f32;
    for k in 0..rayas {
        let x = -(a + 0.2) / 2.0 + ancho_raya * (k as f32 + 0.5);
        let color = if k % 2 == 0 { p.toldo } else { BLANCO };
        let mut t = formas::pieza(TipoPieza::Caja, [ancho_raya, 0.04, f + 0.4], [x, alto + 0.08, 0.05], color);
        t.rot = [12.0, 0.0, 0.0];
        v.push(t);
        v.push(formas::pieza(TipoPieza::Caja, [ancho_raya, 0.22, 0.03], [x, alto - 0.12, f / 2.0 + 0.27], color));
    }
    // Mercadería sobre el mostrador.
    for k in 0..4 {
        let x = -a / 2.0 + 0.35 + k as f32 * (a - 0.7) / 3.0;
        let c = MERCADERIA[(i + k) % MERCADERIA.len()];
        let lado = 0.16 + 0.04 * ((i + k) % 3) as f32;
        v.push(formas::pieza(TipoPieza::Caja, [lado, lado, lado], [x, 0.97 + lado / 2.0, f / 2.0 - 0.3], c));
    }
    v
}

/// REQ-EVE-05: los 6 puestos de la feria, todos juntos en un nodo.
#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Feria {
    base: Base<Node3D>,
    puestos: Vec<Puesto>,
}

impl Feria {
    pub fn crear(puestos: Vec<Puesto>) -> Gd<Self> {
        Gd::from_init_fn(|base| Self { base, puestos })
    }

    pub fn cantidad(&self) -> usize {
        self.puestos.len()
    }
}

#[godot_api]
impl INode3D for Feria {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        let puestos = self.puestos.clone();
        for (i, p) in puestos.iter().enumerate() {
            let mut nodo = Node3D::new_alloc();
            nodo.set_position(Vector3::new(p.x, 0.0, p.z));
            nodo.set_rotation_degrees(Vector3::new(0.0, p.rot_y, 0.0));
            self.base_mut().add_child(&nodo);
            formas::construir(&mut nodo, &piezas(p, i));
        }
    }
}
