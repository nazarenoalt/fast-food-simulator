//! SPEC-008 · Construye el terreno, la plaza, la vereda y la calle.

use carrito_core::forma::{Pieza, TipoPieza};
use carrito_core::plaza::{self, Prop, TipoProp};
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::{formas, modelos};
use crate::luz::LuzNocturna;

const PASTO: [f32; 3] = [0.24, 0.4, 0.17];
const BALDOSA: [f32; 3] = [0.58, 0.55, 0.5];
const CAMINO: [f32; 3] = [0.64, 0.56, 0.44];
const VEREDA: [f32; 3] = [0.48, 0.48, 0.47];
const ASFALTO: [f32; 3] = [0.17, 0.17, 0.18];
const MADERA: [f32; 3] = [0.55, 0.36, 0.2];
const HIERRO: [f32; 3] = [0.15, 0.16, 0.15];

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Plaza {
    base: Base<Node3D>,
}

/// Superficie plana solo visual (el piso con colisión es uno solo, abajo de todo).
fn superficie(padre: &mut Gd<Node3D>, ancho: f32, largo: f32, x: f32, z: f32, y: f32, c: [f32; 3]) {
    padre.add_child(&formas::visual_pieza(&formas::pieza(TipoPieza::Caja, [ancho, 0.01, largo], [x, y, z], c)));
}

fn solida(tipo: TipoPieza, medidas: [f32; 3], pos: [f32; 3], c: [f32; 3]) -> Pieza {
    Pieza { colision: true, ..formas::pieza(tipo, medidas, pos, c) }
}

fn prop(padre: &mut Gd<Node3D>, p: &Prop, i: usize) {
    let mut nodo = Node3D::new_alloc();
    nodo.set_position(Vector3::new(p.x, 0.0, p.z));
    nodo.set_rotation_degrees(Vector3::new(0.0, p.rot_y, 0.0));
    padre.add_child(&nodo);
    // REQ-MOD-11: el modelo del mueble (su colisión viene en el modelo, REQ-MOD-04). Si no
    // carga, las piezas simples (REQ-MOD-09).
    if modelos::agregar(&mut nodo, carrito_core::modelos::modelo_prop(p.tipo, i)).is_some() {
        if p.tipo == TipoProp::Farol {
            // REQ-MUN-02: los faroles son luces nocturnas.
            let mut luz = LuzNocturna::crear([1.0, 0.82, 0.55], 3.0, 13.0, 0.12, false);
            luz.set_position(Vector3::new(0.0, 3.62, 0.0));
            nodo.add_child(&luz);
        }
        return;
    }
    // REQ-MUN-04: todo el mobiliario tiene colisión.
    match p.tipo {
        TipoProp::Banco => formas::construir(
            &mut nodo,
            &[
                solida(TipoPieza::Caja, [1.6, 0.05, 0.42], [0.0, 0.45, 0.0], MADERA),
                solida(TipoPieza::Caja, [1.6, 0.35, 0.05], [0.0, 0.72, -0.2], MADERA),
                solida(TipoPieza::Caja, [0.06, 0.45, 0.42], [-0.7, 0.225, 0.0], HIERRO),
                solida(TipoPieza::Caja, [0.06, 0.45, 0.42], [0.7, 0.225, 0.0], HIERRO),
            ],
        ),
        TipoProp::Arbol => {
            let alto = 3.2 + (p.rot_y % 7.0) * 0.15;
            formas::construir(
                &mut nodo,
                &[
                    solida(TipoPieza::Cilindro, [0.16, alto, 0.0], [0.0, alto / 2.0, 0.0], [0.38, 0.27, 0.18]),
                    formas::pieza(TipoPieza::Esfera, [1.6, 0.0, 0.0], [0.0, alto + 0.6, 0.0], [0.2, 0.42, 0.18]),
                    formas::pieza(TipoPieza::Esfera, [1.1, 0.0, 0.0], [0.7, alto + 0.2, 0.3], [0.24, 0.47, 0.2]),
                    formas::pieza(TipoPieza::Esfera, [1.0, 0.0, 0.0], [-0.6, alto + 0.3, -0.4], [0.18, 0.4, 0.16]),
                ],
            );
        }
        TipoProp::Farol => {
            formas::construir(
                &mut nodo,
                &[
                    solida(TipoPieza::Cilindro, [0.07, 3.6, 0.0], [0.0, 1.8, 0.0], HIERRO),
                    formas::pieza(TipoPieza::Cono, [0.22, 0.25, 0.0], [0.0, 3.85, 0.0], HIERRO),
                ],
            );
            // REQ-MUN-02: los faroles son luces nocturnas.
            let mut luz = LuzNocturna::crear([1.0, 0.82, 0.55], 3.0, 13.0, 0.12, false);
            luz.set_position(Vector3::new(0.0, 3.62, 0.0));
            nodo.add_child(&luz);
        }
        TipoProp::Fuente => {
            formas::construir(
                &mut nodo,
                &[
                    solida(TipoPieza::Cilindro, [3.0, 0.5, 0.0], [0.0, 0.25, 0.0], [0.7, 0.7, 0.68]),
                    formas::pieza(TipoPieza::Cilindro, [2.75, 0.02, 0.0], [0.0, 0.46, 0.0], [0.3, 0.5, 0.7]),
                    solida(TipoPieza::Cilindro, [0.35, 1.5, 0.0], [0.0, 0.75, 0.0], [0.7, 0.7, 0.68]),
                    formas::pieza(TipoPieza::Cilindro, [0.9, 0.12, 0.0], [0.0, 1.5, 0.0], [0.7, 0.7, 0.68]),
                ],
            );
        }
    }
}

