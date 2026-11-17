//! SPEC-006 · Construye el carrito del jugador a partir de los datos.

use carrito_core::carrito::{CarritoArmado, Funcion, armar};
use carrito_core::forma::TipoPieza;
use godot::classes::{INode3D, Label3D, Node3D};
use godot::classes::base_material_3d::BillboardMode;
use godot::prelude::*;

use crate::bloque_stock::BloqueStock;
use crate::datos::catalogo;
use crate::formas;
use crate::hervidor::Hervidor;
use crate::luz::LuzNocturna;

const ACERO: [f32; 3] = [0.82, 0.83, 0.85];

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Carrito {
    base: Base<Node3D>,
    /// Si está vacío, usa la config del jugador (`res://data/carrito_jugador.ron`).
    #[export]
    base_forzada: GString,
}

impl Carrito {
    fn construir_base(&mut self, armado: &CarritoArmado) {
        let b = &armado.base;
        let mut yo = self.to_gd().upcast::<Node3D>();
        let suelo = if b.ruedas { 0.18 } else { 0.02 };
        let alto_cuerpo = b.alto_mostrador - 0.04 - suelo;

        // Mueble (color = estilo, REQ-CAR-09).
        formas::caja_solida(
            &mut yo,
            [b.ancho, alto_cuerpo, b.profundidad],
            [0.0, suelo + alto_cuerpo / 2.0, 0.0],
            armado.color,
            false,
        );
        // Mesada de acero, un poco más grande que el mueble.
        formas::caja_solida(
            &mut yo,
            [b.ancho + 0.04, 0.04, b.profundidad + 0.06],
            [0.0, b.alto_mostrador - 0.02, 0.02],
            ACERO,
            true,
        );
        // Zócalo y ruedas.
        if b.ruedas {
            let r = 0.15;
            for &sx in &[-1.0_f32, 1.0] {
                for &sz in &[-1.0_f32, 1.0] {
                    let mut rueda = formas::pieza(
                        TipoPieza::Cilindro,
                        [r, 0.06, 0.0],
                        [sx * (b.ancho / 2.0 - 0.3), r, sz * (b.profundidad / 2.0 + 0.03)],
                        [0.12, 0.12, 0.12],
                    );
                    rueda.rot = [90.0, 0.0, 0.0];
                    yo.add_child(&formas::visual_pieza(&rueda));
                }
            }
            // Manija para empujarlo.
            let mut manija = formas::pieza(
                TipoPieza::Cilindro,
                [0.015, b.profundidad * 0.8, 0.0],
                [-b.ancho / 2.0 - 0.15, b.alto_mostrador - 0.1, 0.0],
                ACERO,
            );
            manija.rot = [90.0, 0.0, 0.0];
            manija.metal = true;
            yo.add_child(&formas::visual_pieza(&manija));
        }
    }

    fn construir_accesorios(&mut self, armado: &CarritoArmado) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        for c in &armado.colocados {
            // REQ-CAR-03: el accesorio se ubica en la posición y giro del anclaje.
            let mut nodo = Node3D::new_alloc();
            nodo.set_name(&format!("{}_{}", c.anclaje.id, c.accesorio.id));
            nodo.set_position(formas::v3(c.anclaje.pos));
            nodo.set_rotation_degrees(Vector3::new(0.0, c.anclaje.rot_y, 0.0));
            yo.add_child(&nodo);

            formas::construir(&mut nodo, &c.accesorio.forma);

            // REQ-CAR-05: función del accesorio.
            match &c.accesorio.funcion {
                Some(Funcion::Hervidor { interior }) => {
                    nodo.add_child(&Hervidor::crear(*interior));
                }
                Some(Funcion::Deposito { lugares }) => {
                    for (lugar, bloque) in lugares.iter().zip(&c.stock) {
                        let Some(id) = bloque else { continue };
                        let def = catalogo().bloque(id).expect("bloque validado").clone();
                        let mut b = BloqueStock::crear(def);
                        b.set_position(formas::v3(*lugar));
                        nodo.add_child(&b);
                    }
                }
                Some(Funcion::Luz { pos, color, energia, alcance }) => {
                    // REQ-CAR-06: se prende de noche (grupo luces_noche).
                    let mut luz = LuzNocturna::crear(*color, *energia, *alcance, 0.035, true);
                    luz.set_position(formas::v3(*pos));
                    nodo.add_child(&luz);
                }
                None => {}
            }
        }
    }

    /// REQ-CAR-08: muestra el error arriba del carrito, en rojo, además de la consola.
    fn mostrar_error(&mut self, mensaje: &str) {
        godot_error!("Carrito: {mensaje}");
        let mut l = Label3D::new_alloc();
        l.set_text(&format!("ERROR EN EL CARRITO\n{mensaje}"));
        l.set_modulate(Color::from_rgb(1.0, 0.2, 0.2));
        l.set_billboard_mode(BillboardMode::ENABLED);
        l.set_font_size(48);
        l.set_pixel_size(0.003);
        l.set_position(Vector3::new(0.0, 2.6, 0.0));
        l.add_to_group("errores_carrito");
        self.base_mut().add_child(&l);
    }
}

#[godot_api]
impl INode3D for Carrito {
    fn ready(&mut self) {
        let cat = catalogo();
        let mut config = cat.carrito_jugador.clone();
        if !self.base_forzada.is_empty() {
            config.base = self.base_forzada.to_string();
        }
        // REQ-CAR-07, REQ-CAR-08
        match armar(&config, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
            Ok(armado) => {
                self.construir_base(&armado);
                self.construir_accesorios(&armado);
            }
            Err(e) => {
                // Se dibuja al menos la base (si existe) para que se vea dónde está el problema.
                let mensaje = e.to_string();
                let base_sola = carrito_core::carrito::ConfigCarrito {
                    accesorios: Default::default(),
                    stock: Default::default(),
                    ..config
                };
                if let Ok(a) = armar(&base_sola, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
                    self.construir_base(&a);
                }
                self.mostrar_error(&mensaje);
            }
        }
    }
}
