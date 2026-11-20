//! SPEC-003 · Hervidor (baño maría): cuba con agua que calienta lo que tiene adentro.

use carrito_core::forma::TipoPieza;
use carrito_core::hervidor::{AguaHervidor, TEMP_MAX_AGUA};
use carrito_core::sonido::ids;
use godot::classes::base_material_3d::Feature;
use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D, StandardMaterial3D, StaticBody3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::{formas, modelos};

const ESPESOR: f32 = 0.012;
const NIVEL_AGUA: f32 = 0.7;
const ACERO: [f32; 3] = [0.78, 0.79, 0.8];

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Hervidor {
    base: Base<Node3D>,
    interior: [f32; 3],
    agua: AguaHervidor,
    zona_agua: Option<Gd<Area3D>>,
    piloto: Option<Gd<StandardMaterial3D>>,
    mat_agua: Option<Gd<StandardMaterial3D>>,
    /// SPEC-025: modelo 3D (el dibujo; la colisión de la batea la arma el código).
    modelo: Option<String>,
}

#[godot_api]
impl Hervidor {
    /// Enciende o apaga. REQ-COC-09
    #[func]
    pub fn alternar(&mut self) {
        self.agua.alternar();
        self.actualizar_piloto();
        // REQ-SON-08: interruptor y, mientras está prendido, el hervor.
        let yo = self.to_gd().upcast::<Node3D>();
        crate::sonido::sonar_en(&yo, ids::HERVIDOR_INTERRUPTOR, yo.get_global_position());
        crate::sonido::bucle(&yo, ids::HERVIDOR_HIERVE, self.agua.encendido);
    }
}

impl Hervidor {
    pub fn crear(interior: [f32; 3], modelo: Option<String>) -> Gd<Self> {
        Gd::from_init_fn(|base| Self {
            base,
            interior,
            agua: AguaHervidor::default(),
            zona_agua: None,
            piloto: None,
            mat_agua: None,
            modelo,
        })
    }

    /// REQ-MOD-04/05: usa el modelo para el dibujo, con su `pieza_agua` y su `pieza_piloto`.
    /// Devuelve false si no tiene modelo o no carga (entonces se dibujan las piezas simples).
    fn dibujar_modelo(&mut self, yo: &mut Gd<Node3D>) -> bool {
        let Some(m) = self.modelo.clone().and_then(|m| modelos::agregar(yo, &m)) else { return false };
        if let Some(agua) = modelos::buscar(&m, carrito_core::modelos::PIEZA_AGUA) {
            self.mat_agua = modelos::materiales_propios(&agua).into_iter().next().map(|(_, mat)| mat);
        }
        if let Some(piloto) = modelos::buscar(&m, carrito_core::modelos::PIEZA_PILOTO)
            && let Some((_, mut mat)) = modelos::materiales_propios(&piloto).into_iter().next()
        {
            mat.set_feature(Feature::EMISSION, true);
            mat.set_emission(Color::from_rgb(1.0, 0.1, 0.05));
            self.piloto = Some(mat);
        }
        true
    }

    /// REQ-COC-10: dónde va cada uno de `n` alimentos volcados (acostados a lo largo de la cuba).
    pub fn lugares_volcado(&self, n: u32, largo: f32, grosor: f32) -> Vec<Transform3D> {
        let t = self.base().get_global_transform();
        carrito_core::hervidor::acomodar_volcado(n, self.interior, largo, grosor)
            .into_iter()
            .map(|p| Transform3D::new(t.basis.orthonormalized(), t * (formas::v3(p) + Vector3::new(0.0, ESPESOR, 0.0))))
            .collect()
    }

    /// REQ-COC-08, REQ-COC-10 (TASK-0262): lugares libres en la superficie del agua para algo
    /// de `largo` × `grosor`, en orden (una sola capa, flotando). Vacío = hervidor lleno.
    /// BASE-ETAPA-2.5: el agente D descuenta los ocupados y la capa única; el agente B lo usa
    /// al colocar con la mira en el hervidor y al volcar un paquete.
    #[allow(dead_code)] // BASE-ETAPA-2.5
    pub fn lugares_libres(&self, largo: f32, grosor: f32) -> Vec<Transform3D> {
        self.lugares_volcado(1, largo, grosor)
    }

    /// Solo para pruebas.
    pub fn set_temperatura(&mut self, t: f32) {
        self.agua.temp = t;
    }

    /// Texto del cartel. REQ-COC-09
    pub fn cartel(&self) -> String {
        let accion = if self.agua.encendido { "Apagar" } else { "Encender" };
        format!("[E] {accion} hervidor — agua a {:.0} °C", self.agua.temp)
    }

