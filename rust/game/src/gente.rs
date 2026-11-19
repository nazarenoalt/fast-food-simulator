//! SPEC-013 (peatones) y SPEC-009 (clientes): decide qué hace cada persona.

use std::collections::HashMap;

use carrito_core::aderezos::enumerar;
use carrito_core::azar::Azar;
use carrito_core::caminos::{self, Red, TipoNodo};
use carrito_core::clientes::{self, Animo, Evaluacion, Fila, Paciencia, Pedido};
use carrito_core::eventos::Modificador;
use carrito_core::peatones::{Apariencia, Plan, Variedad};
use carrito_core::rutinas::Perfil;
use carrito_core::vestimenta;
use godot::classes::{INode3D, Node3D};
use godot::prelude::*;

use crate::carrito::{self, Carrito};
use crate::datos::{catalogo, plaza};
use crate::dia_noche::{self, DiaNoche};
use crate::hud;
use crate::negocio::{self, Negocio};
use crate::peaton::{Accion, Peaton};
use crate::util;

// Cada tarea de la etapa 5 tiene su archivo (submódulo, ve los campos de `Gente`).
#[path = "gente_cruces.rs"]
mod cruces; // TASK-0509: REQ-AMB-18
#[path = "gente_eventos.rs"]
mod eventos; // TASK-0505: SPEC-019
#[path = "gente_grupos.rs"]
mod grupos; // TASK-0503: REQ-RUT-05 a REQ-RUT-09
#[path = "gente_habituales.rs"]
mod habituales; // TASK-0504: SPEC-030

pub const GRUPO: &str = "gente";
const RADIO_CONVERTIR: f32 = 28.0;

#[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
struct Cliente {
    peaton: Gd<Peaton>,
    pedido: Option<Pedido>,
    paciencia: Paciencia,
    llego: bool,
    rechazados: Vec<InstanceId>,
    /// REQ-RUT-04
    perfil: Perfil,
    /// REQ-HAB-01: si es un habitual, su número (lo maneja `habituales`).
    habitual: Option<usize>,
}

#[derive(GodotClass)]
#[class(base=Node3D)]
#[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
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
    /// REQ-AMB-16: cómo se ven los presentes y los últimos que se fueron.
    variedad: Variedad,
    /// REQ-AMB-15: dónde estaba cada persona en el último cuadro y dónde desaparecieron las
    /// últimas que se fueron.
    donde: HashMap<u64, Vector3>,
    desapariciones: Vec<Vector3>,
    /// REQ-RUT-02: el perfil de cada persona.
    perfiles: HashMap<u64, Perfil>,
    /// Día y hora de este cuadro, y lo que cambian los eventos (REQ-EVE-04).
    dia: u32,
    hora: f32,
    modificador: Modificador,
    // Estado propio de cada tarea (ver los submódulos).
    est_cruces: cruces::Estado,
    est_eventos: eventos::Estado,
    est_grupos: grupos::Estado,
    est_habituales: habituales::Estado,
}

/// De dónde sale la apariencia de alguien que llega.
#[allow(dead_code)] // BASE-ETAPA-5: lo usan las tareas en paralelo; se saca al juntar.
enum Origen {
    /// Alguien nuevo, vestido de esta paleta (REQ-RUT-10, REQ-AMB-16).
    Nueva(carrito_core::peatones::Paleta),
    /// Un habitual que vuelve como era (REQ-HAB-01).
    Vuelve(Apariencia),
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
            variedad: Variedad::default(),
            donde: HashMap::new(),
            desapariciones: Vec::new(),
            perfiles: HashMap::new(),
            dia: 1,
            hora: 17.0,
            modificador: Modificador::default(),
            est_cruces: Default::default(),
            est_eventos: Default::default(),
            est_grupos: Default::default(),
            est_habituales: Default::default(),
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
            self.dia = d.dia();
            (d.hora(), d.minutos_por_segundo())
        };
        self.hora = hora;
        // REQ-EVE-04: lo que cambian los eventos activos.
        self.modificador = plaza().modificador(self.dia, hora);

        // Limpiar a los que ya se fueron.
        self.peatones.retain(|p| p.is_instance_valid());
        let vivos: Vec<u64> = self.peatones.iter().map(|p| p.bind().id).collect();
        self.asientos.retain(|id, _| vivos.contains(id));
        self.perfiles.retain(|id, _| vivos.contains(id));
        self.registrar_idas(&vivos);

        // REQ-AMB-04, REQ-RUT-01, REQ-RUT-03: cantidad de gente según la agenda (adelantada) y
        // los eventos; al empezar, la plaza ya tiene gente.
        let objetivo = plaza().agenda.cantidad_objetivo(hora, &self.modificador);
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
        // REQ-EVE-04: los eventos multiplican la tasa de clientes.
        let tasa = clientes::tasa_clientes(hora, reputacion) * self.modificador.clientes;
        let p = tasa / 60.0 * (min_por_s as f32 * dt);
        // REQ-CLI-12: con el cartel de cerrado colgado no se suman clientes nuevos.
        if clientes::llegan_clientes(&self.fila, self.cartel_cerrado()) && self.azar.chance(p) {
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
        // Lo propio de cada tarea de la etapa 5.
        self.cuadro_grupos(dt);
        self.cuadro_habituales(dt);
        self.cuadro_eventos(dt);
        self.avisar_vecinos();
        self.cuadro_cruces(dt);
    }
}

