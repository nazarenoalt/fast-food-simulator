//! SPEC-011 · Paquete que llega del proveedor: se agarra y se lleva al depósito.

use carrito_core::deposito::{Bloque, DefBloque};
use godot::classes::{BoxShape3D, IRigidBody3D, Node3D, PhysicsMaterial, RigidBody3D};
use godot::prelude::*;

use crate::bloque_stock;
use crate::datos::catalogo;
use crate::formas;

#[derive(GodotClass)]
#[class(base=RigidBody3D, no_init)]
pub struct Paquete {
    base: Base<RigidBody3D>,
    def: DefBloque,
    /// Unidades que le quedan (uno levantado del estante puede venir empezado). REQ-DEP-09
    restantes: u32,
    /// Lo tiene el jugador en la mano. REQ-PRO-05
    pub sostenido: bool,
    /// Ya se acomodó en el depósito (está por desaparecer).
    pub acomodado: bool,
    /// Temperatura del paquete (°C). REQ-HEL-06
    pub temp: f32,
}

impl Paquete {
    pub fn crear(def: DefBloque) -> Gd<Self> {
        let temp = bloque_stock::temp_inicial(&def);
        let restantes = def.capacidad();
        Self::crear_con(def, restantes, temp)
    }

    /// REQ-DEP-09: un paquete con `restantes` unidades y a `temp` °C (levantado del estante).
    pub fn crear_con(def: DefBloque, restantes: u32, temp: f32) -> Gd<Self> {
        let restantes = Bloque::con_restantes(def.clone(), restantes).restantes;
        Gd::from_init_fn(|base| Self { base, def, restantes, sostenido: false, acomodado: false, temp })
    }

    pub fn restantes(&self) -> u32 {
        self.restantes
    }

    pub fn def(&self) -> &DefBloque {
        &self.def
    }

    pub fn descripcion(&self) -> String {
        let (n, total) = (self.restantes, self.def.capacidad());
        let unidades = if n == total { format!("{n} unidades") } else { format!("{n}/{total} unidades") };
        carrito_core::aderezos::capitalizar(&format!("{} ({unidades})", self.def.nombre))
    }
}

#[godot_api]
impl IRigidBody3D for Paquete {
    fn physics_process(&mut self, delta: f64) {
        // REQ-HEL-06: suelto, se va calentando hasta el ambiente.
        self.temp = carrito_core::heladera::acercar(
            self.temp,
            carrito_core::TEMP_AMBIENTE,
            carrito_core::heladera::K_PAQUETE,
            delta as f32,
        );
    }

    fn ready(&mut self) {
        let def = self.def.clone();
        let [tx, ty, tz] = def.tamano();
        let masa_unidad = catalogo().producto(&def.producto).map(|p| p.masa).unwrap_or(0.05);
        let mut yo = self.to_gd();
        yo.set_mass(masa_unidad * self.restantes as f32 + 0.05);
        yo.set_angular_damp(2.0);
        yo.set_collision_layer(1 | formas::CAPA_OBJETOS);
        let mut mat = PhysicsMaterial::new_gd();
        mat.set_friction(1.0);
        mat.set_bounce(0.05);
        yo.set_physics_material_override(&mat);

        // El dibujo se arma con la base del paquete en y = 0; el cuerpo está centrado.
        let mut visual = Node3D::new_alloc();
        visual.set_position(Vector3::new(0.0, -ty / 2.0, 0.0));
        yo.add_child(&visual);
        bloque_stock::construir_visual(&mut visual, &def, self.restantes);

        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(tx + 0.01, ty + 0.01, tz + 0.01));
        yo.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
    }
}
