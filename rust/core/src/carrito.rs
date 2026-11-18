//! SPEC-006 · Carrito modular: bases, anclajes y accesorios.

use std::collections::BTreeMap;
use std::fmt;

use serde::Deserialize;

use crate::forma::Pieza;

/// REQ-CAR-04
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Deserialize)]
pub enum Categoria {
    Decoracion,
    Equipamiento,
    Cerco,
    Carpa,
    Telon,
    Cocina,
    Deposito,
    Sombrilla,
    Luz,
}

/// REQ-CAR-03
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Anclaje {
    pub id: String,
    pub pos: [f32; 3],
    /// Giro en Y, grados.
    #[serde(default)]
    pub rot_y: f32,
    pub categorias: Vec<Categoria>,
}

/// REQ-CAR-11: puerta que gira sobre una bisagra vertical. El panel se extiende hacia +X
/// desde la bisagra (en el giro cero); `apertura` es el giro final en Y, en grados
/// (positivo = el borde libre va hacia -Z, o sea hacia el lado del vendedor).
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefPuerta {
    /// Posición de la bisagra, relativa a la base (en el piso de la abertura).
    pub bisagra: [f32; 3],
    pub ancho: f32,
    pub alto: f32,
    pub apertura: f32,
}

/// REQ-CAR-01. Convención: el frente (lado del cliente) mira a +Z; el vendedor se para en -Z.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct BaseCarrito {
    pub id: String,
    pub nombre: String,
    pub ancho: f32,
    pub profundidad: f32,
    pub alto_mostrador: f32,
    pub color: [f32; 3],
    pub ruedas: bool,
    pub precio: f32,
    /// REQ-CAR-10: centro de la bandeja de entrega (relativo a la base).
    pub entrega: [f32; 3],
    /// REQ-CAR-10: primer lugar de la fila de clientes; la fila sigue hacia +X.
    pub fila: [f32; 3],
    /// REQ-CAR-11: sin puerta por defecto.
    #[serde(default)]
    pub puerta: Option<DefPuerta>,
    pub anclajes: Vec<Anclaje>,
}

impl BaseCarrito {
    pub fn anclaje(&self, id: &str) -> Option<&Anclaje> {
        self.anclajes.iter().find(|a| a.id == id)
    }
}

/// Qué hace un accesorio además de verse. REQ-CAR-05
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub enum Funcion {
    /// Interior útil (ancho, alto, profundidad) de la cuba.
    Hervidor {
        interior: [f32; 3],
    },
    /// Posiciones (relativas al accesorio) donde se apoya cada bloque de stock.
    Deposito {
        lugares: Vec<[f32; 3]>,
    },
    Luz {
        pos: [f32; 3],
        color: [f32; 3],
        energia: f32,
        alcance: f32,
    },
    /// Un pomo por aderezo (SPEC-012), separados `separacion` metros en X.
    Aderezos {
        tipos: Vec<String>,
        separacion: f32,
    },
    /// REQ-PAP-06: objetos sueltos que el accesorio trae ya apoyados.
    Surtido {
        objetos: Vec<ObjetoInicial>,
    },
    /// REQ-PAP-07: texto sobre un tablero. `pos` = centro del texto (relativo al accesorio),
    /// `tamano` = alto de las letras en metros.
    Cartel {
        texto: String,
        pos: [f32; 3],
        tamano: f32,
        color: [f32; 3],
    },
}

/// Un producto suelto de un Surtido (REQ-PAP-06).
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ObjetoInicial {
    pub producto: String,
    pub pos: [f32; 3],
    /// Giro en Y, grados.
    #[serde(default)]
    pub rot_y: f32,
}

/// REQ-CAR-05
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Accesorio {
    pub id: String,
    pub nombre: String,
    pub categoria: Categoria,
    pub precio: f32,
    #[serde(default)]
    pub forma: Vec<Pieza>,
    #[serde(default)]
    pub funcion: Option<Funcion>,
}

/// El carrito del jugador (`godot/data/carrito_jugador.ron`). REQ-CAR-07
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ConfigCarrito {
    pub base: String,
    /// REQ-CAR-09: color propio (estilo). Si falta, el de la base.
    #[serde(default)]
    pub color: Option<[f32; 3]>,
    /// anclaje → accesorio
    pub accesorios: BTreeMap<String, String>,
    /// anclaje con depósito → bloque en cada lugar
    #[serde(default)]
    pub stock: BTreeMap<String, Vec<Option<String>>>,
}

