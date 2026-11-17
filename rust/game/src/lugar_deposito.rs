//! SPEC-004 / SPEC-011 · Un lugar del depósito: tiene a lo sumo un bloque, y acomoda solo
//! los paquetes que se dejan adentro si está libre.

use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D};
use godot::prelude::*;

use crate::bloque_stock::BloqueStock;
use crate::formas;
use crate::paquete::Paquete;

pub const GRUPO: &str = "lugares_deposito";

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct LugarDeposito {
    base: Base<Node3D>,
    zona: Option<Gd<Area3D>>,
}

impl LugarDeposito {
    /// REQ-DEP-07: un lugar está ocupado si tiene un bloque que no está por desaparecer.
    pub fn ocupado(&self) -> bool {
        self.base()
            .get_children()
            .iter_shared()
            .filter_map(|n| n.try_cast::<BloqueStock>().ok())
            .any(|b| !b.is_queued_for_deletion())
    }

    pub fn bloque(&self) -> Option<Gd<BloqueStock>> {
        self.base()
            .get_children()
            .iter_shared()
            .filter_map(|n| n.try_cast::<BloqueStock>().ok())
            .find(|b| !b.is_queued_for_deletion())
    }

    /// Centro de la zona donde hay que dejar un paquete (global).
    pub fn centro_zona(&self) -> Vector3 {
        self.base().get_global_position() + Vector3::new(0.0, 0.15, 0.0)
    }
}

#[godot_api]
impl INode3D for LugarDeposito {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        let mut zona = Area3D::new_alloc();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(0.22, 0.3, 0.4));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, 0.15, 0.0));
        zona.set_monitorable(false);
        self.base_mut().add_child(&zona);
        self.zona = Some(zona);
    }

    fn physics_process(&mut self, _delta: f64) {
        if self.ocupado() {
            return;
        }
        let Some(zona) = &self.zona else { return };
        // REQ-PRO-06: un paquete suelto dentro de un lugar libre se acomoda solo.
        for cuerpo in zona.get_overlapping_bodies().iter_shared() {
            let Ok(mut paquete) = cuerpo.try_cast::<Paquete>() else { continue };
            let def = {
                let p = paquete.bind();
                if p.sostenido || p.acomodado {
                    continue;
                }
                p.def().clone()
            };
            paquete.bind_mut().acomodado = true;
            paquete.queue_free();
            let bloque = BloqueStock::crear(def);
            self.base_mut().add_child(&bloque);
            return;
        }
    }
}
