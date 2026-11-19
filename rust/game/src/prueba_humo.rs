//! Prueba de humo (SPEC-000): abre el mundo real sin pantalla y verifica los criterios de
//! aceptación de integración. Se corre con `tools/prueba_humo.sh`.

use carrito_core::coccion::Punto;
use carrito_core::plaza;
use godot::classes::{INode, Input, MeshInstance3D, Node, Node3D, PackedScene, StandardMaterial3D};
use godot::prelude::*;

use crate::aderecera::Pomo;
use crate::armado::ModoArmado;
use crate::bloque_stock::BloqueStock;
use crate::carrito::Carrito;
use crate::comida::Comida;
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::jugador::Jugador;
use crate::lugar_deposito::LugarDeposito;
use crate::luz::{GRUPO_LUCES_NOCHE, LuzNocturna};
use crate::negocio::Negocio;
use crate::palomas::Palomas;
use crate::paquete::Paquete;
use crate::parrilla::Parrilla;
use crate::peaton::Peaton;
use crate::plancha::Plancha;
use crate::sonido::Sonido;
use crate::transito::{Autos, Nubes};
use carrito_core::tostado::EstadoPan;

#[path = "prueba_humo_pelar.rs"]
mod pelar; // SPEC-029: pelar y cortar
// TASK-0358: vender papas en cajita y cartel de cerrado.
#[path = "prueba_humo_vender.rs"]
mod vender;
#[path = "prueba_humo_gente.rs"]
mod gente_humo; // TASK-0506: la gente se renueva (REQ-AMB-15/16)
#[path = "prueba_humo_freir.rs"]
mod freir; // SPEC-029: freír con el colador

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
    hamburguesa: Option<Gd<Comida>>,
    chorizo: Option<Gd<Comida>>,
    mundo: Option<Gd<Node>>,
    autos_antes: Vec<f32>,
    nube_antes: Option<Vector3>,
    panchos_antes: Vec<InstanceId>,
    pedido: Option<carrito_core::clientes::Pedido>,
    saldo_antes: f32,
    /// Disparos de sonido al empezar cada tramo, para medir los de la etapa 3. REQ-SON-08
    disparos_ref: u32,
    reputacion_antes: f32,
    perdidos_antes: u32,
    paquetes_antes: usize,
    lugar: Option<Gd<LugarDeposito>>,
    superpuestos: usize,
    muestras: usize,
    reintentos: u32,
    /// SPEC-026 / REQ-CAR-13: segundo carrito (carro grande) con lo de las papas.
    carro_papas: Option<Gd<Carrito>>,
    fase_papas: u32,
    /// Qué chequeo corre al final del paso 31 (papas y puerta, pelar, freír, vender, gente).
    cadena_papas: u32,
    /// SPEC-027: fase de la prueba de ampliaciones y lo que se mide entre cuadros.
    fase_amp: u32,
    bloque_cajon: Option<(Gd<BloqueStock>, Vector3)>,
    /// SPEC-028: fase de la prueba del logo.
    fase_logo: u32,
    /// SPEC-002 (etapa 2.5): fase de la prueba de agarre y lo que se mide entre cuadros.
    fase_agarre: u32,
    salchichas_hervidor: usize,
    carnes: Option<(Gd<Comida>, Gd<Comida>)>,
    jugador_antes: Option<Transform3D>,
    /// SPEC-029 / REQ-CLI-12: la prueba de vender papas y del cartel de cerrado.
    vender: vender::Vender,
    /// SPEC-029: fase de la prueba de freír, la papa y los cuadros que lleva en el aceite.
    fase_freir: u32,
    papa_freir: Option<Gd<Comida>>,
    cuadros_freir: u32,
}

/// Material (de la primera superficie) de la pieza `nombre` de un modelo. SPEC-025
fn material_pieza(raiz: &Gd<Node>, nombre: &str) -> Option<Gd<StandardMaterial3D>> {
    let n = raiz.find_child_ex(nombre).recursive(true).owned(false).done()?;
    let mi = n.try_cast::<MeshInstance3D>().ok()?;
    mi.get_active_material(0)?.try_cast::<StandardMaterial3D>().ok()
}

/// Material de la primera parte que brilla de noche (lamparita, tubo de luz…). REQ-MOD-07
fn material_luz(raiz: &Gd<Node>) -> Option<Gd<StandardMaterial3D>> {
    let carrito = todos::<Carrito>(raiz).pop()?.upcast::<Node>();
    let mut pila = vec![carrito];
    while let Some(n) = pila.pop() {
        let nombre = n.get_name().to_string();
        if carrito_core::modelos::PIEZAS_LUZ.iter().any(|p| nombre.starts_with(p))
            && let Some(m) = n.clone().try_cast::<MeshInstance3D>().ok().and_then(|mi| mi.get_active_material(0))
            && let Ok(m) = m.try_cast::<StandardMaterial3D>()
        {
            return Some(m);
        }
        pila.extend(n.get_children().iter_shared());
    }
    None
}

