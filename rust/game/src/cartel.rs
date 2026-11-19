//! SPEC-009 · Cartel de cerrado (REQ-CLI-12, REQ-CLI-13): el clic con la mano libre o E lo saca
//! (desaparece) o lo vuelve a colgar. La regla (arranca colgado; colgado no llegan clientes
//! nuevos; dónde queda la zona de uso) es de `carrito_core::clientes`; acá solo se esconde el
//! dibujo y se pone la colisión de la mira, que no se mueve.

use carrito_core::clientes::{CartelCerrado as EstadoCartel, ZONA_CARTEL_CENTRO, ZONA_CARTEL_MEDIDAS};
use godot::classes::{BoxShape3D, Node3D, StaticBody3D};
use godot::prelude::*;

use crate::formas;

pub const NOMBRE: &str = "CartelCerrado";
const DIBUJO: &str = "Dibujo";
const ZONA: &str = "Zona";

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct CartelCerrado {
    base: Base<Node3D>,
    estado: EstadoCartel,
}

#[godot_api]
impl CartelCerrado {
    /// REQ-CLI-13: el clic o E lo saca o lo cuelga.
    #[func]
    pub fn alternar(&mut self) {
        self.estado.alternar();
        self.acomodar();
        let pos = self.base().get_global_position();
        crate::sonido::sonar_en(&self.to_gd(), carrito_core::sonido::ids::APOYAR, pos);
    }
}

impl CartelCerrado {
    /// Envuelve el dibujo del accesorio (lo que ya colgó de `nodo`: el modelo o sus piezas) para
    /// esconderlo entero, y le agrega al lado la zona de uso que solo ve la mira. REQ-CLI-13
    pub fn envolver(nodo: &mut Gd<Node3D>) -> Gd<Self> {
        let hijos: Vec<Gd<Node>> = nodo.get_children().iter_shared().collect();
        let mut cartel = Gd::from_init_fn(|base| Self { base, estado: EstadoCartel::default() });
        cartel.set_name(NOMBRE);
        nodo.add_child(&cartel);
        let mut dibujo = Node3D::new_alloc();
        dibujo.set_name(DIBUJO);
        cartel.add_child(&dibujo);
        for mut h in hijos {
            h.reparent_ex(&dibujo).keep_global_transform(false).done();
        }
        // La zona queda donde cuelga aunque el cartel no se vea, y no asoma sobre la mesada.
        let mut forma = BoxShape3D::new_gd();
        forma.set_size(formas::v3(ZONA_CARTEL_MEDIDAS));
        let mut cuerpo = StaticBody3D::new_alloc();
        cuerpo.set_name(ZONA);
        cuerpo.set_collision_layer(formas::CAPA_USABLES);
        cuerpo.set_collision_mask(0);
        cuerpo.add_child(&formas::nodo_colision(
            forma.upcast(),
            Transform3D::new(Basis::IDENTITY, formas::v3(ZONA_CARTEL_CENTRO)),
        ));
        cartel.add_child(&cuerpo);
        cartel.bind_mut().acomodar();
        cartel
    }

    pub fn estado(&self) -> EstadoCartel {
        self.estado
    }

    pub fn colgado(&self) -> bool {
        self.estado.colgado
    }

    pub fn cartel(&self) -> String {
        self.estado.accion().to_string()
    }

    /// Se ve el dibujo del cartel (para la prueba de humo). REQ-CLI-13
    pub fn dibujo_visible(&self) -> bool {
        self.base().get_node_or_null(DIBUJO).and_then(|n| n.try_cast::<Node3D>().ok()).is_some_and(|d| d.is_visible())
    }

    /// Centro global de la zona de uso (para la prueba de humo y las fotos). REQ-CLI-13
    pub fn centro_zona(&self) -> Vector3 {
        self.base().get_global_transform() * formas::v3(ZONA_CARTEL_CENTRO)
    }

    fn acomodar(&mut self) {
        let se_ve = self.estado.se_ve();
        if let Some(mut d) = self.base().get_node_or_null(DIBUJO).and_then(|n| n.try_cast::<Node3D>().ok()) {
            d.set_visible(se_ve);
        }
    }
}
