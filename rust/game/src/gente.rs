//! SPEC-013 (peatones) y SPEC-009 (clientes): decide qué hace cada persona.

use std::collections::HashMap;

use carrito_core::aderezos::enumerar;
use carrito_core::azar::Azar;
use carrito_core::caminos::{self, Red, TipoNodo};
use carrito_core::clientes::{self, Animo, Fila, Paciencia, Pedido};
use carrito_core::peatones::{self, Plan};
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::carrito::{self, Carrito};
use crate::datos::catalogo;
use crate::dia_noche::{self, DiaNoche};
use crate::hud;
use crate::negocio::{self, Negocio};
use crate::peaton::{Accion, Peaton};
use crate::util;

pub const GRUPO: &str = "gente";
const RADIO_CONVERTIR: f32 = 28.0;

struct Cliente {
    peaton: Gd<Peaton>,
    pedido: Option<Pedido>,
    paciencia: Paciencia,
    llego: bool,
    rechazados: Vec<InstanceId>,
}

#[derive(GodotClass)]
#[class(base=Node3D)]
pub struct Gente {
    base: Base<Node3D>,
    red: Red,
    azar: Azar,
    sig_id: u64,
    peatones: Vec<Gd<Peaton>>,
    asientos: HashMap<u64, usize>,
    fila: Fila,
    clientes: HashMap<u64, Cliente>,
    t_spawn: f32,
    poblado: bool,
}

fn color_animo(a: Animo) -> Color {
    match a {
        Animo::Contento => Color::from_rgb(0.55, 1.0, 0.55),
        Animo::Impaciente => Color::from_rgb(1.0, 0.9, 0.35),
        Animo::Enojado => Color::from_rgb(1.0, 0.4, 0.35),
    }
}

/// "Pancho con mostaza y ketchup" / "Pancho sin aderezos". REQ-CLI-05
fn texto_pedido(p: &Pedido) -> String {
    let nombre = catalogo().producto(&p.producto).map(|d| d.nombre.clone()).unwrap_or_default();
    let nombre = carrito_core::aderezos::capitalizar(&nombre);
    if p.aderezos.is_empty() {
        format!("{nombre} sin aderezos")
    } else {
        let ad: Vec<String> =
            p.aderezos.iter().map(|a| catalogo().aderezo(a).map(|d| d.nombre.clone()).unwrap_or_default()).collect();
        format!("{nombre} con {}", enumerar(&ad))
    }
}

#[godot_api]
impl INode3D for Gente {
    fn init(base: Base<Node3D>) -> Self {
        Self {
            base,
            red: caminos::red(),
            azar: Azar::new(77),
            sig_id: 1,
            peatones: Vec::new(),
            asientos: HashMap::new(),
            fila: Fila::default(),
            clientes: HashMap::new(),
            t_spawn: 0.0,
            poblado: false,
        }
    }

    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        let yo = self.to_gd();
        let Some(dn) = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO) else { return };
        let (hora, min_por_s) = {
            let d = dn.bind();
            (d.hora(), d.minutos_por_segundo())
        };

        // Limpiar a los que ya se fueron.
        self.peatones.retain(|p| p.is_instance_valid());
        let vivos: Vec<u64> = self.peatones.iter().map(|p| p.bind().id).collect();
        self.asientos.retain(|id, _| vivos.contains(id));

        // REQ-AMB-04: cantidad de gente según la hora; al empezar, la plaza ya tiene gente.
        let objetivo = peatones::cantidad_objetivo(hora);
        if !self.poblado {
            self.poblado = true;
            for _ in 0..objetivo {
                self.nuevo_paseante(false);
            }
        }
        self.t_spawn -= dt;
        let paseantes = self.peatones.len() - self.clientes.len();
        if paseantes < objetivo && self.t_spawn <= 0.0 {
            self.nuevo_paseante(true);
            self.t_spawn = 1.5;
        }

        // REQ-CLI-01: llegada de clientes (proceso al azar con la tasa por hora de juego).
        let reputacion = util::unico::<Negocio>(&yo, negocio::GRUPO).map(|n| n.bind().reputacion()).unwrap_or(3.0);
        let p = clientes::tasa_clientes(hora, reputacion) / 60.0 * (min_por_s as f32 * dt);
        if !self.fila.llena() && self.azar.chance(p) {
            self.nuevo_cliente(false);
        }
        // REQ-CLI-11: tecla de prueba.
        if godot::classes::Input::singleton().is_action_just_pressed("traer_cliente")
            && !self.fila.llena()
            && !crate::armado::escribiendo()
        {
            self.nuevo_cliente(false);
        }

        self.atender_clientes(dt);
        self.avisar_vecinos();
    }
}

