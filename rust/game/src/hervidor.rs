//! SPEC-003 · Hervidor (baño maría): cuba con agua que calienta lo que tiene adentro.

use carrito_core::forma::TipoPieza;
use carrito_core::hervidor::{AguaHervidor, NIVEL_AGUA, TEMP_MAX_AGUA};
use carrito_core::sonido::ids;
use godot::classes::base_material_3d::Feature;
use godot::classes::{Area3D, BoxShape3D, INode3D, Node3D, StandardMaterial3D, StaticBody3D};
use godot::prelude::*;

use std::collections::HashMap;

use crate::comida::{self, Comida};
use crate::datos::catalogo;
use crate::{formas, modelos};

const ESPESOR: f32 = 0.012;
/// Qué tan rápido lo que flota vuelve a la superficie y se acuesta (1/s). REQ-COC-08
const GANANCIA_FLOTAR: f32 = 10.0;
const GANANCIA_ACOSTAR: f32 = 8.0;
/// Velocidad máxima con la que sube o baja hacia la superficie (m/s).
const VELOCIDAD_MAX_FLOTAR: f32 = 1.0;
/// Freno del agua a lo que se mueve de costado, por cuadro.
const FRENO_AGUA: f32 = 0.9;
/// Qué tan rápido va a su lugar en la fila (1/s) y a qué velocidad máxima (m/s). REQ-COC-08
const GANANCIA_FILA: f32 = 4.0;
const VELOCIDAD_MAX_FILA: f32 = 0.3;
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
    /// Lugar de la superficie de cada cosa que flota (desde el centro del piso). REQ-COC-08
    lugares: HashMap<InstanceId, ([f32; 3], Gd<Comida>)>,
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
            lugares: HashMap::new(),
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

    /// REQ-COC-10: dónde van los primeros `n` alimentos volcados (en los lugares libres).
    pub fn lugares_volcado(&self, n: u32, largo: f32, grosor: f32) -> Vec<Transform3D> {
        self.lugares_libres(largo, grosor).into_iter().take(n as usize).collect()
    }

    /// REQ-COC-08, REQ-COC-10 (TASK-0262): lugares libres en la superficie del agua para algo
    /// de `largo` × `grosor`, en orden (una sola capa, flotando, acostado a lo largo de la
    /// cuba). Descuenta lo que ya está en el agua. Vacío = hervidor lleno.
    pub fn lugares_libres(&self, largo: f32, grosor: f32) -> Vec<Transform3D> {
        let t = self.base().get_global_transform();
        let ocupados: Vec<[f32; 3]> = self
            .en_el_agua()
            .iter()
            .map(|c| self.lugares.get(&c.instance_id()).map(|(l, _)| *l).unwrap_or_else(|| self.en_la_cuba(c)))
            .collect();
        carrito_core::hervidor::lugares_libres(self.interior, largo, grosor, &ocupados)
            .into_iter()
            .map(|p| Transform3D::new(t.basis.orthonormalized(), self.a_global(p)))
            .collect()
    }

    /// Lo que está en el agua (sin lo que tiene el jugador en la mano). REQ-COC-08
    pub fn en_el_agua(&self) -> Vec<Gd<Comida>> {
        let Some(zona) = &self.zona_agua else { return Vec::new() };
        zona.get_overlapping_bodies()
            .iter_shared()
            .filter_map(|c| c.try_cast::<Comida>().ok())
            .filter(|c| !c.is_queued_for_deletion() && !c.bind().sostenida)
            .collect()
    }

    /// Altura (global) de la superficie del agua. REQ-COC-08
    pub fn altura_superficie(&self) -> f32 {
        let alto = ESPESOR + carrito_core::hervidor::altura_superficie(self.interior);
        (self.base().get_global_transform() * Vector3::new(0.0, alto, 0.0)).y
    }

    /// Posición de un alimento en la cuba (desde el centro del piso interior).
    fn en_la_cuba(&self, c: &Gd<Comida>) -> [f32; 3] {
        let p = self.base().get_global_transform().affine_inverse() * c.get_global_position();
        [p.x, p.y - ESPESOR, p.z]
    }

    fn a_global(&self, p: [f32; 3]) -> Vector3 {
        self.base().get_global_transform() * (formas::v3(p) + Vector3::new(0.0, ESPESOR, 0.0))
    }

    /// REQ-COC-08, REQ-COC-10: cada cosa que entra al agua se queda con el lugar libre de la
    /// superficie más cercano (en filas a lo largo de la cuba) hasta que sale; así no se
    /// apilan. Entre las que flotan en su lugar no chocan (se acomodan sin trabarse cruzadas:
    /// cada una tiene su lugar). Si no queda lugar, flota donde está y choca con todo.
    fn repartir_lugares(&mut self, cuerpos: &[Gd<Comida>]) {
        let ids: Vec<InstanceId> = cuerpos.iter().map(|c| c.instance_id()).collect();
        let salen: Vec<InstanceId> = self.lugares.keys().filter(|id| !ids.contains(id)).copied().collect();
        for id in salen {
            if let Some((_, mut c)) = self.lugares.remove(&id)
                && c.is_instance_valid()
            {
                for (_, otra) in self.lugares.values_mut() {
                    if otra.is_instance_valid() {
                        c.remove_collision_exception_with(&*otra);
                        otra.remove_collision_exception_with(&c);
                    }
                }
            }
        }
        for c in cuerpos {
            if self.lugares.contains_key(&c.instance_id()) {
                continue;
            }
            let (largo, grosor) = catalogo()
                .producto(c.bind().producto())
                .map(|d| {
                    let (media_altura, medio_ancho, _) = comida::medidas_de(d);
                    (medio_ancho * 2.0, media_altura * 2.0)
                })
                .unwrap_or((0.15, 0.022));
            let ocupados: Vec<[f32; 3]> = self.lugares.values().map(|(l, _)| *l).collect();
            let p = self.en_la_cuba(c);
            let distancia = |l: &[f32; 3]| (l[0] - p[0]).powi(2) + (l[2] - p[2]).powi(2);
            if let Some(l) = carrito_core::hervidor::lugares_libres(self.interior, largo, grosor, &ocupados)
                .into_iter()
                .min_by(|a, b| distancia(a).total_cmp(&distancia(b)))
            {
                let mut nueva = c.clone();
                for (_, otra) in self.lugares.values() {
                    if otra.is_instance_valid() {
                        nueva.add_collision_exception_with(otra);
                    }
                }
                self.lugares.insert(c.instance_id(), (l, c.clone()));
            }
        }
    }

    /// REQ-COC-08 (TASK-0262): lo que está en el agua flota: sube o baja hasta tener el centro
    /// en la superficie, se acuesta (su eje Y hacia arriba o hacia abajo, lo más cercano: la
    /// salchicha queda con el largo horizontal) y va a su `lugar` (global), alineado con el largo
    /// de la cuba (`eje_cuba`). Se maneja con la velocidad, compensando la gravedad del paso de
    /// física, para que no se hunda ni se apile en el fondo.
    fn flotar(c: &mut Gd<Comida>, lugar: Option<Vector3>, eje_cuba: Vector3, superficie: f32, dt: f32) {
        if dt <= 0.0 {
            return;
        }
        let ganancia = |g: f32| (g * dt).min(0.5) / dt;
        let pos = c.get_global_position();
        let g = c.get_gravity() * c.get_gravity_scale();
        let mut v = c.get_linear_velocity();
        let falta = superficie - pos.y;
        v.y = (falta * ganancia(GANANCIA_FLOTAR)).clamp(-VELOCIDAD_MAX_FLOTAR, VELOCIDAD_MAX_FLOTAR) - g.y * dt;
        match lugar {
            Some(l) => {
                let mut h = Vector3::new(l.x - pos.x, 0.0, l.z - pos.z) * ganancia(GANANCIA_FILA);
                if h.length() > VELOCIDAD_MAX_FILA {
                    h = h.normalized() * VELOCIDAD_MAX_FILA;
                }
                v.x = h.x;
                v.z = h.z;
            }
            None => {
                v.x *= FRENO_AGUA;
                v.z *= FRENO_AGUA;
            }
        }
        c.set_linear_velocity(v);

        let base = c.get_global_transform().basis;
        let eje = base.col_b().normalized();
        let arriba = if eje.y >= 0.0 { Vector3::UP } else { Vector3::DOWN };
        let mut w = eje.cross(arriba) * ganancia(GANANCIA_ACOSTAR);
        // Girar sobre la vertical hasta quedar a lo largo de la cuba (para cualquier lado).
        let largo = Vector3::new(base.col_a().x, 0.0, base.col_a().z);
        w.y = if lugar.is_some() && largo.length() > 0.1 {
            let largo = largo.normalized();
            let e = if largo.dot(eje_cuba) >= 0.0 { eje_cuba } else { -eje_cuba };
            largo.cross(e).y.atan2(largo.dot(e)) * ganancia(GANANCIA_ACOSTAR)
        } else {
            c.get_angular_velocity().y * FRENO_AGUA
        };
        c.set_angular_velocity(w);
    }

    /// Solo para pruebas.
    pub fn encendido(&self) -> bool {
        self.agua.encendido
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

        // REQ-COC-08: todo alimento dentro del agua toma su temperatura (REQ-COC-05: en el
        // agua no se pasa ni se quema) y flota.
        let temp = self.agua.temp;
        if let Some(zona) = &self.zona_agua {
            for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                if let Ok(mut c) = cuerpo.try_cast::<Comida>() {
                    c.bind_mut().exponer_agua(temp);
                }
            }
        }
        let cuerpos = self.en_el_agua();
        self.repartir_lugares(&cuerpos);
        let superficie = self.altura_superficie();
        let eje_cuba = {
            let x = self.base().get_global_transform().basis.col_a();
            Vector3::new(x.x, 0.0, x.z).normalized()
        };
        for mut c in cuerpos {
            let lugar = self.lugares.get(&c.instance_id()).map(|(l, _)| self.a_global(*l));
            Self::flotar(&mut c, lugar, eje_cuba, superficie, delta as f32);
        }
    }
}