impl Gente {
    /// REQ-AMB-15, REQ-AMB-16: quien ya no está se fue (por una salida del borde): se anota
    /// dónde desapareció y su apariencia pasa a la memoria de las que se fueron.
    fn registrar_idas(&mut self, vivos: &[u64]) {
        let idas: Vec<u64> = self.donde.keys().copied().filter(|id| !vivos.contains(id)).collect();
        for id in idas {
            if let Some(p) = self.donde.remove(&id) {
                self.desapariciones.push(p);
            }
        }
        let sobran = self.desapariciones.len().saturating_sub(64);
        self.desapariciones.drain(..sobran);
        self.variedad.quedan(vivos);
        for p in &self.peatones {
            self.donde.insert(p.bind().id, p.get_global_position());
        }
    }

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

    /// Una persona de ese perfil, vestida según la hora (REQ-RUT-10) y sin repetir a nadie
    /// (REQ-AMB-16), con su velocidad (REQ-RUT-02).
    fn agregar(&mut self, en: usize, acciones: Vec<Accion>, perfil: Perfil, plan: Plan) -> Gd<Peaton> {
        let paleta = vestimenta::paleta(perfil, self.hora);
        // Un corredor que no trota (REQ-RUT-11, de noche) camina como cualquiera.
        let perfil_vel = if perfil == Perfil::Corredor && plan != Plan::Trotar { Perfil::Paseante } else { perfil };
        let vel = plaza().agenda.velocidad(&mut self.azar, perfil_vel);
        self.agregar_con(en, acciones, perfil, plan, Origen::Nueva(paleta), vel)
    }

    /// Como `agregar`, eligiendo de dónde sale la apariencia y la velocidad.
    fn agregar_con(
        &mut self,
        en: usize,
        acciones: Vec<Accion>,
        perfil: Perfil,
        plan: Plan,
        origen: Origen,
        vel: f32,
    ) -> Gd<Peaton> {
        let id = self.sig_id;
        self.sig_id += 1;
        let ap = match origen {
            Origen::Nueva(paleta) => {
                let mut ap = self.variedad.nueva_con(&mut self.azar, id, &paleta); // REQ-AMB-16
                self.retocar_por_evento(&mut ap, perfil); // REQ-EVE-07
                ap
            }
            Origen::Vuelve(ap) => {
                self.variedad.vuelve(id, ap.clone()); // REQ-HAB-01
                ap
            }
        };
        let mut p = Peaton::crear(id, ap, vel, plan == Plan::PasearPerro, acciones);
        let pos = self.pos(en);
        self.base_mut().add_child(&p);
        p.set_global_position(pos);
        self.peatones.push(p.clone());
        self.perfiles.insert(id, perfil); // REQ-RUT-02
        p
    }

    /// Asientos de la red que nadie ocupa y se pueden usar a esta hora (REQ-RUT-11).
    fn asientos_libres(&self) -> Vec<usize> {
        let ocupados: Vec<usize> = self.asientos.values().copied().collect();
        self.red
            .de_tipo(|t| matches!(t, TipoNodo::Asiento { .. }))
            .into_iter()
            .filter(|a| !ocupados.contains(a))
            .filter(|a| vestimenta::asiento_permitido(self.red.pos[*a], self.hora))
            .collect()
    }

    /// REQ-RUT-02, REQ-RUT-11: la actividad de alguien de ese perfil a esta hora.
    fn plan_para(&mut self, perfil: Perfil) -> Plan {
        for _ in 0..12 {
            let plan = plaza().agenda.sortear_plan(&mut self.azar, perfil);
            if vestimenta::plan_permitido(perfil, plan, self.hora) {
                return plan;
            }
        }
        Plan::Pasear
    }

