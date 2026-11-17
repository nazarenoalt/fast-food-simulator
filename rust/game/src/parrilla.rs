//! SPEC-015 · Parrilla de carbón: brasas que se calientan, se gastan y cocinan lo apoyado encima.

use carrito_core::forma::TipoPieza;
use carrito_core::parrilla::{ErrorParrilla, Parrilla as EstadoParrilla, resplandor};
use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D, StandardMaterial3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::dia_noche::{self, DiaNoche};
use crate::formas;
use crate::util;

/// Alto de la parrilla: la rejilla donde se apoya la comida (m).
const ALTO: f32 = 0.08;
const ALTO_ZONA: f32 = 0.05;
const HIERRO: [f32; 3] = [0.14, 0.14, 0.15];

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Parrilla {
    base: Base<Node3D>,
    superficie: [f32; 2],
    estado: EstadoParrilla,
    zona: Option<Gd<Area3D>>,
    brasas: Option<Gd<StandardMaterial3D>>,
}

#[godot_api]
impl Parrilla {
    /// Enciende o apaga (solo se enciende con carbón). REQ-PAR-01
    #[func]
    pub fn alternar(&mut self) -> bool {
        self.estado.alternar().is_ok()
    }
}

impl Parrilla {
    pub fn crear(superficie: [f32; 2]) -> Gd<Self> {
        Gd::from_init_fn(|base| Self { base, superficie, estado: EstadoParrilla::default(), zona: None, brasas: None })
    }

    /// REQ-PAR-01: enciende o apaga; si no se puede, devuelve el motivo para avisarle al jugador.
    pub fn usar(&mut self) -> Result<(), ErrorParrilla> {
        self.estado.alternar()
    }

    /// REQ-PAR-01: carga `kg` de carbón de una bolsa.
    pub fn cargar(&mut self, kg: f32) -> Result<(), ErrorParrilla> {
        self.estado.cargar(kg)
    }

    /// Solo para pruebas.
    pub fn set_temperatura(&mut self, t: f32) {
        self.estado.temp = t;
    }

    pub fn estado(&self) -> EstadoParrilla {
        self.estado
    }

    /// Texto del cartel. REQ-PAR-03
    pub fn cartel(&self) -> String {
        let accion = if self.estado.encendida { "Apagar" } else { "Encender" };
        format!("[E] {accion} parrilla — carbón {:.1} kg · {:.0} °C", self.estado.carbon, self.estado.temp)
            .replace('.', ",")
    }

    fn actualizar_brasas(&mut self) {
        let r = resplandor(self.estado.temp);
        if let Some(m) = &mut self.brasas {
            // REQ-PAR-03: resplandor de las brasas según su temperatura.
            m.set_emission_energy_multiplier(r * 3.0);
            m.set_albedo(Color::from_rgb(0.12 + 0.75 * r, 0.1 + 0.2 * r, 0.1));
        }
    }
}

#[godot_api]
impl INode3D for Parrilla {
    fn ready(&mut self) {
        let [w, d] = self.superficie;
        let mut yo = self.to_gd().upcast::<Node3D>();

        // Cajón de hierro con las brasas adentro; la rejilla queda a ALTO.
        formas::caja_solida(&mut yo, [w + 0.04, ALTO - 0.02, d + 0.04], [0.0, (ALTO - 0.02) / 2.0, 0.0], HIERRO, true);
        let mat = formas::material([0.12, 0.1, 0.1], 1.0, false, 0.0);
        let mut lecho =
            formas::instancia_malla(formas::malla(TipoPieza::Caja, [w - 0.02, 0.01, d - 0.02]), mat.clone());
        lecho.set_position(Vector3::new(0.0, ALTO - 0.02, 0.0));
        yo.add_child(&lecho);
        self.brasas = Some(mat);

        // Rejilla: barras finas a lo ancho, con un plano sólido muy fino para apoyar la comida.
        formas::caja_solida(&mut yo, [w, 0.006, d], [0.0, ALTO - 0.003, 0.0], HIERRO, true);
        let n = 9;
        for i in 0..n {
            let z = -d / 2.0 + (i as f32 + 0.5) * d / n as f32;
            let mut b = formas::visual_pieza(&formas::pieza(
                TipoPieza::Caja,
                [w, 0.008, 0.008],
                [0.0, ALTO + 0.002, z],
                HIERRO,
            ));
            b.set_position(Vector3::new(0.0, ALTO + 0.002, z));
            yo.add_child(&b);
        }

        // Zona que detecta lo apoyado encima. REQ-PAR-04
        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(w, ALTO_ZONA, d));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, ALTO + ALTO_ZONA / 2.0, 0.0));
        zona.set_monitorable(false);
        yo.add_child(&zona);
        self.zona = Some(zona);
        self.actualizar_brasas();
    }

    fn physics_process(&mut self, delta: f64) {
        // REQ-PAR-02: el carbón se gasta por hora de juego (con el ×30 de prueba, más rápido).
        let min_por_s = util::unico::<DiaNoche>(&self.to_gd(), dia_noche::GRUPO)
            .map(|d| d.bind().minutos_por_segundo())
            .unwrap_or(1.0);
        let horas = (delta * min_por_s / 60.0) as f32;
        self.estado.paso(delta as f32, horas);
        self.actualizar_brasas();

        // REQ-PAR-04: lo apoyado encima toma la temperatura de la parrilla por su lado de abajo.
        let temp = self.estado.temp;
        if let Some(zona) = &self.zona {
            for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                if let Ok(mut c) = cuerpo.try_cast::<Comida>() {
                    c.bind_mut().exponer(temp);
                }
            }
        }
    }
}
