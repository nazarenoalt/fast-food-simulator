//! SPEC-007 · Día y noche: mueve el sol, cambia el cielo y prende las luces.

use carrito_core::forma::TipoPieza;
use carrito_core::reloj::Reloj;
use godot::classes::base_material_3d::{Flags, ShadingMode};
use godot::classes::directional_light_3d::{ShadowMode, SkyMode};
use godot::classes::environment::{AmbientSource, BgMode, ToneMapper};
use godot::classes::light_3d::Param;
use godot::classes::sky::ProcessMode as SkyProcessMode;
use godot::classes::{
    DirectionalLight3D, Environment, INode, Input, MeshInstance3D, Node, ProceduralSkyMaterial, Sky, WorldEnvironment,
};
use godot::prelude::*;

use crate::luz::{GRUPO_LUCES_NOCHE, LuzNocturna};
use crate::{formas, nocturno};

pub const GRUPO: &str = "dia_noche";

/// REQ-AMB-12: tamaño aparente del disco del sol en el cielo (grados).
const TAMANO_DISCO_SOL: f32 = 1.0;

/// REQ-DIA-08, REQ-AMB-14: ajustes de las sombras del sol (TASK-0258). El sol gira un poquito
/// cada cuadro y Godot vuelve a dibujar el mapa de sombras con la grilla girada: los bordes se
/// corren de a un texel ("tiemblan como líquido"). Se achica el texel en lo cercano (4 tramos
/// más cortos y repartidos hacia adelante) y se suaviza el borde con PCF (desenfoque y
/// filtrado de `project.godot`), sin PCSS (tamaño 0: su ruido por píxel hierve al moverse).
pub mod sombras {
    /// Hasta dónde hay sombras (m): toda la plaza vista desde el carrito.
    pub const DISTANCIA_MAX: f32 = 100.0;
    /// Dónde termina cada tramo, como parte de la distancia: 6 m, 18 m, 45 m y 100 m.
    pub const TRAMOS: [f32; 3] = [0.06, 0.18, 0.45];
    /// Desde dónde se desvanecen, como parte de la distancia.
    pub const DESVANECER: f32 = 0.85;
    /// Desenfoque del borde (PCF).
    pub const DESENFOQUE: f32 = 1.5;
    /// Corrimientos contra el "acné" (manchas que se mueven con el sol en las superficies).
    pub const BIAS: f32 = 0.1;
    pub const NORMAL_BIAS: f32 = 2.0;
    /// Profundidad del "pancake" (m): los que tapan desde fuera de la vista igual hacen sombra.
    pub const PANCAKE: f32 = 20.0;
}

/// REQ-DIA-08: la luz del sol con sombras estables y suaves.
fn configurar_sombras_sol(sol: &mut Gd<DirectionalLight3D>) {
    sol.set_shadow(true);
    sol.set_sky_mode(SkyMode::LIGHT_ONLY);
    // Sin tamaño aparente: PCF en vez de PCSS (el disco del cielo lo pinta otra luz).
    sol.set_param(Param::SIZE, 0.0);
    // REQ-AMB-14: sombras continuas, tramos mezclados (sin cortes redondos).
    sol.set_shadow_mode(ShadowMode::PARALLEL_4_SPLITS);
    sol.set_blend_splits(true);
    sol.set_param(Param::SHADOW_MAX_DISTANCE, sombras::DISTANCIA_MAX);
    sol.set_param(Param::SHADOW_SPLIT_1_OFFSET, sombras::TRAMOS[0]);
    sol.set_param(Param::SHADOW_SPLIT_2_OFFSET, sombras::TRAMOS[1]);
    sol.set_param(Param::SHADOW_SPLIT_3_OFFSET, sombras::TRAMOS[2]);
    sol.set_param(Param::SHADOW_FADE_START, sombras::DESVANECER);
    sol.set_param(Param::SHADOW_BLUR, sombras::DESENFOQUE);
    sol.set_param(Param::SHADOW_BIAS, sombras::BIAS);
    sol.set_param(Param::SHADOW_NORMAL_BIAS, sombras::NORMAL_BIAS);
    sol.set_param(Param::SHADOW_PANCAKE_SIZE, sombras::PANCAKE);
}