    /// REQ-AMB-04, REQ-AMB-05, REQ-RUT-01, REQ-RUT-02: alguien de la agenda con un plan.
    fn nuevo_paseante(&mut self, desde_salida: bool) {
        let perfil = plaza().agenda.sortear_perfil(&mut self.azar, self.hora, &self.modificador);
        // REQ-RUT-05 a REQ-RUT-09: los perfiles con comportamiento propio o en grupo.
        if self.planear_grupo(perfil, desde_salida) {
            return;
        }
        let mut plan = self.plan_para(perfil);
        // Si no hay banco libre (o permitido a esta hora), pasea: así no se pierde gente de la
        // agenda que prefiere sentarse (oficinistas, jubilados).
        let libres = self.asientos_libres();
        if plan == Plan::Sentarse && libres.is_empty() {
            plan = Plan::Pasear;
        }
        let inicio = if desde_salida { self.salida_al_azar() } else { self.al_azar(|t| *t == TipoNodo::Paso) };
        let salida = self.salida_al_azar();
        let c = self.azar.rango(-0.4, 0.4);
        match plan {
            Plan::Sentarse => {
                let Some(&asiento) = self.azar.elegir(&libres) else { return };
                let TipoNodo::Asiento { rot_y } = self.red.tipo[asiento] else { return };
                let mut ida = self.ruta(inicio, asiento, c);
                let vuelta = self.ruta(asiento, salida, c);
                let segundos = plaza().agenda.quieto(&mut self.azar, perfil);
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
                    perfil,
                    plan,
                );
                let id = p.bind().id;
                self.asientos.insert(id, asiento);
            }
            Plan::Charlar => {
                // Dos personas que se juntan a charlar en un lugar.
                let lugar = self.al_azar(|t| *t == TipoNodo::Charla);
                let centro = self.pos(lugar);
                let segundos = plaza().agenda.quieto(&mut self.azar, perfil);
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
                        perfil,
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
                self.agregar(inicio, vec![Accion::Caminar(ruta), Accion::Desaparecer], perfil, plan);
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
                // Un chico no viene solo a comprar (REQ-RUT-06).
                !self.clientes.contains_key(&b.id)
                    && !b.ocupado_quieto()
                    && !self.asientos.contains_key(&b.id)
                    && !self.est_grupos.es_chico(b.id)
            })
            .map(|p| (p.clone(), p.get_global_position().distance_to(destino)))
            .filter(|(_, d)| *d < RADIO_CONVERTIR)
            .min_by(|a, b| a.1.total_cmp(&b.1))
            .map(|(p, _)| p);

