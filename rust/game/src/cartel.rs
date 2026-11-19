//! SPEC-009 · Cartel de cerrado (REQ-CLI-12, REQ-CLI-13): E lo descuelga (queda acostado sobre
//! el mostrador) o lo vuelve a colgar. La regla (arranca colgado; colgado no llegan clientes
//! nuevos) es de `carrito_core::clientes`; acá solo se acomoda el dibujo y la colisión de la mira.

use carrito_core::clientes::CartelCerrado as EstadoCartel;
use godot::classes::{BoxShape3D, Node3D, StaticBody3D};
use godot::prelude::*;

use crate::formas;

pub const NOMBRE: &str = "CartelCerrado";

/// Acostado: un cuarto de vuelta sobre el clavo, hacia el vendedor: el tablero (que cuelga hasta
/// 26 cm abajo del clavo) queda boca abajo sobre la mesada, que está 12 mm arriba del clavo; se
/// sube lo que mide de grueso (11 mm) más un poquito.
const GIRO_ACOSTADO: f32 = 90.0;
const ALTO_ACOSTADO: f32 = 0.024;

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct CartelCerrado {
    base: Base<Node3D>,
    estado: EstadoCartel,
}

#[godot_api]
impl CartelCerrado {
    /// REQ-CLI-13: E lo descuelga o lo cuelga.
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
    /// girarlo entero sobre el clavo, y le agrega una colisión que solo ve la mira. REQ-CLI-13
    pub fn envolver(nodo: &mut Gd<Node3D>) -> Gd<Self> {
        let hijos: Vec<Gd<Node>> = nodo.get_children().iter_shared().collect();
        let mut cartel = Gd::from_init_fn(|base| Self { base, estado: EstadoCartel::default() });
        cartel.set_name(NOMBRE);
        nodo.add_child(&cartel);
        for mut h in hijos {
            h.reparent_ex(&cartel).keep_global_transform(false).done();
        }
        // El tablero cuelga del clavo (REQ-PAP-07: 0,32 × 0,16, unos 18 cm abajo). La caja sube
        // un poco por encima de la mesada para que se lo vea desde adentro del carrito.
        let mut forma = BoxShape3D::new_gd();
        forma.set_size(Vector3::new(0.34, 0.3, 0.04));
        let mut cuerpo = StaticBody3D::new_alloc();
        cuerpo.set_collision_layer(formas::CAPA_USABLES);
        cuerpo.set_collision_mask(0);
        cuerpo.add_child(&formas::nodo_colision(
            forma.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, -0.11, 0.0)),
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

    fn acomodar(&mut self) {
        let (giro, pos) = if self.estado.colgado {
            (0.0, Vector3::ZERO)
        } else {
            (GIRO_ACOSTADO, Vector3::new(0.0, ALTO_ACOSTADO, 0.0))
        };
        let mut yo = self.to_gd();
        yo.set_rotation_degrees(Vector3::new(giro, 0.0, 0.0));
        yo.set_position(pos);
    }
}
