//! SPEC-012 · Pomos de aderezo con nivel visible.

use carrito_core::aderezos::{DefAderezo, ErrorAderezo, Pomo as PomoCore};
use carrito_core::forma::TipoPieza;
use godot::classes::{INode3D, MeshInstance3D, Node3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::datos::catalogo;
use crate::formas;

pub const GRUPO: &str = "pomos";
const ALTO: f32 = 0.17;
const RADIO: f32 = 0.028;

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Pomo {
    base: Base<Node3D>,
    def: DefAderezo,
    pomo: PomoCore,
    relleno: Option<Gd<MeshInstance3D>>,
}

impl Pomo {
    pub fn crear(def: DefAderezo) -> Gd<Self> {
        let pomo = PomoCore::lleno(&def);
        Gd::from_init_fn(|base| Self { base, def, pomo, relleno: None })
    }

    pub fn aderezo(&self) -> &str {
        &self.def.id
    }

    pub fn usos(&self) -> u32 {
        self.pomo.usos
    }

    /// Solo para pruebas.
    pub fn set_usos(&mut self, u: u32) {
        self.pomo.usos = u.min(self.pomo.max);
        self.actualizar_nivel();
    }

    /// REQ-ADE-06
    pub fn cartel(&self) -> String {
        self.pomo.cartel(&self.def.nombre)
    }

    /// REQ-ADE-03, REQ-ADE-04
    pub fn aplicar(&mut self, comida: &mut Gd<Comida>) -> Result<(), ErrorAderezo> {
        let mut c = comida.bind_mut();
        let admite = c.admite_aderezo(&self.def.id); // REQ-ADE-07
        let mut puestos = c.aderezos().to_vec();
        self.pomo.aplicar(admite, &mut puestos)?;
        c.set_aderezos(puestos);
        drop(c);
        self.actualizar_nivel();
        Ok(())
    }

    /// REQ-ADE-05
    pub fn recargar(&mut self, repone: &str) -> Result<(), ErrorAderezo> {
        self.pomo.recargar(repone)?;
        self.actualizar_nivel();
        Ok(())
    }

    /// REQ-ADE-02: el relleno de color baja con los usos.
    fn actualizar_nivel(&mut self) {
        let nivel = self.pomo.nivel();
        if let Some(r) = &mut self.relleno {
            let alto = (ALTO - 0.02) * nivel.max(0.001);
            r.set_scale(Vector3::new(1.0, nivel.max(0.001), 1.0));
            r.set_position(Vector3::new(0.0, 0.006 + alto / 2.0, 0.0));
            r.set_visible(nivel > 0.0);
        }
    }
}

#[godot_api]
impl INode3D for Pomo {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        let mut yo = self.to_gd().upcast::<Node3D>();
        let c = self.def.color;

        // Envase semitransparente con colisión (para que la mira lo detecte).
        let mut envase =
            formas::pieza(TipoPieza::Cilindro, [RADIO, ALTO, 0.0], [0.0, ALTO / 2.0, 0.0], [0.95, 0.95, 0.95]);
        envase.alfa = 0.35;
        envase.colision = true;
        formas::construir(&mut yo, &[envase]);
        // Pico y tapa del color del aderezo.
        yo.add_child(&formas::visual_pieza(&formas::pieza(
            TipoPieza::Cono,
            [0.02, 0.05, 0.0],
            [0.0, ALTO + 0.025, 0.0],
            c,
        )));
        yo.add_child(&formas::visual_pieza(&formas::pieza(
            TipoPieza::Cilindro,
            [0.004, 0.02, 0.0],
            [0.0, ALTO + 0.055, 0.0],
            c,
        )));

        // Relleno (el nivel que queda).
        let relleno = formas::instancia_malla(
            formas::malla(TipoPieza::Cilindro, [RADIO * 0.85, ALTO - 0.02, 0.0]),
            formas::material(c, 1.0, false, 0.0),
        );
        yo.add_child(&relleno);
        self.relleno = Some(relleno);
        self.actualizar_nivel();
    }
}

/// Arma los pomos de una aderecera (REQ-ADE-02) como hijos de `padre`.
pub fn construir(padre: &mut Gd<Node3D>, tipos: &[String], separacion: f32) {
    let n = tipos.len() as f32;
    for (i, t) in tipos.iter().enumerate() {
        let Some(def) = catalogo().aderezo(t) else { continue };
        let mut p = Pomo::crear(def.clone());
        p.set_position(Vector3::new((i as f32 - (n - 1.0) / 2.0) * separacion, 0.015, -0.22));
        padre.add_child(&p);
    }
}
