//! Carga del contenido del juego desde archivos `.ron` (en `godot/data/`).
//!
//! Este módulo no lee archivos: recibe el texto. Así funciona igual desde Godot
//! (que lee de `res://`, también dentro de un juego exportado) y desde los tests.

use serde::Deserialize;

use crate::aderezos::DefAderezo;
use crate::armado::Combinacion;
use crate::carrito::{Accesorio, BaseCarrito, ConfigCarrito};
use crate::coccion::PerfilCoccion;
use crate::deposito::DefBloque;
use crate::forma::Pieza;
use crate::logo::{DisenoLogo, LugarLogo};

/// Forma de colisión de un producto.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub enum Colision {
    Caja {
        medidas: [f32; 3],
    },
    /// Cápsula acostada a lo largo del eje X.
    Capsula {
        radio: f32,
        largo: f32,
    },
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefProducto {
    pub id: String,
    pub nombre: String,
    /// kg
    pub masa: f32,
    pub colision: Colision,
    pub forma: Vec<Pieza>,
    #[serde(default)]
    pub coccion: Option<PerfilCoccion>,
    /// REQ-PLA-04: se cocina por lados (hamburguesa): cada lado tiene su propio estado.
    #[serde(default)]
    pub por_lados: bool,
    /// REQ-ECO-03: precio de venta (solo productos que se venden).
    #[serde(default)]
    pub precio: Option<f32>,
    /// REQ-ADE-07: aderezos que admite (vacío = ninguno).
    #[serde(default)]
    pub aderezos: Vec<String>,
    /// REQ-CLI-04: función del carrito que hace falta para ofrecerlo (`Hervidor`, `Plancha`,
    /// `Parrilla`...). Sin valor, siempre se puede.
    #[serde(default)]
    pub requiere: Option<String>,
    /// REQ-ADE-05: si es un repuesto, qué aderezo repone.
    #[serde(default)]
    pub repone: Option<String>,
    /// REQ-MOD-01: modelo 3D que reemplaza a `forma`.
    #[serde(default)]
    pub modelo: Option<String>,
    /// REQ-MOD-12: altura (desde el centro) donde se dibujan los aderezos.
    #[serde(default)]
    pub altura_aderezos: Option<f32>,
    /// REQ-HEL-03: carne que se echa a perder si no se mantiene fría.
    #[serde(default)]
    pub perecedero: bool,
    /// REQ-PAR-06: pan que se tuesta por cada cara (pan del choripán).
    #[serde(default)]
    pub pan: bool,
    /// REQ-PAR-01: si es una bolsa de carbón, cuántos kg trae.
    #[serde(default)]
    pub carbon: Option<f32>,
    /// REQ-FRE-03: se prepara a mano (pelar, cortar): herramienta, pasadas y resultado.
    #[serde(default)]
    pub preparar: Option<crate::preparar::Preparacion>,
}

