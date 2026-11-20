//! SPEC-001 (jugador) y SPEC-002 (interacción y agarre).

use godot::classes::input::MouseMode;
use godot::classes::{
    Camera3D, CapsuleShape3D, CharacterBody3D, ICharacterBody3D, Input, InputEvent, InputEventKey,
    InputEventMouseButton, InputEventMouseMotion, InputMap, KinematicCollision3D, Node, Object, ProjectSettings,
    RayCast3D, RigidBody3D,
};
use godot::global::{Key, MouseButton};
use godot::prelude::*;

use crate::aderecera::Pomo;
use crate::armado;
use crate::bloque_stock::BloqueStock;
use crate::cartel::CartelCerrado;
use crate::comida::{self, Comida};
use crate::datos::catalogo;
use crate::formas;
use crate::freidora::{self, Colador, Freidora};
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::hud::{self, Hud};
use crate::lugar_deposito::{self, LugarDeposito};
use crate::paquete::Paquete;
use crate::parrilla::Parrilla;
use crate::plancha::Plancha;
use crate::preparar;
use crate::puerta::PuertaCarrito;
use crate::sonido;
use crate::tienda;
use carrito_core::agarre::{self, AccionClic, Mira};
use carrito_core::datos::Colision;
use carrito_core::deposito::Empaque;
use carrito_core::movimiento::{self, Balanceo};
use carrito_core::sonido::ids;

const VEL_CAMINAR: f32 = 3.5; // REQ-JUG-03
const VEL_CORRER: f32 = 6.0; // REQ-JUG-03
const ALTO: f32 = 1.75; // REQ-JUG-05
const RADIO: f32 = 0.3; // REQ-JUG-05
const ALTO_OJOS: f32 = 1.65; // REQ-JUG-05
/// REQ-JUG-09: escalón más alto que se sube caminando.
const ESCALON_MAX: f32 = 0.30;
const ALCANCE: f32 = 2.5; // REQ-INT-01
/// REQ-INT-09: cuántas comidas que flotan atraviesa la cruz para ver si abajo está el hervidor.
const ATRAVESAR_MAX: usize = 3;
const RESORTE: f32 = 20.0; // REQ-INT-04
const VEL_MAX_MANO: f32 = 12.0; // REQ-INT-04
/// REQ-INT-04: qué tan rápido gira hacia el giro de la cámara (1/s) y tope (rad/s).
const RESORTE_GIRO: f32 = 15.0;
const GIRO_MAX_MANO: f32 = 20.0;
const DIST_TRABADO: f32 = 1.5; // REQ-INT-05
const VEL_TIRO: f32 = 4.0; // REQ-INT-06
/// Metros entre paso y paso. REQ-SON-08
const LARGO_PASO: f32 = 1.6;

/// Lo que está bajo la mira.
pub enum Objetivo {
    Comida(Gd<Comida>),
    Hervidor(Gd<Hervidor>),
    Plancha(Gd<Plancha>),
    Parrilla(Gd<Parrilla>),
    Heladera(Gd<Heladera>),
    Bloque(Gd<BloqueStock>),
    Paquete(Gd<Paquete>),
    Pomo(Gd<Pomo>),
    Puerta(Gd<PuertaCarrito>),
    Cartel(Gd<CartelCerrado>),
    Freidora(Gd<Freidora>), // REQ-FRE-05
}

/// REQ-INT-08: lo que hace el clic con lo que tenés en la mano (lo decide
/// `agarre::accion_clic`) y dónde queda. El cartel y el clic salen de acá.
#[derive(Clone)]
struct Colocacion {
    accion: AccionClic,
    /// Dónde queda (en el colador, el punto de la mira). `None` al soltar o con el hervidor lleno.
    destino: Option<Transform3D>,
    /// REQ-FRE-07
    colador: Option<Gd<Colador>>,
    /// REQ-INT-09: el lugar libre del depósito donde se guarda el paquete.
    lugar: Option<Gd<LugarDeposito>>,
}

/// REQ-INT-06: lo que toca la cruz al colocar (y el hervidor, si es parte de uno).
struct Toque {
    punto: Vector3,
    normal: Vector3,
    tocado: Option<Gd<Object>>,
    hervidor: Option<Gd<Hervidor>>,
}

#[derive(GodotClass)]
#[class(base=CharacterBody3D)]
pub struct Jugador {
    base: Base<CharacterBody3D>,
    camara: Option<Gd<Camera3D>>,
    rayo: Option<Gd<RayCast3D>>,
    /// Lo que tiene en la mano: comida o paquete (REQ-INT-03).
    mano: Option<Gd<RigidBody3D>>,
    segundos_en_mano: f32,
    /// REQ-INT-03: lo agarrado estaba dado vuelta (se respeta al sostenerlo y al colocarlo).
    volteado: bool,
    /// REQ-INT-09: rayo de la cámara a un lugar del depósito (para ver que no haya nada en medio).
    rayo_lugar: Option<Gd<RayCast3D>>,
    pitch: f32,
    gravedad: f32,
    /// Metros caminados desde el último paso que sonó. REQ-SON-08
    paso_m: f32,
    /// REQ-JUG-10
    balanceo: Balanceo,
    /// REQ-INT-08: lo último que mostró el cartel (qué tenía en la mano, desde dónde miraba y qué
    /// iba a hacer el clic), para que el clic haga eso mismo.
    cartel_clic: Option<(InstanceId, Transform3D, Colocacion)>,
}

fn a3(v: Vector3) -> [f32; 3] {
    [v.x, v.y, v.z]
}

fn registrar_acciones() {
    let mut mapa = InputMap::singleton();
    for (accion, tecla) in [
        ("adelante", Key::W),
        ("atras", Key::S),
        ("izquierda", Key::A),
        ("derecha", Key::D),
        ("saltar", Key::SPACE),
        ("correr", Key::SHIFT),
        ("usar", Key::E),
        ("tiempo_rapido", Key::T),
        ("tienda", Key::TAB),
        ("armado", Key::B), // REQ-TIE-01
        ("traer_cliente", Key::C),
    ] {
        if !mapa.has_action(accion) {
            mapa.add_action(accion);
            let mut ev = InputEventKey::new_gd();
            ev.set_physical_keycode(tecla);
            mapa.action_add_event(accion, &ev);
        }
    }
}