/// REQ-CAR-08: errores con el detalle exacto.
#[derive(Debug, Clone, PartialEq)]
pub enum ErrorCarrito {
    BaseInexistente(String),
    AnclajeInexistente { base: String, anclaje: String },
    AccesorioInexistente { anclaje: String, accesorio: String },
    CategoriaNoPermitida { anclaje: String, accesorio: String, categoria: Categoria, permitidas: Vec<Categoria> },
    StockSinDeposito { anclaje: String },
    StockDemasiadosBloques { anclaje: String, lugares: usize, pedidos: usize },
    BloqueInexistente { anclaje: String, bloque: String },
}

impl fmt::Display for ErrorCarrito {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use ErrorCarrito::*;
        match self {
            BaseInexistente(b) => write!(f, "No existe la base de carrito \"{b}\""),
            AnclajeInexistente { base, anclaje } => {
                write!(f, "La base \"{base}\" no tiene el anclaje \"{anclaje}\"")
            }
            AccesorioInexistente { anclaje, accesorio } => {
                write!(f, "Anclaje \"{anclaje}\": no existe el accesorio \"{accesorio}\"")
            }
            CategoriaNoPermitida { anclaje, accesorio, categoria, permitidas } => {
                write!(f, "Anclaje \"{anclaje}\": \"{accesorio}\" es {categoria:?}, y ahí solo van {permitidas:?}")
            }
            StockSinDeposito { anclaje } => {
                write!(f, "Stock en \"{anclaje}\", pero ahí no hay un accesorio de depósito")
            }
            StockDemasiadosBloques { anclaje, lugares, pedidos } => {
                write!(f, "Depósito en \"{anclaje}\" tiene {lugares} lugares y se pidieron {pedidos} bloques")
            }
            BloqueInexistente { anclaje, bloque } => {
                write!(f, "Depósito en \"{anclaje}\": no existe el bloque \"{bloque}\"")
            }
        }
    }
}

/// Un accesorio ya ubicado en su anclaje.
#[derive(Debug, Clone, PartialEq)]
pub struct Colocado {
    pub anclaje: Anclaje,
    pub accesorio: Accesorio,
    /// Solo para depósitos: bloque por lugar.
    pub stock: Vec<Option<String>>,
}

/// Resultado de validar una configuración: todo lo necesario para construir el carrito.
#[derive(Debug, Clone, PartialEq)]
pub struct CarritoArmado {
    pub base: BaseCarrito,
    pub color: [f32; 3],
    pub colocados: Vec<Colocado>,
}

