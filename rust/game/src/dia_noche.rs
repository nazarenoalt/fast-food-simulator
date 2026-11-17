//! SPEC-007 · Día y noche: mueve el sol, cambia el cielo y prende las luces.

use carrito_core::reloj::Reloj;
use godot::classes::environment::{AmbientSource, BgMode, ToneMapper};
use godot::classes::sky::ProcessMode as SkyProcessMode;
use godot::classes::{
    DirectionalLight3D, Environment, INode, Input, Node, ProceduralSkyMaterial, Sky, WorldEnvironment,
};
use godot::prelude::*;

use crate::formas;
use crate::luz::{GRUPO_LUCES_NOCHE, LuzNocturna};

pub const GRUPO: &str = "dia_noche";

#[derive(GodotClass)]
#[class(base=Node)]
pub struct DiaNoche {
    base: Base<Node>,
    reloj: Reloj,
    noche: Option<bool>,
    sol: Option<Gd<DirectionalLight3D>>,
    luna: Option<Gd<DirectionalLight3D>>,
    entorno: Option<Gd<Environment>>,
    cielo: Option<Gd<ProceduralSkyMaterial>>,
}

#[godot_api]
impl INode for DiaNoche {
    fn init(base: Base<Node>) -> Self {
        Self { base, reloj: Reloj::default(), noche: None, sol: None, luna: None, entorno: None, cielo: None }
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
        sol.set_shadow(true);
        sol.set_name("Sol");
        self.base_mut().add_child(&sol);

        let mut luna = DirectionalLight3D::new_alloc();
        luna.set_color(Color::from_rgb(0.6, 0.7, 1.0));
        luna.set_name("Luna");
        // Fija, alta en el cielo.
        luna.set_rotation_degrees(Vector3::new(-55.0, 160.0, 0.0));
        self.base_mut().add_child(&luna);

        self.sol = Some(sol);
        self.luna = Some(luna);
        self.entorno = Some(env);
        self.cielo = Some(cielo);
        self.aplicar();
        // Las luces se crean después que este nodo: se prenden/apagan en el primer cuadro.
        self.noche = None;
    }

    fn process(&mut self, delta: f64) {
        // REQ-DIA-07
        if Input::singleton().is_action_just_pressed("tiempo_rapido") {
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
}

impl DiaNoche {
    pub fn hora_texto(&self) -> String {
        let rapido = if self.reloj.multiplicador > 1.0 { "  ×30" } else { "" };
        format!("Día {}  {}{rapido}", self.reloj.dia, self.reloj.hora_texto())
    }

    fn aplicar(&mut self) {
        let sol = self.reloj.sol();

        // REQ-DIA-03, REQ-DIA-04
        if let Some(luz) = &mut self.sol {
            let d = formas::v3(sol.direccion());
            luz.set_position(d * 100.0);
            if d.y.abs() < 0.999 {
                luz.look_at(Vector3::ZERO);
            }
            luz.set_color(formas::color(sol.color()));
            luz.set_param(godot::classes::light_3d::Param::ENERGY, sol.energia());
            luz.set_visible(sol.energia() > 0.001);
        }
        // REQ-DIA-05
        if let Some(luna) = &mut self.luna {
            luna.set_param(godot::classes::light_3d::Param::ENERGY, sol.energia_luna());
            luna.set_visible(sol.energia_luna() > 0.001);
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
        let Some(arbol) = self.base().get_tree_or_null() else { return };
        for n in arbol.get_nodes_in_group(GRUPO_LUCES_NOCHE).iter_shared() {
            if let Ok(mut l) = n.try_cast::<LuzNocturna>() {
                l.bind_mut().set_encendida(on);
            }
        }
    }
}