#[godot_api]
impl ICharacterBody3D for Jugador {
    fn init(base: Base<CharacterBody3D>) -> Self {
        // Arranca mirando un poco hacia abajo, para ver el mostrador.
        let pitch = -18f32.to_radians();
        Self {
            base,
            camara: None,
            rayo: None,
            mano: None,
            segundos_en_mano: 0.0,
            volteado: false,
            rayo_lugar: None,
            pitch,
            gravedad: 9.8,
            paso_m: 0.0,
            balanceo: Balanceo::default(),
            cartel_clic: None,
        }
    }

    fn ready(&mut self) {
        registrar_acciones();
        self.base_mut().add_to_group("jugador");
        self.gravedad =
            ProjectSettings::singleton().get_setting("physics/3d/default_gravity").try_to::<f64>().unwrap_or(9.8)
                as f32;

        // REQ-JUG-08 / REQ-CAR-11: si la base dice dónde aparece el jugador (ej. adentro del
        // carro kiosco), se lo pone ahí; si no, queda donde lo dejó la escena.
        let tree = self.base().get_tree();
        if let Some(c) = tree.get_first_node_in_group(crate::carrito::GRUPO)
            && let Some(p) = c.try_cast::<crate::carrito::Carrito>().ok().and_then(|c| c.bind().posicion_jugador())
        {
            self.base_mut().set_global_position(p);
        }

        // REQ-JUG-05: cápsula de 1,75 m y radio 0,3; ojos a 1,65 m.
        let mut forma = CapsuleShape3D::new_gd();
        forma.set_radius(RADIO);
        forma.set_height(ALTO);
        let col = formas::nodo_colision(
            forma.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, ALTO / 2.0, 0.0)),
        );
        self.base_mut().add_child(&col);

        let mut camara = Camera3D::new_alloc();
        camara.set_position(Vector3::new(0.0, ALTO_OJOS, 0.0));
        camara.set_rotation(Vector3::new(self.pitch, 0.0, 0.0));
        camara.set_fov(75.0);
        camara.set_near(0.03);
        self.base_mut().add_child(&camara);
        camara.make_current();

        // REQ-INT-01: lo que está a 2,5 m o menos bajo la mira.
        let mut rayo = RayCast3D::new_alloc();
        rayo.set_target_position(Vector3::new(0.0, 0.0, -ALCANCE));
        rayo.set_collision_mask(1 | formas::CAPA_USABLES); // REQ-CLI-13: también el cartel
        let yo = self.to_gd();
        rayo.add_exception(&yo);
        camara.add_child(&rayo);
        let mut rayo_lugar = RayCast3D::new_alloc();
        rayo_lugar.add_exception(&yo);
        rayo_lugar.set_enabled(false);
        camara.add_child(&rayo_lugar);

        self.camara = Some(camara);
        self.rayo = Some(rayo);
        self.rayo_lugar = Some(rayo_lugar);
        Input::singleton().set_mouse_mode(MouseMode::CAPTURED);
    }

    fn unhandled_input(&mut self, event: Gd<InputEvent>) {
        let mut input = Input::singleton();
        let capturado = input.get_mouse_mode() == MouseMode::CAPTURED;

        if let Ok(mov) = event.clone().try_cast::<InputEventMouseMotion>() {
            if capturado {
                // REQ-JUG-02: mirar con el mouse, vertical limitado a ±85°.
                let r = mov.get_relative();
                let sens = movimiento::SENSIBILIDAD;
                self.base_mut().rotate_y(-r.x * sens);
                self.pitch = (self.pitch - r.y * sens).clamp(-85f32.to_radians(), 85f32.to_radians());
                let p = self.pitch;
                if let Some(c) = &mut self.camara {
                    c.set_rotation(Vector3::new(p, 0.0, 0.0));
                }
            }
        } else if let Ok(boton) = event.clone().try_cast::<InputEventMouseButton>() {
            if !boton.is_pressed() {
                return;
            }
            // REQ-JUG-07: clic captura el mouse (salvo con el panel del proveedor abierto).
            if !capturado {
                if tienda::abierta() || armado::menu_abierto() {
                    return;
                }
                input.set_mouse_mode(MouseMode::CAPTURED);
                return;
            }
            // REQ-TIE-01: en el modo armado los clics son del modo armado.
            if armado::activo() {
                return;
            }
            match boton.get_button_index() {
                MouseButton::LEFT => self.clic_izquierdo(),
                MouseButton::RIGHT => self.tirar(),
                _ => {}
            }
        } else if let Ok(tecla) = event.try_cast::<InputEventKey>() {
            // REQ-JUG-07: Esc libera el mouse.
            if tecla.is_pressed() && tecla.get_keycode() == Key::ESCAPE {
                input.set_mouse_mode(MouseMode::VISIBLE);
            }
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        self.mover(dt);
        // REQ-TIE-01: en el modo armado no se usa nada y el cartel es del modo armado.
        if armado::activo() {
            self.actualizar_mano(dt);
            return;
        }
        if Input::singleton().is_action_just_pressed("usar") {
            self.usar();
        }
        self.actualizar_mano(dt);
        self.actualizar_cartel();
    }
}

impl Jugador {
    /// REQ-JUG-09: prueba subir `ESCALON_MAX`, avanzar y bajar hasta apoyar. Si arriba hay techo,
    /// si sigue chocando (es una pared) o si no hay piso, no hace nada.
    fn subir_escalon(&mut self, avance: Vector3) {
        let t = self.base().get_global_transform();
        let arriba = Vector3::UP * ESCALON_MAX;
        if self.base_mut().test_move(t, arriba) {
            return;
        }
        // Avanza lo suficiente para apoyar arriba del borde (no en la punta), sin pasar el radio.
        let paso = avance.normalized() * avance.length().max(RADIO * 0.66);
        let t_arriba = t.translated(arriba);
        if self.base_mut().test_move(t_arriba, paso) {
            return;
        }
        let t_adelante = t_arriba.translated(paso);
        let col = KinematicCollision3D::new_gd();
        if !self.base_mut().test_move_ex(t_adelante, -arriba).collision(&col).done() {
            return;
        }
        let bajada = col.get_travel();
        if (arriba + bajada).y < 0.02 || col.get_normal().y < 0.7 {
            return;
        }
        self.base_mut().set_global_position(t_adelante.origin + bajada);
    }

