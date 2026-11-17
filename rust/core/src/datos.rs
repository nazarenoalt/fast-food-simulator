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
    /// REQ-ADE-03
    #[serde(default)]
    pub admite_aderezos: bool,
    /// REQ-ADE-05: si es un repuesto, qué aderezo repone.
    #[serde(default)]
    pub repone: Option<String>,
    /// REQ-PAR-06: pan que se tuesta por cada cara (pan del choripán).
    #[serde(default)]
    pub pan: bool,
    /// REQ-PAR-01: si es una bolsa de carbón, cuántos kg trae.
    #[serde(default)]
    pub carbon: Option<f32>,
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
}

impl Catalogo {
    pub fn aderezo(&self, id: &str) -> Option<&DefAderezo> {
        self.aderezos.iter().find(|a| a.id == id)
    }
    /// Productos que se venden (tienen precio). REQ-CLI-04
    pub fn menu(&self) -> Vec<String> {
        self.productos.iter().filter(|p| p.precio.is_some()).map(|p| p.id.clone()).collect()
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
) -> Result<Catalogo, ErrorDatos> {
    let p: ArchivoProductos = parsear("productos.ron", productos)?;
    let aderezos: Vec<DefAderezo> = parsear("aderezos.ron", aderezos)?;
    let error = |archivo: &str, mensaje: String| ErrorDatos { archivo: archivo.into(), mensaje };
    for prod in &p.productos {
        if let Some(a) = &prod.repone {
            if !aderezos.iter().any(|x| &x.id == a) {
                return Err(error("productos.ron", format!("\"{}\" repone un aderezo inexistente \"{a}\"", prod.id)));
            }
        }
    }
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
    }
    Ok(Catalogo {
        productos: p.productos,
        combinaciones: p.combinaciones,
        bloques,
        accesorios,
        bases: lista_bases,
        carrito_jugador: parsear("carrito_jugador.ron", carrito_jugador)?,
        aderezos,
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
            &leer("carrito_jugador.ron"),
            &leer("aderezos.ron"),
        )
        .unwrap_or_else(|e| panic!("{e}"))
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
    fn req_dep_01_bloques_de_panes_y_salchichas() {
        let c = catalogo_real();
        assert!(c.bloques.iter().any(|b| b.producto == "pan_pancho"));
        assert!(c.bloques.iter().any(|b| b.producto == "salchicha"));
        assert_eq!(c.bloque("bolsa_panes_12").unwrap().capacidad(), 12);
    }

    #[test]
    fn req_eco_03_precio_del_pancho() {
        let c = catalogo_real();
        assert_eq!(c.producto("pancho").unwrap().precio, Some(2500.0));
        assert_eq!(c.menu(), vec!["pancho".to_string()]);
    }

    #[test]
    fn req_ade_01_tres_aderezos_de_40_usos() {
        let c = catalogo_real();
        for id in ["mostaza", "ketchup", "mayonesa"] {
            assert_eq!(c.aderezo(id).map(|a| a.usos), Some(40), "{id}");
        }
        assert!(c.producto("pancho").unwrap().admite_aderezos);
        assert!(!c.producto("salchicha").unwrap().admite_aderezos);
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
        let a =
            c.accesorios.iter().find(|a| matches!(a.funcion, Some(crate::carrito::Funcion::Aderezos { .. }))).unwrap();
        assert_eq!(a.categoria, crate::carrito::Categoria::Equipamiento);
        assert!(c.carrito_jugador.accesorios.values().any(|v| v == &a.id));
    }

    #[test]
    fn producto_inexistente_en_bloque_da_error_claro() {
        let prod = leer("productos.ron");
        let bloques = r#"[(id: "x", nombre: "x", producto: "fantasma", grilla: (1,1,1),
            separacion: (0.1,0.1,0.1), empaque: Bolsa, color_empaque: (1,1,1), precio: 1)]"#;
        let e = cargar_catalogo(&prod, bloques, "[]", &[], "", &leer("aderezos.ron")).unwrap_err();
        assert!(e.mensaje.contains("fantasma"));
    }
}
