//! Materiales que brillan solo de noche (ventanas, vidrieras, faros) y material de nubes.
//! Se comparten: cambiar uno cambia todos los objetos que lo usan, sin recorrer la escena.

use std::cell::RefCell;

use godot::classes::StandardMaterial3D;
use godot::classes::base_material_3d::{Feature, Flags, ShadingMode};
use godot::prelude::*;

use crate::formas;

thread_local! {
    static NOCTURNOS: RefCell<Vec<(Gd<StandardMaterial3D>, f32)>> = const { RefCell::new(Vec::new()) };
    static NUBES: RefCell<Vec<Gd<StandardMaterial3D>>> = const { RefCell::new(Vec::new()) };
    static ES_DE_NOCHE: RefCell<bool> = const { RefCell::new(false) };
}

/// Material con color de día `base` que de noche brilla con `brillo` y `energia`.
pub fn material(base: [f32; 3], brillo: [f32; 3], energia: f32) -> Gd<StandardMaterial3D> {
    let mut m = formas::material(base, 1.0, false, 0.0);
    m.set_feature(Feature::EMISSION, true);
    m.set_emission(formas::color(brillo));
    let noche = ES_DE_NOCHE.with(|n| *n.borrow());
    m.set_emission_energy_multiplier(if noche { energia } else { 0.0 });
    NOCTURNOS.with(|v| v.borrow_mut().push((m.clone(), energia)));
    m
}

/// Suma un material que ya existe (ej. la lamparita de un modelo): brilla con `energia`
/// solo de noche. REQ-MOD-07
pub fn registrar(mut m: Gd<StandardMaterial3D>, energia: f32) {
    m.set_feature(Feature::EMISSION, true);
    let noche = ES_DE_NOCHE.with(|n| *n.borrow());
    m.set_emission_energy_multiplier(if noche { energia } else { 0.0 });
    NOCTURNOS.with(|v| v.borrow_mut().push((m, energia)));
}

/// REQ-DIA-06, REQ-AMB-02, REQ-AMB-09
pub fn set_noche(on: bool) {
    ES_DE_NOCHE.with(|n| *n.borrow_mut() = on);
    NOCTURNOS.with(|v| {
        let mut v = v.borrow_mut();
        // Se olvidan los materiales que ya nadie usa (escena descargada).
        v.retain(|(m, _)| m.get_reference_count() > 1);
        for (m, e) in v.iter_mut() {
            m.set_emission_energy_multiplier(if on { *e } else { 0.0 });
        }
    });
}

/// Suelta todo al cerrar el juego.
pub fn limpiar() {
    NOCTURNOS.with(|v| v.borrow_mut().clear());
    NUBES.with(|v| v.borrow_mut().clear());
}

/// Material compartido de las nubes (sin niebla, sin sombra propia).
pub fn material_nube() -> Gd<StandardMaterial3D> {
    let mut m = StandardMaterial3D::new_gd();
    m.set_albedo(Color::from_rgb(0.97, 0.97, 0.98));
    m.set_roughness(1.0);
    m.set_flag(Flags::DISABLE_FOG, true);
    m.set_shading_mode(ShadingMode::PER_VERTEX);
    NUBES.with(|v| v.borrow_mut().push(m.clone()));
    m
}

/// REQ-AMB-11
pub fn set_color_nubes(c: [f32; 3]) {
    NUBES.with(|v| {
        for m in v.borrow_mut().iter_mut() {
            m.set_albedo(formas::color(c));
        }
    });
}
