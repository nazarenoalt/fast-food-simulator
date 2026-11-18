//! Prueba de humo (SPEC-000): abre el mundo real sin pantalla y verifica los criterios de
//! aceptación de integración. Se corre con `tools/prueba_humo.sh`.

use carrito_core::coccion::Punto;
use carrito_core::plaza;
use godot::classes::{INode, Node, Node3D, PackedScene};
use godot::prelude::*;

use crate::aderecera::Pomo;
use crate::bloque_stock::BloqueStock;
use crate::carrito::Carrito;
use crate::comida::Comida;
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::hervidor::Hervidor;
use crate::jugador::Jugador;
use crate::lugar_deposito::LugarDeposito;
use crate::luz::{GRUPO_LUCES_NOCHE, LuzNocturna};
use crate::negocio::Negocio;
use crate::palomas::Palomas;
use crate::paquete::Paquete;
use crate::peaton::Peaton;
use crate::sonido::Sonido;
use crate::transito::{Autos, Nubes};

#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct PruebaHumo {
    base: Base<Node>,
    cuadro: u32,
    paso: u32,
    espera_hasta: u32,
    fallas: Vec<String>,
    salchicha: Option<Gd<Comida>>,
    pan: Option<Gd<Comida>>,
    mundo: Option<Gd<Node>>,
    autos_antes: Vec<f32>,
    nube_antes: Option<Vector3>,
    panchos_antes: Vec<InstanceId>,
    pedido: Option<carrito_core::clientes::Pedido>,
    saldo_antes: f32,
    reputacion_antes: f32,
    perdidos_antes: u32,
    paquetes_antes: usize,
    lugar: Option<Gd<LugarDeposito>>,
    superpuestos: usize,
    muestras: usize,
}

fn todos<T: GodotClass + Inherits<Node>>(raiz: &Gd<Node>) -> Vec<Gd<T>> {
    let mut v = Vec::new();
    let mut pila = vec![raiz.clone()];
    while let Some(n) = pila.pop() {
        for h in n.get_children().iter_shared() {
            pila.push(h.clone());
        }
        if let Ok(t) = n.try_cast::<T>() {
            v.push(t);
        }
    }
    v
}

impl PruebaHumo {
    fn chequear(&mut self, ok: bool, que: &str) {
        if ok {
            godot_print!("  OK    {que}");
        } else {
            godot_print!("  FALLA {que}");
            self.fallas.push(que.to_string());
        }
    }

    fn esperar(&mut self, cuadros: u32) {
        self.espera_hasta = self.cuadro + cuadros;
    }

    fn mundo(&self) -> Gd<Node> {
        self.mundo.clone().expect("mundo cargado")
    }

    fn agregar_comida(&self, producto: &str, pos: Vector3) -> Gd<Comida> {
        let mut c = Comida::crear(producto);
        self.mundo().add_child(&c);
        c.set_global_position(pos);
        c
    }

    fn terminar(&mut self) {
        if self.fallas.is_empty() {
            godot_print!("PRUEBA DE HUMO: todo OK");
            self.base().get_tree().quit_ex().exit_code(0).done();
        } else {
            godot_print!("PRUEBA DE HUMO: {} falla(s): {:?}", self.fallas.len(), self.fallas);
            self.base().get_tree().quit_ex().exit_code(1).done();
        }
    }
}

#[godot_api]
impl INode for PruebaHumo {
    fn ready(&mut self) {
        let escena = load::<PackedScene>("res://scenes/main.tscn");
        let mundo = escena.instantiate().expect("instanciar main.tscn");
        self.base_mut().add_child(&mundo);
        self.mundo = Some(mundo);
        godot_print!("PRUEBA DE HUMO: arrancando");
    }