impl DefProducto {
    /// REQ-ADE-03
    pub fn admite_aderezos(&self) -> bool {
        !self.aderezos.is_empty()
    }
    /// REQ-ADE-07
    pub fn admite_aderezo(&self, id: &str) -> bool {
        self.aderezos.iter().any(|a| a == id)
    }
    /// REQ-COC-10: se cocina entero (no por lados) en el agua, como la salchicha.
    pub fn va_al_hervidor(&self) -> bool {
        self.coccion.is_some() && !self.por_lados
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ArchivoProductos {
    pub productos: Vec<DefProducto>,
    pub combinaciones: Vec<Combinacion>,
}

/// Todo el contenido junto.
#[derive(Debug, Clone, PartialEq)]
pub struct Catalogo {
    pub productos: Vec<DefProducto>,
    pub combinaciones: Vec<Combinacion>,
    pub bloques: Vec<DefBloque>,
    pub accesorios: Vec<Accesorio>,
    pub bases: Vec<BaseCarrito>,
    pub carrito_jugador: ConfigCarrito,
    pub aderezos: Vec<DefAderezo>,
    /// REQ-LOG-01
    pub logos: Vec<DisenoLogo>,
}

impl Catalogo {
    /// REQ-LOG-01
    pub fn diseno(&self, id: &str) -> Option<&DisenoLogo> {
        self.logos.iter().find(|d| d.id == id)
    }
    pub fn aderezo(&self, id: &str) -> Option<&DefAderezo> {
        self.aderezos.iter().find(|a| a.id == id)
    }
    /// Productos que se venden (tienen precio). REQ-CLI-04
    pub fn menu(&self) -> Vec<String> {
        self.productos.iter().filter(|p| p.precio.is_some()).map(|p| p.id.clone()).collect()
    }
    /// REQ-CLI-04: productos con precio que se pueden cocinar con las `funciones` del carrito
    /// (nombres de `Funcion::nombre`), con los aderezos que admiten.
    pub fn menu_para(&self, funciones: &[&str]) -> Vec<crate::clientes::ItemMenu> {
        self.productos
            .iter()
            .filter(|p| p.precio.is_some())
            .filter(|p| p.requiere.as_deref().is_none_or(|r| funciones.contains(&r)))
            .map(|p| crate::clientes::ItemMenu { producto: p.id.clone(), aderezos: p.aderezos.clone() })
            .collect()
    }
    pub fn producto(&self, id: &str) -> Option<&DefProducto> {
        self.productos.iter().find(|p| p.id == id)
    }
    pub fn bloque(&self, id: &str) -> Option<&DefBloque> {
        self.bloques.iter().find(|b| b.id == id)
    }
    pub fn ids_bloques(&self) -> Vec<String> {
        self.bloques.iter().map(|b| b.id.clone()).collect()
    }
}

/// Error de carga con el nombre del archivo.
#[derive(Debug, Clone, PartialEq)]
pub struct ErrorDatos {
    pub archivo: String,
    pub mensaje: String,
}

impl std::fmt::Display for ErrorDatos {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.archivo, self.mensaje)
    }
}

pub fn parsear<T: for<'de> Deserialize<'de>>(archivo: &str, texto: &str) -> Result<T, ErrorDatos> {
    ron::from_str(texto).map_err(|e| ErrorDatos { archivo: archivo.to_string(), mensaje: e.to_string() })
}

