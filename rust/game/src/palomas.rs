//! SPEC-013 · Palomas que picotean en la plaza y salen volando si te acercás.

use carrito_core::azar::Azar;
use carrito_core::caminos::{self, TipoNodo};
use carrito_core::forma::TipoPieza;
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::{formas, util};

const CANTIDAD: usize = 16;
pub const DISTANCIA_SUSTO: f32 = 3.5; // REQ-AMB-10

#[derive(Clone, Copy, PartialEq)]
enum Estado {
    Suelo,
    Volando,
    Fuera,
    Bajando,
}

struct Paloma {
    nodo: Gd<Node3D>,
    cabeza: Gd<Node3D>,
    alas: Vec<Gd<Node3D>>,
    estado: Estado,
    t: f32,
    desde: Vector3,
    hasta: Vector3,
}

#[derive(GodotClass)]
#[class(base=Node3D)]
pub struct Palomas {
    base: Base<Node3D>,
    azar: Azar,
    lugares: Vec<Vector3>,
    palomas: Vec<Paloma>,
}

impl Palomas {
    fn lugar_al_azar(&mut self) -> Vector3 {
        let base = *self.azar.elegir(&self.lugares).unwrap_or(&Vector3::ZERO);
        base + Vector3::new(self.azar.rango(-1.2, 1.2), 0.0, self.azar.rango(-1.2, 1.2))
    }

    pub fn volando(&self) -> usize {
        self.palomas.iter().filter(|p| p.estado != Estado::Suelo).count()
    }

    pub fn posiciones_en_suelo(&self) -> Vec<Vector3> {
        self.palomas.iter().filter(|p| p.estado == Estado::Suelo).map(|p| p.nodo.get_global_position()).collect()
    }
}

#[godot_api]
impl INode3D for Palomas {
    fn init(base: Base<Node3D>) -> Self {
        Self { base, azar: Azar::new(31), lugares: Vec::new(), palomas: Vec::new() }
    }