    fn physics_process(&mut self, _delta: f64) {
        self.cuadro += 1;
        // REQ-AMB-13: mientras la plaza está llena (pasos 8 a 11), se cuenta cuántas veces
        // dos personas quedan encimadas (a menos de 0,3 m).
        if (8..=11).contains(&self.paso) {
            let mundo = self.mundo();
            let pos: Vec<Vector3> = todos::<Peaton>(&mundo).iter().map(|p| p.get_global_position()).collect();
            self.muestras += 1;
            for i in 0..pos.len() {
                for j in (i + 1)..pos.len() {
                    if Vector2::new(pos[i].x - pos[j].x, pos[i].z - pos[j].z).length() < 0.3 {
                        self.superpuestos += 1;
                    }
                }
            }
        }
        if self.cuadro < self.espera_hasta {
            return;
        }
        let mundo = self.mundo();
        match self.paso {
            // Esperar a que todo se construya y se asiente.
            0 => self.esperar(30),
            1 => {
                // REQ-JUG-08: el jugador aparece detrás del mostrador.
                let jugadores = todos::<Jugador>(&mundo);
                let z = jugadores.first().map(|j| j.get_global_position().z).unwrap_or(0.0);
                self.chequear(z < plaza::Z_VEREDA, "REQ-JUG-08 jugador detrás del mostrador");
                self.chequear(todos::<Hervidor>(&mundo).len() == 1, "REQ-CAR-07 el carrito tiene su hervidor");

                // CA-DEP-01: saco 3 panes, quedan 9 visibles.
                let mut panes = todos::<BloqueStock>(&mundo)
                    .into_iter()
                    .find(|b| b.bind().producto() == "pan_pancho")
                    .expect("bolsa de panes");
                for _ in 0..3 {
                    let (prod, pos) = panes.bind_mut().sacar().expect("sacar pan");
                    self.agregar_comida(&prod, pos);
                }
                let (r, v) = (panes.bind().restantes(), panes.bind().unidades_visibles());
                self.chequear(r == 9 && v == 9, &format!("CA-DEP-01 quedan 9 panes visibles (hay {v})"));

                // CA-DEP-02: saco las 12 salchichas de un paquete → el paquete desaparece.
                let mut caja = todos::<BloqueStock>(&mundo)
                    .into_iter()
                    .find(|b| b.bind().producto() == "salchicha")
                    .expect("paquete de salchichas");
                for _ in 0..12 {
                    caja.bind_mut().sacar();
                }
                self.chequear(caja.is_queued_for_deletion(), "CA-DEP-02 paquete vacío desaparece");

                // CA-COC-01: hervidor encendido con agua caliente; tiro una salchicha.
                let mut h = todos::<Hervidor>(&mundo).pop().unwrap();
                h.bind_mut().alternar();
                h.bind_mut().set_temperatura(95.0);
                let encima = h.get_global_position() + Vector3::new(0.0, 0.15, 0.0);
                self.salchicha = Some(self.agregar_comida("salchicha", encima));
                // 75 s de juego a 60 cuadros por segundo.
                self.esperar(75 * 60);
            }
            2 => {
                let s = self.salchicha.clone().unwrap();
                let punto = s.bind().punto();
                let temp = s.bind().estado_coccion().map(|e| e.temp).unwrap_or(0.0);
                self.chequear(
                    punto == Some(Punto::Cocido),
                    &format!("CA-COC-01 salchicha cocida en el hervidor ({punto:?}, {temp:.0} °C)"),
                );
                let h = todos::<Hervidor>(&mundo).pop().unwrap();
                let dentro = s.get_global_position().y < h.get_global_position().y + 0.2;
                self.chequear(dentro, "CA-INT-01 la salchicha quedó dentro del hervidor (no lo atravesó)");

                // CA-COC-02: la saco y deja de cocinarse.
                let mut s2 = s.clone();
                s2.set_global_position(Vector3::new(3.0, 0.3, plaza::Z_VEREDA));
                s2.set_linear_velocity(Vector3::ZERO);
                self.esperar(60 * 60);
            }
            3 => {
                let s = self.salchicha.clone().unwrap();
                self.chequear(s.bind().punto() == Some(Punto::Cocido), "CA-COC-02 afuera no se sigue cocinando");

                // CA-ARM-01: pan sobre la mesada, salchicha suelta encima → pancho.
                let carrito =
                    todos::<Node3D>(&mundo).into_iter().find(|n| n.get_name().to_string() == "Carrito").unwrap();
                let sobre_mesada = carrito.get_global_position() + Vector3::new(0.4, 1.0, 0.0);
                self.pan = Some(self.agregar_comida("pan_pancho", sobre_mesada));
                self.esperar(60);
            }
            4 => {
                let pan = self.pan.clone().unwrap();
                let mut s = self.salchicha.clone().unwrap();
                s.set_global_position(pan.get_global_position() + Vector3::new(0.0, 0.08, 0.0));
                s.set_global_rotation(Vector3::ZERO);
                s.set_linear_velocity(Vector3::ZERO);
                self.esperar(90);
            }
            5 => {
                let panchos: Vec<_> =
                    todos::<Comida>(&mundo).into_iter().filter(|c| c.bind().producto() == "pancho").collect();
                let detalle = panchos.first().and_then(|p| p.bind().detalle().map(str::to_string));
                self.chequear(
                    panchos.len() == 1 && detalle.as_deref() == Some("salchicha cocida"),
                    &format!("CA-ARM-01 se armó un pancho ({} panchos, detalle {detalle:?})", panchos.len()),
                );

                // REQ-ARM-04: dos salchichas juntas no hacen nada.
                let base = Vector3::new(-3.0, 0.3, plaza::Z_VEREDA);
                self.agregar_comida("salchicha", base);
                self.agregar_comida("salchicha", base + Vector3::new(0.0, 0.05, 0.0));

                // CA-DIA-01: a las 20:00 las luces están prendidas.
                let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                dn.bind_mut().set_minuto(20.0 * 60.0);
                self.esperar(10);
            }
            6 => {
                let salchichas =
                    todos::<Comida>(&mundo).into_iter().filter(|c| c.bind().producto() == "salchicha").count();
                self.chequear(salchichas >= 2, "REQ-ARM-04 salchicha + salchicha no se combinan");

                let luces = self.base().get_tree().get_nodes_in_group(GRUPO_LUCES_NOCHE);
                let prendidas = luces
                    .iter_shared()
                    .filter_map(|n| n.try_cast::<LuzNocturna>().ok())
                    .filter(|l| l.bind().encendida())
                    .count();
                self.chequear(
                    luces.len() > 5 && prendidas == luces.len(),
                    &format!("CA-DIA-01 de noche todas las luces prendidas ({prendidas}/{})", luces.len()),
                );
                let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                dn.bind_mut().set_minuto(12.0 * 60.0);
                self.esperar(10);
            }
            7 => {
                let luces = self.base().get_tree().get_nodes_in_group(GRUPO_LUCES_NOCHE);
                let prendidas = luces
                    .iter_shared()
                    .filter_map(|n| n.try_cast::<LuzNocturna>().ok())
                    .filter(|l| l.bind().encendida())
                    .count();
                self.chequear(prendidas == 0, "REQ-DIA-06 de día las luces apagadas");
                self.chequear(
                    todos::<Node3D>(&mundo).iter().all(|n| !n.is_in_group("errores_carrito")),
                    "REQ-CAR-08 sin errores en la config del carrito",
                );

                // ── Etapa 2: ambientación ──
                let ciudad =
                    todos::<Node3D>(&mundo).into_iter().find(|n| n.get_name().to_string() == "Ciudad").unwrap();
                self.chequear(ciudad.get_child_count() > 30, "REQ-AMB-01 hay edificios alrededor");
                self.autos_antes = todos::<Autos>(&mundo)[0].bind().posiciones();
                self.nube_antes = todos::<Nubes>(&mundo)[0].bind().posicion_primera();
                let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                dn.bind_mut().set_minuto(13.0 * 60.0);
                self.esperar(180);
            }
            8 => {
                let ahora = todos::<Autos>(&mundo)[0].bind().posiciones();
                self.chequear(ahora != self.autos_antes, "REQ-AMB-08 los autos circulan");
                let nube = todos::<Nubes>(&mundo)[0].bind().posicion_primera();
                self.chequear(nube != self.nube_antes, "REQ-AMB-11 las nubes se mueven");
                let gente = todos::<Gente>(&mundo).pop().unwrap();
                let n = gente.bind().cantidad();
                self.chequear(n >= 15, &format!("REQ-AMB-04 hay gente en la plaza a las 13:00 ({n})"));

                // CA-CLI-01: llega un cliente y pide.
                let mut g = gente.clone();
                if g.bind().largo_fila() == 0 {
                    g.bind_mut().forzar_cliente();
                }
                self.esperar(60);
            }
            9 => {
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                let pidio = gente.bind().pedido_del_primero();
                self.chequear(pidio.is_some(), &format!("REQ-CLI-04 el primero de la fila pidió: {pidio:?}"));
                // Para probar los aderezos sí o sí, el pedido pasa a ser con mostaza y ketchup.
                let pedido = carrito_core::clientes::Pedido {
                    producto: "pancho".into(),
                    aderezos: vec!["mostaza".into(), "ketchup".into()],
                };
                gente.bind_mut().set_pedido_del_primero(pedido.clone());
                self.pedido = Some(pedido);
                // Armo el pancho: salchicha cocida sobre un pan en la mesada.
                self.panchos_antes = todos::<Comida>(&mundo)
                    .iter()
                    .filter(|c| c.bind().producto() == "pancho")
                    .map(|c| c.instance_id())
                    .collect();
                let carrito = todos::<Carrito>(&mundo).pop().unwrap();
                let pos = carrito.get_global_position() + Vector3::new(0.05, 1.0, 0.1);
                self.pan = Some(self.agregar_comida("pan_pancho", pos));
                let mut s = self.agregar_comida("salchicha", pos + Vector3::new(0.0, 0.1, 0.0));
                s.bind_mut().forzar_avance(5.0);
                self.esperar(90);
            }
            10 => {
                let mut pancho = todos::<Comida>(&mundo)
                    .into_iter()
                    .find(|c| c.bind().producto() == "pancho" && !self.panchos_antes.contains(&c.instance_id()))
                    .expect("se armó el pancho");
                // CA-ADE-01: le pongo los aderezos del pedido.
                let pedido = self
                    .pedido
                    .clone()
                    .unwrap_or(carrito_core::clientes::Pedido { producto: "pancho".into(), aderezos: vec![] });
                let mut ok_usos = true;
                for a in &pedido.aderezos {
                    let mut pomo = todos::<Pomo>(&mundo).into_iter().find(|p| p.bind().aderezo() == a).expect("pomo");
                    let antes = pomo.bind().usos();
                    let r = pomo.bind_mut().aplicar(&mut pancho);
                    ok_usos &= r.is_ok() && pomo.bind().usos() == antes - 1;
                }
                let tiene = pancho.bind().aderezos().to_vec();
                self.chequear(
                    ok_usos && tiene == pedido.aderezos,
                    &format!(
                        "CA-ADE-01 aderezos puestos y pomos gastados ({tiene:?}) — {}",
                        pancho.bind().descripcion()
                    ),
                );
                let mut repetido = todos::<Pomo>(&mundo).into_iter().find(|p| p.bind().aderezo() == "mostaza").unwrap();
                if tiene.contains(&"mostaza".to_string()) {
                    self.chequear(
                        repetido.bind_mut().aplicar(&mut pancho).is_err(),
                        "REQ-ADE-04 no se repite un aderezo",
                    );
                }
                // Lo apoyo en la bandeja.
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                self.saldo_antes = negocio.bind().saldo();
                let carrito = todos::<Carrito>(&mundo).pop().unwrap();
                let bandeja = carrito.bind().pos_bandeja();
                pancho.set_global_position(bandeja + Vector3::new(0.0, 0.05, 0.0));
                pancho.set_global_rotation(Vector3::ZERO);
                pancho.set_linear_velocity(Vector3::ZERO);
                self.esperar(60);
            }
            11 => {
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                let (saldo, ventas) = (negocio.bind().saldo(), negocio.bind().ventas_de_hoy());
                self.chequear(
                    saldo >= self.saldo_antes + 2500.0 && ventas == 1,
                    &format!(
                        "CA-CLI-01 / CA-ECO-01 el cliente pagó (caja {} → {saldo}, ventas {ventas})",
                        self.saldo_antes
                    ),
                );
                let tasa = self.superpuestos as f32 / self.muestras.max(1) as f32;
                self.chequear(
                    tasa < 0.05,
                    &format!(
                        "REQ-AMB-13 la gente no se atraviesa ({} encimadas en {} cuadros)",
                        self.superpuestos, self.muestras
                    ),
                );
                // CA-CLI-02: el siguiente se cansa de esperar.
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                if gente.bind().largo_fila() == 0 {
                    gente.bind_mut().forzar_cliente();
                }
                gente.bind_mut().set_paciencia_del_primero(0.3);
                self.reputacion_antes = negocio.bind().reputacion();
                self.perdidos_antes = negocio.bind().perdidos_de_hoy();
                self.esperar(60);
            }
            12 => {
                let mut negocio = todos::<Negocio>(&mundo).pop().unwrap();
                let (rep, perdidos) = (negocio.bind().reputacion(), negocio.bind().perdidos_de_hoy());
                self.chequear(
                    perdidos == self.perdidos_antes + 1 && rep < self.reputacion_antes,
                    &format!("CA-CLI-02 se fue enojado y bajó la reputación ({:.2} → {rep:.2})", self.reputacion_antes),
                );
                // CA-ECO-02: sin plata no se compra.
                negocio.bind_mut().set_saldo(1000.0);
                let r = negocio.bind_mut().comprar("bolsa_panes_12");
                self.chequear(
                    r.is_err() && negocio.bind().saldo() == 1000.0,
                    "CA-ECO-02 no se puede comprar sin plata",
                );
                negocio.bind_mut().set_saldo(30_000.0);
                // CA-PRO-01: compro a las 10:00, llega a las 11:00.
                let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                dn.bind_mut().set_minuto(10.0 * 60.0);
                let r = negocio.bind_mut().comprar("bolsa_panes_12");
                self.chequear(
                    r.is_ok() && negocio.bind().saldo() == 30_000.0 - 1800.0,
                    &format!("REQ-PRO-02 compra hecha: {r:?}"),
                );
                self.paquetes_antes = todos::<Paquete>(&mundo).len();
                dn.bind_mut().set_minuto(10.0 * 60.0 + 59.0);
                self.esperar(5);
            }
            13 => {
                let n = todos::<Paquete>(&mundo).len();
                self.chequear(n == self.paquetes_antes, "REQ-PRO-03 a las 10:59 todavía no llegó");
                let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                dn.bind_mut().set_minuto(11.0 * 60.0 + 1.0);
                self.esperar(10);
            }
            14 => {
                let paquetes = todos::<Paquete>(&mundo);
                self.chequear(paquetes.len() == self.paquetes_antes + 1, "REQ-PRO-04 a las 11:00 llegó el paquete");
                // Lo llevo a un lugar libre del estante.
                let lugar =
                    todos::<LugarDeposito>(&mundo).into_iter().find(|l| !l.bind().ocupado()).expect("lugar libre");
                let mut p = paquetes.into_iter().last().unwrap();
                p.set_global_position(lugar.bind().centro_zona());
                p.set_global_rotation(Vector3::ZERO);
                p.set_linear_velocity(Vector3::ZERO);
                self.lugar = Some(lugar);
                self.esperar(60);
            }
            15 => {
                let lugar = self.lugar.clone().unwrap();
                let restantes = lugar.bind().bloque().map(|b| b.bind().restantes());
                self.chequear(
                    restantes == Some(12) && todos::<Paquete>(&mundo).len() == self.paquetes_antes,
                    &format!("CA-PRO-01 / REQ-PRO-06 el paquete quedó guardado con sus 12 panes ({restantes:?})"),
                );
                // REQ-ADE-05: recargar un pomo con un repuesto.
                let mut pomo = todos::<Pomo>(&mundo).into_iter().find(|p| p.bind().aderezo() == "mostaza").unwrap();
                pomo.bind_mut().set_usos(5);
                let repuesto = self.agregar_comida("repuesto_mostaza", Vector3::new(4.0, 0.3, plaza::Z_VEREDA));
                let repone = repuesto.bind().repone().map(str::to_string).unwrap_or_default();
                let ok = pomo.bind_mut().recargar(&repone).is_ok();
                self.chequear(ok && pomo.bind().usos() == 40, "REQ-ADE-05 el repuesto llena el pomo");
                // CA-AMB-02: me acerco a una paloma.
                let palomas = todos::<Palomas>(&mundo).pop().unwrap();
                let en_suelo = palomas.bind().posiciones_en_suelo();
                if let (Some(p), Some(mut j)) = (en_suelo.first(), todos::<Jugador>(&mundo).pop()) {
                    j.set_global_position(*p + Vector3::new(1.5, 0.05, 0.0));
                }
                self.esperar(20);
            }
            16 => {
                let palomas = todos::<Palomas>(&mundo).pop().unwrap();
                self.chequear(palomas.bind().volando() >= 1, "CA-AMB-02 la paloma salió volando");

                // CA-SON-03: el audio (aunque sea el driver Dummy) existe y no rompe nada.
                let sonidos = todos::<Sonido>(&mundo);
                self.chequear(sonidos.len() == 1, "REQ-SON-01 hay un nodo central de sonido");
                let mut son = sonidos.into_iter().next().unwrap();
                self.chequear(son.bind().buses_creados(), "REQ-SON-01 existen los buses Ambiente, Efectos y Música");
                self.chequear(
                    carrito_core::sonido::ids::TODOS.iter().all(|id| son.bind().tiene_sonido(id)),
                    "REQ-SON-02 sonidos.ron define todos los sonidos del juego",
                );
                self.chequear(
                    son.bind().disparos() >= 1,
                    &format!("REQ-SON-08 el juego disparó sonidos solo ({})", son.bind().disparos()),
                );
                let antes = son.bind().disparos();
                crate::sonido::sonar(&son, carrito_core::sonido::ids::TIENDA_ABRIR);
                self.chequear(son.bind().disparos() == antes + 1, "CA-SON-03 se dispara un sonido sin fallar");
                // REQ-SON-09: sin archivos de audio, igual funciona (los que faltan se omiten).
                // REQ-SON-09: los archivos que faltan se omiten sin error (solo se informa cuántos).
                godot_print!("  [info] archivos de audio que faltan: {}", son.bind().faltantes());
                // REQ-SON-01: M silencia y reactiva.
                let master = || godot::classes::AudioServer::singleton().get_bus_volume_db(0);
                son.bind_mut().alternar_silencio();
                let mudo = son.bind().silenciado() && master() <= -79.0;
                son.bind_mut().alternar_silencio();
                self.chequear(
                    mudo && !son.bind().silenciado() && master() > -1.0,
                    "CA-SON-03 silenciar y reactivar el sonido",
                );
                self.chequear(
                    son.bind().volumen_bus(carrito_core::sonido::Bus::Musica) == 0.5,
                    "REQ-SON-01 la música arranca a 0,5",
                );
                // Frena el audio y deja pasar unos cuadros antes de cerrar.
                son.bind_mut().detener_todo();
                self.esperar(30);
            }
            17 => {
                self.terminar();
            }
            _ => {}
        }
        self.paso += 1;
    }
}
