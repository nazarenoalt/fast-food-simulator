//! Luz que se prende de noche (faroles de la plaza, focos del carrito). REQ-CAR-06, REQ-DIA-06

use carrito_core::forma::TipoPieza;
use godot::classes::{INode3D, Node3D, OmniLight3D, StandardMaterial3D};
use godot::prelude::*;

use crate::formas;

pub const GRUPO_LUCES_NOCHE: &str = "luces_noche";

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct LuzNocturna {
    base: Base<Node3D>,
    color: [f32; 3],
    energia: f32,
    alcance: f32,
    radio_foco: f32,
    sombras: bool,
    encendida: bool,
    luz: Option<Gd<OmniLight3D>>,
    mat_foco: Option<Gd<StandardMaterial3D>>,
}

impl LuzNocturna {
    pub fn crear(color: [f32; 3], energia: f32, alcance: f32, radio_foco: f32, sombras: bool) -> Gd<Self> {
        Gd::from_init_fn(|base| Self {
            base,
            color,
            energia,
            alcance,
            radio_foco,
            sombras,
            encendida: false,
            luz: None,
            mat_foco: None,
        })
    }

    pub fn encendida(&self) -> bool {
        self.encendida
    }

    pub fn set_encendida(&mut self, on: bool) {
        self.encendida = on;
        if let Some(l) = &mut self.luz {
            l.set_visible(on);
        }
        if let Some(m) = &mut self.mat_foco {
            m.set_emission_energy_multiplier(if on { 6.0 } else { 0.0 });
            let c = if on { self.color } else { [0.6, 0.6, 0.55] };
            m.set_albedo(formas::color(c));
        }
    }
}

#[godot_api]
impl INode3D for LuzNocturna {
    fn ready(&mut self) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        yo.add_to_group(GRUPO_LUCES_NOCHE);

        let mat = formas::material(self.color, 1.0, false, 0.01);
        let foco = formas::instancia_malla(formas::malla(TipoPieza::Esfera, [self.radio_foco, 0.0, 0.0]), mat.clone());
        yo.add_child(&foco);
        self.mat_foco = Some(mat);

        let mut luz = OmniLight3D::new_alloc();
        luz.set_color(formas::color(self.color));
        luz.set_param(godot::classes::light_3d::Param::ENERGY, self.energia);
        luz.set_param(godot::classes::light_3d::Param::RANGE, self.alcance);
        luz.set_shadow(self.sombras);
        // Que no ilumine el propio foco desde adentro.
        luz.set_position(Vector3::new(0.0, -self.radio_foco * 1.5, 0.0));
        yo.add_child(&luz);
        self.luz = Some(luz);
        let on = self.encendida;
        self.set_encendida(on);
    }
}
