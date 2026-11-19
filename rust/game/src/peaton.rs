//! SPEC-013 · Un peatón: cuerpo simple animado que ejecuta una lista de acciones.
//! También es el cuerpo de los clientes (SPEC-009); quien decide qué hace es `Gente`.

use std::collections::VecDeque;

use carrito_core::forma::TipoPieza;
use carrito_core::peatones::Apariencia;
use godot::classes::base_material_3d::BillboardMode;
use godot::classes::{AnimatableBody3D, CapsuleShape3D, INode3D, Label3D, Node3D};
use godot::prelude::*;

use crate::formas;

pub const GRUPO: &str = "peatones";

#[derive(Debug, Clone)]
#[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
pub enum Accion {
    Caminar(Vec<Vector3>),
    /// REQ-AMB-05
    Sentarse {
        rot_y: f32,
        segundos: f32,
    },
    Charlar {
        mirar: Vector3,
        segundos: f32,
    },
    /// Quedarse parado (mirando a un punto, si se da): frente a un puesto, esperando al grupo
    /// o en el cordón (REQ-EVE-06, REQ-RUT-08, REQ-AMB-18).
    Esperar {
        mirar: Option<Vector3>,
        segundos: f32,
    },
    /// Saltar con los brazos arriba (festejo, REQ-EVE-09).
    Saltar {
        segundos: f32,
    },
    /// Ir al lugar de la fila que indique `Gente` y quedarse ahí (SPEC-009).
    EnFila,
    Desaparecer,
}

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Peaton {
    base: Base<Node3D>,
    pub id: u64,
    ap: Apariencia,
    vel: f32,
    con_perro: bool,
    acciones: VecDeque<Accion>,
    actual: Option<Accion>,
    paso_ruta: usize,
    t_accion: f32,
    lugar_fila: Option<(Vector3, Vector3)>,
    fase: f32,
    t_vida: f32,
    gesto: f32,
    cuerpo: Option<Gd<Node3D>>,
    piernas: Vec<Gd<Node3D>>,
    brazos: Vec<Gd<Node3D>>,
    globo: Option<Gd<Label3D>>,
    globo_fijo: String,
    globo_temporal: f32,
    perro: Option<Gd<Node3D>>,
    patas_perro: Vec<Gd<Node3D>>,
    comiendo: bool,
    /// Dónde están las personas cercanas (y el jugador), para esquivarlas. REQ-AMB-13
    vecinos: Vec<[f32; 2]>,
}

impl Peaton {
    pub fn crear(id: u64, ap: Apariencia, vel: f32, con_perro: bool, acciones: Vec<Accion>) -> Gd<Self> {
        Gd::from_init_fn(|base| Self {
            base,
            id,
            ap,
            vel,
            con_perro,
            acciones: acciones.into(),
            actual: None,
            paso_ruta: 0,
            t_accion: 0.0,
            lugar_fila: None,
            fase: 0.0,
            t_vida: 0.0,
            gesto: (id as f32 * 1.7) % std::f32::consts::TAU,
            cuerpo: None,
            piernas: Vec::new(),
            brazos: Vec::new(),
            globo: None,
            globo_fijo: String::new(),
            globo_temporal: 0.0,
            perro: None,
            patas_perro: Vec::new(),
            comiendo: false,
            vecinos: Vec::new(),
        })
    }

    /// Cómo se ve (REQ-HAB-01: un habitual vuelve con la misma).
    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    pub fn apariencia(&self) -> &Apariencia {
        &self.ap
    }

    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    /// Lo que está haciendo ahora.
    pub fn accion_actual(&self) -> Option<&Accion> {
        self.actual.as_ref()
    }

    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    /// Cuántas acciones le quedan después de la actual.
    pub fn acciones_pendientes(&self) -> usize {
        self.acciones.len()
    }

    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    pub fn velocidad(&self) -> f32 {
        self.vel
    }

    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    /// Cambia la velocidad de marcha (m/s), por ejemplo para alcanzar o esperar al grupo.
    pub fn set_velocidad(&mut self, v: f32) {
        self.vel = v.max(0.0);
    }

    /// REQ-AMB-13: `Gente` avisa, cada cuadro, quién anda cerca.
    pub fn set_vecinos(&mut self, v: Vec<[f32; 2]>) {
        self.vecinos = v;
    }