/// REQ-CAR-07, REQ-CAR-08
pub fn armar(
    config: &ConfigCarrito,
    bases: &[BaseCarrito],
    accesorios: &[Accesorio],
    bloques_existentes: &[String],
) -> Result<CarritoArmado, ErrorCarrito> {
    let base =
        bases.iter().find(|b| b.id == config.base).ok_or_else(|| ErrorCarrito::BaseInexistente(config.base.clone()))?;

    // Un BTreeMap ya garantiza un accesorio como máximo por anclaje (REQ-CAR-08).
    let mut colocados = Vec::new();
    for (anclaje_id, acc_id) in &config.accesorios {
        let anclaje = base
            .anclaje(anclaje_id)
            .ok_or_else(|| ErrorCarrito::AnclajeInexistente { base: base.id.clone(), anclaje: anclaje_id.clone() })?;
        let acc = accesorios.iter().find(|a| &a.id == acc_id).ok_or_else(|| ErrorCarrito::AccesorioInexistente {
            anclaje: anclaje_id.clone(),
            accesorio: acc_id.clone(),
        })?;
        if !anclaje.categorias.contains(&acc.categoria) {
            return Err(ErrorCarrito::CategoriaNoPermitida {
                anclaje: anclaje_id.clone(),
                accesorio: acc_id.clone(),
                categoria: acc.categoria,
                permitidas: anclaje.categorias.clone(),
            });
        }
        colocados.push(Colocado { anclaje: anclaje.clone(), accesorio: acc.clone(), stock: Vec::new() });
    }

    for (anclaje_id, bloques) in &config.stock {
        let colocado = colocados
            .iter_mut()
            .find(|c| &c.anclaje.id == anclaje_id)
            .ok_or_else(|| ErrorCarrito::StockSinDeposito { anclaje: anclaje_id.clone() })?;
        let Some(Funcion::Deposito { lugares }) = &colocado.accesorio.funcion else {
            return Err(ErrorCarrito::StockSinDeposito { anclaje: anclaje_id.clone() });
        };
        if bloques.len() > lugares.len() {
            return Err(ErrorCarrito::StockDemasiadosBloques {
                anclaje: anclaje_id.clone(),
                lugares: lugares.len(),
                pedidos: bloques.len(),
            });
        }
        for b in bloques.iter().flatten() {
            if !bloques_existentes.contains(b) {
                return Err(ErrorCarrito::BloqueInexistente { anclaje: anclaje_id.clone(), bloque: b.clone() });
            }
        }
        let mut stock = bloques.clone();
        stock.resize(lugares.len(), None);
        colocado.stock = stock;
    }

    Ok(CarritoArmado { base: base.clone(), color: config.color.unwrap_or(base.color), colocados })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::datos::tests::catalogo_real;

    fn config(base: &str, acc: &[(&str, &str)]) -> ConfigCarrito {
        ConfigCarrito {
            base: base.into(),
            color: None,
            accesorios: acc.iter().map(|(a, b)| (a.to_string(), b.to_string())).collect(),
            stock: BTreeMap::new(),
        }
    }

    fn armar_cfg(c: &ConfigCarrito) -> Result<CarritoArmado, ErrorCarrito> {
        let cat = catalogo_real();
        let bloques: Vec<String> = cat.bloques.iter().map(|b| b.id.clone()).collect();
        armar(c, &cat.bases, &cat.accesorios, &bloques)
    }

    #[test]
    fn req_car_01_02_hay_tres_bases_de_distinto_tamano() {
        let cat = catalogo_real();
        let ids: Vec<_> = cat.bases.iter().map(|b| b.id.as_str()).collect();
        for id in ["barra_chica", "barra_mediana", "carro_grande"] {
            assert!(ids.contains(&id), "falta la base {id}");
        }
        let mut anchos: Vec<f32> = cat.bases.iter().map(|b| b.ancho).collect();
        anchos.dedup();
        assert_eq!(anchos.len(), cat.bases.len(), "las bases tienen que ser de distinto tamaño");
    }

    #[test]
    fn req_car_03_anclajes_con_id_unico_y_categorias() {
        for b in catalogo_real().bases {
            let mut ids: Vec<_> = b.anclajes.iter().map(|a| &a.id).collect();
            let n = ids.len();
            ids.sort();
            ids.dedup();
            assert_eq!(ids.len(), n, "anclajes repetidos en {}", b.id);
            assert!(b.anclajes.iter().all(|a| !a.categorias.is_empty()));
        }
    }

    #[test]
    fn req_car_04_05_hay_accesorios_de_todas_las_categorias() {
        use Categoria::*;
        let cat = catalogo_real();
        for c in [Decoracion, Equipamiento, Cerco, Carpa, Telon, Cocina, Deposito, Sombrilla, Luz] {
            assert!(cat.accesorios.iter().any(|a| a.categoria == c), "falta un accesorio {c:?}");
        }
    }

    #[test]
    fn req_car_07_config_del_jugador_es_valida() {
        let cat = catalogo_real();
        let armado = armar_cfg(&cat.carrito_jugador).expect("carrito_jugador.ron inválido");
        assert!(armado.colocados.iter().any(|c| matches!(c.accesorio.funcion, Some(Funcion::Hervidor { .. }))));
        assert!(armado.colocados.iter().any(|c| c.stock.iter().flatten().count() > 0));
    }

    #[test]
    fn req_car_08_errores_exactos() {
        let e = armar_cfg(&config("no_existe", &[])).unwrap_err();
        assert_eq!(e, ErrorCarrito::BaseInexistente("no_existe".into()));

        let e = armar_cfg(&config("barra_chica", &[("techo_volador", "sombrilla_roja")])).unwrap_err();
        assert!(matches!(e, ErrorCarrito::AnclajeInexistente { .. }));

        let e = armar_cfg(&config("barra_chica", &[("mostrador_izq", "nada")])).unwrap_err();
        assert!(matches!(e, ErrorCarrito::AccesorioInexistente { .. }));

        // CA-CAR-02: sombrilla en un anclaje de mostrador.
        let e = armar_cfg(&config("barra_chica", &[("mostrador_izq", "sombrilla_roja")])).unwrap_err();
        assert!(matches!(e, ErrorCarrito::CategoriaNoPermitida { .. }));
        assert!(e.to_string().contains("mostrador_izq") && e.to_string().contains("sombrilla_roja"));
    }

    #[test]
    fn req_car_08_stock_validado() {
        let mut c = config("barra_chica", &[("mostrador_izq", "hervidor_chico")]);
        c.stock.insert("mostrador_izq".into(), vec![Some("bolsa_panes_12".into())]);
        assert!(matches!(armar_cfg(&c), Err(ErrorCarrito::StockSinDeposito { .. })));

        let mut c = config("barra_chica", &[("lateral", "estante_deposito")]);
        c.stock.insert("lateral".into(), vec![Some("caja_de_nada".into())]);
        assert!(matches!(armar_cfg(&c), Err(ErrorCarrito::BloqueInexistente { .. })));

        let mut c = config("barra_chica", &[("lateral", "estante_deposito")]);
        c.stock.insert("lateral".into(), vec![None; 50]);
        assert!(matches!(armar_cfg(&c), Err(ErrorCarrito::StockDemasiadosBloques { .. })));
    }

    #[test]
    fn req_car_10_bandeja_sobre_el_mostrador_y_fila_adelante() {
        for b in catalogo_real().bases {
            assert!((b.entrega[1] - b.alto_mostrador).abs() < 0.01, "{}: bandeja a la altura del mostrador", b.id);
            assert!(b.entrega[0].abs() < b.ancho / 2.0 && b.entrega[2].abs() < b.profundidad / 2.0);
            assert!(b.fila[2] > b.profundidad / 2.0 + 0.3, "{}: la fila va adelante del carrito", b.id);
        }
    }

    #[test]
    fn req_car_09_color_propio() {
        let mut c = config("barra_chica", &[]);
        assert_eq!(armar_cfg(&c).unwrap().color, armar_cfg(&c).unwrap().base.color);
        c.color = Some([0.1, 0.2, 0.3]);
        assert_eq!(armar_cfg(&c).unwrap().color, [0.1, 0.2, 0.3]);
    }

    #[test]
    fn ca_car_01_misma_config_en_carro_grande() {
        // Todos los anclajes que usa el jugador existen también en el carro grande.
        let cat = catalogo_real();
        let mut c = cat.carrito_jugador.clone();
        c.base = "carro_grande".into();
        armar_cfg(&c).expect("la config del jugador debería funcionar en el carro grande");
    }

    // ── SPEC-006: puerta ────────────────────────────────────

    #[test]
    fn req_car_11_solo_el_carro_grande_tiene_puerta_y_entra_en_su_pared() {
        for b in catalogo_real().bases {
            match (&b.puerta, b.id.as_str()) {
                (Some(p), "carro_grande") => {
                    assert!(p.apertura > 0.0 && p.apertura <= 120.0, "se abre hacia afuera, hasta 120°");
                    assert!(p.ancho > 0.4 && p.alto > 0.4);
                    // La bisagra está sobre la pared del lado del vendedor y el panel cabe en ella.
                    assert!((p.bisagra[2] + b.profundidad / 2.0).abs() < 0.01);
                    assert!(p.bisagra[0].abs() + p.ancho <= b.ancho / 2.0);
                    assert!(p.bisagra[1] >= 0.0 && p.bisagra[1] + p.alto < b.alto_mostrador);
                }
                (None, id) => assert_ne!(id, "carro_grande", "el carro grande tiene que tener puerta"),
                (Some(_), id) => panic!("{id} no debería tener puerta"),
            }
        }
    }

    // ── SPEC-025: papas, utensilios, freidora y cartel ──────

    fn color_de(cat: &crate::datos::Catalogo, id: &str) -> [f32; 3] {
        cat.producto(id).unwrap().forma[0].color
    }

    #[test]
    fn req_pap_01_estados_de_la_papa_se_distinguen() {
        let cat = catalogo_real();
        let ids = ["papa_cruda_sin_pelar", "papa_pelada", "papa_cortada", "papas_fritas"];
        for id in ids {
            let p = cat.producto(id).unwrap_or_else(|| panic!("falta {id}"));
            assert!(p.masa > 0.0 && !p.forma.is_empty());
            assert!(p.precio.is_none(), "{id}: todavía no se vende");
        }
        for (i, a) in ids.iter().enumerate() {
            for b in &ids[i + 1..] {
                let (pa, pb) = (cat.producto(a).unwrap(), cat.producto(b).unwrap());
                assert!(
                    color_de(&cat, a) != color_de(&cat, b) || pa.forma.len() != pb.forma.len(),
                    "{a} y {b} se ven iguales"
                );
            }
        }
        // La pelada es más clara que la que tiene cáscara; las fritas son más doradas (menos azul) que las cortadas.
        assert!(color_de(&cat, "papa_pelada")[2] > color_de(&cat, "papa_cruda_sin_pelar")[2]);
        assert!(color_de(&cat, "papas_fritas")[2] < color_de(&cat, "papa_cortada")[2]);
    }

    #[test]
    fn req_pap_02_03_envases_y_bolsa_de_papas() {
        let cat = catalogo_real();
        assert!(cat.producto("cajita_papas").is_some());
        let pack = cat.bloque("pack_cajitas").expect("falta pack_cajitas");
        assert_eq!(pack.producto, "cajita_papas");
        let bolsa = cat.bloque("bolsa_papas").expect("falta bolsa_papas");
        assert_eq!(bolsa.producto, "papa_cruda_sin_pelar");
        assert_eq!(bolsa.empaque, crate::deposito::Empaque::Bolsa);
        assert!(bolsa.capacidad() >= 10 && bolsa.precio > 0.0);
        // Cabe en un lugar del estante (zona de 0.22 × 0.3 × 0.4).
        let [x, y, z] = bolsa.tamano();
        assert!(x <= 0.25 && y <= 0.3 && z <= 0.4, "la bolsa no entra en el estante: {x}×{y}×{z}");
    }

    #[test]
    fn req_pap_04_utensilios() {
        let cat = catalogo_real();
        for id in ["pelapapas", "cuchillo", "colador_freidora"] {
            let p = cat.producto(id).unwrap_or_else(|| panic!("falta {id}"));
            assert!(p.precio.is_none() && p.coccion.is_none(), "{id} no se vende ni se cocina");
            assert!(p.forma.len() >= 2 && p.masa > 0.0);
        }
        assert_eq!(cat.menu(), vec!["pancho".to_string()], "los utensilios no entran al menú");
    }

    fn accesorio<'a>(cat: &'a crate::datos::Catalogo, id: &str) -> &'a Accesorio {
        cat.accesorios.iter().find(|a| a.id == id).unwrap_or_else(|| panic!("falta el accesorio {id}"))
    }

    #[test]
    fn req_pap_05_freidora_con_cuba_que_retiene_el_colador() {
        let cat = catalogo_real();
        let f = accesorio(&cat, "freidora");
        assert_eq!(f.categoria, Categoria::Cocina);
        assert!(f.forma.iter().filter(|p| p.colision).count() >= 5, "fondo y cuatro paredes con colisión");
        // La cuba es más grande que el colador, así que lo contiene.
        let colador = cat.producto("colador_freidora").unwrap();
        let crate::datos::Colision::Caja { medidas: [cw, _, cd] } = colador.colision else {
            panic!("colisión de caja")
        };
        let fondo = f.forma.iter().find(|p| p.colision && p.medidas[1] < 0.02).expect("fondo");
        assert!(fondo.medidas[0] > cw + 0.04 && fondo.medidas[2] > cd + 0.04);
    }

    #[test]
    fn req_pap_06_surtido() {
        let cat = catalogo_real();
        let objetos = |id: &str| match &accesorio(&cat, id).funcion {
            Some(Funcion::Surtido { objetos }) => objetos.iter().map(|o| o.producto.clone()).collect::<Vec<_>>(),
            otra => panic!("{id} debería tener Surtido, tiene {otra:?}"),
        };
        assert_eq!(objetos("freidora"), vec!["colador_freidora"]);
        let tabla = objetos("tabla_de_cortar");
        for p in ["cuchillo", "pelapapas", "papa_cruda_sin_pelar"] {
            assert!(tabla.contains(&p.to_string()), "la tabla trae {p}");
        }
        assert_eq!(accesorio(&cat, "tabla_de_cortar").categoria, Categoria::Equipamiento);
    }

    #[test]
    fn req_pap_06_surtido_con_producto_inexistente_da_error_claro() {
        use std::fs;
        let dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data");
        let leer = |n: &str| fs::read_to_string(dir.join(n)).unwrap();
        let acc = r#"[(id: "x", nombre: "x", categoria: Cocina, precio: 1,
            funcion: Some(Surtido(objetos: [(producto: "fantasma", pos: (0, 0, 0))])))]"#;
        let e = crate::datos::cargar_catalogo(
            &leer("productos.ron"),
            &leer("bloques.ron"),
            acc,
            &[],
            "",
            &leer("aderezos.ron"),
        )
        .unwrap_err();
        assert!(e.mensaje.contains("fantasma") && e.mensaje.contains("\"x\""), "{e}");
    }

    #[test]
    fn req_pap_07_cartel_de_cerrado() {
        let cat = catalogo_real();
        let c = accesorio(&cat, "cartel_cerrado");
        assert_eq!(c.categoria, Categoria::Decoracion);
        let Some(Funcion::Cartel { texto, tamano, pos, .. }) = &c.funcion else { panic!("sin función Cartel") };
        assert_eq!(texto, "CERRADO");
        assert!(*tamano > 0.03 && *tamano < 0.2);
        // El texto va apenas delante del tablero (hacia el cliente, +Z), así que se lee de frente.
        let tablero = c.forma.iter().find(|p| p.tipo == crate::forma::TipoPieza::Caja && p.medidas[0] > 0.2).unwrap();
        assert!(pos[2] > tablero.pos[2] && pos[2] < tablero.pos[2] + 0.05);
    }

    #[test]
    fn req_pap_08_todo_se_puede_ubicar_en_cada_base() {
        let cat = catalogo_real();
        for b in &cat.bases {
            for acc in ["freidora", "tabla_de_cortar", "cartel_cerrado"] {
                let a = accesorio(&cat, acc);
                assert!(
                    b.anclajes.iter().any(|an| an.categorias.contains(&a.categoria)),
                    "{}: no hay dónde poner {acc}",
                    b.id
                );
            }
            // El cartel tiene su propio anclaje, para que no le quite lugar a nada.
            let ancla =
                b.anclajes.iter().find(|a| a.id == "cartel").unwrap_or_else(|| panic!("{}: sin anclaje cartel", b.id));
            assert_eq!(ancla.categorias, vec![Categoria::Decoracion]);
            assert!(ancla.pos[0].abs() < b.ancho / 2.0, "{}: el cartel queda dentro del carrito", b.id);
        }
    }

    #[test]
    fn ca_pap_01_carro_grande_con_todo_lo_nuevo() {
        let mut c = config(
            "carro_grande",
            &[
                ("mostrador_izq", "freidora"),
                ("mostrador_centro", "tabla_de_cortar"),
                ("mostrador_der", "hervidor_chico"),
                ("cartel", "cartel_cerrado"),
            ],
        );
        c.stock.insert("lateral".into(), vec![Some("bolsa_papas".into()), Some("pack_cajitas".into())]);
        c.accesorios.insert("lateral".into(), "estante_deposito".into());
        let armado = armar_cfg(&c).expect("la config con papas debería ser válida");
        assert_eq!(armado.colocados.len(), 5);
        // La misma regla de siempre: un cartel en un anclaje de mostrador es un error.
        let mal = config("carro_grande", &[("mostrador_izq", "cartel_cerrado")]);
        assert!(matches!(armar_cfg(&mal), Err(ErrorCarrito::CategoriaNoPermitida { .. })));
    }
}