fn parecido(c: Color, esperado: [f32; 3]) -> bool {
    (c.r - esperado[0]).abs() < 0.02 && (c.g - esperado[1]).abs() < 0.02 && (c.b - esperado[2]).abs() < 0.02
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

    /// SPEC-017: modo armado sobre el carrito del jugador (CA-TIE-01..04, REQ-TIE-05/08/10).
    fn chequear_armado(&mut self) {
        use carrito_core::tienda::{Origen, PALETA};
        let mundo = self.mundo();
        let Some(mut m) = todos::<ModoArmado>(&mundo).pop() else {
            self.chequear(false, "REQ-TIE-01 hay modo armado");
            return;
        };
        let carrito = todos::<Carrito>(&mundo).into_iter().next().expect("carrito");
        let mut neg = todos::<Negocio>(&mundo).into_iter().next().expect("negocio");
        let puestos = || carrito.bind().accesorios_puestos();
        let saldo = |n: &Gd<Negocio>| n.bind().saldo();
        neg.bind_mut().set_saldo(1_000_000.0);

        // REQ-AMP-11: con la sombrilla puesta, el techo choca y no se pone.
        m.bind_mut().elegir("techo", "techo_plano_mediano", Origen::Tienda);
        self.chequear(
            !puestos().contains_key("techo") && (saldo(&neg) - 1_000_000.0).abs() < 0.5,
            "REQ-AMP-11 con la sombrilla, el techo choca y no se cobra",
        );
        m.bind_mut().guardar("sombra");
        m.bind_mut().elegir("techo", "techo_plano_mediano", Origen::Tienda);
        self.chequear(
            puestos().get("techo").map(String::as_str) == Some("techo_plano_mediano")
                && (saldo(&neg) - (1_000_000.0 - 180.0)).abs() < 0.5,
            "CA-TIE-01 compro un techo plano y la caja baja su precio",
        );

        let mut plancha = todos::<Plancha>(&mundo).into_iter().next().expect("plancha");
        plancha.bind_mut().set_temperatura(200.0);
        let id = plancha.instance_id();
        m.bind_mut().mover("mostrador_centro", "mostrador_izq");
        let p = puestos();
        self.chequear(
            p.get("mostrador_izq").map(String::as_str) == Some("plancha_chica")
                && p.get("mostrador_centro").map(String::as_str) == Some("hervidor_chico")
                && plancha.is_instance_valid()
                && plancha.instance_id() == id
                && plancha.bind().temperatura() >= 190.0,
            "CA-TIE-02 muevo la plancha (se intercambia con el hervidor) y sigue caliente",
        );

        let antes = saldo(&neg);
        m.bind_mut().vender_accesorio("sombrilla_roja");
        self.chequear(
            !puestos().contains_key("sombra") && (saldo(&neg) - antes - 36.0).abs() < 0.5,
            "CA-TIE-03 guardo la sombrilla y la vendo a la mitad",
        );

        let con_bloques = carrito.bind().deposito_con_bloques("lateral");
        m.bind_mut().guardar("lateral");
        self.chequear(
            puestos().contains_key("lateral") == con_bloques,
            "REQ-TIE-05 un depósito con mercadería no se guarda",
        );

        m.bind_mut().guardar("mostrador_izq");
        self.chequear(
            !carrito.bind().menu().iter().any(|i| i.producto == "hamburguesa"),
            "CA-TIE-04 sin plancha no se piden hamburguesas",
        );

        m.bind_mut().pintar(PALETA[3].1);
        self.chequear(carrito.bind().color() == PALETA[3].1, "REQ-TIE-08 pinto el carrito de verde");

        if con_bloques {
            m.bind_mut().guardar("lateral"); // no se puede: el estante se queda
        }
        m.bind_mut().cambiar_base("carro_grande");
        let base = carrito.bind().base_actual().map(|b| b.id.clone());
        self.chequear(
            base.as_deref() == Some("carro_grande")
                && puestos().get("mostrador_centro").map(String::as_str) == Some("hervidor_chico")
                && !puestos().contains_key("techo"),
            "REQ-TIE-10 paso al carro grande: el hervidor pasa y el techo mediano se guarda",
        );
        m.bind_mut().cambiar_base("barra_mediana");
        self.chequear(
            carrito.bind().base_actual().map(|b| b.id.as_str()) == Some("barra_mediana")
                && (saldo(&neg) - (antes + 36.0 - 3800.0)).abs() < 0.5,
            "REQ-TIE-10 vuelvo a la barra mediana guardada, gratis",
        );
        m.bind_mut().cerrar_panel();
    }

    /// SPEC-027 sobre el carrito del jugador (barra mediana, después de chequear_armado): guirnalda
    /// con techo, alacena de cajones con un bloque, choque toldo/carpa, y el food truck con el
    /// jugador que entra por la puerta subiendo el escalón. Se llama en varios cuadros; devuelve
    /// true al terminar.
    fn chequear_ampliaciones(&mut self) -> bool {
        use carrito_core::tienda::Origen;
        let mundo = self.mundo();
        let Some(mut m) = todos::<ModoArmado>(&mundo).pop() else { return true };
        let carrito = todos::<Carrito>(&mundo).into_iter().next().expect("carrito");
        let puestos = || carrito.bind().accesorios_puestos();
        let mut jugador = todos::<Jugador>(&mundo).pop().expect("jugador");
        let local = |c: &Gd<Carrito>, p: Vector3| c.get_global_transform().affine_inverse() * p;
        match self.fase_amp {
            0 => {
                let marcas = |m: &Gd<ModoArmado>| m.bind().marcas_visibles();
                let sin = !marcas(&m).iter().any(|a| a == "guirnalda");
                m.bind_mut().elegir("techo", "techo_plano_mediano", Origen::Guardado);
                let con = marcas(&m).iter().any(|a| a == "guirnalda");
                self.chequear(sin && con, "CA-AMP-03 sin techo no aparece la guirnalda; con techo sí");
                m.bind_mut().elegir("guirnalda", "guirnalda_luces_mediano", Origen::Tienda);
                m.bind_mut().elegir("bahia_1", "alacena_cajones", Origen::Tienda);
                let c = carrito.bind();
                self.chequear(
                    puestos().get("guirnalda").map(String::as_str) == Some("guirnalda_luces_mediano")
                        && c.tapa_visible(1) == Some(false)
                        && c.tapa_visible(2) == Some(true),
                    "REQ-AMP-04 pongo la guirnalda y una cajonera: se esconde la tapa de su bahía",
                );
                let nodo = c.nodo_puesto("bahia_1").expect("alacena");
                drop(c);
                let lugares = crate::carrito::lugares_de(&nodo);
                let mut cajon = todos::<crate::puerta::PuertaCarrito>(&nodo.clone().upcast())
                    .into_iter()
                    .filter(|p| p.bind().es_cajon())
                    .min_by(|a, b| b.get_global_position().y.total_cmp(&a.get_global_position().y))
                    .expect("cajón de arriba");
                self.chequear(lugares.len() == 6, "REQ-AMP-05 la cajonera tiene 6 lugares");
                // El bloque va en el lugar 1, que es del cajón de arriba.
                let def = crate::datos::catalogo().bloque("bolsa_panes_12").unwrap().clone();
                let bloque = BloqueStock::crear(def);
                let mut l1 = lugares[0].clone();
                l1.add_child(&bloque);
                self.chequear(!cajon.bind().abierta(), "REQ-AMP-06 los cajones arrancan cerrados");
                cajon.bind_mut().alternar();
                let antes = bloque.get_global_position();
                self.bloque_cajon = Some((bloque, antes));
                self.esperar(40);
            }
            1 => {
                let (b, antes) = self.bloque_cajon.take().expect("bloque");
                let d = b.get_global_position().distance_to(antes);
                self.chequear(
                    (d - carrito_core::ampliaciones::SALIDA_CAJON).abs() < 0.02,
                    &format!("CA-AMP-02 abro el cajón y la bolsa sale con él ({d:.2} m)"),
                );
                m.bind_mut().guardar("techo");
                let inv = m.bind().inventario();
                self.chequear(
                    !puestos().contains_key("guirnalda") && inv.contains(&"guirnalda_luces_mediano".to_string()),
                    "CA-AMP-03 saco el techo y la guirnalda va al inventario",
                );
                m.bind_mut().elegir("toldo", "toldo_rayado_mediano", Origen::Tienda);
                m.bind_mut().elegir("techo", "carpa_2x2", Origen::Tienda);
                self.chequear(
                    puestos().contains_key("toldo") && !puestos().contains_key("techo"),
                    "CA-AMP-04 con el toldo rayado, la carpa avisa que choca",
                );
                // Food truck: el toldo y la cajonera (con su bolsa) pasan; el jugador va afuera.
                // El estante del costado no tiene lugar ahí: se vacía (REQ-TIE-10) y se guarda.
                if let Some(n) = carrito.bind().nodo_puesto("lateral") {
                    for l in crate::carrito::lugares_de(&n) {
                        if let Some(mut b) = l.bind().bloque() {
                            b.queue_free();
                        }
                    }
                }
                self.esperar(2);
                self.fase_amp = 10;
                return false;
            }
            10 => {
                m.bind_mut().guardar("lateral");
                m.bind_mut().cambiar_base("food_truck");
                m.bind_mut().cerrar_panel();
                let b = carrito.bind().base_actual().cloned().expect("base");
                let pj = local(&carrito, jugador.get_global_position());
                let puerta = carrito.bind().puerta();
                self.chequear(
                    b.id == "food_truck"
                        && puestos().contains_key("toldo")
                        && puestos().contains_key("bahia_1")
                        && pj.z > b.profundidad / 2.0
                        && puerta.as_ref().is_some_and(|p| !p.bind().abierta()),
                    &format!(
                        "REQ-AMP-01/02 cambio al food truck: arranco afuera, adelante, con la puerta cerrada \
                         ({} toldo {} bahia {} z {:.2} puerta {:?})",
                        b.id,
                        puestos().contains_key("toldo"),
                        puestos().contains_key("bahia_1"),
                        pj.z,
                        puerta.as_ref().map(|p| p.bind().abierta())
                    ),
                );
                if let Some(mut p) = puerta {
                    p.bind_mut().alternar();
                }
                // Al pie del escalón, mirando a la puerta (+Z del carrito), y camina.
                let t = carrito.get_global_transform();
                // Por el medio de lo que deja libre la hoja abierta (la bisagra está en x 0,10).
                let desde = t * Vector3::new(0.52, 0.05, -2.0);
                let hacia = t * Vector3::new(0.52, 0.05, 0.0);
                jugador.set_global_position(desde);
                jugador.look_at(Vector3::new(hacia.x, desde.y, hacia.z));
                self.esperar(40);
                self.fase_amp = 2;
                return false;
            }
            2 => {
                Input::singleton().action_press("adelante");
                self.esperar(70);
            }
            3 => {
                Input::singleton().action_release("adelante");
                let pj = local(&carrito, jugador.get_global_position());
                self.chequear(
                    pj.y > 0.45 && pj.z > -1.05,
                    &format!(
                        "CA-AMP-01 / REQ-JUG-09 subo el escalón y entro por la puerta (y {:.2}, z {:.2})",
                        pj.y, pj.z
                    ),
                );
                self.fase_amp = 99; // listo: no se repite
                return true;
            }
            _ => return true,
        }
        self.fase_amp += 1;
        false
    }

    /// SPEC-028 sobre el carrito del jugador (el food truck, después de chequear_ampliaciones):
    /// pongo, rechazo, apago y saco el logo, con lugares de la base y de accesorios. Se llama en
    /// varios cuadros; devuelve true al terminar.
    fn chequear_logo(&mut self) -> bool {
        use carrito_core::tienda::Origen;
        use godot::classes::base_material_3d::{Feature, TextureParam};
        let mundo = self.mundo();
        let Some(mut m) = todos::<ModoArmado>(&mundo).pop() else { return true };
        let carrito = todos::<Carrito>(&mundo).into_iter().next().expect("carrito");
        let calcos = |c: &Gd<Carrito>| c.bind().calcomanias();
        let cuantas = |c: &Gd<Carrito>, lugar: &str| calcos(c).iter().filter(|(l, _)| l == lugar).count();
        let material = |c: &Gd<Carrito>, lugar: &str| {
            calcos(c)
                .into_iter()
                .find(|(l, _)| l == lugar)
                .and_then(|(_, mi)| mi.get_material_override())
                .and_then(|m| m.try_cast::<StandardMaterial3D>().ok())
        };
        match self.fase_logo {
            0 => {
                let lugares = m.bind_mut().lugares_logo();
                self.chequear(
                    lugares == ["Costados", "Atrás"],
                    &format!("REQ-LOG-06 el food truck tiene Costados y Atrás ({lugares:?})"),
                );
                self.chequear(calcos(&carrito).is_empty(), "REQ-LOG-09 sin logo no hay calcomanías");
                let r = m.bind_mut().poner_logo("estrella", "Panchos El Tano");
                self.chequear(
                    r.is_ok() && cuantas(&carrito, "Costados") == 2 && cuantas(&carrito, "Atrás") == 1,
                    "CA-LOG-01 pongo la estrella con \"Panchos El Tano\": 2 calcomanías a los costados y 1 atrás",
                );
                let largo = m.bind_mut().poner_logo("estrella", "abcdefghijklmnopqrs");
                let arroba = m.bind_mut().poner_logo("estrella", "Panchos @ Tano");
                let texto = carrito.bind().logo().map(|l| l.texto);
                self.chequear(
                    largo.is_err() && arroba.is_err() && texto.as_deref() == Some("Panchos El Tano"),
                    "CA-LOG-02 19 letras o un @ se rechazan y queda el texto anterior",
                );
                m.bind_mut().alternar_lugar_logo("Costados");
                self.chequear(
                    cuantas(&carrito, "Costados") == 0 && cuantas(&carrito, "Atrás") == 1,
                    "CA-LOG-03 apago los costados: queda el de atrás",
                );
                m.bind_mut().elegir("cartel_techo", "cartel_luminoso", Origen::Tienda);
                let brilla = |m: Option<Gd<StandardMaterial3D>>| m.is_some_and(|m| m.get_feature(Feature::EMISSION));
                self.chequear(
                    cuantas(&carrito, "Cartel luminoso") == 1
                        && brilla(material(&carrito, "Cartel luminoso"))
                        && !brilla(material(&carrito, "Atrás")),
                    "REQ-LOG-06 / CA-LOG-04 el cartel luminoso lleva el logo y brilla de noche; el de atrás no",
                );
                self.esperar(5);
            }
            1 => {
                // REQ-LOG-02: la imagen se dibujó (fondo azul y letras crema). Sin pantalla
                // (--headless) Godot no dibuja: ahí no se mira.
                let con_pantalla = godot::classes::DisplayServer::singleton().get_name() != "headless";
                let img = material(&carrito, "Atrás")
                    .filter(|_| con_pantalla)
                    .and_then(|m| m.get_texture(TextureParam::ALBEDO))
                    .and_then(|t| t.get_image());
                match img.filter(|i| !i.is_empty()) {
                    Some(img) => {
                        let d = crate::datos::catalogo().diseno("estrella").expect("estrella").clone();
                        let (mut fondo, mut letras) = (0, 0);
                        for y in (0..img.get_height()).step_by(2) {
                            for x in (0..img.get_width()).step_by(2) {
                                let c = img.get_pixel(x, y);
                                fondo += parecido(c, d.fondo) as u32;
                                letras += parecido(c, d.texto) as u32;
                            }
                        }
                        self.chequear(
                            fondo > 200 && letras > 20,
                            &format!(
                                "REQ-LOG-02 la calcomanía dibuja el logo ({fondo} px de fondo, {letras} de letras)"
                            ),
                        );
                    }
                    None => godot_print!("  (sin pantalla: no se mira la imagen del logo)"),
                }
                m.bind_mut().guardar("cartel_techo");
                let lugares = m.bind_mut().lugares_logo();
                self.chequear(
                    !lugares.iter().any(|l| l == "Cartel luminoso") && cuantas(&carrito, "Cartel luminoso") == 0,
                    "CA-LOG-03 saco el cartel luminoso: su lugar desaparece",
                );
                m.bind_mut().alternar_lugar_logo("Costados");
                m.bind_mut().cambiar_base("carro_kiosco");
                self.chequear(
                    cuantas(&carrito, "Óvalos") == 5,
                    "REQ-LOG-08 cambio al kiosco: el logo va a sus 5 óvalos",
                );
                m.bind_mut().sacar_logo();
                self.chequear(calcos(&carrito).is_empty(), "REQ-LOG-09 saco el logo: no queda ninguna calcomanía");
                m.bind_mut().cambiar_base("food_truck");
                m.bind_mut().cerrar_panel();
                self.fase_logo = 99; // listo: no se repite
                return true;
            }
            _ => return true,
        }
        self.fase_logo += 1;
        false
    }

    /// SPEC-026 y REQ-CAR-13: arma un segundo carrito (carro grande, plateado) con la freidora
    /// doble, la tabla, el cartel adelante y las bolsas de papas, y abre y cierra su puerta. Se llama en
    /// varios cuadros; devuelve true al terminar.
    fn chequear_papas_y_puerta(&mut self) -> bool {
        let mundo = self.mundo();
        match self.fase_papas {
            0 => {
                let mut cfg = crate::datos::catalogo().carrito_jugador.clone();
                cfg.base = "carro_grande".into();
                cfg.color = Some([0.76, 0.78, 0.8]); // REQ-CAR-09: plateado
                cfg.accesorios = [
                    ("mostrador_izq", "freidora_doble"),
                    ("mostrador_centro", "tabla_papas"),
                    ("cartel", "cartel_cerrado"),
                    ("lateral", "estante_deposito"),
                ]
                .iter()
                .map(|(a, b)| (a.to_string(), b.to_string()))
                .collect();
                cfg.stock = [(
                    "lateral".to_string(),
                    vec![
                        Some("bolsa_papas_5kg".to_string()),
                        Some("bolsa_papas_2kg".to_string()),
                        Some("pack_cajitas".to_string()),
                        None,
                    ],
                )]
                .into_iter()
                .collect();
                let mut c = Carrito::new_alloc();
                c.bind_mut().forzar_config(cfg);
                c.set_position(Vector3::new(0.0, 0.0, -30.0));
                mundo.clone().add_child(&c);
                self.carro_papas = Some(c);
                self.esperar(120);
            }
            1 => {
                let c = self.carro_papas.clone().unwrap();
                let errores = self.base().get_tree().get_nodes_in_group("errores_carrito").len();
                self.chequear(errores == 0, "CA-PAP-01 el carro grande con lo de las papas se arma sin errores");
                let nodo = c.clone().upcast::<Node3D>();
                let modelos = ["pieza_aceite_1", "tabla_papas_cuerpo", "cartel_cerrado_cuerpo"]
                    .iter()
                    .all(|n| crate::modelos::buscar(&nodo, n).is_some());
                self.chequear(modelos, "REQ-PAP-05/07 freidora doble, tabla y cartel con su modelo");
                let suelta = |p: &str| {
                    todos::<Comida>(&mundo).into_iter().filter(|x| x.bind().producto() == p).collect::<Vec<_>>()
                };
                let base = c.get_global_position();
                let coladores = suelta("colador_freidora");
                let adentro = coladores.iter().all(|x| {
                    let p = x.get_global_position() - base;
                    (p.x + 1.1).abs() < 0.3 && p.y > 1.2 && p.y < 1.3 && (p.z - 0.045).abs() < 0.1
                });
                self.chequear(
                    coladores.len() == 2 && adentro,
                    &format!(
                        "CA-PAP-01 los dos coladores quedan dentro de la freidora ({:?})",
                        coladores.iter().map(|x| x.get_global_position() - base).collect::<Vec<_>>()
                    ),
                );
                let cuchillo = suelta("cuchillo").pop();
                let sobre_tabla = cuchillo.as_ref().is_some_and(|x| x.get_global_position().y - base.y > 1.02);
                let mut agarrado = false;
                if let (Some(k), Some(mut j)) = (cuchillo, todos::<Jugador>(&mundo).pop()) {
                    j.bind_mut().agarrar(k.clone().upcast());
                    agarrado = k.bind().sostenida;
                    j.bind_mut().soltar();
                }
                self.chequear(
                    sobre_tabla && agarrado && suelta("pelapapas").len() == 1,
                    "REQ-PAP-06 la tabla trae cuchillo y pelapapas, y el cuchillo se agarra",
                );
                let mut bolsas: Vec<u32> = todos::<BloqueStock>(&mundo)
                    .into_iter()
                    .filter(|b| b.bind().producto() == "papa_cruda")
                    .map(|b| b.bind().restantes())
                    .collect();
                bolsas.sort();
                self.chequear(
                    bolsas == [12, 24],
                    &format!("REQ-PAP-03 las bolsas de 2 kg (12) y 5 kg (24) entran en el estante ({bolsas:?})"),
                );
                // REQ-PAP-07: el cartel cuelga adelante (lo ven los clientes), del canto de la mesada.
                let cartel = nodo.find_child_ex("cartel_cartel_cerrado").recursive(true).owned(false).done();
                let adelante = cartel.and_then(|n| n.try_cast::<Node3D>().ok()).map(|n| n.get_global_position() - base);
                self.chequear(
                    adelante.is_some_and(|p| p.z > 0.6 && p.x.abs() < 0.01 && (p.y - 0.988).abs() < 0.01),
                    &format!("REQ-PAP-07 el cartel de cerrado cuelga adelante ({adelante:?})"),
                );
                let puerta = c.bind().puerta();
                let cerrada = puerta.as_ref().is_some_and(|p| !p.bind().abierta() && p.bind().angulo() == 0.0);
                self.chequear(cerrada, "REQ-CAR-11 la puerta del carro grande arranca cerrada");
                if let Some(mut p) = puerta {
                    p.bind_mut().alternar();
                }
                self.esperar(45);
            }
            2 => {
                let mut p = self.carro_papas.clone().unwrap().bind().puerta().unwrap();
                let a = p.bind().angulo();
                let pieza = crate::modelos::buscar(&p.clone().upcast::<Node3D>(), "pieza_puerta")
                    .map(|n| n.get_rotation_degrees().y)
                    .unwrap_or(0.0);
                self.chequear(
                    p.bind().abierta() && (a - 105.0).abs() < 0.5 && (pieza - 105.0).abs() < 0.5,
                    &format!("CA-CAR-04 con E la puerta se abre ({a:.0}°, pieza {pieza:.0}°)"),
                );
                p.bind_mut().alternar();
                self.esperar(45);
            }
            _ => {
                let p = self.carro_papas.clone().unwrap().bind().puerta().unwrap();
                let a = p.bind().angulo();
                self.chequear(!p.bind().abierta() && a == 0.0, &format!("CA-CAR-04 otra vez E: se cierra ({a:.0}°)"));
                return true;
            }
        }
        self.fase_papas += 1;
        false
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
                // CA-CAR-03: si la base dice dónde aparece el jugador (carro kiosco), arranca ahí
                // adentro, y la puerta del modelo está abierta.
                if let Some(c) = todos::<Carrito>(&mundo).pop()
                    && let Some(p) = c.bind().posicion_jugador()
                {
                    let j = jugadores.first().map(|j| j.get_global_position()).unwrap_or(Vector3::ZERO);
                    let d = Vector2::new(j.x - p.x, j.z - p.z).length();
                    let puerta = c
                        .clone()
                        .upcast::<Node>()
                        .find_child_ex("pieza_puerta")
                        .recursive(true)
                        .owned(false)
                        .done()
                        .and_then(|n| n.try_cast::<Node3D>().ok())
                        .map(|n| n.get_rotation_degrees().y);
                    self.chequear(
                            d < 0.3 && j.y > 0.1 && puerta.is_some_and(|g| g > 45.0),
                            &format!("CA-CAR-03 el jugador arranca adentro (a {d:.2} m, y {:.2}) y la puerta está abierta ({puerta:?}°)", j.y),
                        );
                }
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
                let carrito = todos::<Node3D>(&mundo).into_iter().find(|n| n.get_name() == "Carrito").unwrap();
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
                // CA-MOD-02: el pancho es el modelo, con la salchicha del color de su cocción.
                let cocida = crate::datos::catalogo()
                    .producto("salchicha")
                    .and_then(|p| p.coccion.clone())
                    .zip(panchos.first().and_then(|p| p.bind().estado_coccion()));
                let color_ok = match (panchos.first(), cocida) {
                    (Some(p), Some((perfil, e))) => material_pieza(&p.clone().upcast(), "pieza_salchicha")
                        .is_some_and(|m| parecido(m.get_albedo(), e.color(&perfil))),
                    _ => false,
                };
                self.chequear(color_ok, "CA-MOD-02 el pancho modelado muestra la salchicha del color de su cocción");

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
                // CA-MOD-03: la lamparita del foco (modelo) brilla de noche.
                let brillo = material_luz(&mundo).map(|m| m.get_emission_energy_multiplier());
                self.chequear(
                    brillo.is_some_and(|b| b > 0.0),
                    &format!("CA-MOD-03 de noche las luces del carrito brillan ({brillo:?})"),
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
                let brillo = material_luz(&mundo).map(|m| m.get_emission_energy_multiplier());
                self.chequear(
                    brillo == Some(0.0),
                    &format!("CA-MOD-03 de día las luces del carrito están apagadas ({brillo:?})"),
                );
                // CA-MOD-01: el carrito es el modelo, pintado del color de la config.
                let color = crate::datos::catalogo().carrito_jugador.color.unwrap_or([0.0; 3]);
                let carrito: Option<Gd<Node>> = todos::<Carrito>(&mundo).pop().map(|c| c.upcast());
                let pintado = carrito
                    .as_ref()
                    .and_then(|c| material_pieza(c, "pieza_pintura"))
                    .is_some_and(|m| parecido(m.get_albedo(), color));
                self.chequear(pintado, "CA-MOD-01 el carrito es el modelo, pintado del color de carrito_jugador.ron");
                // REQ-MOD-11: la plaza usa los modelos (bancos y las tres variantes de plátano).
                let nombres: std::collections::BTreeSet<String> = todos::<Node3D>(&mundo)
                    .iter()
                    .map(|n| n.get_name().to_string())
                    .filter(|n| {
                        n.starts_with("banco")
                            || n.starts_with("arbol_platano")
                            || n.starts_with("farol")
                            || n.starts_with("fuente")
                    })
                    .collect();
                let variantes = ["arbol_platano_a", "arbol_platano_b", "arbol_platano_c"]
                    .iter()
                    .filter(|v| nombres.iter().any(|n| n.starts_with(**v)))
                    .count();
                self.chequear(
                    nombres.iter().any(|n| n.starts_with("banco")) && variantes == 3,
                    &format!("REQ-MOD-11 la plaza usa los modelos ({variantes} variantes de plátano)"),
                );
                self.chequear(
                    todos::<Node3D>(&mundo).iter().all(|n| !n.is_in_group("errores_carrito")),
                    "REQ-CAR-08 sin errores en la config del carrito",
                );

                // ── Etapa 2: ambientación ──
                let ciudad = todos::<Node3D>(&mundo).into_iter().find(|n| n.get_name() == "Ciudad").unwrap();
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
                    saldo >= self.saldo_antes + 10.0 && ventas == 1,
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
                // El primero de la fila puede venir caminando todavía (su paciencia corre recién
                // cuando llega): se le da hasta 20 s de juego antes de dar la falla.
                if perdidos == self.perdidos_antes && self.reintentos < 20 {
                    self.reintentos += 1;
                    let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                    gente.bind_mut().set_paciencia_del_primero(0.3);
                    self.esperar(60);
                    self.paso -= 1; // se repite este paso
                } else {
                    self.chequear(
                        perdidos == self.perdidos_antes + 1 && rep < self.reputacion_antes,
                        &format!(
                            "CA-CLI-02 se fue enojado y bajó la reputación ({:.2} → {rep:.2})",
                            self.reputacion_antes
                        ),
                    );
                    // CA-ECO-02: sin plata no se compra.
                    negocio.bind_mut().set_saldo(4.0);
                    let r = negocio.bind_mut().comprar("bolsa_panes_12");
                    self.chequear(
                        r.is_err() && negocio.bind().saldo() == 4.0,
                        "CA-ECO-02 no se puede comprar sin plata",
                    );
                    negocio.bind_mut().set_saldo(120.0);
                    // CA-PRO-01: compro a las 10:00, llega a las 11:00.
                    let mut dn = todos::<DiaNoche>(&mundo).pop().unwrap();
                    dn.bind_mut().set_minuto(10.0 * 60.0);
                    let r = negocio.bind_mut().comprar("bolsa_panes_12");
                    self.chequear(
                        r.is_ok() && negocio.bind().saldo() == 120.0 - 7.0,
                        &format!("REQ-PRO-02 compra hecha: {r:?}"),
                    );
                    self.paquetes_antes = todos::<Paquete>(&mundo).len();
                    dn.bind_mut().set_minuto(10.0 * 60.0 + 59.0);
                    self.esperar(5);
                }
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
                self.esperar(1);
            }
            17 => {
                // CA-PLA-01: plancha encendida, apoyo una hamburguesa.
                self.chequear(todos::<Plancha>(&mundo).len() == 1, "REQ-PLA-01 el carrito tiene su plancha");
                let mut pl = todos::<Plancha>(&mundo).pop().unwrap();
                // Me paro al lado: el sonido 3D no suena lejos. REQ-SON-04
                self.pararse_al_lado(&mundo, pl.get_global_position());
                self.disparos_ref = disparos_de_sonido(&mundo);
                pl.bind_mut().alternar();
                pl.bind_mut().set_temperatura(200.0);
                let encima = pl.get_global_position() + Vector3::new(0.0, 0.06, 0.0);
                self.hamburguesa = Some(self.agregar_comida("hamburguesa", encima));
                // 75 s de juego.
                self.esperar(75 * 60);
            }
            18 => {
                // REQ-SON-08: sonó el interruptor y empezó el chisporroteo con la carne encima.
                let d = disparos_de_sonido(&mundo) - self.disparos_ref;
                self.chequear(d >= 2, &format!("REQ-SON-08 la plancha dispara interruptor y chisporroteo ({d})"));
                let h = self.hamburguesa.clone().unwrap();
                let l = h.bind().estado_lados().expect("la hamburguesa se cocina por lados");
                self.chequear(
                    l.lados[0].avance > 6.0 && l.lados[1].avance == 0.0,
                    &format!(
                        "CA-PLA-01 se cocina el lado de abajo ({:.1}) y el de arriba sigue crudo ({:.1})",
                        l.lados[0].avance, l.lados[1].avance
                    ),
                );
                self.chequear(h.bind().punto() == Some(Punto::Crudo), "REQ-PLA-05 con un lado crudo está cruda");
                // CA-PLA-02: la doy vuelta (E) y espero.
                h.clone().bind_mut().dar_vuelta();
                self.esperar(75 * 60);
            }
            19 => {
                let h = self.hamburguesa.clone().unwrap();
                let l = h.bind().estado_lados().unwrap();
                self.chequear(
                    l.lados[1].avance > 6.0 && l.lados[0].avance < 14.0,
                    &format!(
                        "REQ-PLA-07 dada vuelta se cocinó el otro lado ({:.1}) y el primero no se pasó ({:.1})",
                        l.lados[1].avance, l.lados[0].avance
                    ),
                );
                self.chequear(h.bind().punto() == Some(Punto::Cocido), "CA-PLA-02 queda cocida de los dos lados");
                // CA-PAR-01: sin carbón no se enciende; cargo una bolsa, enciendo y apoyo un chorizo.
                let mut pa = todos::<Parrilla>(&mundo).pop().expect("REQ-PAR-01 el carrito tiene su parrilla");
                self.pararse_al_lado(&mundo, pa.get_global_position());
                self.disparos_ref = disparos_de_sonido(&mundo);
                self.chequear(!pa.bind_mut().alternar(), "REQ-PAR-01 sin carbón no se enciende");
                self.chequear(pa.bind_mut().cargar(1.0).is_ok(), "REQ-PAR-01 entra una bolsa de carbón");
                self.chequear(pa.bind_mut().cargar(3.0).is_err(), "REQ-PAR-01 no entra más de 3 kg");
                self.chequear(pa.bind_mut().alternar(), "REQ-PAR-01 con carbón se enciende");
                let encima = pa.get_global_position() + Vector3::new(0.0, 0.12, 0.0);
                self.chorizo = Some(self.agregar_comida("chorizo", encima));
                self.esperar(90 * 60);
            }
            20 => {
                // REQ-SON-08: sonó el carbón al cargar y empezaron las brasas al prender.
                let d = disparos_de_sonido(&mundo) - self.disparos_ref;
                self.chequear(d >= 2, &format!("REQ-SON-08 la parrilla dispara carbón y brasas ({d})"));
                let pa = todos::<Parrilla>(&mundo).pop().unwrap();
                let e = pa.bind().estado();
                self.chequear(e.temp > 100.0, &format!("CA-PAR-01 las brasas se calentaron ({:.0} °C)", e.temp));
                self.chequear(
                    e.carbon < 0.5 && e.carbon > 0.0,
                    &format!("REQ-PAR-02 el carbón baja ({:.2} kg)", e.carbon),
                );
                let c = self.chorizo.clone().unwrap();
                let l = c.bind().estado_lados().expect("el chorizo se cocina por lados");
                self.chequear(
                    l.lados[0].avance > 3.0 && l.lados[1].avance == 0.0,
                    &format!("REQ-PAR-04 se cocina el lado de abajo del chorizo ({:.1})", l.lados[0].avance),
                );
                self.esperar(40 * 60);
            }
            21 => {
                // CA-PAR-02: sigue prendida un rato largo: se queda sin carbón y se apaga.
                let pa = todos::<Parrilla>(&mundo).pop().unwrap();
                let e = pa.bind().estado();
                self.chequear(e.carbon == 0.0 && !e.encendida, "CA-PAR-02 sin carbón la parrilla se apaga sola");
                // CA-PAR-03: pan tostado (avance de las dos caras forzado) en la vereda.
                let base = Vector3::new(-5.0, 0.3, plaza::Z_VEREDA);
                let mut pan = self.agregar_comida("pan_choripan", base);
                pan.bind_mut().forzar_avance(5.0);
                self.chequear(
                    pan.bind().estado_pan() == Some(EstadoPan::Tostado),
                    "REQ-PAR-06 el pan con avance 5 está tostado",
                );
                self.pan = Some(pan);
                self.esperar(60);
            }
            22 => {
                let pan = self.pan.clone().unwrap();
                let mut c = self.chorizo.clone().unwrap();
                c.bind_mut().forzar_avance(12.0);
                c.set_global_position(pan.get_global_position() + Vector3::new(0.0, 0.09, 0.0));
                c.set_global_rotation(Vector3::ZERO);
                c.set_linear_velocity(Vector3::ZERO);
                self.esperar(90);
            }
            23 => {
                let choripanes: Vec<_> =
                    todos::<Comida>(&mundo).into_iter().filter(|c| c.bind().producto() == "choripan").collect();
                self.chequear(choripanes.len() == 1, &format!("REQ-PAR-07 se armó un choripán ({})", choripanes.len()));
                if let Some(ch) = choripanes.first() {
                    let ped = carrito_core::clientes::Pedido { producto: "choripan".into(), aderezos: vec![] };
                    let r = carrito_core::clientes::evaluar(&ped, &ch.bind().entregado(), 12.0, 0.0);
                    self.chequear(
                        r.is_ok(),
                        &format!("CA-PAR-03 el cliente acepta el choripán ({:?})", ch.bind().detalle()),
                    );
                }
                // CA-HEL-01 / CA-HEL-02: una hamburguesa fría en la heladera cerrada y otra afuera.
                let he = todos::<Heladera>(&mundo).pop().expect("REQ-HEL-01 el carrito tiene su heladera");
                self.chequear(!he.bind().abierta() && he.bind().temperatura() < 5.0, "REQ-HEL-01 cerrada y a 4 °C");
                let dentro = he.get_global_transform() * Vector3::new(0.0, 0.12, 0.0);
                let mut a = self.agregar_comida("hamburguesa", dentro);
                a.bind_mut().fijar_temperatura(4.0); // sale de un paquete frío (REQ-HEL-06)
                self.hamburguesa = Some(a);
                self.pan = Some(self.agregar_comida("hamburguesa", Vector3::new(-6.0, 0.3, plaza::Z_VEREDA)));
                // 430 s de juego: a 20 °C la carne se echa a perder en unos 417 s.
                self.esperar(430 * 60);
            }
            24 => {
                let a = self.hamburguesa.clone().unwrap();
                let fa = a.bind().frescura().map(|f| f.porcentaje).unwrap_or(0.0);
                self.chequear(fa >= 99.9, &format!("CA-HEL-01 en la heladera sigue fresca ({fa:.1} %)"));
                let b = self.pan.clone().unwrap();
                let f = b.bind().frescura().expect("REQ-HEL-03 la hamburguesa es perecedera");
                self.chequear(
                    f.echada_a_perder(),
                    &format!("CA-HEL-02 afuera se echó a perder ({:.1} %)", f.porcentaje),
                );
                self.chequear(b.bind().descripcion().contains("echada a perder"), "REQ-HEL-04 el cartel avisa");
                let ped = carrito_core::clientes::Pedido { producto: "hamburguesa".into(), aderezos: vec![] };
                let r = carrito_core::clientes::evaluar(&ped, &b.bind().entregado(), 16.0, 0.0);
                self.chequear(
                    r == Err(carrito_core::clientes::Rechazo::EchadaAPerder),
                    "REQ-HEL-04 el cliente rechaza lo echado a perder",
                );
                // REQ-HEL-07: con 30 % de frescura (y cocida) descuenta una estrella.
                let mut c = a.clone();
                c.bind_mut().set_frescura(30.0);
                c.bind_mut().forzar_avance(7.0);
                let r = carrito_core::clientes::evaluar(&ped, &c.bind().entregado(), 16.0, 0.0);
                self.chequear(
                    r.map(|e| e.estrellas) == Ok(4.0),
                    &format!("REQ-HEL-07 con frescura dudosa descuenta una estrella ({r:?})"),
                );
                // CA-HEL-03: dejo la puerta abierta.
                let mut he = todos::<Heladera>(&mundo).pop().unwrap();
                // Me paro al lado de la heladera: el sonido 3D no suena lejos. REQ-SON-04
                self.pararse_al_lado(&mundo, he.get_global_position());
                self.disparos_ref = disparos_de_sonido(&mundo);
                he.bind_mut().alternar();
                self.esperar(120 * 60);
            }
            25 => {
                self.chequear(
                    disparos_de_sonido(&mundo) > self.disparos_ref,
                    "REQ-SON-08 la puerta de la heladera dispara su sonido",
                );
                let he = todos::<Heladera>(&mundo).pop().unwrap();
                let t = he.bind().temperatura();
                self.chequear(
                    he.bind().abierta() && t > 6.0,
                    &format!("CA-HEL-03 con la puerta abierta el interior sube ({t:.1} °C)"),
                );
                self.chequear(he.bind().cartel().contains("Cerrar"), "CA-HEL-03 el cartel lo muestra");
                // REQ-HEL-06: la carne llega a 4 °C; lo demás, al ambiente.
                let cat = crate::datos::catalogo();
                let carne = Paquete::crear(cat.bloque("caja_hamburguesas_12").unwrap().clone());
                let panes = Paquete::crear(cat.bloque("bolsa_panes_12").unwrap().clone());
                self.chequear(
                    carne.bind().temp == 4.0 && panes.bind().temp == 20.0,
                    "REQ-HEL-06 los paquetes de carne vienen a 4 °C",
                );
                // Llega un cliente nuevo para probar el menú (REQ-CLI-04).
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                if gente.bind().largo_fila() == 0 {
                    gente.bind_mut().forzar_cliente();
                }
                self.esperar(20 * 60);
            }
            26 => {
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                let pidio = gente.bind().pedido_del_primero();
                self.chequear(pidio.is_some(), &format!("REQ-CLI-04 el cliente pidió: {pidio:?}"));
                // REQ-ADE-07: al choripán le entra chimichurri, pero no papas pay ni ketchup.
                let mut choripan = todos::<Comida>(&mundo)
                    .into_iter()
                    .find(|c| c.bind().producto() == "choripan")
                    .expect("hay un choripán");
                let pomo = |id: &str| todos::<Pomo>(&mundo).into_iter().find(|p| p.bind().aderezo() == id);
                let mut chimi = pomo("chimichurri").expect("REQ-ADE-01 hay pomo de chimichurri");
                let antes = chimi.bind().usos();
                let ok = chimi.bind_mut().aplicar(&mut choripan).is_ok() && chimi.bind().usos() == antes - 1;
                self.chequear(ok, "REQ-ADE-07 el choripán admite chimichurri");
                let mut papas = pomo("papas_pay").expect("REQ-ADE-01 hay pomo de papas pay");
                let mut ketchup = pomo("ketchup").unwrap();
                self.chequear(
                    papas.bind_mut().aplicar(&mut choripan).is_err()
                        && ketchup.bind_mut().aplicar(&mut choripan).is_err(),
                    "REQ-ADE-07 el choripán no admite papas pay ni ketchup",
                );
                // CA-CLI: pide choripán con chimichurri y se lo entrego.
                let pedido = carrito_core::clientes::Pedido {
                    producto: "choripan".into(),
                    aderezos: vec!["chimichurri".into()],
                };
                gente.bind_mut().set_pedido_del_primero(pedido);
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                self.saldo_antes = negocio.bind().saldo();
                let carrito = todos::<Carrito>(&mundo).pop().unwrap();
                let bandeja = carrito.bind().pos_bandeja();
                choripan.set_global_position(bandeja + Vector3::new(0.0, 0.05, 0.0));
                choripan.set_global_rotation(Vector3::ZERO);
                choripan.set_linear_velocity(Vector3::ZERO);
                self.esperar(120);
            }
            27 => {
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                let saldo = negocio.bind().saldo();
                self.chequear(
                    saldo >= self.saldo_antes + 12.0,
                    &format!("CA-CLI-01 el cliente pagó el choripán (caja {} → {saldo})", self.saldo_antes),
                );
                // CA-PLA-03: el siguiente pide hamburguesa.
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                if gente.bind().largo_fila() == 0 {
                    gente.bind_mut().forzar_cliente();
                }
                self.esperar(20 * 60);
            }
            28 => {
                let mut gente = todos::<Gente>(&mundo).pop().unwrap();
                gente.bind_mut().set_pedido_del_primero(carrito_core::clientes::Pedido {
                    producto: "hamburguesa".into(),
                    aderezos: vec![],
                });
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                self.saldo_antes = negocio.bind().saldo();
                let carrito = todos::<Carrito>(&mundo).pop().unwrap();
                let bandeja = carrito.bind().pos_bandeja();
                let mut h = self.agregar_comida("hamburguesa", bandeja + Vector3::new(0.0, 0.05, 0.0));
                h.bind_mut().fijar_temperatura(4.0);
                h.bind_mut().forzar_quemado();
                self.hamburguesa = Some(h);
                self.esperar(120);
            }
            29 => {
                let gente = todos::<Gente>(&mundo).pop().unwrap();
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                let sigue = gente.bind().pedido_del_primero().is_some_and(|p| p.producto == "hamburguesa");
                self.chequear(
                    negocio.bind().saldo() == self.saldo_antes && sigue,
                    "CA-PLA-03 el cliente rechaza la hamburguesa quemada y sigue esperando",
                );
                // La saco y le doy una bien cocida.
                if let Some(mut h) = self.hamburguesa.take() {
                    h.queue_free();
                }
                let carrito = todos::<Carrito>(&mundo).pop().unwrap();
                let bandeja = carrito.bind().pos_bandeja();
                let mut h = self.agregar_comida("hamburguesa", bandeja + Vector3::new(0.0, 0.05, 0.0));
                h.bind_mut().fijar_temperatura(4.0);
                h.bind_mut().forzar_avance(7.0);
                self.esperar(120);
            }
            30 => {
                let negocio = todos::<Negocio>(&mundo).pop().unwrap();
                let saldo = negocio.bind().saldo();
                self.chequear(
                    saldo >= self.saldo_antes + 14.0,
                    &format!("REQ-CLI-04 la hamburguesa cocida se paga (caja {} → {saldo})", self.saldo_antes),
                );

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
            31 => {
                if self.fase_agarre < 3 {
                    self.chequear_agarre(); // SPEC-002 v2, REQ-DEP-09, REQ-COC-10, REQ-HEL-08
                    self.paso -= 1;
                } else {
                    if self.fase_papas == 0 && self.fase_amp == 0 {
                        self.chequear_armado(); // SPEC-017, una sola vez
                    }
                    if !self.chequear_ampliaciones() {
                        self.paso -= 1; // SPEC-027: se repite este paso hasta terminar
                    } else if !self.chequear_logo() {
                        self.paso -= 1; // SPEC-028: se repite este paso hasta terminar
                    } else {
                        // Etapa 3.5 en orden; cada chequeo corre hasta terminar y pasa al que sigue.
                        let listo = match self.cadena_papas {
                            0 => self.chequear_papas_y_puerta(),
                            1 => self.chequear_pelar(),  // SPEC-029: pelar y cortar
                            2 => self.chequear_freir(),  // SPEC-029: freír con el colador
                            3 => self.chequear_vender(), // TASK-0358: papas en cajita y cartel
                            4 => self.chequear_gente_se_renueva(), // TASK-0506: REQ-AMB-15/16
                            _ => true,
                        };
                        if listo {
                            self.cadena_papas += 1;
                        }
                        if self.cadena_papas >= 5 {
                            self.terminar();
                        } else {
                            self.paso -= 1; // se repite este paso hasta terminar
                        }
                    }
                }
            }
            _ => {}
        }
        self.paso += 1;
    }
}