    #[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
    /// Hace `accion` ya y después sigue con lo que estaba haciendo (si caminaba, retoma el
    /// camino desde donde iba). Para pararse frente a un puesto o esperar en el cordón.
    pub fn intercalar(&mut self, accion: Accion) {
        if let Some(actual) = self.actual.take() {
            let resto = match actual {
                Accion::Caminar(ruta) => Accion::Caminar(ruta[self.paso_ruta.min(ruta.len())..].to_vec()),
                otra => otra,
            };
            self.acciones.push_front(resto);
        }
        self.acciones.push_front(accion);
        self.levantarse();
    }

    pub fn reemplazar_acciones(&mut self, acciones: Vec<Accion>) {
        self.acciones = acciones.into();
        self.actual = None;
        self.levantarse();
    }

    pub fn ocupado_quieto(&self) -> bool {
        matches!(self.actual, Some(Accion::Sentarse { .. } | Accion::Charlar { .. }))
    }

    pub fn set_lugar_fila(&mut self, pos: Vector3, mirar: Vector3) {
        self.lugar_fila = Some((pos, mirar));
    }

    /// Llegó a su lugar de la fila.
    pub fn en_lugar(&self) -> bool {
        match (&self.actual, self.lugar_fila) {
            (Some(Accion::EnFila), Some((p, _))) => {
                let d = p - self.base().get_global_position();
                Vector2::new(d.x, d.z).length() < 0.15
            }
            _ => false,
        }
    }

    /// REQ-CLI-05: texto fijo del globo (pedido) con color de paciencia.
    pub fn globo(&mut self, texto: &str, color: Color) {
        self.globo_fijo = texto.to_string();
        if self.globo_temporal <= 0.0
            && let Some(g) = &mut self.globo
        {
            g.set_text(texto);
            g.set_visible(!texto.is_empty());
            g.set_modulate(color);
        }
    }

    /// Un mensaje que dura unos segundos (rechazo, pago, enojo).
    pub fn decir(&mut self, texto: &str, color: Color, segundos: f32) {
        self.globo_temporal = segundos;
        if let Some(g) = &mut self.globo {
            g.set_text(texto);
            g.set_visible(true);
            g.set_modulate(color);
        }
    }

    /// Se va comiendo: un pancho en la mano.
    pub fn comer(&mut self) {
        self.comiendo = true;
        if let Some(brazo) = self.brazos.get_mut(1) {
            let largo = self.ap.altura * 0.36;
            let mut pancho = Node3D::new_alloc();
            for p in [
                formas::pieza(TipoPieza::Capsula, [0.027, 0.17, 0.0], [0.0; 3], [0.86, 0.6, 0.32]),
                formas::pieza(TipoPieza::Capsula, [0.011, 0.155, 0.0], [0.0, 0.024, 0.0], [0.72, 0.3, 0.2]),
            ] {
                let mut p = p;
                p.rot = [0.0, 0.0, 90.0];
                pancho.add_child(&formas::visual_pieza(&p));
            }
            pancho.set_position(Vector3::new(0.0, -largo, 0.08));
            pancho.set_rotation_degrees(Vector3::new(0.0, 90.0, 0.0));
            brazo.add_child(&pancho);
        }
    }

    fn levantarse(&mut self) {
        if let Some(c) = &mut self.cuerpo {
            c.set_position(Vector3::ZERO);
        }
    }