impl Gente {
    /// REQ-AMB-13: a cada peatón le pasa las posiciones de quienes tiene a menos de 2 m
    /// (incluido el jugador), para que los esquive.
    fn avisar_vecinos(&mut self) {
        let yo = self.to_gd();
        let mut posiciones: Vec<[f32; 2]> = self
            .peatones
            .iter()
            .map(|p| {
                let v = p.get_global_position();
                [v.x, v.z]
            })
            .collect();
        let n = posiciones.len();
        if let Some(j) = util::unico::<Node3D>(&yo, "jugador") {
            let v = j.get_global_position();
            posiciones.push([v.x, v.z]);
        }
        for (i, p) in self.peatones.iter_mut().enumerate().take(n) {
            let a = posiciones[i];
            let cerca: Vec<[f32; 2]> = posiciones
                .iter()
                .enumerate()
                .filter(|(k, b)| *k != i && (a[0] - b[0]).hypot(a[1] - b[1]) < 2.0)
                .map(|(_, b)| *b)
                .collect();
            p.bind_mut().set_vecinos(cerca);
        }
    }

    fn pos(&self, nodo: usize) -> Vector3 {
        let p = self.red.pos[nodo];
        Vector3::new(p[0], 0.0, p[1])
    }

    /// Camino entre dos nodos, con un corrimiento lateral propio de cada persona.
    fn ruta(&mut self, desde: usize, hasta: usize, corrimiento: f32) -> Vec<Vector3> {
        let Some(nodos) = self.red.camino(desde, hasta) else { return vec![self.pos(hasta)] };
        let n = nodos.len();
        nodos
            .iter()
            .enumerate()
            .map(|(i, &k)| {
                let mut p = self.pos(k);
                if i > 0 && i + 1 < n {
                    p.x += corrimiento;
                    p.z += corrimiento * 0.7;
                }
                p
            })
            .collect()
    }

    fn al_azar(&mut self, f: impl Fn(&TipoNodo) -> bool) -> usize {
        let v = self.red.de_tipo(f);
        *self.azar.elegir(&v).unwrap_or(&0)
    }

    fn salida_al_azar(&mut self) -> usize {
        self.al_azar(|t| *t == TipoNodo::Salida)
    }

    fn agregar(&mut self, en: usize, acciones: Vec<Accion>, plan: Plan) -> Gd<Peaton> {
        let id = self.sig_id;
        self.sig_id += 1;
        let ap = peatones::apariencia(&mut self.azar);
        let vel = peatones::velocidad(&mut self.azar, plan);
        let mut p = Peaton::crear(id, ap, vel, plan == Plan::PasearPerro, acciones);
        let pos = self.pos(en);
        self.base_mut().add_child(&p);
        p.set_global_position(pos);
        self.peatones.push(p.clone());
        p
    }

