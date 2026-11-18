//! SPEC-006 · Puerta de una base de carrito (carro grande, kiosco): E la abre o la cierra.
//! El estado y la animación son de `carrito_core::puerta`; acá solo se gira la pieza.

use carrito_core::puerta::Puerta as EstadoPuerta;
use carrito_core::sonido::ids;
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::sonido;

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct PuertaCarrito {
    base: Base<Node3D>,
    estado: EstadoPuerta,
    pieza: Option<Gd<Node3D>>,
}

#[godot_api]
impl PuertaCarrito {
    /// Abre o cierra la puerta, con su sonido (que no es el de la heladera). REQ-CAR-13
    #[func]
    pub fn alternar(&mut self) {
        self.estado.alternar();
        let pos = self.base().get_global_position();
        sonido::sonar_en(&self.to_gd(), ids::CARRITO_PUERTA, pos);
    }
}

impl PuertaCarrito {
    /// Envuelve la `pieza_puerta` de un modelo: este nodo queda en la bisagra (el origen de la
    /// pieza) y la pieza adentro, así el rayo del jugador que pega en su colisión (hija de la
    /// pieza) llega a este nodo. REQ-CAR-11, REQ-CAR-13
    pub fn envolver(mut pieza: Gd<Node3D>, apertura: f32, abierta: bool) -> Option<Gd<Self>> {
        let mut padre = pieza.get_parent()?;
        let mut nodo =
            Gd::from_init_fn(|base| Self { base, estado: EstadoPuerta::nueva(apertura, abierta), pieza: None });
        nodo.set_name("Puerta");
        let t = pieza.get_transform();
        nodo.set_transform(Transform3D::new(Basis::IDENTITY, t.origin));
        padre.add_child(&nodo);
        pieza.reparent(&nodo);
        pieza.set_transform(Transform3D::new(t.basis, Vector3::ZERO));
        nodo.bind_mut().pieza = Some(pieza);
        nodo.bind_mut().girar();
        Some(nodo)
    }

    pub fn abierta(&self) -> bool {
        self.estado.abierta()
    }

    /// Grados que está abierta ahora (0 = cerrada).
    pub fn angulo(&self) -> f32 {
        self.estado.angulo()
    }

    pub fn cartel(&self) -> String {
        self.estado.cartel().to_string()
    }

    fn girar(&mut self) {
        let a = self.estado.angulo();
        if let Some(p) = &mut self.pieza {
            p.set_rotation_degrees(Vector3::new(0.0, a, 0.0));
        }
    }
}

#[godot_api]
impl INode3D for PuertaCarrito {
    fn physics_process(&mut self, delta: f64) {
        // REQ-CAR-13: gira hasta el ángulo final en medio segundo.
        if self.estado.paso(delta as f32) {
            self.girar();
        }
    }
}