    fn construir(&mut self) {
        let ap = self.ap.clone();
        let h = ap.altura;
        let cadera = 0.47 * h;
        let largo_pierna = cadera;
        let hombros = 0.78 * h;
        let mut cuerpo = Node3D::new_alloc();

        // REQ-AMB-06: ropa y piel variadas.
        let parte = |padre: &mut Gd<Node3D>, tipo, medidas, pos: [f32; 3], color| {
            padre.add_child(&formas::visual_pieza(&formas::pieza(tipo, medidas, pos, color)));
        };
        parte(
            &mut cuerpo,
            TipoPieza::Caja,
            [0.3 * h * 0.85, hombros - cadera, 0.12 * h],
            [0.0, (hombros + cadera) / 2.0, 0.0],
            ap.remera,
        );
        parte(
            &mut cuerpo,
            TipoPieza::Caja,
            [0.3 * h * 0.8, 0.06 * h, 0.12 * h],
            [0.0, cadera + 0.02 * h, 0.0],
            ap.pantalon,
        );
        parte(&mut cuerpo, TipoPieza::Cilindro, [0.03 * h, 0.05 * h, 0.0], [0.0, hombros + 0.02 * h, 0.0], ap.piel);
        let radio_cabeza = 0.065 * h;
        let y_cabeza = hombros + 0.04 * h + radio_cabeza;
        parte(&mut cuerpo, TipoPieza::Esfera, [radio_cabeza, 0.0, 0.0], [0.0, y_cabeza, 0.0], ap.piel);
        // Pelo o gorra.
        let mut pelo =
            formas::pieza(TipoPieza::Esfera, [radio_cabeza * 1.04, 0.0, 0.0], [0.0, y_cabeza + 0.012, -0.008], ap.pelo);
        pelo.escala = [1.0, 0.75, 1.0];
        cuerpo.add_child(&formas::visual_pieza(&pelo));
        if let Some(gorra) = ap.gorra {
            parte(
                &mut cuerpo,
                TipoPieza::Cilindro,
                [radio_cabeza * 1.08, 0.04, 0.0],
                [0.0, y_cabeza + radio_cabeza * 0.55, 0.0],
                gorra,
            );
            parte(
                &mut cuerpo,
                TipoPieza::Caja,
                [0.08, 0.01, 0.07],
                [0.0, y_cabeza + radio_cabeza * 0.4, radio_cabeza + 0.02],
                gorra,
            );
        }
        // Ojos, para que se note hacia dónde mira (+Z).
        for x in [-0.025, 0.025] {
            parte(
                &mut cuerpo,
                TipoPieza::Esfera,
                [0.009, 0.0, 0.0],
                [x, y_cabeza + 0.01, radio_cabeza * 0.92],
                [0.05, 0.05, 0.05],
            );
        }

        // Piernas y brazos con pivote arriba (para la animación de caminar).
        for x in [-0.06 * h, 0.06 * h] {
            let mut piv = Node3D::new_alloc();
            piv.set_position(Vector3::new(x, cadera, 0.0));
            parte(
                &mut piv,
                TipoPieza::Caja,
                [0.075 * h, largo_pierna, 0.085 * h],
                [0.0, -largo_pierna / 2.0, 0.0],
                ap.pantalon,
            );
            parte(
                &mut piv,
                TipoPieza::Caja,
                [0.08 * h, 0.04, 0.14 * h],
                [0.0, -largo_pierna + 0.02, 0.02],
                [0.12, 0.1, 0.1],
            );
            cuerpo.add_child(&piv);
            self.piernas.push(piv);
        }
        let largo_brazo = 0.36 * h;
        for x in [-0.17 * h, 0.17 * h] {
            let mut piv = Node3D::new_alloc();
            piv.set_position(Vector3::new(x, hombros - 0.02 * h, 0.0));
            parte(
                &mut piv,
                TipoPieza::Caja,
                [0.06 * h, largo_brazo * 0.5, 0.065 * h],
                [0.0, -largo_brazo * 0.25, 0.0],
                ap.remera,
            );
            // REQ-RUT-10: con manga larga el antebrazo va del color de la ropa y se ve la mano.
            let antebrazo = if ap.manga_larga { ap.remera } else { ap.piel };
            parte(
                &mut piv,
                TipoPieza::Caja,
                [0.05 * h, largo_brazo * 0.5, 0.055 * h],
                [0.0, -largo_brazo * 0.75, 0.0],
                antebrazo,
            );
            if ap.manga_larga {
                parte(&mut piv, TipoPieza::Caja, [0.045 * h, 0.05 * h, 0.05 * h], [0.0, -largo_brazo, 0.0], ap.piel);
            }
            cuerpo.add_child(&piv);
            self.brazos.push(piv);
        }
        self.base_mut().add_child(&cuerpo);
        self.cuerpo = Some(cuerpo);

        // Colisión: el jugador choca con la gente y lo que tira rebota.
        let mut cuerpo_fisico = AnimatableBody3D::new_alloc();
        let mut s = CapsuleShape3D::new_gd();
        s.set_radius(0.22);
        s.set_height(h);
        cuerpo_fisico.add_child(&formas::nodo_colision(
            s.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, h / 2.0, 0.0)),
        ));
        self.base_mut().add_child(&cuerpo_fisico);

        // REQ-CLI-05: globo de pedido.
        let mut g = Label3D::new_alloc();
        g.set_billboard_mode(BillboardMode::ENABLED);
        g.set_font_size(40);
        g.set_outline_size(10);
        g.set_pixel_size(0.0035);
        g.set_draw_flag(godot::classes::label_3d::DrawFlags::DISABLE_DEPTH_TEST, true);
        g.set_position(Vector3::new(0.0, h + 0.35, 0.0));
        g.set_visible(false);
        self.base_mut().add_child(&g);
        self.globo = Some(g);

        // REQ-AMB-05: perro (se mueve por su cuenta, siguiendo al dueño).
        if self.con_perro {
            let mut perro = Node3D::new_alloc();
            let pelaje = if self.id.is_multiple_of(3) {
                [0.15, 0.12, 0.1]
            } else if self.id % 3 == 1 {
                [0.65, 0.45, 0.25]
            } else {
                [0.9, 0.88, 0.82]
            };
            parte(&mut perro, TipoPieza::Caja, [0.16, 0.16, 0.42], [0.0, 0.3, 0.0], pelaje);
            parte(&mut perro, TipoPieza::Caja, [0.14, 0.14, 0.17], [0.0, 0.42, 0.25], pelaje);
            parte(&mut perro, TipoPieza::Caja, [0.07, 0.06, 0.08], [0.0, 0.4, 0.36], [0.1, 0.08, 0.07]);
            parte(&mut perro, TipoPieza::Caja, [0.04, 0.04, 0.18], [0.0, 0.38, -0.27], pelaje);
            for (x, z) in [(-0.06, 0.15), (0.06, 0.15), (-0.06, -0.15), (0.06, -0.15)] {
                let mut piv = Node3D::new_alloc();
                piv.set_position(Vector3::new(x, 0.24, z));
                parte(&mut piv, TipoPieza::Caja, [0.045, 0.24, 0.045], [0.0, -0.12, 0.0], pelaje);
                perro.add_child(&piv);
                self.patas_perro.push(piv);
            }
            perro.set_as_top_level(true);
            self.base_mut().add_child(&perro);
            let pos = self.base().get_global_position();
            perro.set_global_position(pos + Vector3::new(0.7, 0.0, 0.0));
            self.perro = Some(perro);
        }
    }

    /// Mueve hacia `destino`. Devuelve `true` al llegar.
    fn caminar_hacia(&mut self, destino: Vector3, dt: f32) -> bool {
        let pos = self.base().get_global_position();
        let mut d = destino - pos;
        d.y = 0.0;
        let dist = d.length();
        if dist < 0.08 {
            return true;
        }
        // REQ-AMB-13: se corre para no chocar y frena si tiene a alguien encima.
        let (dir, factor) = carrito_core::peatones::esquivar([pos.x, pos.z], [d.x / dist, d.z / dist], &self.vecinos);
        let paso = (self.vel * factor * dt).min(dist);
        let dir = Vector3::new(dir[0], 0.0, dir[1]);
        self.base_mut().set_global_position(Vector3::new(pos.x + dir.x * paso, 0.0, pos.z + dir.z * paso));
        self.mirar_hacia(dir, dt);
        self.fase += dt * self.vel * factor * 4.2;
        false
    }

    fn mirar_hacia(&mut self, dir: Vector3, dt: f32) {
        if dir.length() < 0.01 {
            return;
        }
        let objetivo = dir.x.atan2(dir.z);
        let actual = self.base().get_rotation().y;
        let mut diff = objetivo - actual;
        while diff > std::f32::consts::PI {
            diff -= std::f32::consts::TAU;
        }
        while diff < -std::f32::consts::PI {
            diff += std::f32::consts::TAU;
        }
        self.base_mut().set_rotation(Vector3::new(0.0, actual + diff * (dt * 8.0).min(1.0), 0.0));
    }

    /// REQ-AMB-06: piernas y brazos que se balancean al caminar; pose sentado y gestos.
    fn animar(&mut self, moviendo: bool, dt: f32) {
        let sentado = matches!(self.actual, Some(Accion::Sentarse { .. }));
        let charlando = matches!(self.actual, Some(Accion::Charlar { .. }));
        let saltando = matches!(self.actual, Some(Accion::Saltar { .. }));
        let amplitud = if moviendo { if self.vel > 2.0 { 0.9 } else { 0.55 } } else { 0.0 };
        let s = self.fase.sin() * amplitud;
        for (i, p) in self.piernas.iter_mut().enumerate() {
            let a = if sentado {
                -1.45
            } else if i == 0 {
                s
            } else {
                -s
            };
            p.set_rotation(Vector3::new(a, 0.0, 0.0));
        }
        self.gesto += dt;
        for (i, b) in self.brazos.iter_mut().enumerate() {
            let mut a = if i == 0 { -s } else { s };
            if charlando {
                // Gestos al hablar: cada tanto levanta un brazo.
                let g = (self.gesto * 1.3 + i as f32 * 2.1).sin();
                a = if g > 0.6 { -0.9 * (g - 0.6) / 0.4 } else { 0.0 };
            }
            if self.comiendo && i == 1 {
                let g = (self.gesto * 0.8).sin();
                a = if g > 0.3 { -1.9 } else { -0.5 };
            }
            if sentado {
                a = -0.3;
            }
            if saltando {
                // REQ-EVE-09: brazos arriba, agitándolos.
                a = -2.8 + (self.gesto * 9.0 + i as f32).sin() * 0.25;
            }
            b.set_rotation(Vector3::new(a, 0.0, 0.0));
        }
        if let Some(c) = &mut self.cuerpo {
            let y = if sentado {
                0.47 - 0.47 * self.ap.altura
            } else if saltando {
                (self.t_accion * 6.5).sin().abs() * 0.22
            } else if moviendo {
                (self.fase * 2.0).sin().abs() * 0.02
            } else {
                0.0
            };
            c.set_position(Vector3::new(0.0, y, if sentado { -0.1 } else { 0.0 }));
        }
    }

    fn mover_perro(&mut self, dt: f32) {
        let t = self.base().get_global_transform();
        let Some(perro) = &mut self.perro else { return };
        let objetivo = t * Vector3::new(0.65, 0.0, -0.3);
        let pos = perro.get_global_position();
        let d = objetivo - pos;
        let moviendose = d.length() > 0.05;
        perro.set_global_position(pos + d * (dt * 3.0).min(1.0));
        if d.length() > 0.02 {
            perro.set_rotation(Vector3::new(0.0, d.x.atan2(d.z), 0.0));
        }
        let fase = self.t_vida * 12.0;
        for (i, p) in self.patas_perro.iter_mut().enumerate() {
            let a =
                if moviendose { (fase + if i % 2 == 0 { 0.0 } else { std::f32::consts::PI }).sin() * 0.6 } else { 0.0 };
            p.set_rotation(Vector3::new(a, 0.0, 0.0));
        }
    }
}