    /// REQ-AMB-04, REQ-AMB-05: un paseante con un plan.
    fn nuevo_paseante(&mut self, desde_salida: bool) {
        let plan = peatones::elegir_plan(&mut self.azar);
        let inicio = if desde_salida { self.salida_al_azar() } else { self.al_azar(|t| *t == TipoNodo::Paso) };
        let salida = self.salida_al_azar();
        let c = self.azar.rango(-0.4, 0.4);
        match plan {
            Plan::Sentarse => {
                let ocupados: Vec<usize> = self.asientos.values().copied().collect();
                let libres: Vec<usize> = self
                    .red
                    .de_tipo(|t| matches!(t, TipoNodo::Asiento { .. }))
                    .into_iter()
                    .filter(|a| !ocupados.contains(a))
                    .collect();
                let Some(&asiento) = self.azar.elegir(&libres) else { return };
                let TipoNodo::Asiento { rot_y } = self.red.tipo[asiento] else { return };
                let mut ida = self.ruta(inicio, asiento, c);
                let vuelta = self.ruta(asiento, salida, c);
                let segundos = peatones::duracion_quieto(&mut self.azar, plan);
                if !desde_salida {
                    ida = vec![self.pos(asiento)];
                }
                let p = self.agregar(
                    if desde_salida { inicio } else { asiento },
                    vec![
                        Accion::Caminar(ida),
                        Accion::Sentarse { rot_y, segundos },
                        Accion::Caminar(vuelta),
                        Accion::Desaparecer,
                    ],
                    plan,
                );
                let id = p.bind().id;
                self.asientos.insert(id, asiento);
            }
            Plan::Charlar => {
                // Dos personas que se juntan a charlar en un lugar.
                let lugar = self.al_azar(|t| *t == TipoNodo::Charla);
                let centro = self.pos(lugar);
                let segundos = peatones::duracion_quieto(&mut self.azar, plan);
                for lado in [-1.0_f32, 1.0] {
                    let destino = centro + Vector3::new(lado * 0.45, 0.0, 0.0);
                    let otro = centro - Vector3::new(lado * 0.45, 0.0, 0.0);
                    let mut ida = self.ruta(inicio, lugar, c + lado * 0.3);
                    ida.push(destino);
                    let s2 = self.salida_al_azar();
                    let vuelta = self.ruta(lugar, s2, c);
                    let empieza = if desde_salida { inicio } else { lugar };
                    let mut p = self.agregar(
                        empieza,
                        vec![
                            Accion::Caminar(ida),
                            Accion::Charlar { mirar: otro, segundos },
                            Accion::Caminar(vuelta),
                            Accion::Desaparecer,
                        ],
                        plan,
                    );
                    if !desde_salida {
                        p.set_global_position(destino);
                    }
                }
            }
            Plan::Pasear | Plan::Trotar | Plan::PasearPerro => {
                // Pasa por uno o dos lugares de la plaza y se va.
                let mut ruta = Vec::new();
                let mut desde = inicio;
                let paradas = if plan == Plan::Trotar { 3 } else { 1 + self.azar.entero(2) };
                for _ in 0..paradas {
                    let hasta = self.al_azar(|t| *t == TipoNodo::Paso);
                    ruta.extend(self.ruta(desde, hasta, c));
                    desde = hasta;
                }
                ruta.extend(self.ruta(desde, salida, c));
                self.agregar(inicio, vec![Accion::Caminar(ruta), Accion::Desaparecer], plan);
            }
        }
    }