#[godot_api]
impl INode3D for Plaza {
    fn ready(&mut self) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        let t = plaza::TAMANO_TERRENO;
        let l = plaza::LADO_PLAZA;

        // REQ-MUN-01: piso con colisión (la cara de arriba queda en y = 0).
        formas::caja_solida(&mut yo, [t, 1.0, t], [0.0, -0.5, 0.0], PASTO, false);
        // Campo lejano solo visual, para que no se vea el borde del mundo.
        superficie(&mut yo, 1200.0, 1200.0, 0.0, 0.0, -0.02, [0.2, 0.33, 0.15]);

        // REQ-MUN-02: plaza con caminos en cruz y anillo alrededor de la fuente.
        let a = plaza::ANCHO_CAMINO;
        superficie(&mut yo, l, a, 0.0, 0.0, 0.005, CAMINO);
        superficie(&mut yo, a, l, 0.0, 0.0, 0.006, CAMINO);
        superficie(&mut yo, 9.0, 9.0, 0.0, 0.0, 0.007, BALDOSA);
        // Borde de baldosas alrededor de la plaza.
        for &s in &[-1.0_f32, 1.0] {
            superficie(&mut yo, l + 2.0, 1.0, 0.0, s * (l / 2.0 + 0.5), 0.005, BALDOSA);
            superficie(&mut yo, 1.0, l + 2.0, s * (l / 2.0 + 0.5), 0.0, 0.005, BALDOSA);
        }

        // REQ-MUN-03: vereda y calle del lado norte.
        superficie(&mut yo, t, plaza::ANCHO_VEREDA, 0.0, plaza::Z_VEREDA, 0.006, VEREDA);
        superficie(&mut yo, t, plaza::ANCHO_CALLE, 0.0, plaza::Z_CALLE, 0.006, ASFALTO);
        let mut x = -t / 2.0 + 2.0;
        while x < t / 2.0 {
            superficie(&mut yo, 2.0, 0.15, x, plaza::Z_CALLE, 0.008, [0.9, 0.9, 0.85]);
            x += 5.0;
        }
        // Cordón de la vereda.
        yo.add_child(&formas::visual_pieza(&formas::pieza(
            TipoPieza::Caja,
            [t, 0.12, 0.2],
            [0.0, 0.06, plaza::Z_VEREDA - plaza::ANCHO_VEREDA / 2.0],
            [0.75, 0.75, 0.72],
        )));

        // REQ-MUN-05: distribución fija.
        for (i, p) in plaza::distribucion().iter().enumerate() {
            prop(&mut yo, p, i);
        }
    }
}