impl PruebaHumo {
    /// Salchichas sueltas dentro de la cuba del hervidor (y las que hay). REQ-COC-10
    fn salchichas_en_hervidor(mundo: &Gd<Node>) -> Vec<Gd<Comida>> {
        let Some(h) = todos::<Hervidor>(mundo).pop() else { return Vec::new() };
        let t = h.get_global_transform();
        todos::<Comida>(mundo)
            .into_iter()
            .filter(|c| c.bind().producto() == "salchicha" && !c.is_queued_for_deletion())
            .filter(|c| {
                let p = t.affine_inverse() * c.get_global_position();
                p.x.abs() < 0.2 && p.z.abs() < 0.15 && p.y > -0.02 && p.y < 0.2
            })
            .collect()
    }

    /// Agarre de la etapa 2.5: levantar un paquete del estante, volcar salchichas al hervidor,
    /// colocar una salchicha en el pan apuntando, y que lo cocido no se pudra. Una fase por llamada.
    fn chequear_agarre(&mut self) {
        let mundo = self.mundo();
        let Some(mut j) = todos::<Jugador>(&mundo).pop() else {
            self.chequear(false, "REQ-INT-03 hay jugador");
            self.fase_agarre = 3;
            return;
        };
        let lejos = Vector3::new(-5.0, 0.3, plaza::Z_VEREDA);
        match self.fase_agarre {
            0 => {
                self.jugador_antes = Some(j.get_global_transform());
                if let Some(viejo) = j.bind_mut().soltar() {
                    let mut viejo = viejo;
                    viejo.set_global_position(lejos);
                }
                // REQ-DEP-09: levanto un paquete del estante con lo que le queda.
                // (las bolsas de papas no: las cuenta REQ-PAP-03 más adelante)
                let libres: Vec<Gd<BloqueStock>> = todos::<BloqueStock>(&mundo)
                    .into_iter()
                    .filter(|b| !b.is_queued_for_deletion() && b.bind().restantes() > 0)
                    .filter(|b| b.bind().producto() != "papa_cruda")
                    .collect();
                let bloque = libres.iter().find(|b| b.bind().producto() == "pan_pancho").or(libres.first()).cloned();
                if let Some(b) = bloque {
                    let n = b.bind().restantes();
                    j.bind_mut().levantar(b.clone());
                    let paquete = j.bind().en_mano().and_then(|m| m.try_cast::<Paquete>().ok());
                    let ok = b.is_queued_for_deletion()
                        && paquete.as_ref().is_some_and(|p| p.bind().restantes() == n && p.bind().sostenido);
                    self.chequear(ok, &format!("REQ-DEP-09 levanto un paquete del estante con sus {n} unidades"));
                    if let Some(mut p) = j.bind_mut().soltar() {
                        p.set_global_position(lejos + Vector3::new(1.0, 0.0, 0.0));
                    }
                } else {
                    self.chequear(false, "REQ-DEP-09 hay un bloque en el depósito");
                }

                // REQ-COC-10: con una caja de salchichas en la mano, E sobre el hervidor las vuelca.
                self.salchichas_hervidor = Self::salchichas_en_hervidor(&mundo).len();
                let def = crate::datos::catalogo().bloque("caja_salchichas_12").expect("caja de salchichas").clone();
                let mut caja = Paquete::crear(def);
                mundo.clone().add_child(&caja);
                caja.set_global_position(j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
                j.bind_mut().agarrar(caja.clone().upcast());
                if let Some(h) = todos::<Hervidor>(&mundo).pop() {
                    j.bind_mut().volcar(&h);
                }
                self.chequear(
                    caja.is_queued_for_deletion() && j.bind().en_mano().is_none(),
                    "REQ-COC-10 el paquete volcado se va de la mano",
                );

                // REQ-HEL-08: una hamburguesa cocida y enfriada no pierde frescura; una cruda sí.
                let mut cocida = self.agregar_comida("hamburguesa", lejos + Vector3::new(0.0, 0.0, 0.5));
                let mut cruda = self.agregar_comida("hamburguesa", lejos + Vector3::new(0.3, 0.0, 0.5));
                cocida.bind_mut().forzar_avance(8.0);
                for c in [&mut cocida, &mut cruda] {
                    c.bind_mut().set_frescura(80.0);
                    c.bind_mut().fijar_temperatura(20.0);
                }
                self.carnes = Some((cocida, cruda));

                // REQ-INT-10: un pan en el suelo, para ponerle la salchicha apuntando.
                self.pan = Some(self.agregar_comida("pan_pancho", lejos + Vector3::new(-1.0, 0.0, 0.0)));
                self.esperar(90);
            }
            1 => {
                let dentro = Self::salchichas_en_hervidor(&mundo);
                self.chequear(
                    dentro.len() == self.salchichas_hervidor + 12,
                    &format!(
                        "REQ-COC-10 las 12 salchichas quedan dentro del hervidor ({} → {})",
                        self.salchichas_hervidor,
                        dentro.len()
                    ),
                );
                for mut c in dentro {
                    c.queue_free();
                }
                // CA-INT-03: con una salchicha en la mano apunto al pan y hago clic: pancho.
                let pan = self.pan.clone().expect("pan");
                let pos = pan.get_global_position();
                j.set_global_position(Vector3::new(pos.x, pos.y - 0.03, pos.z + 1.2));
                j.set_velocity(Vector3::ZERO);
                let s = self.agregar_comida("salchicha", j.get_global_position() + Vector3::new(0.2, 1.4, -0.4));
                j.bind_mut().agarrar(s.upcast());
                j.bind_mut().apuntar_a(pos);
                j.bind_mut().colocar();
                self.panchos_antes = todos::<Comida>(&mundo)
                    .iter()
                    .filter(|c| c.bind().producto() == "pancho")
                    .map(|c| c.instance_id())
                    .collect();
                self.esperar(30);
            }
            _ => {
                let nuevo = todos::<Comida>(&mundo)
                    .into_iter()
                    .find(|c| c.bind().producto() == "pancho" && !self.panchos_antes.contains(&c.instance_id()));
                // El pan ya se borró al armarse el pancho: se mira sin clonarlo (clonar un objeto
                // borrado hace caer el juego con los controles estrictos de godot-rust).
                let armado = self.pan.as_ref().is_none_or(|p| !p.is_instance_valid() || p.is_queued_for_deletion());
                self.chequear(
                    armado && nuevo.is_some(),
                    "CA-INT-03 apunto la salchicha al pan, hago clic y se arma el pancho",
                );
                if let Some(mut p) = nuevo {
                    p.queue_free();
                }
                if let Some((mut cocida, mut cruda)) = self.carnes.take() {
                    let (fc, fr) = (
                        cocida.bind().frescura().map(|f| f.porcentaje).unwrap_or(0.0),
                        cruda.bind().frescura().map(|f| f.porcentaje).unwrap_or(100.0),
                    );
                    self.chequear(
                        fc == 80.0 && fr < 80.0,
                        &format!("REQ-HEL-08 la hamburguesa cocida no se pudre (cocida {fc:.2} %, cruda {fr:.2} %)"),
                    );
                    cocida.queue_free();
                    cruda.queue_free();
                }
                if let Some(t) = self.jugador_antes.take() {
                    j.set_global_transform(t);
                }
                self.fase_agarre = 3;
                return;
            }
        }
        self.fase_agarre += 1;
    }
}

/// Cuántos sonidos disparó el juego hasta ahora. REQ-SON-08
fn disparos_de_sonido(mundo: &Gd<Node>) -> u32 {
    todos::<Sonido>(mundo).first().map(|s| s.bind().disparos()).unwrap_or(0)
}

impl PruebaHumo {
    /// Lleva al jugador (y su cámara, el oído) a 1 m de `pos`. REQ-SON-04
    fn pararse_al_lado(&self, mundo: &Gd<Node>, pos: Vector3) {
        if let Some(mut j) = todos::<Jugador>(mundo).pop() {
            j.set_global_position(pos + Vector3::new(0.0, 0.05, 1.0));
        }
    }
}