    /// REQ-CLI-02: un cliente. Si hay un paseante cerca, se tienta y viene; si no, llega
    /// caminando desde la salida más cercana.
    fn nuevo_cliente(&mut self, ya_en_la_fila: bool) -> Option<u64> {
        let yo = self.to_gd();
        let carrito = util::unico::<Carrito>(&yo, carrito::GRUPO)?;
        let destino = carrito.bind().posicion_fila(self.fila.len());
        let nodo_fila = self.red.mas_cercano(destino.x, destino.z);

        let cercano = self
            .peatones
            .iter()
            .filter(|p| {
                let b = p.bind();
                !self.clientes.contains_key(&b.id) && !b.ocupado_quieto() && !self.asientos.contains_key(&b.id)
            })
            .map(|p| (p.clone(), p.get_global_position().distance_to(destino)))
            .filter(|(_, d)| *d < RADIO_CONVERTIR)
            .min_by(|a, b| a.1.total_cmp(&b.1))
            .map(|(p, _)| p);

        let mut peaton = match (ya_en_la_fila, cercano) {
            (true, _) => {
                let mut p = self.agregar(nodo_fila, vec![Accion::EnFila], Plan::Pasear);
                p.set_global_position(destino);
                p
            }
            (false, Some(mut p)) => {
                let pos = p.get_global_position();
                let desde = self.red.mas_cercano(pos.x, pos.z);
                let ruta = self.ruta(desde, nodo_fila, 0.0);
                p.bind_mut().reemplazar_acciones(vec![Accion::Caminar(ruta), Accion::EnFila]);
                p
            }
            (false, None) => {
                let salidas = self.red.de_tipo(|t| *t == TipoNodo::Salida);
                let inicio = salidas
                    .into_iter()
                    .min_by(|&a, &b| self.pos(a).distance_to(destino).total_cmp(&self.pos(b).distance_to(destino)))
                    .unwrap_or(0);
                let ruta = self.ruta(inicio, nodo_fila, 0.0);
                self.agregar(inicio, vec![Accion::Caminar(ruta), Accion::EnFila], Plan::Pasear)
            }
        };
        let id = peaton.bind().id;
        self.fila.unirse(id)?;
        peaton.bind_mut().set_lugar_fila(destino, carrito.bind().mirada_fila());
        self.clientes.insert(
            id,
            Cliente { peaton, pedido: None, paciencia: Paciencia::default(), llego: false, rechazados: Vec::new() },
        );
        Some(id)
    }

    fn despedir(&mut self, id: u64) {
        self.fila.salir(id);
        let Some(mut c) = self.clientes.remove(&id) else { return };
        if !c.peaton.is_instance_valid() {
            return;
        }
        let pos = c.peaton.get_global_position();
        let desde = self.red.mas_cercano(pos.x, pos.z);
        let salida = self.salida_al_azar();
        let corr = self.azar.rango(-0.3, 0.3);
        let ruta = self.ruta(desde, salida, corr);
        c.peaton.bind_mut().reemplazar_acciones(vec![Accion::Caminar(ruta), Accion::Desaparecer]);
    }

