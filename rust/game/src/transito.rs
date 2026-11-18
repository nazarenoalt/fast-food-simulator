//! SPEC-013 · Autos que circulan por la calle y nubes que cruzan el cielo.

use carrito_core::ciudad::{self, AutoInicial, CARRILES};
use carrito_core::forma::TipoPieza;
use godot::classes::geometry_instance_3d::ShadowCastingSetting;
use godot::classes::{AnimatableBody3D, BoxShape3D, INode3D, Node3D};
use godot::prelude::*;

use crate::peaton;
use crate::{formas, nocturno, util};

struct Auto {
    nodo: Gd<Node3D>,
    ruedas: Vec<Gd<Node3D>>,
    carril: usize,
    x: f32,
    v: f32,
    crucero: f32,
    /// Ya pasó cerca del jugador (para sonar una sola vez por pasada). REQ-SON-08
    cerca: bool,
}

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Autos {
    base: Base<Node3D>,
    autos: Vec<Auto>,
}

impl Autos {
    fn crear_auto(&mut self, a: &AutoInicial) -> Auto {
        let mut nodo = Node3D::new_alloc();
        let (z, sentido) = CARRILES[a.carril];
        // El auto se arma mirando a +X; los que van al oeste se giran.
        nodo.set_rotation_degrees(Vector3::new(0.0, if sentido > 0.0 { 0.0 } else { 180.0 }, 0.0));
        nodo.set_position(Vector3::new(a.x, 0.0, z));
        self.base_mut().add_child(&nodo);
        let c = a.color;
        for p in [
            formas::pieza(TipoPieza::Caja, [4.1, 0.65, 1.75], [0.0, 0.6, 0.0], c),
            formas::pieza(TipoPieza::Caja, [2.1, 0.55, 1.6], [-0.25, 1.2, 0.0], c),
            formas::pieza(TipoPieza::Caja, [2.0, 0.45, 1.62], [-0.25, 1.2, 0.0], [0.15, 0.2, 0.25]),
            formas::pieza(TipoPieza::Caja, [0.05, 0.4, 1.5], [0.82, 1.18, 0.0], [0.15, 0.2, 0.25]),
        ] {
            nodo.add_child(&formas::visual_pieza(&p));
        }
        // REQ-AMB-09: faros y luces traseras que se prenden de noche.
        let faro = nocturno::material([0.9, 0.9, 0.85], [1.0, 0.95, 0.8], 5.0);
        let trasera = nocturno::material([0.5, 0.05, 0.05], [1.0, 0.1, 0.05], 3.0);
        for zf in [-0.6, 0.6] {
            let mut f = formas::instancia_malla(formas::malla(TipoPieza::Caja, [0.05, 0.14, 0.3]), faro.clone());
            f.set_position(Vector3::new(2.06, 0.72, zf));
            nodo.add_child(&f);
            let mut t = formas::instancia_malla(formas::malla(TipoPieza::Caja, [0.05, 0.12, 0.28]), trasera.clone());
            t.set_position(Vector3::new(-2.06, 0.75, zf));
            nodo.add_child(&t);
        }
        let mut ruedas = Vec::new();
        for (x, zr) in [(-1.3, -0.82), (1.3, -0.82), (-1.3, 0.82), (1.3, 0.82)] {
            let mut piv = Node3D::new_alloc();
            piv.set_position(Vector3::new(x, 0.33, zr));
            let mut r = formas::pieza(TipoPieza::Cilindro, [0.33, 0.22, 0.0], [0.0; 3], [0.08, 0.08, 0.08]);
            r.rot = [90.0, 0.0, 0.0];
            piv.add_child(&formas::visual_pieza(&r));
            let mut taza = formas::pieza(TipoPieza::Caja, [0.3, 0.06, 0.23], [0.0; 3], [0.7, 0.7, 0.72]);
            taza.rot = [0.0, 0.0, 0.0];
            piv.add_child(&formas::visual_pieza(&taza));
            nodo.add_child(&piv);
            ruedas.push(piv);
        }
        // Colisión (empuja objetos sueltos; frena antes de llegar al jugador).
        let mut cuerpo = AnimatableBody3D::new_alloc();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(4.1, 1.4, 1.75));
        cuerpo.add_child(&formas::nodo_colision(
            s.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, 0.75, 0.0)),
        ));
        nodo.add_child(&cuerpo);
        Auto { nodo, ruedas, carril: a.carril, x: a.x, v: a.crucero, crucero: a.crucero, cerca: false }
    }

    pub fn posiciones(&self) -> Vec<f32> {
        self.autos.iter().map(|a| a.x).collect()
    }
}