    fn ready(&mut self) {
        let red = caminos::red();
        self.lugares = red
            .de_tipo(|t| *t == TipoNodo::Paso)
            .into_iter()
            .map(|i| Vector3::new(red.pos[i][0], 0.0, red.pos[i][1]))
            .filter(|p| p.x.abs() < 19.0 && p.z.abs() < 19.0)
            .collect();
        for i in 0..CANTIDAD {
            let gris = [0.5 + (i % 3) as f32 * 0.08, 0.5 + (i % 3) as f32 * 0.08, 0.55 + (i % 3) as f32 * 0.08];
            let mut nodo = Node3D::new_alloc();
            let mut cuerpo = formas::pieza(TipoPieza::Esfera, [0.09, 0.0, 0.0], [0.0, 0.11, 0.0], gris);
            cuerpo.escala = [0.8, 0.75, 1.3];
            nodo.add_child(&formas::visual_pieza(&cuerpo));
            nodo.add_child(&formas::visual_pieza(&formas::pieza(
                TipoPieza::Caja,
                [0.07, 0.02, 0.1],
                [0.0, 0.13, -0.13],
                [0.3, 0.3, 0.33],
            )));
            let mut cabeza = Node3D::new_alloc();
            cabeza.set_position(Vector3::new(0.0, 0.17, 0.08));
            cabeza.add_child(&formas::visual_pieza(&formas::pieza(
                TipoPieza::Esfera,
                [0.045, 0.0, 0.0],
                [0.0, 0.0, 0.02],
                [0.35, 0.38, 0.45],
            )));
            cabeza.add_child(&formas::visual_pieza(&formas::pieza(
                TipoPieza::Caja,
                [0.015, 0.012, 0.03],
                [0.0, -0.005, 0.07],
                [0.9, 0.7, 0.3],
            )));
            nodo.add_child(&cabeza);
            let mut alas = Vec::new();
            for s in [-1.0_f32, 1.0] {
                let mut piv = Node3D::new_alloc();
                piv.set_position(Vector3::new(s * 0.06, 0.14, 0.0));
                piv.add_child(&formas::visual_pieza(&formas::pieza(
                    TipoPieza::Caja,
                    [0.16, 0.012, 0.11],
                    [s * 0.08, 0.0, 0.0],
                    gris,
                )));
                nodo.add_child(&piv);
                alas.push(piv);
            }
            let pos = self.lugar_al_azar();
            self.base_mut().add_child(&nodo);
            nodo.set_global_position(pos);
            nodo.set_rotation(Vector3::new(0.0, self.azar.rango(0.0, std::f32::consts::TAU), 0.0));
            let t = self.azar.rango(0.0, 5.0);
            self.palomas.push(Paloma { nodo, cabeza, alas, estado: Estado::Suelo, t, desde: pos, hasta: pos });
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        let yo = self.to_gd();
        let jugador = util::unico::<Node3D>(&yo, "jugador").map(|j| j.get_global_position());
        let mut nuevos: Vec<(usize, Vector3)> = Vec::new();
        for (i, p) in self.palomas.iter_mut().enumerate() {
            p.t += dt;
            match p.estado {
                Estado::Suelo => {
                    // Picotear: la cabeza baja y sube; cada tanto gira un poco.
                    let pico = ((p.t * 5.0 + i as f32).sin() > 0.7) as i32 as f32;
                    p.cabeza.set_rotation(Vector3::new(pico * 0.9, 0.0, 0.0));
                    if (p.t * 0.7 + i as f32).sin() > 0.995 {
                        p.nodo.rotate_y(0.6);
                    }
                    // REQ-AMB-10: si el jugador se acerca, sale volando.
                    let pos = p.nodo.get_global_position();
                    if let Some(j) = jugador {
                        if Vector2::new(j.x - pos.x, j.z - pos.z).length() < DISTANCIA_SUSTO {
                            let lejos = Vector3::new(pos.x - j.x, 0.0, pos.z - j.z).normalized_or_zero();
                            p.estado = Estado::Volando;
                            // REQ-SON-08: aleteo al salir volando.
                            crate::sonido::sonar_en(&yo, carrito_core::sonido::ids::PALOMA_ALETEO, pos);
                            p.t = 0.0;
                            p.desde = pos;
                            p.hasta = pos + lejos * 14.0 + Vector3::new(0.0, 9.0, 0.0);
                            p.nodo.set_rotation(Vector3::new(0.0, lejos.x.atan2(lejos.z), 0.0));
                        }
                    }
                }
                Estado::Volando => {
                    let f = (p.t / 2.5).min(1.0);
                    p.nodo.set_global_position(p.desde.lerp(p.hasta, f * f));
                    let aleteo = (p.t * 28.0).sin() * 0.9;
                    for (k, a) in p.alas.iter_mut().enumerate() {
                        a.set_rotation(Vector3::new(0.0, 0.0, if k == 0 { aleteo } else { -aleteo }));
                    }
                    if f >= 1.0 {
                        p.estado = Estado::Fuera;
                        p.t = 0.0;
                        p.nodo.set_visible(false);
                    }
                }
                Estado::Fuera => {
                    if p.t > 8.0 + (i as f32 * 1.3) % 7.0 {
                        nuevos.push((i, Vector3::ZERO));
                    }
                }
                Estado::Bajando => {
                    let f = (p.t / 2.0).min(1.0);
                    p.nodo.set_global_position(p.desde.lerp(p.hasta, 1.0 - (1.0 - f) * (1.0 - f)));
                    let aleteo = (p.t * 22.0).sin() * 0.7 * (1.0 - f);
                    for (k, a) in p.alas.iter_mut().enumerate() {
                        a.set_rotation(Vector3::new(0.0, 0.0, if k == 0 { aleteo } else { -aleteo }));
                    }
                    if f >= 1.0 {
                        p.estado = Estado::Suelo;
                        p.t = 0.0;
                    }
                }
            }
        }
        // Vuelven a bajar en otro lugar.
        for (i, _) in nuevos {
            let hasta = self.lugar_al_azar();
            let p = &mut self.palomas[i];
            p.estado = Estado::Bajando;
            p.t = 0.0;
            p.hasta = hasta;
            p.desde = hasta + Vector3::new(-8.0, 10.0, 4.0);
            p.nodo.set_visible(true);
            let d = p.hasta - p.desde;
            p.nodo.set_rotation(Vector3::new(0.0, d.x.atan2(d.z), 0.0));
        }
    }
}
