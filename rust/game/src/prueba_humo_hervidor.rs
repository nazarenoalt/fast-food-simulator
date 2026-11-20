//! Prueba de humo de la etapa 2.5 · agente D: REQ-COC-05, REQ-COC-08, REQ-COC-10, REQ-DIA-08. (TASK-0250)

use carrito_core::coccion::Punto;
use godot::classes::{DirectionalLight3D, ProjectSettings};
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::comida::{self, Comida};
use crate::datos::catalogo;
use crate::dia_noche::{DiaNoche, sombras};
use crate::hervidor::Hervidor;
use crate::jugador::Jugador;
use crate::paquete::Paquete;

/// Cuadros para que se acomoden en el agua después de volcarlas.
const ESPERA_VOLCADO: u32 = 120;
const ESPERA_LLENO: u32 = 60;
/// Segundos de juego en el agua caliente después de dejarlas a punto de pasarse.
const SEGUNDOS_EN_AGUA: u32 = 40;
/// Avance con el que se las deja (a 1 del de Pasado, 13): sin el freno, en ~15 s se pasarían.
const AVANCE_CASI_PASADA: f32 = 12.0;
/// Qué tan lejos de la superficie puede quedar el centro de lo que flota (m).
const TOLERANCIA_SUPERFICIE: f32 = 0.008;

/// Dirección hacia el sol (eje Z de su luz).
fn dir_sol(sol: &Gd<DirectionalLight3D>) -> Vector3 {
    sol.get_global_transform().basis.col_c().normalized()
}

/// Ángulo entre dos direcciones (con atan2: con acos un ángulo chiquito da 0 en f32).
fn grados_entre(a: Vector3, b: Vector3) -> f32 {
    a.cross(b).length().atan2(a.dot(b)).to_degrees()
}