/// Arma el catálogo a partir de los textos de cada archivo.
/// `bases` es una lista (nombre de archivo, texto), uno por carrito (REQ-CAR-01).
pub fn cargar_catalogo(
    productos: &str,
    bloques: &str,
    accesorios: &str,
    bases: &[(String, String)],
    carrito_jugador: &str,
    aderezos: &str,
    logos: &str,
) -> Result<Catalogo, ErrorDatos> {
    let p: ArchivoProductos = parsear("productos.ron", productos)?;
    let aderezos: Vec<DefAderezo> = parsear("aderezos.ron", aderezos)?;
    let error = |archivo: &str, mensaje: String| ErrorDatos { archivo: archivo.into(), mensaje };
    for prod in &p.productos {
        for a in &prod.aderezos {
            if !aderezos.iter().any(|x| &x.id == a) {
                return Err(error("productos.ron", format!("\"{}\" admite un aderezo inexistente \"{a}\"", prod.id)));
            }
        }
        if let Some(r) = &prod.requiere
            && !crate::carrito::Funcion::NOMBRES.contains(&r.as_str())
        {
            return Err(error("productos.ron", format!("\"{}\" requiere una función desconocida \"{r}\"", prod.id)));
        }
        if let Some(a) = &prod.repone
            && !aderezos.iter().any(|x| &x.id == a)
        {
            return Err(error("productos.ron", format!("\"{}\" repone un aderezo inexistente \"{a}\"", prod.id)));
        }
    }
    // REQ-FRE-03: herramienta y resultado de cada preparación existen.
    crate::preparar::validar(&p.productos).map_err(|m| error("productos.ron", m))?;
    let bloques: Vec<DefBloque> = parsear("bloques.ron", bloques)?;
    for b in &bloques {
        if !p.productos.iter().any(|x| x.id == b.producto) {
            return Err(ErrorDatos {
                archivo: "bloques.ron".into(),
                mensaje: format!("el bloque \"{}\" usa el producto inexistente \"{}\"", b.id, b.producto),
            });
        }
    }
    let mut lista_bases = Vec::new();
    for (nombre, texto) in bases {
        lista_bases.push(parsear::<BaseCarrito>(nombre, texto)?);
    }
    lista_bases.sort_by(|a, b| a.ancho.total_cmp(&b.ancho));
    let accesorios: Vec<Accesorio> = parsear("accesorios.ron", accesorios)?;
    for acc in &accesorios {
        if let Some(crate::carrito::Funcion::Aderezos { tipos, .. }) = &acc.funcion {
            for t in tipos {
                if !aderezos.iter().any(|x| &x.id == t) {
                    return Err(error("accesorios.ron", format!("\"{}\" usa el aderezo inexistente \"{t}\"", acc.id)));
                }
            }
        }
        // REQ-TIE-11: las bases donde entra tienen que existir.
        for b in acc.bases.iter().flatten() {
            if !lista_bases.iter().any(|x| &x.id == b) {
                return Err(error("accesorios.ron", format!("\"{}\" entra en la base inexistente \"{b}\"", acc.id)));
            }
        }
        // REQ-PAP-06: lo que trae un Surtido tiene que existir.
        if let Some(f) = &acc.funcion {
            for o in f.objetos_iniciales() {
                if !p.productos.iter().any(|x| x.id == o.producto) {
                    return Err(error(
                        "accesorios.ron",
                        format!("\"{}\" trae el producto inexistente \"{}\"", acc.id, o.producto),
                    ));
                }
            }
        }
    }
    // REQ-LOG-01, REQ-LOG-05: diseños sin repetir y lugares con nombre y tamaño.
    let logos: Vec<DisenoLogo> = parsear("logos.ron", logos)?;
    for (i, d) in logos.iter().enumerate() {
        if logos[i + 1..].iter().any(|o| o.id == d.id) {
            return Err(error("logos.ron", format!("el diseño \"{}\" está repetido", d.id)));
        }
    }
    let lugar_malo = |l: &LugarLogo| l.lugar.trim().is_empty() || l.tam[0] <= 0.0 || l.tam[1] <= 0.0;
    for b in &lista_bases {
        if let Some(l) = b.logos.iter().find(|l| lugar_malo(l)) {
            return Err(error(&format!("{}.ron", b.id), format!("lugar de logo sin nombre o sin tamaño: {l:?}")));
        }
    }
    for a in &accesorios {
        if let Some(l) = a.logos.iter().find(|l| lugar_malo(l)) {
            return Err(error("accesorios.ron", format!("\"{}\": lugar de logo sin nombre o sin tamaño: {l:?}", a.id)));
        }
    }
    // REQ-LOG-10: el logo de arranque, con un diseño que exista y un texto válido.
    let carrito_jugador: ConfigCarrito = parsear("carrito_jugador.ron", carrito_jugador)?;
    if let Some(l) = &carrito_jugador.logo {
        if !logos.iter().any(|d| d.id == l.diseno) {
            return Err(error("carrito_jugador.ron", format!("no existe el diseño de logo \"{}\"", l.diseno)));
        }
        if let Err(e) = crate::logo::validar_texto(&l.texto) {
            return Err(error("carrito_jugador.ron", format!("logo: {e}")));
        }
    }
    Ok(Catalogo {
        productos: p.productos,
        combinaciones: p.combinaciones,
        bloques,
        accesorios,
        bases: lista_bases,
        carrito_jugador,
        aderezos,
        logos,
    })
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use std::path::PathBuf;

    fn dir_datos() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data")
    }

    fn leer(nombre: &str) -> String {
        std::fs::read_to_string(dir_datos().join(nombre)).unwrap_or_else(|e| panic!("{nombre}: {e}"))
    }

    /// Carga los archivos reales del juego.
    pub(crate) fn catalogo_real() -> Catalogo {
        catalogo_con_jugador(&leer("carrito_jugador.ron")).unwrap_or_else(|e| panic!("{e}"))
    }

    /// Los archivos reales, con otro `carrito_jugador.ron`.
    pub(crate) fn catalogo_con_jugador(jugador: &str) -> Result<Catalogo, ErrorDatos> {
        let mut bases = Vec::new();
        for e in std::fs::read_dir(dir_datos().join("carritos")).unwrap() {
            let p = e.unwrap().path();
            if p.extension().is_some_and(|x| x == "ron") {
                let nombre = p.file_name().unwrap().to_string_lossy().to_string();
                bases.push((nombre, std::fs::read_to_string(&p).unwrap()));
            }
        }
        cargar_catalogo(
            &leer("productos.ron"),
            &leer("bloques.ron"),
            &leer("accesorios.ron"),
            &bases,
            jugador,
            &leer("aderezos.ron"),
            &leer("logos.ron"),
        )
    }

    #[test]
    fn los_datos_del_juego_cargan() {
        let c = catalogo_real();
        assert!(c.producto("salchicha").is_some());
        assert!(c.producto("pan_pancho").is_some());
        assert!(c.producto("pancho").is_some());
    }

    #[test]
    fn req_coc_05_perfil_de_salchicha_en_datos_coincide_con_el_testeado() {
        let c = catalogo_real();
        let perfil = c.producto("salchicha").unwrap().coccion.clone().unwrap();
        assert_eq!(perfil, crate::coccion::perfil_salchicha());
    }

    #[test]
    fn req_pla_04_06_hamburguesa_se_cocina_por_lados_con_el_perfil_testeado() {
        let c = catalogo_real();
        let h = c.producto("hamburguesa").unwrap();
        assert!(h.por_lados);
        assert_eq!(h.coccion.clone().unwrap(), crate::lados::perfil_hamburguesa());
        // REQ-PLA-05: una mitad por lado, para teñirlas por separado.
        let lados: Vec<_> = h.forma.iter().filter_map(|p| p.tinte_lado).collect();
        assert_eq!(lados, vec![0, 1]);
    }

    #[test]
    fn req_par_05_chorizo_se_cocina_por_lados_con_el_perfil_testeado() {
        let c = catalogo_real();
        let h = c.producto("chorizo").unwrap();
        assert!(h.por_lados);
        assert_eq!(h.coccion.clone().unwrap(), crate::lados::perfil_chorizo());
        let lados: Vec<_> = h.forma.iter().filter_map(|p| p.tinte_lado).collect();
        assert_eq!(lados, vec![0, 1]);
    }

    #[test]
    fn req_hel_01_03_heladera_y_productos_perecederos_en_datos() {
        let c = catalogo_real();
        let a = c
            .accesorios
            .iter()
            .find(|a| matches!(a.funcion, Some(crate::carrito::Funcion::Heladera { .. })))
            .expect("hay una heladera");
        assert_eq!(a.categoria, crate::carrito::Categoria::Cocina);
        assert!(c.carrito_jugador.accesorios.values().any(|v| v == &a.id));
        let perecederos: Vec<_> = c.productos.iter().filter(|p| p.perecedero).map(|p| p.id.as_str()).collect();
        assert_eq!(perecederos, vec!["hamburguesa", "chorizo"]);
        assert!(!c.producto("salchicha").unwrap().perecedero, "la salchicha viene envasada");
    }

    #[test]
    fn req_par_06_07_pan_de_choripan_y_choripan_en_datos() {
        let c = catalogo_real();
        let pan = c.producto("pan_choripan").unwrap();
        assert!(pan.pan && pan.por_lados);
        assert_eq!(pan.coccion.clone().unwrap(), crate::tostado::perfil_pan());
        assert_eq!(crate::armado::combinar(&c.combinaciones, "pan_choripan", "chorizo"), Some("choripan"));
        let m = pan.masa + c.producto("chorizo").unwrap().masa;
        assert!((c.producto("choripan").unwrap().masa - m).abs() < 1e-6, "REQ-ARM-05");
        assert!(c.bloques.iter().any(|b| b.producto == "pan_choripan"));
    }

    #[test]
    fn req_coc_10_solo_lo_que_se_cocina_entero_va_al_hervidor() {
        let c = catalogo_real();
        let va = |id: &str| c.producto(id).unwrap().va_al_hervidor();
        assert!(va("salchicha"));
        for id in ["hamburguesa", "chorizo", "pan_choripan", "pan_pancho", "pancho", "papa_cruda"] {
            assert!(!va(id), "{id} no va al hervidor");
        }
    }

    #[test]
    fn req_hel_08_las_comidas_listas_no_son_perecederas() {
        let c = catalogo_real();
        for r in &c.combinaciones {
            assert!(!c.producto(&r.resultado).unwrap().perecedero, "{} no se echa a perder", r.resultado);
        }
    }

    #[test]
    fn req_par_01_parrilla_y_bolsas_de_carbon_en_datos() {
        let c = catalogo_real();
        let a =
            c.accesorios.iter().find(|a| matches!(a.funcion, Some(crate::carrito::Funcion::Parrilla { .. }))).unwrap();
        assert_eq!(a.categoria, crate::carrito::Categoria::Cocina);
        assert!(c.carrito_jugador.accesorios.values().any(|v| v == &a.id));
        assert_eq!(c.producto("bolsa_carbon").unwrap().carbon, Some(1.0));
        assert!(c.bloques.iter().any(|b| b.producto == "bolsa_carbon"));
        assert!(c.bloques.iter().any(|b| b.producto == "chorizo"));
    }

    #[test]
    fn req_pla_01_plancha_en_el_carrito_del_jugador() {
        let c = catalogo_real();
        let a =
            c.accesorios.iter().find(|a| matches!(a.funcion, Some(crate::carrito::Funcion::Plancha { .. }))).unwrap();
        assert_eq!(a.categoria, crate::carrito::Categoria::Cocina);
        assert!(c.carrito_jugador.accesorios.values().any(|v| v == &a.id));
    }

    #[test]
    fn req_arm_01_regla_del_pancho_en_datos() {
        let c = catalogo_real();
        assert_eq!(crate::armado::combinar(&c.combinaciones, "pan_pancho", "salchicha"), Some("pancho"));
        let pancho = c.producto("pancho").unwrap();
        assert!(pancho.forma.iter().any(|p| p.tinte_coccion), "REQ-ARM-03: el pancho muestra el color de la salchicha");
        let masa = c.producto("pan_pancho").unwrap().masa + c.producto("salchicha").unwrap().masa;
        assert!((pancho.masa - masa).abs() < 1e-6, "REQ-ARM-05");
    }

    #[test]
    fn req_fre_11_papas_en_cajita_en_datos() {
        let c = catalogo_real();
        assert_eq!(crate::armado::combinar(&c.combinaciones, "cajita_papas", "papas_fritas"), Some("papas_en_cajita"));
        let p = c.producto("papas_en_cajita").unwrap();
        assert_eq!(p.precio, Some(8.0));
        assert_eq!(p.aderezos, vec!["ketchup".to_string(), "mayonesa".to_string()]);
        assert_eq!(p.requiere.as_deref(), Some("Freidora"));
        assert!(p.coccion.is_none(), "no se cocina: conserva la cocción de las papas (REQ-ARM-03)");
        assert!(p.forma.iter().any(|x| x.tinte_coccion), "los bastones muestran el color de las papas");
        let masa = c.producto("cajita_papas").unwrap().masa + c.producto("papas_fritas").unwrap().masa;
        assert!((p.masa - masa).abs() < 1e-6, "REQ-ARM-05");
        // Ninguno de los ingredientes se vende suelto.
        assert!(c.producto("cajita_papas").unwrap().precio.is_none());
        assert!(c.producto("papas_fritas").unwrap().precio.is_none());
    }

    #[test]
    fn req_dep_01_bloques_de_panes_y_salchichas() {
        let c = catalogo_real();
        assert!(c.bloques.iter().any(|b| b.producto == "pan_pancho"));
        assert!(c.bloques.iter().any(|b| b.producto == "salchicha"));
        assert_eq!(c.bloque("bolsa_panes_12").unwrap().capacidad(), 12);
    }

    #[test]
    fn req_eco_03_precio_del_pancho() {
        let c = catalogo_real();
        assert_eq!(c.producto("pancho").unwrap().precio, Some(10.0));
        let mut menu = c.menu();
        menu.sort();
        assert_eq!(menu, ["choripan", "hamburguesa", "pancho", "papas_en_cajita"].map(String::from).to_vec());
        assert_eq!(c.producto("hamburguesa").unwrap().precio, Some(14.0));
        assert_eq!(c.producto("choripan").unwrap().precio, Some(12.0));
    }

    #[test]
    fn req_eco_07_precios_en_escala_de_pancho_a_10() {
        // Todo precio es un entero de pesos (al menos $1): la escala es la del pancho a $10.
        let c = catalogo_real();
        let entero = |p: f32| p >= 1.0 && p.fract() == 0.0;
        assert!(c.productos.iter().filter_map(|p| p.precio).all(entero));
        assert!(c.bloques.iter().all(|b| entero(b.precio)), "bloques");
        assert!(c.accesorios.iter().all(|a| entero(a.precio)), "accesorios");
        assert!(c.bases.iter().all(|b| entero(b.precio)), "bases");
        // Nada cuesta más que 1000 panchos ni el stock más que 3 panchos.
        assert!(c.bases.iter().all(|b| b.precio <= 10_000.0));
        assert!(c.bloques.iter().all(|b| b.precio <= 30.0));
    }

    #[test]
    fn req_ade_01_tres_aderezos_de_40_usos() {
        let c = catalogo_real();
        for id in ["mostaza", "ketchup", "mayonesa"] {
            assert_eq!(c.aderezo(id).map(|a| a.usos), Some(40), "{id}");
        }
        assert!(c.producto("pancho").unwrap().admite_aderezos());
        assert!(!c.producto("salchicha").unwrap().admite_aderezos());
    }

    #[test]
    fn req_ade_05_repuestos_se_compran_como_bloques() {
        let c = catalogo_real();
        for id in ["mostaza", "ketchup", "mayonesa"] {
            let repuesto = c.productos.iter().find(|p| p.repone.as_deref() == Some(id)).expect("repuesto");
            assert!(c.bloques.iter().any(|b| b.producto == repuesto.id), "bloque de {}", repuesto.id);
        }
    }

    #[test]
    fn req_ade_02_aderecera_en_el_carrito() {
        let c = catalogo_real();
        // La aderecera que lleva el jugador tiene un pomo de cada aderezo.
        let a = c
            .accesorios
            .iter()
            .filter(|a| matches!(a.funcion, Some(crate::carrito::Funcion::Aderezos { .. })))
            .find(|a| c.carrito_jugador.accesorios.values().any(|v| v == &a.id))
            .expect("el carrito del jugador lleva una aderecera");
        assert_eq!(a.categoria, crate::carrito::Categoria::Equipamiento);
        if let Some(crate::carrito::Funcion::Aderezos { tipos, .. }) = &a.funcion {
            for ad in &c.aderezos {
                assert!(tipos.contains(&ad.id), "falta el pomo de {}", ad.id);
            }
        }
    }

    #[test]
    fn req_ade_01_07_papas_pay_y_chimichurri_con_sus_productos() {
        let c = catalogo_real();
        for id in ["papas_pay", "chimichurri"] {
            assert_eq!(c.aderezo(id).map(|a| a.usos), Some(40), "{id}");
        }
        assert!(c.producto("pancho").unwrap().admite_aderezo("papas_pay"));
        assert!(!c.producto("pancho").unwrap().admite_aderezo("chimichurri"));
        let choripan = c.producto("choripan").unwrap();
        assert!(choripan.admite_aderezo("chimichurri") && choripan.admite_aderezo("mostaza"));
        assert!(!choripan.admite_aderezo("ketchup"));
        assert!(!c.producto("hamburguesa").unwrap().admite_aderezos());
    }

    #[test]
    fn req_cli_04_menu_segun_las_funciones_del_carrito() {
        let c = catalogo_real();
        let ids = |f: &[&str]| {
            let mut v: Vec<String> = c.menu_para(f).into_iter().map(|i| i.producto).collect();
            v.sort();
            v
        };
        assert_eq!(ids(&["Hervidor", "Plancha", "Parrilla"]), vec!["choripan", "hamburguesa", "pancho"]);
        assert_eq!(ids(&["Hervidor"]), vec!["pancho"], "sin plancha ni parrilla solo hay pancho");
        // SPEC-029: las papas en cajita, solo con freidora.
        assert_eq!(ids(&["Freidora"]), vec!["papas_en_cajita"]);
        assert_eq!(
            ids(&["Hervidor", "Plancha", "Parrilla", "Freidora"]),
            vec!["choripan", "hamburguesa", "pancho", "papas_en_cajita"]
        );
        assert!(ids(&[]).is_empty());
    }

    #[test]
    fn req_cli_04_el_carrito_del_jugador_ofrece_todo_el_menu() {
        let c = catalogo_real();
        let colocados: Vec<&str> = c
            .carrito_jugador
            .accesorios
            .values()
            .filter_map(|id| c.accesorios.iter().find(|a| &a.id == id))
            .filter_map(|a| a.funcion.as_ref())
            .map(|f| f.nombre())
            .collect();
        // Pancho, hamburguesa y choripán; sin freidora no hay papas (SPEC-029).
        assert_eq!(c.menu_para(&colocados).len(), 3);
    }

    #[test]
    fn producto_inexistente_en_bloque_da_error_claro() {
        let prod = leer("productos.ron");
        let bloques = r#"[(id: "x", nombre: "x", producto: "fantasma", grilla: (1,1,1),
            separacion: (0.1,0.1,0.1), empaque: Bolsa, color_empaque: (1,1,1), precio: 1)]"#;
        let e = cargar_catalogo(&prod, bloques, "[]", &[], "", &leer("aderezos.ron"), "[]").unwrap_err();
        assert!(e.mensaje.contains("fantasma"));
    }
}