#[derive(GodotClass)]
#[class(base=Node)]
pub struct DiaNoche {
    base: Base<Node>,
    reloj: Reloj,
    noche: Option<bool>,
    sol: Option<Gd<DirectionalLight3D>>,
    disco_sol: Option<Gd<DirectionalLight3D>>,
    luna: Option<Gd<DirectionalLight3D>>,
    entorno: Option<Gd<Environment>>,
    cielo: Option<Gd<ProceduralSkyMaterial>>,
    disco_luna: Option<Gd<MeshInstance3D>>,
}

#[godot_api]
impl INode for DiaNoche {
    fn init(base: Base<Node>) -> Self {
        Self {
            base,
            reloj: Reloj::default(),
            noche: None,
            sol: None,
            disco_sol: None,
            luna: None,
            entorno: None,
            cielo: None,
            disco_luna: None,
        }
    }

    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);

        let cielo = ProceduralSkyMaterial::new_gd();
        let mut sky = Sky::new_gd();
        sky.set_material(&cielo);
        sky.set_process_mode(SkyProcessMode::INCREMENTAL);

        let mut env = Environment::new_gd();
        env.set_background(BgMode::SKY);
        env.set_sky(&sky);
        env.set_ambient_source(AmbientSource::SKY);
        env.set_tonemapper(ToneMapper::FILMIC);
        env.set_glow_enabled(true);
        env.set_ssao_enabled(true);
        // Niebla suave: esconde el horizonte y da profundidad. Su color sigue al cielo.
        env.set_fog_enabled(true);
        env.set_fog_density(0.004);
        env.set_fog_sky_affect(0.0);
        let mut we = WorldEnvironment::new_alloc();
        we.set_environment(&env);
        self.base_mut().add_child(&we);

        let mut sol = DirectionalLight3D::new_alloc();
        configurar_sombras_sol(&mut sol);
        sol.set_name("Sol");
        self.base_mut().add_child(&sol);

        // REQ-AMB-12: el disco del sol lo dibuja otra luz que solo pinta el cielo (con su tamaño
        // aparente); así la luz que hace sombra no usa sombras PCSS (REQ-DIA-08).
        let mut disco_sol = DirectionalLight3D::new_alloc();
        disco_sol.set_sky_mode(SkyMode::SKY_ONLY);
        disco_sol.set_shadow(false);
        disco_sol.set_param(Param::SIZE, TAMANO_DISCO_SOL);
        disco_sol.set_name("DiscoSol");
        self.base_mut().add_child(&disco_sol);

        let mut luna = DirectionalLight3D::new_alloc();
        luna.set_color(Color::from_rgb(0.6, 0.7, 1.0));
        luna.set_name("Luna");
        // Fija, alta en el cielo.
        luna.set_rotation_degrees(Vector3::new(-55.0, 160.0, 0.0));
        self.base_mut().add_child(&luna);

        // REQ-AMB-12: disco de la luna, lejos, en la dirección de su luz.
        let mut mat = formas::material([0.92, 0.93, 1.0], 1.0, false, 1.5);
        mat.set_shading_mode(ShadingMode::UNSHADED);
        mat.set_flag(Flags::DISABLE_FOG, true);
        let mut disco = formas::instancia_malla(formas::malla(TipoPieza::Esfera, [7.0, 0.0, 0.0]), mat);
        disco.set_cast_shadows_setting(godot::classes::geometry_instance_3d::ShadowCastingSetting::OFF);
        let dir = luna.get_transform().basis.col_c();
        disco.set_position(dir * 280.0);
        self.base_mut().add_child(&disco);
        self.disco_luna = Some(disco);

        self.sol = Some(sol);
        self.disco_sol = Some(disco_sol);
        self.luna = Some(luna);
        self.entorno = Some(env);
        self.cielo = Some(cielo);
        self.aplicar();
        // Las luces se crean después que este nodo: se prenden/apagan en el primer cuadro.
        self.noche = None;
    }

    fn process(&mut self, delta: f64) {
        // REQ-DIA-07
        if Input::singleton().is_action_just_pressed("tiempo_rapido") && !crate::armado::escribiendo() {
            self.reloj.alternar_rapido();
        }
        // REQ-DIA-01, REQ-DIA-02
        self.reloj.avanzar(delta);
        self.aplicar();
    }
}