#[godot_api]
impl INode3D for Autos {
    fn ready(&mut self) {
        for a in ciudad::autos_iniciales() {
            let auto = self.crear_auto(&a);
            self.autos.push(auto);
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        let yo = self.to_gd();
        // Obstáculos: el jugador y los peatones (REQ-AMB-08).
        let mut obstaculos: Vec<(f32, f32)> = util::todos::<Node3D>(&yo, peaton::GRUPO)
            .iter()
            .map(|p| (p.get_global_position().x, p.get_global_position().z))
            .collect();
        let mut jugador = None;
        if let Some(j) = util::unico::<Node3D>(&yo, "jugador") {
            let p = j.get_global_position();
            obstaculos.push((p.x, p.z));
            jugador = Some(p);
        }
        let autos: Vec<(usize, f32)> = self.autos.iter().map(|a| (a.carril, a.x)).collect();
        for (i, a) in self.autos.iter_mut().enumerate() {
            let (z, sentido) = CARRILES[a.carril];
            let mut cerca: Option<f32> = None;
            let mut mirar = |d: Option<f32>| {
                if let Some(d) = d {
                    cerca = Some(cerca.map_or(d, |c: f32| c.min(d)));
                }
            };
            for (j, &(carril, x)) in autos.iter().enumerate() {
                if j != i && carril == a.carril {
                    // El auto de adelante cuenta con su largo (4 m).
                    mirar(ciudad::distancia_adelante(a.x, a.carril, x, z).map(|d| (d - 4.0).max(0.0)));
                }
            }
            for &(x, oz) in &obstaculos {
                mirar(ciudad::distancia_adelante(a.x, a.carril, x, oz).map(|d| (d - 2.2).max(0.0)));
            }
            let deseada = ciudad::velocidad_deseada(a.crucero, cerca);
            let cambio = (deseada - a.v).clamp(-9.0 * dt, 3.0 * dt);
            a.v += cambio;
            a.x = ciudad::envolver(a.x + a.v * sentido * dt);
            a.nodo.set_position(Vector3::new(a.x, 0.0, z));
            // REQ-SON-08: un auto que pasa cerca suena una vez por pasada.
            if let Some(j) = jugador {
                let d = Vector2::new(a.x - j.x, z - j.z).length();
                if d < 14.0 && !a.cerca && a.v > 3.0 {
                    a.cerca = true;
                    crate::sonido::sonar_en(&yo, carrito_core::sonido::ids::AUTO_PASA, Vector3::new(a.x, 1.0, z));
                } else if d > 22.0 {
                    a.cerca = false;
                }
            }
            for r in &mut a.ruedas {
                r.rotate_z(-a.v * dt / 0.33);
            }
        }
    }
}

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Nubes {
    base: Base<Node3D>,
    nubes: Vec<Gd<Node3D>>,
}

#[godot_api]
impl INode3D for Nubes {
    fn ready(&mut self) {
        let mat = nocturno::material_nube();
        for n in ciudad::nubes() {
            let mut nodo = Node3D::new_alloc();
            nodo.set_position(Vector3::new(n.x, n.altura, n.z));
            for (d, r) in &n.bolas {
                let mut b = formas::instancia_malla(formas::malla(TipoPieza::Esfera, [*r, 0.0, 0.0]), mat.clone());
                b.set_position(formas::v3(*d));
                b.set_scale(Vector3::new(1.0, 0.55, 1.0));
                b.set_cast_shadows_setting(ShadowCastingSetting::OFF);
                nodo.add_child(&b);
            }
            self.base_mut().add_child(&nodo);
            self.nubes.push(nodo);
        }
    }

    fn process(&mut self, delta: f64) {
        // REQ-AMB-11: se mueven con el viento y vuelven a entrar por el otro lado.
        let dt = delta as f32;
        for n in &mut self.nubes {
            let p = n.get_position();
            n.set_position(Vector3::new(
                ciudad::envolver_nube(p.x + ciudad::VIENTO[0] * dt),
                p.y,
                ciudad::envolver_nube(p.z + ciudad::VIENTO[1] * dt),
            ));
        }
    }
}

impl Nubes {
    pub fn posicion_primera(&self) -> Option<Vector3> {
        self.nubes.first().map(|n| n.get_position())
    }
}
