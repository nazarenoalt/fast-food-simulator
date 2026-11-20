//! SPEC-031 · Arranque de la partida: el producto elegido y el carrito inicial (TASK-0267).
//!
//! El carrito inicial es la base común de `carrito_jugador.ron` más lo del producto elegido en
//! `arranque.ron` (REQ-ARR-02). La rampa de la primera semana (REQ-ARR-05) vive en
//! `clientes.rs`.

use std::collections::BTreeMap;

use serde::Deserialize;

use crate::carrito::{CarritoArmado, ConfigCarrito, armar};
use crate::datos::Catalogo;

/// REQ-ARR-01: texto del panel del arranque.
pub const TITULO: &str = "¿Con qué arrancás?";
/// REQ-ARR-03: anclaje donde va el cartel de cerrado (REQ-PAP-07).
pub const ANCLAJE_CARTEL: &str = "cartel";
/// REQ-ARR-03: el accesorio del cartel de cerrado.
pub const CARTEL_CERRADO: &str = "cartel_cerrado";

/// Lo que se le suma a la base común: anclaje → accesorio y anclaje con depósito → bloques.
#[derive(Debug, Clone, PartialEq, Default, Deserialize)]
pub struct Agregado {
    #[serde(default)]
    pub accesorios: BTreeMap<String, String>,
    #[serde(default)]
    pub stock: BTreeMap<String, Vec<Option<String>>>,
}

/// REQ-ARR-01, REQ-ARR-02: un botón del panel y lo que trae su carrito.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct OpcionArranque {
    /// Id del producto (`productos.ron`): el único que queda en el menú.
    pub producto: String,
    /// Texto del botón.
    pub nombre: String,
    #[serde(default)]
    pub accesorios: BTreeMap<String, String>,
    #[serde(default)]
    pub stock: BTreeMap<String, Vec<Option<String>>>,
}

impl OpcionArranque {
    fn agregado(&self) -> Agregado {
        Agregado { accesorios: self.accesorios.clone(), stock: self.stock.clone() }
    }
}

/// `godot/data/arranque.ron`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Arranque {
    /// REQ-ARR-01: en el orden de los botones.
    pub productos: Vec<OpcionArranque>,
    /// REQ-ARR-04: los cuatro equipos de la prueba de humo.
    pub prueba: Agregado,
}

impl Arranque {
    pub fn opcion(&self, producto: &str) -> Option<&OpcionArranque> {
        self.productos.iter().find(|o| o.producto == producto)
    }
}

/// Lee `arranque.ron`.
pub fn parsear(texto: &str) -> Result<Arranque, String> {
    ron::from_str(texto).map_err(|e| format!("arranque.ron: {e}"))
}

/// La base común más lo agregado; si un anclaje está en las dos, manda lo agregado.
fn sumar(base_comun: &ConfigCarrito, agregado: &Agregado) -> ConfigCarrito {
    let mut c = base_comun.clone();
    c.accesorios.extend(agregado.accesorios.clone());
    c.stock.extend(agregado.stock.clone());
    c
}

/// REQ-ARR-02, REQ-ARR-03: el carrito inicial para el producto elegido (con el cartel colgado,
/// que ya viene en la base común).
pub fn config_para(base_comun: &ConfigCarrito, opcion: &OpcionArranque) -> ConfigCarrito {
    sumar(base_comun, &opcion.agregado())
}

/// REQ-ARR-04: el carrito de la prueba de humo: los cuatro equipos y sin el cartel de cerrado.
pub fn config_prueba(base_comun: &ConfigCarrito, arranque: &Arranque) -> ConfigCarrito {
    let mut c = sumar(base_comun, &arranque.prueba);
    c.accesorios.remove(ANCLAJE_CARTEL);
    c
}

/// REQ-CLI-04: productos del menú de un carrito armado (según las funciones de lo puesto).
pub fn menu_de(armado: &CarritoArmado, catalogo: &Catalogo) -> Vec<String> {
    let funciones: Vec<&str> =
        armado.colocados.iter().filter_map(|c| c.accesorio.funcion.as_ref()).map(|f| f.nombre()).collect();
    catalogo.menu_para(&funciones).into_iter().map(|i| i.producto).collect()
}

