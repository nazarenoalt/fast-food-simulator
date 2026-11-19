//! SPEC-006 · Carrito modular: bases, anclajes y accesorios.

use std::collections::BTreeMap;
use std::fmt;

use serde::Deserialize;

use crate::forma::Pieza;
use crate::logo::{Logo, LugarLogo};

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
    /// REQ-CAR-04: cerramiento para comer al costado del carro (porche de nylon).
    Porche,
    /// REQ-TIE-13: cosas de piso para los clientes (mesa alta, banqueta, maceta).
    Mobiliario,
    /// REQ-CAR-04 / REQ-PAP-07: cartel que cuelga adelante, del canto del mostrador.
    Cartel,
    /// REQ-AMP-09: techos y marquesinas (con caños adelante; la carpa sigue en Carpa).
    Techo,
    /// REQ-AMP-07: toldos del frente.
    Toldo,
    /// REQ-AMP-04: alacenas que encastran en las bahías bajo la mesada.
    Alacena,
    /// REQ-AMP-10: guirnaldas de luces colgadas de los caños de un techo.
    Guirnalda,
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
    /// REQ-AMP-10: el anclaje solo se usa si en el carrito hay algo de esta categoría.
    #[serde(default)]
    pub requiere: Option<Categoria>,
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
    /// REQ-MOD-01: modelo 3D ("familia/id" → godot/modelos/familia/id.glb).
    #[serde(default)]
    pub modelo: Option<String>,
    /// REQ-CAR-11: dónde aparece el jugador (si falta, el lugar de la escena).
    #[serde(default)]
    pub jugador: Option<[f32; 3]>,
    /// REQ-CAR-11: dónde deja el proveedor el pallet (si falta, al costado del carrito).
    #[serde(default)]
    pub pallet: Option<[f32; 3]>,
    /// REQ-CAR-11: grados que se abre la puerta del modelo (`pieza_puerta`, REQ-CAR-13).
    #[serde(default)]
    pub puerta: Option<f32>,
    /// REQ-CAR-11: si la puerta arranca abierta (si no, cerrada).
    #[serde(default)]
    pub puerta_abierta: bool,
    /// REQ-LOG-05: lugares de la base donde va el logo.
    #[serde(default)]
    pub logos: Vec<LugarLogo>,
}

impl BaseCarrito {
    pub fn anclaje(&self, id: &str) -> Option<&Anclaje> {
        self.anclajes.iter().find(|a| a.id == id)
    }

