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
    /// Plancha de cocina (SPEC-014): superficie (ancho, profundidad) en metros.
    Plancha {
        superficie: [f32; 2],
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
}