#[godot_api]
impl INode3D for Peaton {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        self.construir();
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        self.t_vida += dt;
        if self.globo_temporal > 0.0 {
            self.globo_temporal -= dt;
            if self.globo_temporal <= 0.0 {
                let texto = self.globo_fijo.clone();
                if let Some(g) = &mut self.globo {
                    g.set_text(&texto);
                    g.set_visible(!texto.is_empty());
                }
            }
        }

        if self.actual.is_none() {
            self.actual = self.acciones.pop_front();
            self.paso_ruta = 0;
            self.t_accion = 0.0;
            self.levantarse();
        }
        let mut moviendo = false;
        let mut terminada = false;
        match self.actual.clone() {
            None => {}
            Some(Accion::Caminar(ruta)) => {
                if let Some(&p) = ruta.get(self.paso_ruta) {
                    moviendo = true;
                    if self.caminar_hacia(p, dt) {
                        self.paso_ruta += 1;
                    }
                } else {
                    terminada = true;
                }
            }
            Some(Accion::Sentarse { rot_y, segundos }) => {
                self.base_mut().set_rotation(Vector3::new(0.0, rot_y.to_radians(), 0.0));
                self.t_accion += dt;
                terminada = self.t_accion >= segundos;
            }
            Some(Accion::Charlar { mirar, segundos }) => {
                let d = mirar - self.base().get_global_position();
                self.mirar_hacia(Vector3::new(d.x, 0.0, d.z), dt);
                self.t_accion += dt;
                terminada = self.t_accion >= segundos;
            }
            Some(Accion::Esperar { mirar, segundos }) => {
                if let Some(m) = mirar {
                    let d = m - self.base().get_global_position();
                    self.mirar_hacia(Vector3::new(d.x, 0.0, d.z), dt);
                }
                self.t_accion += dt;
                terminada = self.t_accion >= segundos;
            }
            Some(Accion::Saltar { segundos }) => {
                self.t_accion += dt;
                terminada = self.t_accion >= segundos;
            }
            Some(Accion::EnFila) => {
                if let Some((p, mirar)) = self.lugar_fila {
                    if !self.caminar_hacia(p, dt) {
                        moviendo = true;
                    } else {
                        self.mirar_hacia(mirar, dt);
                    }
                }
            }
            Some(Accion::Desaparecer) => {
                self.base_mut().queue_free();
            }
        }
        if terminada {
            self.actual = None;
        }
        self.animar(moviendo, dt);
        self.mover_perro(dt);
    }
}