    fn mover(&mut self, dt: f32) {
        let input = Input::singleton();
        let mut v = self.base().get_velocity();

        // REQ-JUG-04: gravedad del proyecto; salto solo apoyado.
        let apoyado = self.base().is_on_floor();
        if !apoyado {
            v.y -= self.gravedad * dt;
        } else if input.is_action_just_pressed("saltar") && !armado::escribiendo() {
            v.y = movimiento::VEL_SALTO;
        }

        // REQ-JUG-01: WASD relativo a hacia dónde mira; REQ-JUG-03: correr con Shift.
        // REQ-LOG-07: mientras se escribe el nombre del puesto, las teclas no lo mueven.
        let ejes = if armado::escribiendo() {
            Vector2::ZERO
        } else {
            input.get_vector("izquierda", "derecha", "adelante", "atras")
        };
        let basis = self.base().get_global_transform().basis;
        let mut dir = basis * Vector3::new(ejes.x, 0.0, ejes.y);
        dir.y = 0.0;
        let vel = if input.is_action_pressed("correr") { VEL_CORRER } else { VEL_CAMINAR };
        let camina = dir.length() > 0.01;
        let pedida = if camina { dir.normalized() * vel } else { Vector3::ZERO };
        // REQ-JUG-10: la velocidad va hacia la pedida de a poco (arranca y frena suave).
        let [vx, vz] = movimiento::acercar_velocidad([v.x, v.z], [pedida.x, pedida.z], apoyado, dt);
        v.x = vx;
        v.z = vz;
        self.base_mut().set_velocity(v);
        self.base_mut().move_and_slide();
        // REQ-JUG-09: si choca de frente con un borde bajo (escalón), sube a ese nivel.
        if apoyado && self.base().is_on_wall() && camina {
            self.subir_escalon(pedida * dt);
        }

        // REQ-JUG-10: la cámara se balancea al caminar y vuelve al centro al parar.
        let real = self.base().get_real_velocity();
        let en_piso = self.base().is_on_floor();
        let sube = self.balanceo.paso(Vector2::new(real.x, real.z).length(), en_piso, dt);
        if let Some(c) = &mut self.camara {
            c.set_position(Vector3::new(0.0, ALTO_OJOS + sube, 0.0));
        }

        // REQ-SON-08: un paso cada tanto caminado, solo apoyado en el piso.
        let horizontal = Vector2::new(v.x, v.z).length();
        if self.base().is_on_floor() && horizontal > 0.5 {
            self.paso_m += horizontal * dt;
            if self.paso_m >= LARGO_PASO {
                self.paso_m = 0.0;
                sonido::sonar(&self.to_gd(), ids::PASOS_JUGADOR);
            }
        } else if horizontal <= 0.5 {
            self.paso_m = LARGO_PASO * 0.6;
        }

        // REQ-JUG-06: empuja suavemente los objetos con física que toca.
        let n = self.base().get_slide_collision_count();
        for i in 0..n {
            let Some(choque) = self.base_mut().get_slide_collision(i) else { continue };
            let Some(obj) = choque.get_collider() else { continue };
            if let Ok(mut cuerpo) = obj.try_cast::<RigidBody3D>() {
                let normal = choque.get_normal();
                let impulso = -normal * cuerpo.get_mass() * 0.6;
                cuerpo.apply_central_impulse(Vector3::new(impulso.x, 0.0, impulso.z));
            }
        }
    }

    /// Solo para pruebas: gira el cuerpo y la cámara para que la mira apunte a `punto`.
    pub fn apuntar_a(&mut self, punto: Vector3) {
        let ojos = self.base().get_global_position() + Vector3::new(0.0, ALTO_OJOS, 0.0);
        let d = punto - ojos;
        let horizontal = Vector2::new(d.x, d.z).length();
        self.base_mut().set_global_rotation(Vector3::new(0.0, (-d.x).atan2(-d.z), 0.0));
        self.pitch = d.y.atan2(horizontal).clamp(-85f32.to_radians(), 85f32.to_radians());
        let p = self.pitch;
        if let Some(c) = &mut self.camara {
            c.set_rotation(Vector3::new(p, 0.0, 0.0));
        }
    }

    /// Alto de la cámara sobre los pies, con el balanceo (para pruebas). REQ-JUG-10
    pub fn alto_camara(&self) -> f32 {
        self.camara.as_ref().map(|c| c.get_position().y).unwrap_or(ALTO_OJOS)
    }

    /// La cámara en el mundo (para pruebas).
    pub fn vista(&self) -> Transform3D {
        self.camara.as_ref().map(|c| c.get_global_transform()).unwrap_or(Transform3D::IDENTITY)
    }

    /// Lo que tiene en la mano (para pruebas).
    pub fn en_mano(&self) -> Option<Gd<RigidBody3D>> {
        self.mano.clone().filter(|c| c.is_instance_valid())
    }