    /// REQ-CLI-03 a REQ-CLI-10
    fn atender_clientes(&mut self, dt: f32) {
        let yo = self.to_gd();
        let Some(carrito) = util::unico::<Carrito>(&yo, carrito::GRUPO) else { return };
        let mut negocio = util::unico::<Negocio>(&yo, negocio::GRUPO);
        let mut se_van: Vec<u64> = Vec::new();
        let ids: Vec<u64> = self.clientes.keys().copied().collect();
        let mirada = carrito.bind().mirada_fila();
        let primero = self.fila.primero();
        let menu = carrito.bind().menu();
        let aderezos = carrito.bind().aderezos_disponibles();

        for id in ids {
            let Some(lugar) = self.fila.lugar(id) else { continue };
            let destino = carrito.bind().posicion_fila(lugar);
            let pedido_nuevo = {
                let c = self.clientes.get_mut(&id).unwrap();
                if !c.peaton.is_instance_valid() {
                    se_van.push(id);
                    continue;
                }
                // REQ-CLI-03: los de atrás avanzan.
                c.peaton.bind_mut().set_lugar_fila(destino, mirada);
                if c.peaton.bind().en_lugar() {
                    if !c.llego {
                        // REQ-SON-08: campanita cuando el cliente llega a la fila.
                        crate::sonido::sonar_en(&yo, carrito_core::sonido::ids::CAMPANITA, destino);
                    }
                    c.llego = true;
                }
                c.llego && Some(id) == primero && c.pedido.is_none()
            };
            // REQ-CLI-04: el primero, al llegar, pide.
            if pedido_nuevo {
                let p = clientes::generar_pedido(&mut self.azar, &menu, &aderezos);
                let c = self.clientes.get_mut(&id).unwrap();
                c.pedido = Some(p);
            }
            let c = self.clientes.get_mut(&id).unwrap();
            if !c.llego {
                continue;
            }
            // REQ-CLI-06: paciencia.
            if c.paciencia.paso(dt, c.pedido.is_some()) {
                c.peaton.bind_mut().globo("", Color::WHITE);
                c.peaton.bind_mut().decir("¡Me cansé de esperar!", Color::from_rgb(1.0, 0.4, 0.35), 3.0);
                if let Some(n) = &mut negocio {
                    n.bind_mut().cliente_perdido();
                }
                hud::avisar(&yo, "Un cliente se fue enojado · ★☆☆☆☆");
                se_van.push(id);
                continue;
            }
            // REQ-CLI-05: globo con el pedido y el color de la paciencia.
            if let Some(p) = &c.pedido {
                let texto = texto_pedido(p);
                let color = color_animo(c.paciencia.animo());
                c.peaton.bind_mut().globo(&texto, color);
            }
        }

        // REQ-CLI-07, REQ-CLI-08: lo que está en la bandeja es para el primero que espera.
        if let Some(id) = primero {
            let listo = self.clientes.get(&id).is_some_and(|c| c.pedido.is_some() && c.llego);
            if listo {
                for mut comida in carrito.bind().comida_en_bandeja() {
                    let c = self.clientes.get_mut(&id).unwrap();
                    if c.rechazados.contains(&comida.instance_id()) {
                        continue;
                    }
                    let entregado = comida.bind().entregado();
                    let pedido = c.pedido.clone().unwrap();
                    let precio = catalogo().producto(&pedido.producto).and_then(|p| p.precio).unwrap_or(0.0);
                    match clientes::evaluar(&pedido, &entregado, precio, c.paciencia.usada()) {
                        Err(rechazo) => {
                            c.rechazados.push(comida.instance_id());
                            c.paciencia.penalizar(clientes::PENALIDAD_RECHAZO_S);
                            c.peaton.bind_mut().decir(rechazo.frase(), Color::from_rgb(1.0, 0.5, 0.4), 3.0);
                            hud::avisar(&yo, &format!("El cliente lo rechazó: {}", rechazo.frase()));
                        }
                        Ok(ev) => {
                            // REQ-CLI-09, REQ-CLI-10
                            let texto = negocio.as_mut().map(|n| n.bind_mut().venta(&ev)).unwrap_or_default();
                            comida.queue_free();
                            c.peaton.bind_mut().globo("", Color::WHITE);
                            c.peaton.bind_mut().decir(&texto, Color::from_rgb(0.6, 1.0, 0.6), 3.5);
                            c.peaton.bind_mut().comer();
                            hud::avisar(&yo, &format!("Venta: {texto}"));
                            // REQ-SON-08
                            crate::sonido::sonar(&yo, carrito_core::sonido::ids::COBRO);
                            se_van.push(id);
                        }
                    }
                    break;
                }
            }
        }

        for id in se_van {
            self.despedir(id);
        }
    }

    // ── Para pruebas ──────────────────────────────────────────────

    pub fn forzar_cliente(&mut self) -> Option<u64> {
        self.nuevo_cliente(true)
    }

    pub fn pedido_del_primero(&self) -> Option<Pedido> {
        self.fila.primero().and_then(|id| self.clientes.get(&id)).and_then(|c| c.pedido.clone())
    }

    pub fn set_paciencia_del_primero(&mut self, s: f32) {
        if let Some(c) = self.fila.primero().and_then(|id| self.clientes.get_mut(&id)) {
            c.paciencia.restante = s;
        }
    }

    pub fn largo_fila(&self) -> usize {
        self.fila.len()
    }

    pub fn cantidad(&self) -> usize {
        self.peatones.len()
    }

    /// Para pruebas: cambia el pedido del primero (para probar aderezos sí o sí).
    pub fn set_pedido_del_primero(&mut self, p: Pedido) {
        if let Some(c) = self.fila.primero().and_then(|id| self.clientes.get_mut(&id)) {
            c.pedido = Some(p);
        }
    }
}
