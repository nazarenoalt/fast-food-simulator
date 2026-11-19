//! SPEC-014 · Plancha: superficie que se calienta y cocina lo que se apoya encima.

use carrito_core::plancha::{Plancha as EstadoPlancha, TEMP_MAX};
use carrito_core::sonido::ids;
use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D, StandardMaterial3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::formas;

const ESPESOR: f32 = 0.03;
/// Alto de la zona que detecta lo apoyado (m sobre la superficie).
const ALTO_ZONA: f32 = 0.05;
const ACERO: [f32; 3] = [0.3, 0.3, 0.32];

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Plancha {
    base: Base<Node3D>,
    superficie: [f32; 2],
    estado: EstadoPlancha,
    zona: Option<Gd<Area3D>>,
    piloto: Option<Gd<StandardMaterial3D>>,
    mat_superficie: Option<Gd<StandardMaterial3D>>,
    /// REQ-SON-08: ya suena el chisporroteo (para encender/apagar solo al cambiar).
    chisporrotea: bool,
}

/// REQ-SON-08: por debajo de esta temperatura (°C) la carne no chisporrotea.
const TEMP_CHISPOROTEO: f32 = 100.0;

#[godot_api]
impl Plancha {
    /// Enciende o apaga. REQ-PLA-01
    #[func]
    pub fn alternar(&mut self) {
        self.estado.alternar();
        self.actualizar_piloto();
        // REQ-SON-08: el clic del interruptor.
        let yo = self.to_gd().upcast::<Node3D>();
        crate::sonido::sonar_en(&yo, ids::PLANCHA_INTERRUPTOR, yo.get_global_position());
    }
}

impl Plancha {
    pub fn crear(superficie: [f32; 2]) -> Gd<Self> {
        Gd::from_init_fn(|base| Self {
            base,
            superficie,
            estado: EstadoPlancha::default(),
            zona: None,
            piloto: None,
            mat_superficie: None,
            chisporrotea: false,
        })
    }

    /// Solo para pruebas.
    pub fn temperatura(&self) -> f32 {
        self.estado.temp
    }

    pub fn set_temperatura(&mut self, t: f32) {
        self.estado.temp = t;
    }

    /// Texto del cartel. REQ-PLA-01
    pub fn cartel(&self) -> String {
        let accion = if self.estado.encendida { "Apagar" } else { "Encender" };
        format!("[E] {accion} plancha — {:.0} °C", self.estado.temp)
    }

    fn actualizar_piloto(&mut self) {
        let on = self.estado.encendida;
        if let Some(m) = &mut self.piloto {
            // REQ-PLA-01: luz piloto roja encendida.
            m.set_emission_energy_multiplier(if on { 4.0 } else { 0.0 });
            m.set_albedo(if on { Color::from_rgb(1.0, 0.1, 0.05) } else { Color::from_rgb(0.25, 0.05, 0.05) });
        }
    }
}

#[godot_api]
impl INode3D for Plancha {
    fn ready(&mut self) {
        let [w, d] = self.superficie;
        let mut yo = self.to_gd().upcast::<Node3D>();

        // Cuerpo y superficie, con colisión para apoyar la comida. La superficie queda a ESPESOR.
        formas::caja_solida(
            &mut yo,
            [w + 0.04, ESPESOR - 0.008, d + 0.04],
            [0.0, (ESPESOR - 0.008) / 2.0, 0.0],
            ACERO,
            true,
        );
        let mat = formas::material([0.18, 0.18, 0.2], 1.0, true, 0.0);
        let mut tapa =
            formas::instancia_malla(formas::malla(carrito_core::forma::TipoPieza::Caja, [w, 0.008, d]), mat.clone());
        tapa.set_position(Vector3::new(0.0, ESPESOR - 0.004, 0.0));
        yo.add_child(&tapa);
        formas::caja_solida(&mut yo, [w, 0.008, d], [0.0, ESPESOR - 0.004, 0.0], [0.18, 0.18, 0.2], true);
        self.mat_superficie = Some(mat);

        // Zona que detecta lo apoyado encima. REQ-PLA-03
        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(w, ALTO_ZONA, d));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, ESPESOR + ALTO_ZONA / 2.0, 0.0));
        zona.set_monitorable(false);
        yo.add_child(&zona);
        self.zona = Some(zona);

        // Perilla y luz piloto del lado del vendedor (-Z).
        let mut perilla = formas::visual_pieza(&formas::pieza(
            carrito_core::forma::TipoPieza::Cilindro,
            [0.018, 0.02, 0.0],
            [0.0; 3],
            [0.1, 0.1, 0.1],
        ));
        perilla.set_rotation_degrees(Vector3::new(90.0, 0.0, 0.0));
        perilla.set_position(Vector3::new(-w / 4.0, ESPESOR / 2.0, -d / 2.0 - 0.03));
        yo.add_child(&perilla);
        let piloto_mat = formas::material([1.0, 0.1, 0.05], 1.0, false, 0.01);
        let mut piloto = formas::instancia_malla(
            formas::malla(carrito_core::forma::TipoPieza::Esfera, [0.008, 0.0, 0.0]),
            piloto_mat.clone(),
        );
        piloto.set_position(Vector3::new(w / 4.0, ESPESOR / 2.0, -d / 2.0 - 0.024));
        yo.add_child(&piloto);
        self.piloto = Some(piloto_mat);
        self.actualizar_piloto();
    }

    fn physics_process(&mut self, delta: f64) {
        // REQ-PLA-02
        self.estado.paso(delta as f32);

        // La superficie se pone rojiza cuanto más caliente.
        if let Some(m) = &mut self.mat_superficie {
            let f = ((self.estado.temp - 20.0) / (TEMP_MAX - 20.0)).clamp(0.0, 1.0);
            m.set_albedo(Color::from_rgb(0.18 + 0.4 * f, 0.18 + 0.05 * f, 0.2 - 0.08 * f));
        }

        // REQ-PLA-03: lo apoyado encima toma la temperatura de la plancha (por su lado de abajo).
        let temp = self.estado.temp;
        let mut hay_carne = false;
        if let Some(zona) = &self.zona {
            for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                if let Ok(mut c) = cuerpo.try_cast::<Comida>() {
                    hay_carne |= c.bind().por_lados();
                    c.bind_mut().exponer(temp);
                }
            }
        }

        // REQ-SON-08: chisporroteo solo con carne encima y la plancha caliente.
        let suena = self.estado.encendida && temp > TEMP_CHISPOROTEO && hay_carne;
        if suena != self.chisporrotea {
            self.chisporrotea = suena;
            crate::sonido::bucle(&self.to_gd().upcast::<Node3D>(), ids::PLANCHA_CHISPOROTEO, suena);
        }
    }
}