        let sorteado = plaza().agenda.sortear_perfil(&mut self.azar, self.hora, &self.modificador);
        let peaton = match (ya_en_la_fila, cercano) {
            (true, _) => {
                let mut p = self.agregar(nodo_fila, vec![Accion::EnFila], sorteado, Plan::Pasear);
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
                self.agregar(inicio, vec![Accion::Caminar(ruta), Accion::EnFila], sorteado, Plan::Pasear)
            }
        };
        // REQ-RUT-04: el cliente tiene el perfil del paseante que se tentó (o el sorteado).
        let id = peaton.bind().id;
        let perfil = self.perfiles.get(&id).copied().unwrap_or(sorteado);
        self.sumar_a_la_fila(peaton, perfil, 1.0, None)
    }

    /// REQ-CLI-03, REQ-RUT-04: suma a `peaton` a la fila como cliente, con la paciencia de su
    /// perfil multiplicada por `factor` (REQ-HAB-06). Devuelve su id, o `None` si no hay lugar.
    fn sumar_a_la_fila(
        &mut self,
        mut peaton: Gd<Peaton>,
        perfil: Perfil,
        factor: f32,
        habitual: Option<usize>,
    ) -> Option<u64> {
        let carrito = util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO)?;
        let id = peaton.bind().id;
        let lugar = self.fila.unirse(id)?;
        let destino = carrito.bind().posicion_fila(lugar);
        peaton.bind_mut().set_lugar_fila(destino, carrito.bind().mirada_fila());
        let paciencia = Paciencia::con_factor(plaza().agenda.paciencia(perfil) * factor);
        self.clientes.insert(
            id,
            Cliente { peaton, pedido: None, paciencia, llego: false, rechazados: Vec::new(), perfil, habitual },
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
        let mut perdidos: Vec<u64> = Vec::new();
        let mut atendidos: Vec<(u64, Evaluacion, Pedido)> = Vec::new();
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
                // REQ-HAB-04: el habitual pide lo de siempre.
                let p = match self.pedido_habitual(id, &menu, &aderezos) {
                    Some(p) => p,
                    None => clientes::generar_pedido(&mut self.azar, &menu, &aderezos),
                };
                let c = self.clientes.get_mut(&id).unwrap();
                c.pedido = Some(p);
            }
            let texto = self.clientes[&id].pedido.as_ref().map(|p| self.texto_globo(id, p)); // REQ-HAB-05
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
                perdidos.push(id);
                se_van.push(id);
                continue;
            }
            // REQ-CLI-05: globo con el pedido y el color de la paciencia.
            if let Some(texto) = texto {
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
                            let frase = rechazo.frase(&entregado.producto);
                            c.peaton.bind_mut().decir(frase, Color::from_rgb(1.0, 0.5, 0.4), 3.0);
                            hud::avisar(&yo, &format!("El cliente lo rechazó: {frase}"));
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
                            atendidos.push((id, ev, pedido));
                            se_van.push(id);
                        }
                    }
                    break;
                }
            }
        }

        // SPEC-030: los habituales recuerdan cómo los atendieron.
        for (id, ev, pedido) in atendidos {
            self.al_atender(id, &ev, &pedido);
        }
        for id in perdidos {
            self.al_perder(id);
        }
        for id in se_van {
            self.despedir(id);
        }
    }

    /// REQ-CLI-12: el estado del cartel de cerrado del carrito, si tiene.
    fn cartel_cerrado(&self) -> Option<clientes::CartelCerrado> {
        let carrito = util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO)?;
        let cartel = carrito.bind().cartel_cerrado()?;
        Some(cartel.bind().estado())
    }

    // ── Para pruebas ──────────────────────────────────────────────

    /// Una llegada sola, como las de REQ-CLI-01 pero segura (no al azar). Devuelve si se sumó
    /// alguien a la fila: con el cartel colgado, no (REQ-CLI-12).
    pub fn probar_llegada(&mut self) -> bool {
        clientes::llegan_clientes(&self.fila, self.cartel_cerrado()) && self.nuevo_cliente(false).is_some()
    }

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

    /// Para pruebas: hace llegar `n` personas de la agenda desde el borde, a la hora actual.
    /// Devuelve los ids de los que llegaron (un grupo cuenta como varios). REQ-RUT-01
    pub fn probar_paseantes(&mut self, n: usize) -> Vec<u64> {
        let antes = self.sig_id;
        for _ in 0..n {
            self.nuevo_paseante(true);
        }
        (antes..self.sig_id).filter(|id| self.perfiles.contains_key(id)).collect()
    }

    /// Para pruebas: el perfil de una persona presente. REQ-RUT-02
    pub fn perfil_de(&self, id: u64) -> Option<Perfil> {
        self.perfiles.get(&id).copied()
    }

    /// Para pruebas: cuánta gente quiere la agenda ahora (REQ-RUT-03, REQ-EVE-04).
    pub fn objetivo_gente(&self) -> usize {
        plaza().agenda.cantidad_objetivo(self.hora, &self.modificador)
    }

    /// Para pruebas: la paciencia con la que empezó el primero de la fila. REQ-RUT-04
    pub fn paciencia_total_del_primero(&self) -> Option<(Perfil, f32)> {
        self.fila.primero().and_then(|id| self.clientes.get(&id)).map(|c| (c.perfil, c.paciencia.total))
    }

    pub fn largo_fila(&self) -> usize {
        self.fila.len()
    }

    pub fn cantidad(&self) -> usize {
        self.peatones.len()
    }

    /// Para pruebas: dónde desaparecieron las últimas personas que se fueron. REQ-AMB-15
    pub fn desapariciones(&self) -> Vec<Vector3> {
        self.desapariciones.clone()
    }

    /// Para pruebas: nadie presente ni de las últimas que se fueron se ve igual. REQ-AMB-16
    pub fn apariencias_sin_repetir(&self) -> bool {
        self.variedad.sin_repetir() && self.variedad.presentes() == self.peatones.len()
    }

    /// Para pruebas: cambia el pedido del primero (para probar aderezos sí o sí).
    pub fn set_pedido_del_primero(&mut self, p: Pedido) {
        if let Some(c) = self.fila.primero().and_then(|id| self.clientes.get_mut(&id)) {
            c.pedido = Some(p);
        }
    }
}
