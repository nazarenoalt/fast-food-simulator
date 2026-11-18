//! SPEC-016 · Heladera: mantiene frío lo que guarda; la puerta se abre y cierra con E.

use carrito_core::heladera::Heladera as EstadoHeladera;
use carrito_core::sonido::ids;
use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::formas;
use crate::lugar_deposito::LugarDeposito;

const ANCHO_PUERTA: f32 = 0.6;
const ALTO_PUERTA: f32 = 1.2;
const GROSOR_PUERTA: f32 = 0.03;
/// Cuánto se abre la puerta (grados). Gira hacia afuera, hacia +Z.
const ANGULO_ABIERTA: f32 = -100.0;

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Heladera {
    base: Base<Node3D>,
    interior: [f32; 3],
    lugares: Vec<[f32; 3]>,
    estado: EstadoHeladera,
    zona: Option<Gd<Area3D>>,
    puerta: Option<Gd<Node3D>>,
}

#[godot_api]
impl Heladera {
    /// Abre o cierra la puerta. REQ-HEL-01
    #[func]
    pub fn alternar(&mut self) {
        self.estado.alternar_puerta();
        self.actualizar_puerta();
        // REQ-SON-08: la puerta al abrir y al cerrar.
        let yo = self.to_gd().upcast::<Node3D>();
        crate::sonido::sonar_en(&yo, ids::HELADERA_PUERTA, yo.get_global_position());
    }
}

impl Heladera {
    pub fn crear(interior: [f32; 3], lugares: Vec<[f32; 3]>) -> Gd<Self> {
        Gd::from_init_fn(|base| Self {
            base,
            interior,
            lugares,
            estado: EstadoHeladera::default(),
            zona: None,
            puerta: None,
        })
    }

    /// Temperatura del interior, para lo que está guardado adentro. REQ-HEL-05
    pub fn temperatura(&self) -> f32 {
        self.estado.temp
    }

    pub fn abierta(&self) -> bool {
        self.estado.abierta
    }

    /// Texto del cartel. REQ-HEL-01
    pub fn cartel(&self) -> String {
        let accion = if self.estado.abierta { "Cerrar" } else { "Abrir" };
        format!("[E] {accion} heladera — interior a {:.0} °C", self.estado.temp)
    }

    fn actualizar_puerta(&mut self) {
        let grados = if self.estado.abierta { ANGULO_ABIERTA } else { 0.0 };
        if let Some(p) = &mut self.puerta {
            p.set_rotation_degrees(Vector3::new(0.0, grados, 0.0));
        }
    }
}

#[godot_api]
impl INode3D for Heladera {
    fn ready(&mut self) {
        let [w, h, d] = self.interior;
        let mut yo = self.to_gd().upcast::<Node3D>();

        // REQ-HEL-01: un lugar por paquete, como en el depósito (SPEC-004).
        for lugar in self.lugares.clone() {
            let mut l = LugarDeposito::new_alloc();
            l.set_position(formas::v3(lugar));
            yo.add_child(&l);
        }

        // Zona del interior: la comida suelta que está adentro toma su temperatura. REQ-HEL-05
        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(w, h, d));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, 0.04 + h / 2.0, 0.0));
        zona.set_monitorable(false);
        yo.add_child(&zona);
        self.zona = Some(zona);

        // Puerta con bisagra del lado izquierdo, tapa el frente (+Z).
        let mut bisagra = Node3D::new_alloc();
        bisagra.set_position(Vector3::new(-ANCHO_PUERTA / 2.0, 0.0, ANCHO_PUERTA / 2.0 - GROSOR_PUERTA / 2.0));
        yo.add_child(&bisagra);
        let mut puerta_nodo = bisagra.clone();
        formas::caja_solida(
            &mut puerta_nodo,
            [ANCHO_PUERTA, ALTO_PUERTA, GROSOR_PUERTA],
            [ANCHO_PUERTA / 2.0, ALTO_PUERTA / 2.0, GROSOR_PUERTA / 2.0],
            [0.96, 0.96, 0.97],
            true,
        );
        // Manija.
        formas::caja_solida(
            &mut puerta_nodo,
            [0.025, 0.3, 0.03],
            [ANCHO_PUERTA - 0.05, 0.75, GROSOR_PUERTA + 0.015],
            [0.4, 0.4, 0.42],
            true,
        );
        self.puerta = Some(bisagra);
        self.actualizar_puerta();
    }

    fn physics_process(&mut self, delta: f64) {
        // REQ-HEL-02
        self.estado.paso(delta as f32);

        // REQ-HEL-05: la comida suelta adentro usa la temperatura interior como entorno.
        let temp = self.estado.temp;
        if let Some(zona) = &self.zona {
            for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                if let Ok(mut c) = cuerpo.try_cast::<Comida>() {
                    c.bind_mut().exponer_aire(temp);
                }
            }
        }
    }
}