/// Revisa `arranque.ron` contra el catálogo: cada producto arma un carrito válido, su menú tiene
/// solo ese producto (REQ-ARR-02), el cartel está colgado en su anclaje (REQ-ARR-03) y la
/// prueba también arma bien (REQ-ARR-04).
pub fn validar(arranque: &Arranque, catalogo: &Catalogo) -> Result<(), String> {
    let bloques = catalogo.ids_bloques();
    let armar_cfg = |c: &ConfigCarrito, que: &str| {
        armar(c, &catalogo.bases, &catalogo.accesorios, &bloques).map_err(|e| format!("arranque.ron, {que}: {e}"))
    };
    if arranque.productos.is_empty() {
        return Err("arranque.ron: no hay productos para elegir".into());
    }
    let base = &catalogo.carrito_jugador;
    if base.accesorios.get(ANCLAJE_CARTEL).map(String::as_str) != Some(CARTEL_CERRADO) {
        return Err(format!("carrito_jugador.ron: falta \"{CARTEL_CERRADO}\" en el anclaje \"{ANCLAJE_CARTEL}\""));
    }
    for o in &arranque.productos {
        let armado = armar_cfg(&config_para(base, o), &o.producto)?;
        let menu = menu_de(&armado, catalogo);
        if menu != [o.producto.clone()] {
            return Err(format!("arranque.ron, {}: el menú tendría {menu:?}", o.producto));
        }
    }
    armar_cfg(&config_prueba(base, arranque), "prueba")?;
    Ok(())
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use crate::carrito::Funcion;
    use crate::datos::tests::catalogo_base_comun;

    /// El `arranque.ron` real.
    pub(crate) fn arranque_real() -> Arranque {
        let ruta = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data/arranque.ron");
        parsear(&std::fs::read_to_string(ruta).expect("arranque.ron")).unwrap_or_else(|e| panic!("{e}"))
    }

    fn armado(c: &ConfigCarrito) -> CarritoArmado {
        let cat = catalogo_base_comun();
        armar(c, &cat.bases, &cat.accesorios, &cat.ids_bloques()).unwrap_or_else(|e| panic!("{e}"))
    }

    fn funciones(a: &CarritoArmado) -> Vec<&'static str> {
        a.colocados.iter().filter_map(|c| c.accesorio.funcion.as_ref()).map(Funcion::nombre).collect()
    }

    fn accesorios(a: &CarritoArmado) -> Vec<&str> {
        a.colocados.iter().map(|c| c.accesorio.id.as_str()).collect()
    }

    /// Productos de los bloques del estante (en orden).
    fn estante(a: &CarritoArmado) -> Vec<String> {
        let cat = catalogo_base_comun();
        a.colocados
            .iter()
            .flat_map(|c| c.stock.iter().flatten())
            .map(|b| cat.bloque(b).expect("bloque").producto.clone())
            .collect()
    }

    fn para(producto: &str) -> CarritoArmado {
        let ar = arranque_real();
        let o = ar.opcion(producto).unwrap_or_else(|| panic!("falta {producto} en arranque.ron"));
        armado(&config_para(&catalogo_base_comun().carrito_jugador, o))
    }

    #[test]
    fn req_arr_01_cuatro_botones_en_orden() {
        let nombres: Vec<String> = arranque_real().productos.into_iter().map(|o| o.nombre).collect();
        assert_eq!(nombres, ["Pancho", "Hamburguesa", "Choripán", "Papas fritas"]);
        assert_eq!(TITULO, "¿Con qué arrancás?");
    }

    #[test]
    fn req_arr_02_arranque_ron_valido() {
        validar(&arranque_real(), &catalogo_base_comun()).unwrap_or_else(|e| panic!("{e}"));
    }

    #[test]
    fn req_arr_02_base_comun() {
        let cat = catalogo_base_comun();
        let a = armado(&cat.carrito_jugador);
        for id in
            ["heladera_chica", "estante_deposito", "sombrilla_roja", "foco_calido", "telon_panchos", "cartel_cerrado"]
        {
            assert!(accesorios(&a).contains(&id), "la base común trae {id}");
        }
        assert!(menu_de(&a, &cat).is_empty(), "la base común sola no cocina nada");
        assert!(estante(&a).is_empty(), "el estante lo llena el producto");
    }

    #[test]
    fn req_arr_02_cada_producto_con_su_equipo_y_solo_su_menu() {
        let cat = catalogo_base_comun();
        let casos: [(&str, &[&str], &[&str]); 4] = [
            ("pancho", &["Hervidor", "Aderezos"], &["pan_pancho", "pan_pancho", "salchicha", "salchicha"]),
            ("hamburguesa", &["Plancha", "Aderezos"], &["hamburguesa", "hamburguesa"]),
            ("choripan", &["Parrilla", "Aderezos"], &["chorizo", "pan_choripan", "bolsa_carbon"]),
            ("papas_en_cajita", &["Freidora", "Surtido"], &["papa_cruda", "cajita_papas"]),
        ];
        let cocinas = ["Hervidor", "Plancha", "Parrilla", "Freidora"];
        for (producto, equipo, stock) in casos {
            let a = para(producto);
            let f = funciones(&a);
            for e in equipo {
                assert!(f.contains(e), "{producto}: falta {e}");
            }
            for c in cocinas.iter().filter(|c| !equipo.contains(c)) {
                assert!(!f.contains(c), "{producto}: no trae {c}");
            }
            assert_eq!(estante(&a), *stock, "{producto}: estante");
            assert_eq!(menu_de(&a, &cat), [producto], "{producto}: el menú tiene solo ese producto");
            assert_eq!(a.base.id, "barra_mediana");
        }
    }

    #[test]
    fn ca_arr_01_choripan() {
        let a = para("choripan");
        let acc = accesorios(&a);
        assert!(acc.contains(&"parrilla_chica") && acc.contains(&"aderecera_cinco"));
        assert!(!acc.contains(&"hervidor_chico") && !acc.contains(&"plancha_chica"));
        let e = estante(&a);
        for p in ["chorizo", "pan_choripan", "bolsa_carbon"] {
            assert!(e.contains(&p.to_string()), "en el estante hay {p}");
        }
    }

    #[test]
    fn req_arr_03_cartel_colgado_en_su_anclaje() {
        for o in arranque_real().productos {
            let a = para(&o.producto);
            let cartel = a.colocados.iter().find(|c| c.anclaje.id == ANCLAJE_CARTEL).expect("anclaje cartel");
            assert_eq!(cartel.accesorio.id, CARTEL_CERRADO, "{}", o.producto);
        }
        // Arranca colgado: el estado inicial del cartel (REQ-CLI-13).
        assert!(crate::clientes::CartelCerrado::default().colgado);
    }

    #[test]
    fn req_arr_04_prueba_con_los_cuatro_equipos_sin_cartel() {
        let cat = catalogo_base_comun();
        let a = armado(&config_prueba(&cat.carrito_jugador, &arranque_real()));
        let f = funciones(&a);
        for e in ["Hervidor", "Plancha", "Parrilla", "Aderezos"] {
            assert!(f.contains(&e), "la prueba trae {e}");
        }
        assert!(!a.colocados.iter().any(|c| c.anclaje.id == ANCLAJE_CARTEL), "sin el cartel");
        let mut menu = menu_de(&a, &cat);
        menu.sort();
        assert_eq!(menu, ["choripan", "hamburguesa", "pancho"]);
        assert_eq!(estante(&a).len(), 4);
    }

    #[test]
    fn req_arr_02_lo_del_producto_manda_sobre_la_base() {
        let cat = catalogo_base_comun();
        let o = OpcionArranque {
            producto: "x".into(),
            nombre: "X".into(),
            accesorios: [("frente".to_string(), "telon_choripan".to_string())].into_iter().collect(),
            stock: BTreeMap::new(),
        };
        let c = config_para(&cat.carrito_jugador, &o);
        assert_eq!(c.accesorios["frente"], "telon_choripan");
        assert_eq!(c.accesorios.len(), cat.carrito_jugador.accesorios.len());
    }

    #[test]
    fn req_arr_02_errores_de_arranque() {
        let cat = catalogo_base_comun();
        let mut ar = arranque_real();
        ar.productos[0].accesorios.insert("mostrador_centro".into(), "plancha_chica".into());
        let e = validar(&ar, &cat).unwrap_err();
        assert!(e.contains("pancho") && e.contains("menú"), "{e}");
        let mut ar = arranque_real();
        ar.productos[1].stock.insert("lateral".into(), vec![Some("nada".into())]);
        assert!(validar(&ar, &cat).unwrap_err().contains("nada"));
        assert!(parsear("(productos: [], prueba: ())").is_ok_and(|a| validar(&a, &cat).is_err()));
    }
}