    /// REQ-INT-01
    pub fn objetivo(&mut self) -> Option<Objetivo> {
        let rayo = self.rayo.as_mut()?;
        rayo.force_raycast_update();
        if !rayo.is_colliding() {
            return None;
        }
        let mut nodo: Option<Gd<Node>> = rayo.get_collider()?.try_cast::<Node>().ok();
        let punto = rayo.get_collision_point();
        // El objeto puede ser el cuerpo físico o un hijo de un equipo: se sube hasta 4 niveles.
        for _ in 0..4 {
            let n = nodo?;
            let n = match n.try_cast::<Comida>() {
                // REQ-FRE-08: en un colador, la porción de papas que mira.
                Ok(c) => return Some(Objetivo::Comida(freidora::agarrable_en(c, punto))),
                Err(n) => n,
            };
            let n = match n.try_cast::<Hervidor>() {
                Ok(h) => return Some(Objetivo::Hervidor(h)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Plancha>() {
                Ok(p) => return Some(Objetivo::Plancha(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Parrilla>() {
                Ok(p) => return Some(Objetivo::Parrilla(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Heladera>() {
                Ok(h) => return Some(Objetivo::Heladera(h)),
                Err(n) => n,
            };
            let n = match n.try_cast::<BloqueStock>() {
                Ok(b) => return Some(Objetivo::Bloque(b)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Paquete>() {
                Ok(p) => return Some(Objetivo::Paquete(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Pomo>() {
                Ok(p) => return Some(Objetivo::Pomo(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<PuertaCarrito>() {
                Ok(p) => return Some(Objetivo::Puerta(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<CartelCerrado>() {
                Ok(c) => return Some(Objetivo::Cartel(c)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Freidora>() {
                Ok(f) => return Some(Objetivo::Freidora(f)),
                Err(n) => n,
            };
            nodo = n.get_parent();
        }
        None
    }

    /// Punto donde toca la mira (el del último objetivo). REQ-FRE-05
    fn punto_mira(&self) -> Option<Vector3> {
        self.rayo.as_ref().filter(|r| r.is_colliding()).map(|r| r.get_collision_point())
    }

    /// REQ-INT-03, REQ-INT-06 (y REQ-CLI-13): agarrar, colocar o usar el cartel.
    pub fn clic_izquierdo(&mut self) {
        if self.mano.is_some() {
            // REQ-INT-06: colocar donde apunta la mira.
            self.colocar();
            return;
        }
        // REQ-INT-03, REQ-PRO-05: agarrar comida o paquetes; REQ-DEP-09: o levantar un bloque.
        match self.objetivo() {
            Some(Objetivo::Comida(c)) => self.agarrar(c.upcast()),
            Some(Objetivo::Paquete(p)) => self.agarrar(p.upcast()),
            Some(Objetivo::Bloque(b)) => self.levantar(b),
            // REQ-CLI-13: con la mano libre, el clic saca o cuelga el cartel, igual que E.
            Some(Objetivo::Cartel(mut c)) => c.bind_mut().alternar(),
            _ => {}
        }
    }

    /// REQ-DEP-09: el bloque del depósito pasa a ser un paquete en la mano, con lo que le queda.
    pub fn levantar(&mut self, mut bloque: Gd<BloqueStock>) {
        if bloque.is_queued_for_deletion() {
            return;
        }
        let (def, restantes, temp) = {
            let b = bloque.bind();
            (b.def().clone(), b.restantes(), b.temperatura())
        };
        let alto = def.tamano()[1];
        let t = bloque.get_global_transform();
        // El bloque se dibuja con la base en su origen; el paquete está centrado.
        let t = Transform3D::new(t.basis.orthonormalized(), t.origin + t.basis.col_b().normalized() * (alto / 2.0));
        bloque.queue_free();
        let mut p = Paquete::crear_con(def, restantes, temp);
        if let Some(mut padre) = self.base().get_parent() {
            padre.add_child(&p);
        }
        p.set_global_transform(t);
        self.agarrar(p.upcast());
    }

    /// REQ-INT-03, REQ-INT-09: (media altura, medio ancho, media medida mayor) de lo agarrable.
    fn medidas(cuerpo: &Gd<RigidBody3D>) -> (f32, f32, f32) {
        if let Ok(c) = cuerpo.clone().try_cast::<Comida>() {
            return c.bind().medidas();
        }
        if let Ok(p) = cuerpo.clone().try_cast::<Paquete>() {
            let [x, y, z] = p.bind().def().tamano();
            return (y / 2.0, x.max(z) / 2.0, x.max(y).max(z) / 2.0);
        }
        (0.05, 0.05, 0.05)
    }

    /// Giro con el que queda lo colocado: derecho, mirando hacia donde mira el jugador
    /// (y dado vuelta si lo estaba). REQ-INT-09
    fn giro_colocado(&self) -> Basis {
        let giro = self.base().get_global_transform().basis.orthonormalized();
        if self.volteado { giro * Basis::from_axis_angle(Vector3::RIGHT, std::f32::consts::PI) } else { giro }
    }

    /// REQ-INT-03: medidas horizontales (a lo largo de X y de Z locales) de lo agarrable, para
    /// saber cuál es su largo.
    fn ejes_horizontales(cuerpo: &Gd<RigidBody3D>) -> (f32, f32) {
        if let Ok(c) = cuerpo.clone().try_cast::<Comida>()
            && let Some(def) = catalogo().producto(c.bind().producto())
        {
            return match def.colision {
                Colision::Caja { medidas: [x, _, z] } => (x, z),
                Colision::Capsula { radio, largo } => (largo, radio * 2.0),
            };
        }
        if let Ok(p) = cuerpo.clone().try_cast::<Paquete>() {
            let [x, _, z] = p.bind().def().tamano();
            return (x, z);
        }
        (0.1, 0.1)
    }

    /// REQ-INT-09: el hervidor del que es parte lo tocado (su cuba, sus paredes), si hay uno.
    fn hervidor_de(tocado: Option<Gd<Object>>) -> Option<Gd<Hervidor>> {
        let mut nodo = tocado?.try_cast::<Node>().ok();
        for _ in 0..4 {
            let n = nodo?;
            match n.try_cast::<Hervidor>() {
                Ok(h) => return Some(h),
                Err(n) => nodo = n.get_parent(),
            }
        }
        None
    }

    /// REQ-INT-06: lo que toca la cruz a `agarre::ALCANCE_COLOCAR` o menos. Si toca comida que
    /// flota en el hervidor, también da el hervidor de abajo (REQ-INT-09: el agua es parte del
    /// hervidor).
    fn mira_colocar(&mut self) -> Option<Toque> {
        let rayo = self.rayo.as_mut()?;
        // REQ-CLI-13: colocar no ve la zona del cartel de cerrado (es solo para usarlo).
        rayo.set_collision_mask(1);
        rayo.set_target_position(Vector3::new(0.0, 0.0, -agarre::ALCANCE_COLOCAR));
        rayo.force_raycast_update();
        let choque =
            rayo.is_colliding().then(|| (rayo.get_collision_point(), rayo.get_collision_normal(), rayo.get_collider()));
        let mut tocado = choque.as_ref().and_then(|c| c.2.clone());
        let mut hervidor = Self::hervidor_de(tocado.clone());
        // Atraviesa la comida que flota para ver si abajo está el hervidor.
        let mut atravesadas: Vec<Gd<Comida>> = Vec::new();
        while hervidor.is_none() && atravesadas.len() < ATRAVESAR_MAX {
            let Some(c) = tocado.and_then(|o| o.try_cast::<Comida>().ok()) else { break };
            rayo.add_exception(&c);
            atravesadas.push(c);
            rayo.force_raycast_update();
            tocado = if rayo.is_colliding() { rayo.get_collider() } else { None };
            hervidor = Self::hervidor_de(tocado.clone());
        }
        for c in &atravesadas {
            rayo.remove_exception(c);
        }
        rayo.set_target_position(Vector3::new(0.0, 0.0, -ALCANCE));
        rayo.set_collision_mask(1 | formas::CAPA_USABLES);
        let (punto, normal, tocado) = choque?;
        Some(Toque { punto, normal, tocado, hervidor })
    }

    /// REQ-INT-08: qué hace el clic con lo que tenés en la mano ahí donde apuntás, y dónde queda.
    /// Una sola función: de acá salen el cartel y el clic. `None` con la mano vacía.
    fn colocacion(&mut self) -> Option<Colocacion> {
        let mano = self.mano.clone().filter(|c| c.is_instance_valid() && !c.is_queued_for_deletion())?;
        // REQ-INT-06: nada a 3 m o menos (lejos, el cielo): se suelta.
        let Some(Toque { punto, normal, tocado, hervidor }) = self.mira_colocar() else {
            return Some(Colocacion { accion: AccionClic::Soltar, destino: None, colador: None, lugar: None });
        };
        let v3 = |v: Vector3| [v.x, v.y, v.z];
        let comida = mano.clone().try_cast::<Comida>().ok();
        let (media_altura, medio_ancho, _) = Self::medidas(&mano);
        let mut mira = Mira { normal: Some(v3(normal)), ..Mira::default() };

        // REQ-FRE-07: papas sobre un colador van adentro (lleno, se apoyan como siempre).
        let colador = comida.as_ref().and_then(|c| freidora::colador_destino(c, tocado.clone()));
        mira.colador = colador.as_ref().map(|r| r.is_ok());
        let colador = colador.and_then(Result::ok);

        // REQ-INT-10: un agregado sobre su base va a la zona de encastre.
        let mut en_base = None;
        if let Some(c) = &comida
            && let Some(base) = tocado.and_then(|o| o.try_cast::<Comida>().ok())
            && let Some(pos) = base.bind().encastre_para(c.bind().producto())
        {
            mira.base = Some(base.bind().nombre().to_string());
            en_base = Some(Transform3D::new(base.get_global_transform().basis.orthonormalized(), pos));
        }

        // REQ-INT-09, REQ-COC-10: lo que se cocina en agua, con la cruz en el hervidor, va al
        // primer lugar libre del agua (sin lugares: lleno).
        let mut al_agua = None;
        if let (Some(c), Some(h)) = (&comida, &hervidor)
            && Comida::va_al_hervidor(c.bind().producto())
        {
            al_agua = h.bind().lugares_libres(medio_ancho * 2.0, media_altura * 2.0).into_iter().next();
            mira.hervidor = Some(al_agua.is_some());
        }

        // REQ-INT-09: un paquete cerca de un lugar libre (y a la vista) va centrado ahí.
        let mut en_lugar = None;
        let mut lugar = None;
        if mano.clone().try_cast::<Paquete>().is_ok() {
            let libres: Vec<Gd<LugarDeposito>> = self
                .base()
                .get_tree()
                .get_nodes_in_group(lugar_deposito::GRUPO)
                .iter_shared()
                .filter_map(|n| n.try_cast::<LugarDeposito>().ok())
                .filter(|l| !l.bind().ocupado())
                .collect();
            let posiciones: Vec<[f32; 3]> = libres.iter().map(|l| v3(l.get_global_position())).collect();
            if let Some(i) = agarre::lugar_cercano(v3(punto), &posiciones)
                && self.a_la_vista(&libres[i])
            {
                let tl = libres[i].get_global_transform();
                let b = tl.basis.orthonormalized();
                en_lugar = Some(Transform3D::new(b, tl.origin + b.col_b() * (media_altura + agarre::HOLGURA)));
                mira.lugar_libre = true;
                lugar = Some(libres[i].clone());
            }
        }

        let accion = agarre::accion_clic(&mira);
        let destino = match &accion {
            AccionClic::Soltar | AccionClic::HervidorLleno => None,
            AccionClic::Colador => Some(Transform3D::new(Basis::IDENTITY, punto)),
            AccionClic::Armar(_) => en_base,
            AccionClic::AlAgua => al_agua,
            AccionClic::Guardar => en_lugar,
            AccionClic::Apoyar | AccionClic::ColadorLleno => {
                let c = agarre::centro_colocado(v3(punto), v3(normal), media_altura, medio_ancho);
                Some(Transform3D::new(self.giro_colocado(), formas::v3(c)))
            }
        };
        Some(Colocacion { accion, destino, colador, lugar })
    }

    /// REQ-INT-08: lo que dice el cartel. Si la vista casi no se movió desde que se mostró (el
    /// mouse puede moverse un poco entre el cartel y el clic), es lo mismo que se mostró; si no
    /// (las pruebas apuntan de golpe), se decide de nuevo con la misma función.
    fn colocacion_del_cartel(&mut self) -> Option<Colocacion> {
        let id = self.mano.as_ref().filter(|c| c.is_instance_valid())?.instance_id();
        let ahora = self.vista();
        if let Some((de, vista, c)) = &self.cartel_clic
            && *de == id
            && agarre::misma_mira(
                a3(vista.origin),
                a3(-vista.basis.col_c()),
                a3(ahora.origin),
                a3(-ahora.basis.col_c()),
            )
        {
            return Some(c.clone());
        }
        self.colocacion()
    }

    /// REQ-INT-08: lo que haría el clic ahora con lo de la mano (para pruebas).
    pub fn accion_clic(&mut self) -> Option<AccionClic> {
        self.colocacion_del_cartel().map(|c| c.accion)
    }

    /// REQ-INT-09: no hay nada entre los ojos y el lugar (una puerta cerrada, un cajón).
    fn a_la_vista(&mut self, lugar: &Gd<LugarDeposito>) -> bool {
        let destino = lugar.bind().centro_zona();
        let (Some(camara), Some(rayo)) = (&self.camara, &mut self.rayo_lugar) else { return false };
        let local = camara.get_global_transform().affine_inverse() * destino;
        rayo.set_target_position(local);
        rayo.force_raycast_update();
        !rayo.is_colliding() || rayo.get_collision_point().distance_to(destino) < 0.15
    }

    /// REQ-INT-06, REQ-INT-08, REQ-INT-09, REQ-INT-10: hace lo que dice el cartel: deja lo de
    /// la mano donde apunta la cruz o, si ahí no hay dónde apoyarlo, lo suelta y cae.
    pub fn colocar(&mut self) {
        let Some(Colocacion { accion, destino, colador, lugar }) = self.colocacion_del_cartel() else { return };
        self.cartel_clic = None;
        // REQ-COC-08: con el hervidor lleno el clic no hace nada (el cartel lo dice).
        if accion == AccionClic::HervidorLleno {
            return;
        }
        // REQ-INT-08 (TASK-0263): "Guardar" guarda en el acto. Antes el clic solo movía el
        // paquete al lugar y el guardado dependía de que la física lo viera adentro de la zona en
        // los cuadros siguientes (REQ-PRO-06); si algo lo empujaba antes, caía al piso.
        if accion == AccionClic::Guardar
            && let Some(mut l) = lugar
            && let Some(p) = self.paquete_en_mano()
            && self.soltar_en_silencio().is_some()
        {
            if !l.bind_mut().guardar(p.clone()) {
                let mut p = p;
                if let Some(t) = destino {
                    p.set_global_transform(t);
                }
                p.set_sleeping(false);
            }
            return;
        }
        let Some(mut c) = self.soltar() else { return };
        // REQ-FRE-07: adentro del colador.
        if accion == AccionClic::Colador
            && let (Some(mut col), Some(t), Ok(papa)) = (colador, destino, c.clone().try_cast::<Comida>())
        {
            if let Err(e) = col.bind_mut().meter(papa, Some(t.origin)) {
                hud::avisar(&self.to_gd(), e.mensaje());
            }
            return;
        }
        c.set_angular_velocity(Vector3::ZERO);
        c.set_linear_velocity(Vector3::ZERO);
        // REQ-INT-06: sin destino se suelta donde está y cae (sin el empujón del resorte).
        if let Some(t) = destino {
            c.set_global_transform(t);
        }
        // Despierto: si se durmió quieto en la mano, la física lo tiene que ver donde quedó (el
        // agua del hervidor, la zona de encastre) y hacerlo caer si se soltó.
        c.set_sleeping(false);
    }

    /// REQ-COC-10: vuelca en el agua del hervidor las unidades del paquete de la mano que
    /// entran en los lugares libres; si sobran, el paquete queda en la mano con esas.
    pub fn volcar(&mut self, hervidor: &Gd<Hervidor>) {
        let Some(mut paquete) = self.mano.clone().and_then(|m| m.try_cast::<Paquete>().ok()) else { return };
        let (producto, n, temp) = {
            let p = paquete.bind();
            (p.def().producto.clone(), p.restantes(), p.temp)
        };
        let yo = self.to_gd();
        if !Comida::va_al_hervidor(&producto) {
            hud::avisar(&yo, "Eso no se cocina en el agua");
            return;
        }
        let Some(mut padre) = self.base().get_parent() else { return };
        let Some(def) = catalogo().producto(&producto) else { return };
        let (media_altura, medio_ancho, _) = comida::medidas_de(def);
        let libres = hervidor.bind().lugares_libres(medio_ancho * 2.0, media_altura * 2.0);
        let (al_agua, sobran) = agarre::repartir_volcado(n, libres.len());
        if al_agua == 0 {
            hud::avisar(&yo, "Hervidor lleno"); // REQ-COC-08
            return;
        }
        for t in libres.into_iter().take(al_agua as usize) {
            let mut c = Comida::crear(&producto);
            c.bind_mut().fijar_temperatura(temp);
            padre.add_child(&c);
            c.set_global_transform(t);
        }
        if sobran == 0 {
            if let Some(mut p) = self.soltar_en_silencio() {
                p.queue_free();
            }
        } else {
            paquete.bind_mut().quitar(al_agua);
        }
        sonido::sonar_en(&yo, ids::SOLTAR, hervidor.get_global_position());
    }

    fn marcar(cuerpo: &Gd<RigidBody3D>, sostenido: bool) {
        if let Ok(mut c) = cuerpo.clone().try_cast::<Comida>() {
            c.bind_mut().sostenida = sostenido;
        } else if let Ok(mut p) = cuerpo.clone().try_cast::<Paquete>() {
            p.bind_mut().sostenido = sostenido;
        }
    }

    pub fn agarrar(&mut self, mut c: Gd<RigidBody3D>) {
        Self::marcar(&c, true);
        c.set_gravity_scale(0.0);
        // REQ-INT-03: no choca con el jugador (va pegado a la cámara).
        let yo = self.to_gd().upcast::<Node>();
        c.add_collision_exception_with(&yo);
        // REQ-INT-03: solo lo que se cocina por lados conserva qué cara mira abajo.
        let por_lados = c.clone().try_cast::<Comida>().is_ok_and(|c| c.bind().por_lados());
        self.volteado = por_lados && c.get_global_transform().basis.col_b().y < 0.0;
        if let Some(r) = &mut self.rayo {
            r.add_exception(&c);
        }
        if let Some(r) = &mut self.rayo_lugar {
            r.add_exception(&c);
        }
        self.segundos_en_mano = 0.0;
        self.mano = Some(c);
        // REQ-SON-08
        sonido::sonar(&self.to_gd(), ids::AGARRAR);
    }

    pub fn soltar(&mut self) -> Option<Gd<RigidBody3D>> {
        let c = self.soltar_en_silencio()?;
        // REQ-SON-08
        sonido::sonar(&self.to_gd(), ids::SOLTAR);
        Some(c)
    }

    fn soltar_en_silencio(&mut self) -> Option<Gd<RigidBody3D>> {
        let mut c = self.mano.take()?;
        if !c.is_instance_valid() {
            return None;
        }
        Self::marcar(&c, false);
        c.set_gravity_scale(1.0);
        let yo = self.to_gd().upcast::<Node>();
        c.remove_collision_exception_with(&yo);
        if let Some(r) = &mut self.rayo {
            r.remove_exception(&c);
        }
        if let Some(r) = &mut self.rayo_lugar {
            r.remove_exception(&c);
        }
        Some(c)
    }

    /// REQ-INT-06: tirar hacia adelante.
    fn tirar(&mut self) {
        // REQ-INT-06: hacia donde apunta la mira (lo de la mano está corrido a la derecha).
        let mut direccion = self.adelante();
        if let (Some(rayo), Some(c)) = (&mut self.rayo, &self.mano)
            && c.is_instance_valid()
        {
            rayo.force_raycast_update();
            if rayo.is_colliding() {
                let d = rayo.get_collision_point() - c.get_global_position();
                if d.length() > 0.05 {
                    direccion = d.normalized();
                }
            }
        }
        if let Some(mut c) = self.soltar_en_silencio() {
            c.set_linear_velocity(direccion * VEL_TIRO);
            // REQ-SON-08
            sonido::sonar(&self.to_gd(), ids::TIRAR);
        }
    }

    fn adelante(&self) -> Vector3 {
        self.camara.as_ref().map(|c| -c.get_global_transform().basis.col_c()).unwrap_or(Vector3::FORWARD)
    }

    fn paquete_en_mano(&self) -> Option<Gd<Paquete>> {
        self.mano.as_ref().filter(|c| c.is_instance_valid()).and_then(|c| c.clone().try_cast::<Paquete>().ok())
    }

    fn comida_en_mano(&self) -> Option<Gd<Comida>> {
        self.mano.as_ref().filter(|c| c.is_instance_valid()).and_then(|c| c.clone().try_cast::<Comida>().ok())
    }

    /// REQ-INT-07: E usa el objetivo.
    pub fn usar(&mut self) {
        let yo = self.to_gd();
        if self.mano.is_some() {
            // REQ-CLI-13: E saca o cuelga el cartel también con algo en la mano.
            if let Some(Objetivo::Cartel(mut c)) = self.objetivo() {
                c.bind_mut().alternar();
                return;
            }
            // REQ-COC-10: un paquete sobre el hervidor se vuelca en el agua.
            if self.paquete_en_mano().is_some() {
                if let Some(Objetivo::Hervidor(h)) = self.objetivo() {
                    self.volcar(&h);
                }
                return;
            }
            // Con comida en la mano: pomos de aderezo (SPEC-012) y carbón en la parrilla.
            let Some(mut comida) = self.comida_en_mano() else { return };
            // REQ-PAR-01: una bolsa de carbón en la mano se vuelca en la parrilla.
            let carbon = comida.bind().carbon();
            if let (Some(kg), Some(Objetivo::Parrilla(mut parrilla))) = (carbon, self.objetivo()) {
                match parrilla.bind_mut().cargar(kg) {
                    Ok(()) => {
                        self.soltar();
                        comida.queue_free();
                    }
                    Err(e) => hud::avisar(&yo, e.mensaje()),
                }
                return;
            }
            // REQ-FRE-01..03: pelar o cortar con la herramienta de la mano.
            let herramienta = comida.bind().producto().to_string();
            if let Some(Objetivo::Comida(c)) = self.objetivo()
                && preparar::usar(Some(&herramienta), c)
            {
                return;
            }
            let Some(Objetivo::Pomo(mut pomo)) = self.objetivo() else { return };
            let repone = comida.bind().repone().map(str::to_string);
            let resultado = match repone {
                // REQ-ADE-05: recargar con un repuesto (que se gasta).
                Some(a) => pomo.bind_mut().recargar(&a).map(|_| {
                    self.soltar();
                    comida.queue_free();
                }),
                // REQ-ADE-03
                None => pomo.bind_mut().aplicar(&mut comida),
            };
            if let Err(e) = resultado {
                hud::avisar(&yo, e.mensaje());
            }
            return;
        }
        match self.objetivo() {
            Some(Objetivo::Hervidor(mut h)) => h.bind_mut().alternar(),
            // REQ-FRE-05: la cuba bajo la mira.
            Some(Objetivo::Freidora(mut f)) => {
                if let Some(p) = self.punto_mira() {
                    f.bind_mut().alternar_en(p);
                }
            }
            // REQ-FRE-08: E sobre un colador puesto en una cuba lo baja o lo sube.
            Some(Objetivo::Comida(c)) if freidora::alternar_colador(&c) => {}
            // REQ-PLA-01
            Some(Objetivo::Plancha(mut p)) => p.bind_mut().alternar(),
            // REQ-HEL-01
            Some(Objetivo::Heladera(mut h)) => h.bind_mut().alternar(),
            // REQ-CAR-13
            Some(Objetivo::Puerta(mut p)) => p.bind_mut().alternar(),
            // REQ-CLI-13
            Some(Objetivo::Cartel(mut c)) => c.bind_mut().alternar(),
            // REQ-PAR-01
            Some(Objetivo::Parrilla(mut p)) => {
                if let Err(e) = p.bind_mut().usar() {
                    hud::avisar(&yo, e.mensaje());
                }
            }
            // REQ-PLA-07: E sobre una hamburguesa suelta la da vuelta.
            Some(Objetivo::Comida(mut c)) if c.bind().por_lados() => c.bind_mut().dar_vuelta(),
            Some(Objetivo::Bloque(mut b)) => {
                // REQ-HEL-06: lo que sale del paquete conserva la temperatura del paquete.
                let temp = b.bind().temperatura();
                let empaque = b.bind().empaque();
                let sacado = b.bind_mut().sacar();
                if let Some((producto, pos)) = sacado {
                    // REQ-SON-08: bolsa o caja de cartón según el empaque.
                    let id = if empaque == Empaque::Bolsa { ids::SACAR_BOLSA } else { ids::SACAR_CAJA };
                    sonido::sonar_en(&self.to_gd(), id, pos);
                    // REQ-DEP-05: aparece como objeto físico en la mano.
                    let mut c = Comida::crear(&producto);
                    c.bind_mut().fijar_temperatura(temp);
                    c.set_position(pos);
                    if let Some(mut padre) = self.base().get_parent() {
                        padre.add_child(&c);
                    }
                    c.set_global_position(pos);
                    self.agarrar(c.upcast());
                }
            }
            _ => {}
        }
    }

    /// REQ-INT-03, REQ-INT-04, REQ-INT-05
    fn actualizar_mano(&mut self, dt: f32) {
        let Some(c) = &self.mano else { return };
        if !c.is_instance_valid() || c.is_queued_for_deletion() {
            self.mano = None;
            return;
        }
        let Some(camara) = &self.camara else { return };
        let t = camara.get_global_transform();
        let mut c = c.clone();
        // REQ-INT-03: abajo a la derecha de la vista, cerca.
        let (_, _, medio) = Self::medidas(&c);
        let [x, y, z] = agarre::punto_mano(medio);
        let destino = t * Vector3::new(x, y, z);
        let diferencia = destino - c.get_global_position();

        self.segundos_en_mano += dt;
        if self.segundos_en_mano > 0.5 && diferencia.length() > DIST_TRABADO {
            self.soltar();
            return;
        }
        let mut v = diferencia * RESORTE;
        if v.length() > VEL_MAX_MANO {
            v = v.normalized() * VEL_MAX_MANO;
        }
        c.set_linear_velocity(v);
        // REQ-INT-03, REQ-INT-04: el giro va, como resorte, al derecho relativo a la cámara
        // (acostado, cruzado, inclinado hacia los ojos; dado vuelta si va por lados y lo estaba).
        let (ancho_x, fondo_z) = Self::ejes_horizontales(&c);
        let [ex, ey, ez] = agarre::giro_mano(ancho_x, fondo_z, self.volteado).map(formas::v3);
        let objetivo = t.basis.orthonormalized() * Basis::from_cols(ex, ey, ez);
        let actual = c.get_global_transform().basis.orthonormalized().get_quaternion();
        let mut q = (objetivo.get_quaternion() * actual.inverse()).normalized();
        if q.w < 0.0 {
            q = -q; // el camino corto
        }
        let angulo = q.get_angle();
        let w = if angulo > 1e-3 {
            q.get_axis().normalized() * (angulo * RESORTE_GIRO).min(GIRO_MAX_MANO)
        } else {
            Vector3::ZERO
        };
        c.set_angular_velocity(w);
    }

    /// REQ-INT-02, REQ-INT-08
    fn actualizar_cartel(&mut self) {
        let en_mano = self.mano.clone().filter(|c| c.is_instance_valid() && !c.is_queued_for_deletion());
        // REQ-INT-08: qué hace el clic con lo que tenés en la mano, ahí donde apuntás (lo mismo
        // que decide `colocar`).
        let colocacion = self.colocacion();
        let clic = colocacion.as_ref().map(|c| c.accion.cartel()).unwrap_or_default();
        let vista = self.vista();
        self.cartel_clic = en_mano.as_ref().zip(colocacion).map(|(m, c)| (m.instance_id(), vista, c));
        let mano_ocupada = en_mano.is_some();
        let objetivo = self.objetivo();
        let texto = if let Some(m) = en_mano {
            if let Ok(c) = m.clone().try_cast::<Comida>() {
                let c = c.bind();
                let mut t = format!("{}\n{} · [Clic der.] Tirar", c.descripcion(), clic);
                if let (Some(_), Some(Objetivo::Parrilla(_))) = (c.carbon(), &objetivo) {
                    t += " · [E] Cargar carbón en la parrilla";
                }
                if let Some(Objetivo::Pomo(p)) = &objetivo {
                    let p = p.bind();
                    if c.repone().is_some() {
                        t += &format!(" · [E] Recargar {}", p.cartel());
                    } else if c.admite_aderezos() {
                        t += &format!(" · [E] Poner {}", p.cartel());
                    }
                }
                if let Some(Objetivo::Comida(o)) = &objetivo {
                    t += &preparar::cartel(Some(c.producto()), o); // REQ-FRE-01..03
                }
                if let Some(Objetivo::Cartel(k)) = &objetivo {
                    t += &format!(" · {}", k.bind().cartel().replace("[Clic/E]", "[E]")); // REQ-CLI-13
                }
                t
            } else if let Ok(p) = m.try_cast::<Paquete>() {
                let p = p.bind();
                let mut t = format!("{}\n{} · [Clic der.] Tirar", p.descripcion(), clic);
                // REQ-COC-10
                if let Some(Objetivo::Hervidor(h)) = &objetivo
                    && let Some(def) = catalogo().producto(&p.def().producto)
                    && def.va_al_hervidor()
                {
                    // Van las que entran (REQ-COC-08): sin lugar, el hervidor está lleno.
                    let (media_altura, medio_ancho, _) = comida::medidas_de(def);
                    let libres = h.bind().lugares_libres(medio_ancho * 2.0, media_altura * 2.0).len();
                    match agarre::repartir_volcado(p.restantes(), libres) {
                        (0, _) => t += " · Hervidor lleno",
                        (n, _) => t += &format!(" · [E] Echar al agua ({n} × {})", def.nombre),
                    }
                }
                if let Some(Objetivo::Cartel(k)) = &objetivo {
                    t += &format!(" · {}", k.bind().cartel().replace("[Clic/E]", "[E]")); // REQ-CLI-13
                }
                t
            } else {
                String::new()
            }
        } else {
            match objetivo {
                Some(Objetivo::Comida(c)) => {
                    let mut t = format!("[Clic] Agarrar {}", c.bind().descripcion().to_lowercase());
                    if c.bind().por_lados() {
                        t += " · [E] Dar vuelta";
                    }
                    t += &preparar::cartel(None, &c); // REQ-FRE-03: sin la herramienta
                    // REQ-FRE-08
                    if let Some(e) = freidora::cartel_colador(&c) {
                        t += &format!(" · {e}");
                    }
                    t
                }
                Some(Objetivo::Hervidor(h)) => h.bind().cartel(),
                Some(Objetivo::Plancha(p)) => p.bind().cartel(),
                Some(Objetivo::Parrilla(p)) => p.bind().cartel(),
                Some(Objetivo::Heladera(h)) => h.bind().cartel(),
                Some(Objetivo::Puerta(p)) => p.bind().cartel(),
                Some(Objetivo::Cartel(c)) => c.bind().cartel(),
                Some(Objetivo::Freidora(f)) => self.punto_mira().map(|p| f.bind().cartel(p)).unwrap_or_default(),
                Some(Objetivo::Bloque(b)) => b.bind().cartel(),
                Some(Objetivo::Paquete(p)) => format!("[Clic] Agarrar {}", p.bind().descripcion().to_lowercase()),
                Some(Objetivo::Pomo(p)) => format!("{} — agarrá un pancho y apretá E para ponerle", p.bind().cartel()),
                None => String::new(),
            }
        };
        let arbol = self.base().get_tree();
        if let Some(n) = arbol.get_first_node_in_group(hud::GRUPO)
            && let Ok(mut h) = n.try_cast::<Hud>()
        {
            h.bind_mut().set_cartel(&texto);
            h.bind_mut().set_mano_ocupada(mano_ocupada); // REQ-INT-01
        }
    }
}