impl PruebaHumo {
    /// Hervidor prendido a 95 °C: vuelco una caja de 12 salchichas y quedan flotando en la
    /// superficie (acostadas, no en el fondo); con 2 más (14) está lleno y `lugares_libres` da
    /// vacío; dejadas a punto de pasarse y 40 s en el agua (lo que equivale a muchos minutos)
    /// siguen Cocidas. Y el sol se mueve de forma continua con las sombras configuradas para no
    /// temblar. No cambia día ni hora. Se llama cada cuadro hasta que devuelve true.
    pub(super) fn chequear_hervidor(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut h), Some(dn), Some(mut j)) =
            (todos::<Hervidor>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop(), todos::<Jugador>(&mundo).pop())
        else {
            self.chequear(false, "REQ-COC-08 hay hervidor, reloj y jugador");
            return true;
        };
        let Some(sol) = dn.bind().sol() else {
            self.chequear(false, "REQ-DIA-08 hay sol");
            return true;
        };
        let def = catalogo().producto("salchicha").expect("salchicha").clone();
        let (media_altura, medio_ancho, _) = comida::medidas_de(&def);
        let (largo, grosor) = (medio_ancho * 2.0, media_altura * 2.0);
        let en_agua = |h: &Gd<Hervidor>| -> Vec<Gd<Comida>> {
            h.bind().en_el_agua().into_iter().filter(|c| c.bind().producto() == "salchicha").collect()
        };
        let esperar = |yo: &Self, cuadros: u32| yo.cuadro < yo.cuadro5 + cuadros;
        let siguiente = |yo: &mut Self| {
            yo.fase5 += 1;
            yo.cuadro5 = yo.cuadro;
        };
        match self.fase5 {
            0 => {
                self.chequear_sombras(&sol);
                let d = dir_sol(&sol);
                self.notas5 =
                    vec![d.x as f64, d.y as f64, d.z as f64, h.bind().encendido() as u8 as f64, self.cuadro as f64];
                // Hervidor prendido, agua a 95 °C y vacío; nada en la mano.
                if !h.bind().encendido() {
                    h.bind_mut().alternar();
                }
                h.bind_mut().set_temperatura(95.0);
                for mut c in h.bind().en_el_agua().into_iter().chain(Self::salchichas_en_hervidor(&mundo)) {
                    c.queue_free();
                }
                if let Some(mut viejo) = j.bind_mut().soltar() {
                    viejo.set_global_position(Vector3::new(-5.0, 0.3, carrito_core::plaza::Z_VEREDA));
                }
                siguiente(self);
                false
            }
            1 => {
                // REQ-DIA-08: el sol se mueve de forma continua (un poquito cada cuadro).
                let antes = Vector3::new(self.notas5[0] as f32, self.notas5[1] as f32, self.notas5[2] as f32);
                let paso = grados_entre(antes, dir_sol(&sol));
                self.chequear(
                    paso > 0.0 && paso < 0.05,
                    &format!(
                        "REQ-DIA-08 el sol se mueve de forma continua ({paso:.4}° en {} cuadros)",
                        self.cuadro - self.cuadro5
                    ),
                );
                let por_cuadro = paso / (self.cuadro - self.cuadro5).max(1) as f32;
                self.notas5.push(por_cuadro as f64);
                // REQ-COC-08: vacío, entran 14 salchichas en una sola capa.
                let libres = h.bind().lugares_libres(largo, grosor).len();
                self.chequear(libres == 14, &format!("REQ-COC-08 en el hervidor vacío hay 14 lugares ({libres})"));
                // REQ-COC-10: vuelco una caja de 12.
                let bloque = catalogo().bloque("caja_salchichas_12").expect("caja de salchichas").clone();
                let mut caja = Paquete::crear(bloque);
                mundo.clone().add_child(&caja);
                caja.set_global_position(j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
                j.bind_mut().agarrar(caja.clone().upcast());
                j.bind_mut().volcar(&h);
                if !caja.is_queued_for_deletion()
                    && let Some(mut p) = j.bind_mut().soltar()
                {
                    p.queue_free();
                }
                siguiente(self);
                false
            }
            2 => {
                if esperar(self, ESPERA_VOLCADO) {
                    return false;
                }
                let dentro = en_agua(&h).len();
                self.chequear(
                    dentro == 12,
                    &format!("REQ-COC-10 las 12 salchichas volcadas están en el agua ({dentro})"),
                );
                // Completo el hervidor en los lugares libres que quedan.
                for t in h.bind().lugares_libres(largo, grosor) {
                    let c = Comida::crear("salchicha");
                    mundo.clone().add_child(&c);
                    c.clone().set_global_transform(t);
                }
                siguiente(self);
                false
            }
            3 => {
                if esperar(self, ESPERA_LLENO) {
                    return false;
                }
                let salchichas = en_agua(&h);
                let libres = h.bind().lugares_libres(largo, grosor).len();
                self.chequear(
                    salchichas.len() == 14 && libres == 0,
                    &format!("REQ-COC-08 con 14 salchichas está lleno: lugares_libres da vacío ({} adentro, {libres} libres)", salchichas.len()),
                );
                self.chequear_flotan(&h, &salchichas, "recién volcadas");
                for mut c in salchichas {
                    c.bind_mut().forzar_avance(AVANCE_CASI_PASADA);
                }
                siguiente(self);
                false
            }
            4 => {
                if esperar(self, SEGUNDOS_EN_AGUA * 60) {
                    return false;
                }
                let salchichas = en_agua(&h);
                let puntos: Vec<Option<Punto>> = salchichas.iter().map(|c| c.bind().punto()).collect();
                let cocidas = puntos.iter().filter(|p| **p == Some(Punto::Cocido)).count();
                self.chequear(
                    salchichas.len() == 14 && cocidas == 14,
                    &format!(
                        "REQ-COC-05 a 95 °C, {SEGUNDOS_EN_AGUA} s más en el agua a punto de pasarse: siguen Cocidas ({cocidas} de {}, {:?})",
                        salchichas.len(),
                        puntos.iter().find(|p| **p != Some(Punto::Cocido))
                    ),
                );
                self.chequear_flotan(&h, &salchichas, &format!("después de {SEGUNDOS_EN_AGUA} s"));
                // REQ-DIA-08: en ese rato el sol siguió avanzando parejo (sin saltos): lo movido es
                // lo de un cuadro por los cuadros que pasaron (1 min de juego por segundo).
                let antes = Vector3::new(self.notas5[0] as f32, self.notas5[1] as f32, self.notas5[2] as f32);
                let movido = grados_entre(antes, dir_sol(&sol));
                let cuadros = self.cuadro as f64 - self.notas5[4];
                let esperado = (self.notas5[5] * cuadros) as f32;
                self.chequear(
                    movido > 0.0 && (movido - esperado).abs() < esperado * 0.25,
                    &format!(
                        "REQ-DIA-08 el sol siguió moviéndose parejo ({movido:.2}° en {cuadros} cuadros, se esperaban {esperado:.2}°)"
                    ),
                );
                for mut c in salchichas {
                    c.queue_free();
                }
                if h.bind().encendido() != (self.notas5[3] > 0.5) {
                    h.bind_mut().alternar();
                }
                true
            }
            _ => true,
        }
    }

    /// REQ-COC-08: flotan con el centro en la superficie (no en el fondo) y acostadas.
    fn chequear_flotan(&mut self, h: &Gd<Hervidor>, salchichas: &[Gd<Comida>], cuando: &str) {
        let superficie = h.bind().altura_superficie();
        let peor = salchichas.iter().map(|c| (c.get_global_position().y - superficie).abs()).fold(0.0f32, f32::max);
        let paradas =
            salchichas.iter().filter(|c| c.get_global_transform().basis.col_a().normalized().y.abs() > 0.2).count();
        self.chequear(
            !salchichas.is_empty() && peor < TOLERANCIA_SUPERFICIE && paradas == 0,
            &format!(
                "REQ-COC-08 {cuando}: flotan en la superficie, acostadas (peor a {:.1} mm de la superficie, {paradas} no acostadas)",
                peor * 1000.0
            ),
        );
    }

    /// REQ-DIA-08: la luz del sol y el proyecto tienen los ajustes de sombras estables.
    fn chequear_sombras(&mut self, sol: &Gd<DirectionalLight3D>) {
        use godot::classes::directional_light_3d::{ShadowMode, SkyMode};
        use godot::classes::light_3d::Param;
        let ajustes = ProjectSettings::singleton();
        let tamano = ajustes.get_setting("rendering/lights_and_shadows/directional_shadow/size").to::<i64>();
        let filtro = ajustes
            .get_setting("rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality")
            .to::<i64>();
        let ok = sol.has_shadow()
            && sol.get_shadow_mode() == ShadowMode::PARALLEL_4_SPLITS
            && sol.is_blend_splits_enabled()
            && sol.get_sky_mode() == SkyMode::LIGHT_ONLY
            && sol.get_param(Param::SIZE) == 0.0
            && sol.get_param(Param::SHADOW_MAX_DISTANCE) == sombras::DISTANCIA_MAX
            && sol.get_param(Param::SHADOW_SPLIT_1_OFFSET) == sombras::TRAMOS[0]
            && sol.get_param(Param::SHADOW_BLUR) == sombras::DESENFOQUE
            && sol.get_param(Param::SHADOW_NORMAL_BIAS) == sombras::NORMAL_BIAS
            && tamano == 8192
            && filtro == 3;
        self.chequear(
            ok,
            &format!(
                "REQ-DIA-08 sombras estables: 4 tramos mezclados hasta {} m, PCF sin PCSS, atlas {tamano}, filtro {filtro}",
                sol.get_param(Param::SHADOW_MAX_DISTANCE)
            ),
        );
    }
}