#[godot_api]
impl DiaNoche {
    /// Pone el reloj en un minuto del día (0–1439). Para pruebas y para cargar partidas.
    #[func]
    pub fn set_minuto(&mut self, minuto: f64) {
        self.reloj.minuto = minuto.rem_euclid(carrito_core::reloj::MINUTOS_DIA);
        self.aplicar();
    }

    /// Pone el número de día (1 = lunes, REQ-EVE-01). Para pruebas y para cargar partidas.
    #[func]
    pub fn set_dia(&mut self, dia: u32) {
        self.reloj.dia = dia.max(1);
        self.aplicar();
    }
}

impl DiaNoche {
    /// (día − 1) × 1440 + minuto del día.
    pub fn minuto_absoluto(&self) -> f64 {
        (self.reloj.dia as f64 - 1.0) * carrito_core::reloj::MINUTOS_DIA + self.reloj.minuto
    }

    /// Hora del día con decimales (13.5 = 13:30).
    pub fn hora(&self) -> f32 {
        (self.reloj.minuto / 60.0) as f32
    }

    pub fn dia(&self) -> u32 {
        self.reloj.dia
    }

    /// La luz del sol (la que hace sombra). Para pruebas (REQ-DIA-08).
    pub fn sol(&self) -> Option<Gd<DirectionalLight3D>> {
        self.sol.clone()
    }

    /// Minutos de juego que pasan por segundo real (incluye el ×30 de prueba).
    pub fn minutos_por_segundo(&self) -> f64 {
        self.reloj.minutos_por_segundo * self.reloj.multiplicador
    }

    pub fn hora_texto(&self) -> String {
        let rapido = if self.reloj.multiplicador > 1.0 { "  ×30" } else { "" };
        // REQ-EVE-01: el día de la semana al lado de la hora.
        let semana = carrito_core::eventos::dia_semana(self.reloj.dia).texto();
        format!("Día {} · {semana} {}{rapido}", self.reloj.dia, self.reloj.hora_texto())
    }

    fn aplicar(&mut self) {
        let sol = self.reloj.sol();

        // REQ-DIA-03, REQ-DIA-04, REQ-DIA-08: el sol se mueve de forma continua (cada cuadro).
        let d = formas::v3(sol.direccion());
        for luz in [&mut self.sol, &mut self.disco_sol].into_iter().flatten() {
            luz.set_position(d * 100.0);
            if d.y.abs() < 0.999 {
                luz.look_at(Vector3::ZERO);
            }
            luz.set_color(formas::color(sol.color()));
            luz.set_param(Param::ENERGY, sol.energia());
            luz.set_visible(sol.energia() > 0.001);
        }
        // REQ-DIA-05
        if let Some(luna) = &mut self.luna {
            luna.set_param(Param::ENERGY, sol.energia_luna());
            luna.set_visible(sol.energia_luna() > 0.001);
        }
        // REQ-AMB-11, REQ-AMB-12
        nocturno::set_color_nubes(sol.color_nubes());
        if let Some(d) = &mut self.disco_luna {
            d.set_visible(sol.luna_visible());
        }
        if let Some(env) = &mut self.entorno {
            env.set_ambient_light_energy(sol.energia_ambiente());
            env.set_fog_light_color(formas::color(sol.colores_cielo().1));
        }
        if let Some(cielo) = &mut self.cielo {
            let (arriba, horizonte) = sol.colores_cielo();
            cielo.set_sky_top_color(formas::color(arriba));
            cielo.set_sky_horizon_color(formas::color(horizonte));
            cielo.set_ground_horizon_color(formas::color(horizonte));
            cielo.set_ground_bottom_color(formas::color(horizonte));
            cielo.set_energy_multiplier(0.3 + 0.7 * sol.energia_ambiente());
        }

        // REQ-DIA-06: prender/apagar las luces cuando cambia.
        let noche = sol.es_de_noche();
        if self.noche != Some(noche) {
            self.noche = Some(noche);
            self.prender_luces(noche);
        }
    }

    fn prender_luces(&mut self, on: bool) {
        nocturno::set_noche(on);
        let Some(arbol) = self.base().get_tree_or_null() else { return };
        for n in arbol.get_nodes_in_group(GRUPO_LUCES_NOCHE).iter_shared() {
            if let Ok(mut l) = n.try_cast::<LuzNocturna>() {
                l.bind_mut().set_encendida(on);
            }
        }
    }
}
