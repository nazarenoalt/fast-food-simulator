//! Prueba de humo (SPEC-000): abre el mundo real sin pantalla y verifica los criterios de
//! aceptación de integración. Se corre con `tools/prueba_humo.sh`.

use carrito_core::coccion::Punto;
use carrito_core::plaza;
use godot::classes::{INode, Node, Node3D, PackedScene};
use godot::prelude::*;

use crate::bloque_stock::BloqueStock;
use crate::comida::Comida;
use crate::dia_noche::DiaNoche;
use crate::hervidor::Hervidor;
use crate::jugador::Jugador;
use crate::luz::{GRUPO_LUCES_NOCHE, LuzNocturna};

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
                let carrito = todos::<Node3D>(&mundo).into_iter().find(|n| n.get_name().to_string() == "Carrito").unwrap();
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
                let salchichas = todos::<Comida>(&mundo).into_iter().filter(|c| c.bind().producto() == "salchicha").count();
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
                self.terminar();
            }
            _ => {}
        }
        self.paso += 1;
    }
}