    fn actualizar_piloto(&mut self) {
        let on = self.agua.encendido;
        if let Some(m) = &mut self.piloto {
            // REQ-COC-09: luz piloto roja encendida.
            m.set_emission_energy_multiplier(if on { 4.0 } else { 0.0 });
            m.set_albedo(if on { Color::from_rgb(1.0, 0.1, 0.05) } else { Color::from_rgb(0.25, 0.05, 0.05) });
        }
    }
}

#[godot_api]
impl INode3D for Hervidor {
    fn ready(&mut self) {
        let [w, h, d] = self.interior;
        let e = ESPESOR;
        let mut yo = self.to_gd().upcast::<Node3D>();
        let con_modelo = self.dibujar_modelo(&mut yo);

        // Cuba: piso + 4 paredes, con colisión (para que la comida quede adentro). Con modelo,
        // solo la colisión (REQ-MOD-04).
        let alto = h + e;
        let y = alto / 2.0;
        let cajas = [
            ([w + 2.0 * e, e, d + 2.0 * e], [0.0, e / 2.0, 0.0]),
            ([w + 2.0 * e, alto, e], [0.0, y, d / 2.0 + e / 2.0]),
            ([w + 2.0 * e, alto, e], [0.0, y, -d / 2.0 - e / 2.0]),
            ([e, alto, d], [w / 2.0 + e / 2.0, y, 0.0]),
            ([e, alto, d], [-w / 2.0 - e / 2.0, y, 0.0]),
        ];
        if con_modelo {
            let mut cuerpo = StaticBody3D::new_alloc();
            for (m, p) in cajas {
                let mut s = BoxShape3D::new_gd();
                s.set_size(formas::v3(m));
                cuerpo.add_child(&formas::nodo_colision(s.upcast(), Transform3D::new(Basis::IDENTITY, formas::v3(p))));
            }
            yo.add_child(&cuerpo);
        } else {
            for (m, p) in cajas {
                formas::caja_solida(&mut yo, m, p, ACERO, true);
            }
        }

        // Agua (solo visual) y su volumen (zona que calienta). REQ-COC-08
        let alto_agua = h * NIVEL_AGUA;
        if !con_modelo || self.mat_agua.is_none() {
            let mat_agua = formas::material([0.45, 0.65, 0.8], 0.25, false, 0.0);
            let mut agua = formas::instancia_malla(formas::malla(TipoPieza::Caja, [w, alto_agua, d]), mat_agua.clone());
            agua.set_position(Vector3::new(0.0, e + alto_agua / 2.0, 0.0));
            yo.add_child(&agua);
            self.mat_agua = Some(mat_agua);
        }

        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(w, alto_agua, d));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, e + alto_agua / 2.0, 0.0));
        zona.set_monitorable(false);
        yo.add_child(&zona);
        self.zona_agua = Some(zona);

        // Perilla y luz piloto del lado del vendedor (-Z).
        if con_modelo && self.piloto.is_some() {
            self.actualizar_piloto();
            return;
        }
        let mut perilla =
            formas::visual_pieza(&formas::pieza(TipoPieza::Cilindro, [0.018, 0.02, 0.0], [0.0; 3], [0.1, 0.1, 0.1]));
        perilla.set_rotation_degrees(Vector3::new(90.0, 0.0, 0.0));
        perilla.set_position(Vector3::new(-w / 4.0, alto * 0.55, -d / 2.0 - e - 0.01));
        yo.add_child(&perilla);
        let piloto_mat = formas::material([1.0, 0.1, 0.05], 1.0, false, 0.01);
        let mut piloto =
            formas::instancia_malla(formas::malla(TipoPieza::Esfera, [0.008, 0.0, 0.0]), piloto_mat.clone());
        piloto.set_position(Vector3::new(w / 4.0, alto * 0.55, -d / 2.0 - e - 0.004));
        yo.add_child(&piloto);
        self.piloto = Some(piloto_mat);
        self.actualizar_piloto();
    }

    fn physics_process(&mut self, delta: f64) {
        // REQ-COC-07
        self.agua.paso(delta as f32);

        // El agua se ve más clara cuanto más caliente (vapor).
        if let Some(m) = &mut self.mat_agua {
            let f = ((self.agua.temp - 20.0) / (TEMP_MAX_AGUA - 20.0)).clamp(0.0, 1.0);
            m.set_albedo(Color::from_rgba(0.45 + 0.35 * f, 0.65 + 0.2 * f, 0.8 + 0.1 * f, 0.25 + 0.15 * f));
        }

        // REQ-COC-08: todo alimento dentro del agua toma su temperatura.
        let temp = self.agua.temp;
        if let Some(zona) = &self.zona_agua {
            for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                if let Ok(mut c) = cuerpo.try_cast::<Comida>() {
                    c.bind_mut().exponer(temp);
                }
            }
        }
    }
}
