//! SPEC-006 · Puerta del carrito: panel que gira sobre su bisagra al apretar E.

use carrito_core::carrito::DefPuerta;
use carrito_core::forma::TipoPieza;
use carrito_core::puerta::EstadoPuerta;
use carrito_core::sonido::ids;
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::formas;

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct PuertaCarrito {
    base: Base<Node3D>,
    def: DefPuerta,
    /// Color del panel (el del carrito).
    color: [f32; 3],
    estado: EstadoPuerta,
    /// Nodo que gira: la bisagra.
    pivote: Option<Gd<Node3D>>,
}

impl PuertaCarrito {
    pub fn crear(def: DefPuerta, color: [f32; 3]) -> Gd<Self> {
        Gd::from_init_fn(|base| Self { base, def, color, estado: EstadoPuerta::default(), pivote: None })
    }

    /// REQ-CAR-12: abre o cierra.
    pub fn alternar(&mut self) {
        self.estado.alternar();
        let yo = self.to_gd().upcast::<Node3D>();
        crate::sonido::sonar_en(&yo, ids::HELADERA_PUERTA, yo.get_global_position());
    }

    pub fn cartel(&self) -> String {
        self.estado.cartel().to_string()
    }

    pub fn abierta(&self) -> bool {
        self.estado.abierta
    }

    /// Cuánto avanzó la apertura (0 = cerrada, 1 = abierta del todo).
    pub fn progreso(&self) -> f32 {
        self.estado.progreso
    }

    fn girar(&mut self) {
        let grados = self.estado.angulo(self.def.apertura);
        if let Some(p) = &mut self.pivote {
            p.set_rotation_degrees(Vector3::new(0.0, grados, 0.0));
        }
    }
}

#[godot_api]
impl INode3D for PuertaCarrito {
    fn ready(&mut self) {
        let d = self.def.clone();
        let mut yo = self.to_gd().upcast::<Node3D>();
        yo.set_position(formas::v3(d.bisagra));

        // REQ-CAR-13: el hueco oscuro que queda a la vista cuando se abre (pegado a la pared).
        let hueco = formas::pieza(
            TipoPieza::Caja,
            [d.ancho, d.alto, 0.01],
            [d.ancho / 2.0, d.alto / 2.0, -0.005],
            [0.04, 0.04, 0.05],
        );
        yo.add_child(&formas::visual_pieza(&hueco));

        // Pivote en la bisagra; el panel cuelga de él y se extiende hacia +X.
        let mut pivote = Node3D::new_alloc();
        pivote.set_name("Bisagra");
        yo.add_child(&pivote);
        let mut panel =
            formas::pieza(TipoPieza::Caja, [d.ancho, d.alto, 0.03], [d.ancho / 2.0, d.alto / 2.0, -0.025], self.color);
        panel.colision = true;
        // Manija y bisagras de acero.
        let mut manija = formas::pieza(
            TipoPieza::Cilindro,
            [0.012, 0.16, 0.0],
            [d.ancho - 0.08, d.alto / 2.0, -0.05],
            [0.82, 0.83, 0.85],
        );
        manija.metal = true;
        let mut piezas = vec![panel, manija];
        for y in [0.12, d.alto - 0.12] {
            let mut b = formas::pieza(TipoPieza::Cilindro, [0.01, 0.06, 0.0], [0.0, y, -0.025], [0.82, 0.83, 0.85]);
            b.metal = true;
            piezas.push(b);
        }
        formas::construir(&mut pivote, &piezas);
        self.pivote = Some(pivote);
        self.girar();
    }

    fn physics_process(&mut self, delta: f64) {
        // REQ-CAR-12: solo se anima mientras se mueve.
        if self.estado.en_movimiento() {
            self.estado.paso(delta as f32);
            self.girar();
        }
    }
}