    /// REQ-CAR-11 / REQ-PRO-04: lugar del pallet del proveedor, relativo a la base.
    pub fn lugar_pallet(&self) -> [f32; 3] {
        self.pallet.unwrap_or([self.ancho / 2.0 + 1.35, 0.0, -1.0])
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
    /// Parrilla de carbón (SPEC-015): superficie (ancho, profundidad) en metros.
    Parrilla {
        superficie: [f32; 2],
    },
    /// Heladera (SPEC-016): interior útil (ancho, alto, profundidad) y los lugares donde se
    /// apoya cada bloque de stock, como en el depósito. La puerta mira a +Z del accesorio.
    Heladera {
        interior: [f32; 3],
        lugares: Vec<[f32; 3]>,
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
}

/// Un producto suelto de un Surtido (REQ-PAP-06): posición y giro en Y relativos al accesorio.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ObjetoInicial {
    pub producto: String,
    pub pos: [f32; 3],
    /// Giro en Y, grados.
    #[serde(default)]
    pub rot_y: f32,
}

impl Funcion {
    /// Nombres de todas las funciones (los usa `requiere` de los productos).
    pub const NOMBRES: [&'static str; 8] =
        ["Hervidor", "Plancha", "Parrilla", "Heladera", "Deposito", "Luz", "Aderezos", "Surtido"];

    /// REQ-CLI-04: nombre de la función, tal cual se escribe en los datos.
    pub fn nombre(&self) -> &'static str {
        match self {
            Funcion::Hervidor { .. } => "Hervidor",
            Funcion::Plancha { .. } => "Plancha",
            Funcion::Parrilla { .. } => "Parrilla",
            Funcion::Heladera { .. } => "Heladera",
            Funcion::Deposito { .. } => "Deposito",
            Funcion::Luz { .. } => "Luz",
            Funcion::Aderezos { .. } => "Aderezos",
            Funcion::Surtido { .. } => "Surtido",
        }
    }
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
    /// REQ-MOD-01: modelo 3D que reemplaza a `forma`.
    #[serde(default)]
    pub modelo: Option<String>,
    /// REQ-MOD-03: corrimiento del modelo respecto del anclaje.
    #[serde(default)]
    pub pos_modelo: [f32; 3],
    /// REQ-MOD-06: colores por superficie de piezas del modelo: (pieza, [color de cada superficie]).
    #[serde(default)]
    pub superficies: Vec<(String, Vec<[f32; 3]>)>,
    /// REQ-TIE-11: bases donde entra (por tamaño). Si falta, entra en todas.
    #[serde(default)]
    pub bases: Option<Vec<String>>,
    /// REQ-AMP-11: categorías con las que no puede estar en el mismo carrito.
    #[serde(default)]
    pub choca_con: Vec<Categoria>,
    /// REQ-LOG-05: lugares del accesorio donde va el logo.
    #[serde(default)]
    pub logos: Vec<LugarLogo>,
}

impl Accesorio {
    /// REQ-AMP-11: el choque vale para los dos lados.
    pub fn choca(&self, otro: &Accesorio) -> bool {
        self.choca_con.contains(&otro.categoria) || otro.choca_con.contains(&self.categoria)
    }
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
    /// REQ-LOG-10: logo de arranque (se revisa al cargar el catálogo).
    #[serde(default)]
    pub logo: Option<Logo>,
}

/// REQ-CAR-08: errores con el detalle exacto.
#[derive(Debug, Clone, PartialEq)]
pub enum ErrorCarrito {
    BaseInexistente(String),
    AnclajeInexistente {
        base: String,
        anclaje: String,
    },
    AccesorioInexistente {
        anclaje: String,
        accesorio: String,
    },
    CategoriaNoPermitida {
        anclaje: String,
        accesorio: String,
        categoria: Categoria,
        permitidas: Vec<Categoria>,
    },
    StockSinDeposito {
        anclaje: String,
    },
    StockDemasiadosBloques {
        anclaje: String,
        lugares: usize,
        pedidos: usize,
    },
    BloqueInexistente {
        anclaje: String,
        bloque: String,
    },
    /// REQ-AMP-11
    Choque {
        accesorio: String,
        con: String,
    },
    /// REQ-AMP-10
    FaltaRequisito {
        anclaje: String,
        categoria: Categoria,
    },
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
            Choque { accesorio, con } => write!(f, "\"{accesorio}\" choca con \"{con}\""),
            FaltaRequisito { anclaje, categoria } => {
                write!(f, "Anclaje \"{anclaje}\": necesita algo de {categoria:?} puesto en el carrito")
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
    /// REQ-LOG-08
    pub logo: Option<Logo>,
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

    // REQ-AMP-10 / REQ-AMP-11: sin choques y con lo que pide cada anclaje.
    for (i, a) in colocados.iter().enumerate() {
        if let Some(b) = colocados[i + 1..].iter().find(|b| a.accesorio.choca(&b.accesorio)) {
            return Err(ErrorCarrito::Choque { accesorio: a.accesorio.id.clone(), con: b.accesorio.id.clone() });
        }
        if let Some(cat) = a.anclaje.requiere
            && !colocados.iter().any(|c| c.accesorio.categoria == cat)
        {
            return Err(ErrorCarrito::FaltaRequisito { anclaje: a.anclaje.id.clone(), categoria: cat });
        }
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

    let color = config.color.unwrap_or(base.color);
    Ok(CarritoArmado { base: base.clone(), color, colocados, logo: config.logo.clone() })
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
            logo: None,
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
        for c in [Decoracion, Equipamiento, Cerco, Carpa, Telon, Cocina, Deposito, Sombrilla, Luz, Porche, Cartel] {
            assert!(cat.accesorios.iter().any(|a| a.categoria == c), "falta un accesorio {c:?}");
        }
    }

    #[test]
    fn req_car_11_lugares_del_jugador_del_pallet_y_puerta() {
        let cat = catalogo_real();
        let barra = cat.bases.iter().find(|b| b.id == "barra_chica").unwrap();
        assert_eq!(barra.jugador, None, "sin dato, el jugador queda donde lo deja la escena");
        assert_eq!(barra.lugar_pallet(), [barra.ancho / 2.0 + 1.35, 0.0, -1.0], "pallet por defecto al costado");
        let k = cat.bases.iter().find(|b| b.id == "carro_kiosco").unwrap();
        let j = k.jugador.expect("el kiosco dice dónde aparece el jugador");
        assert!(j[0].abs() < k.ancho / 2.0 && j[2].abs() < k.profundidad / 2.0, "aparece adentro del kiosco");
        assert!(j[1] >= 0.15, "sobre el piso de adentro");
        let p = k.lugar_pallet();
        assert!(p[2] < -k.profundidad / 2.0, "el pallet queda afuera, del lado del vendedor");
        assert!(k.puerta.is_some_and(|g| g > 45.0) && k.puerta_abierta, "la puerta arranca abierta");
        assert!(!barra.puerta_abierta && barra.puerta.is_none(), "las barras no tienen puerta");
    }

    #[test]
    fn req_car_12_carro_kiosco() {
        let cat = catalogo_real();
        let k = cat.bases.iter().find(|b| b.id == "carro_kiosco").expect("falta el carro kiosco");
        let cats: Vec<Categoria> = k.anclajes.iter().flat_map(|a| a.categorias.clone()).collect();
        assert!(!cats.contains(&Categoria::Sombrilla) && !cats.contains(&Categoria::Carpa), "trae techo propio");
        assert!(cats.contains(&Categoria::Porche), "tiene lugar para el porche");
        assert!(k.entrega[2] > k.profundidad / 2.0, "la entrega es en la repisa de afuera");
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
            // Sobre el mostrador, o en la repisa de afuera del carro kiosco (REQ-CAR-12).
            assert!(b.entrega[0].abs() < b.ancho / 2.0 && b.entrega[2].abs() < b.profundidad / 2.0 + 0.2, "{}", b.id);
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
        // Una config armada para la barra chica funciona igual en el carro grande (mismos anclajes).
        let mut c = config(
            "barra_chica",
            &[
                ("mostrador_izq", "hervidor_chico"),
                ("lateral", "estante_deposito"),
                ("sombra", "sombrilla_roja"),
                ("luz_1", "foco_calido"),
            ],
        );
        armar_cfg(&c).expect("config de barra chica");
        c.base = "carro_grande".into();
        armar_cfg(&c).expect("la misma config debería funcionar en el carro grande");
    }
}
