//! SPEC-026 · Papas fritas: el contenido (papas, envases, utensilios, freidora y cartel) es
//! solo datos con modelo; acá van las medidas que lo validan. Freír llega en otra etapa.

use crate::carrito::{Accesorio, BaseCarrito};
use crate::forma::TipoPieza;

/// Anclajes de mostrador de una base (`mostrador_izq`, `mostrador_centro`, `mostrador_der`).
fn mostradores(b: &BaseCarrito) -> Vec<[f32; 3]> {
    b.anclajes.iter().filter(|a| a.id.starts_with("mostrador")).map(|a| a.pos).collect()
}

/// REQ-PAP-05: la porción de mesada más chica = la menor distancia en X entre dos anclajes
/// de mostrador vecinos, entre todas las bases.
pub fn porcion_mesada_minima(bases: &[BaseCarrito]) -> f32 {
    let mut minimo = f32::MAX;
    for b in bases {
        let mut xs: Vec<f32> = mostradores(b).iter().map(|p| p[0]).collect();
        xs.sort_by(f32::total_cmp);
        for par in xs.windows(2) {
            minimo = minimo.min(par[1] - par[0]);
        }
    }
    minimo
}

/// REQ-PAP-05: ancho (X) que ocupa un accesorio según su forma de respaldo, que mide lo mismo
/// que su modelo.
pub fn ancho(a: &Accesorio) -> f32 {
    let (mut mn, mut mx) = (f32::MAX, f32::MIN);
    for p in &a.forma {
        let medio = match p.tipo {
            TipoPieza::Caja => p.medidas[0] / 2.0,
            _ => p.medidas[0],
        };
        mn = mn.min(p.pos[0] - medio);
        mx = mx.max(p.pos[0] + medio);
    }
    mx - mn
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::carrito::{Categoria, Funcion, armar};
    use crate::datos::Colision;
    use crate::datos::tests::catalogo_real;

    const ESTADOS: [&str; 4] = ["papa_cruda", "papa_pelada", "papa_cortada", "papas_fritas"];

    fn accesorio<'a>(cat: &'a crate::datos::Catalogo, id: &str) -> &'a Accesorio {
        cat.accesorios.iter().find(|a| a.id == id).unwrap_or_else(|| panic!("falta el accesorio {id}"))
    }

    fn caja(c: &Colision) -> [f32; 3] {
        match c {
            Colision::Caja { medidas } => *medidas,
            Colision::Capsula { .. } => panic!("se esperaba una caja"),
        }
    }

    #[test]
    fn req_pap_01_cuatro_estados_de_la_papa_que_se_distinguen() {
        let cat = catalogo_real();
        for id in ESTADOS {
            let p = cat.producto(id).unwrap_or_else(|| panic!("falta {id}"));
            assert_eq!(p.modelo.as_deref(), Some(format!("comida/{id}").as_str()));
            assert!(p.masa > 0.0 && !p.forma.is_empty(), "{id}");
            assert!(p.precio.is_none() && p.coccion.is_none(), "{id}: todavía no se vende ni se cocina");
        }
        // Se distinguen: el color de respaldo de cada estado es distinto.
        let colores: Vec<[f32; 3]> = ESTADOS.iter().map(|id| cat.producto(id).unwrap().forma[0].color).collect();
        for (i, a) in colores.iter().enumerate() {
            for b in &colores[i + 1..] {
                assert!(a != b || i == 1, "dos estados con el mismo color");
            }
        }
        // La pelada es más clara que la cruda; las fritas, más doradas (menos azul) que las cortadas.
        assert!(colores[1][1] > colores[0][1]);
        assert!(colores[3][2] < colores[2][2]);
        // Pelar achica la papa; cortarla la deja más chata.
        let [cx, cy, _] = caja(&cat.producto("papa_cruda").unwrap().colision);
        let [px, py, _] = caja(&cat.producto("papa_pelada").unwrap().colision);
        let [_, ty, _] = caja(&cat.producto("papa_cortada").unwrap().colision);
        assert!(px < cx && py < cy && ty < py);
    }

    #[test]
    fn req_pap_02_03_cajita_pack_y_bolsa_de_papas() {
        let cat = catalogo_real();
        let cajita = cat.producto("cajita_papas").expect("falta cajita_papas");
        assert_eq!(cajita.modelo.as_deref(), Some("comida/cajita_papas"));
        assert_eq!(cat.bloque("pack_cajitas").expect("falta pack_cajitas").producto, "cajita_papas");
        let bolsa = cat.bloque("bolsa_papas").expect("falta bolsa_papas");
        assert_eq!(bolsa.producto, "papa_cruda");
        assert_eq!(bolsa.modelo.as_deref(), Some("stock/bolsa_papas"));
        assert_eq!(bolsa.empaque, crate::deposito::Empaque::Bolsa);
        assert!(bolsa.capacidad() >= 10 && bolsa.precio > 0.0);
        // Entran en un lugar del estante (0,22 × 0,3 × 0,4), y una papa entra en su lugar de la grilla.
        for b in [bolsa, cat.bloque("pack_cajitas").unwrap()] {
            let [x, y, z] = b.tamano();
            assert!(x <= 0.22 && y <= 0.3 && z <= 0.4, "{} no entra en el estante: {x}×{y}×{z}", b.id);
        }
        let [px, py, pz] = caja(&cat.producto("papa_cruda").unwrap().colision);
        assert!(px <= bolsa.separacion[0] && py <= bolsa.separacion[1] && pz <= bolsa.separacion[2]);
    }

    #[test]
    fn req_pap_04_utensilios_que_se_agarran() {
        let cat = catalogo_real();
        for id in ["pelapapas", "cuchillo", "colador_freidora"] {
            let p = cat.producto(id).unwrap_or_else(|| panic!("falta {id}"));
            assert_eq!(p.modelo.as_deref(), Some(format!("cocina/{id}").as_str()));
            assert!(p.precio.is_none() && p.coccion.is_none(), "{id} no se vende ni se cocina");
            assert!(p.masa > 0.0);
        }
        let menu = cat.menu();
        assert!(
            ESTADOS
                .iter()
                .chain(["pelapapas", "cuchillo", "colador_freidora", "cajita_papas"].iter())
                .all(|id| !menu.contains(&id.to_string()))
        );
    }

    #[test]
    fn req_pap_05_dos_freidoras_por_porcion_de_mesada() {
        let cat = catalogo_real();
        let porcion = porcion_mesada_minima(&cat.bases);
        assert!(porcion > 0.5 && porcion < 0.6, "la del kiosco: {porcion}");
        let f = accesorio(&cat, "freidora");
        let doble = accesorio(&cat, "freidora_doble");
        assert_eq!(f.categoria, Categoria::Cocina);
        assert_eq!(doble.categoria, Categoria::Cocina);
        assert!(2.0 * ancho(f) <= porcion, "dos freidoras ({}) no entran en {porcion}", 2.0 * ancho(f));
        assert!(ancho(doble) <= porcion && ancho(doble) <= 2.0 * ancho(f) + 0.01);
        // El colador (su canasto) es más chico que la cuba (0,206 × 0,31 del modelo).
        let [cx, _, cz] = caja(&cat.producto("colador_freidora").unwrap().colision);
        assert!(cx + 0.01 <= 0.206 && cz + 0.01 <= 0.31);
    }

    #[test]
    fn req_pap_06_surtidos() {
        let cat = catalogo_real();
        let trae = |id: &str| match &accesorio(&cat, id).funcion {
            Some(Funcion::Surtido { objetos }) => objetos.iter().map(|o| o.producto.clone()).collect::<Vec<_>>(),
            otra => panic!("{id} debería tener Surtido, tiene {otra:?}"),
        };
        assert_eq!(trae("freidora"), vec!["colador_freidora"]);
        assert_eq!(trae("freidora_doble"), vec!["colador_freidora", "colador_freidora"]);
        let tabla = trae("tabla_papas");
        for p in ["cuchillo", "pelapapas", "papa_cruda"] {
            assert!(tabla.contains(&p.to_string()), "la tabla trae {p}");
        }
        assert_eq!(accesorio(&cat, "tabla_papas").categoria, Categoria::Equipamiento);
        assert_eq!(Funcion::Surtido { objetos: vec![] }.nombre(), "Surtido");
    }

    #[test]
    fn req_pap_06_surtido_con_producto_inexistente_da_error_claro() {
        let dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data");
        let leer = |n: &str| std::fs::read_to_string(dir.join(n)).unwrap();
        let acc = r#"[(id: "x", nombre: "x", categoria: Cocina, precio: 1,
            funcion: Some(Surtido(objetos: [(producto: "fantasma", pos: (0, 0, 0))])))]"#;
        let e = crate::datos::cargar_catalogo(
            &leer("productos.ron"),
            &leer("bloques.ron"),
            acc,
            &[],
            &leer("carrito_jugador.ron"),
            &leer("aderezos.ron"),
        )
        .unwrap_err();
        assert!(e.mensaje.contains("fantasma") && e.mensaje.contains("\"x\""), "{}", e.mensaje);
    }

    #[test]
    fn req_pap_07_cartel_de_cerrado_colgante() {
        let cat = catalogo_real();
        let c = accesorio(&cat, "cartel_cerrado");
        assert_eq!(c.categoria, Categoria::Decoracion);
        assert_eq!(c.modelo.as_deref(), Some("accesorios/cartel_cerrado"));
        // El tablero cuelga: no apoya en el mostrador.
        let tablero = c.forma.iter().max_by(|a, b| a.pos[1].total_cmp(&b.pos[1])).unwrap();
        assert!(tablero.pos[1] - tablero.medidas[1] / 2.0 > 0.1);
        // Entra en un anclaje de mostrador de cada base.
        for b in &cat.bases {
            assert!(
                b.anclajes
                    .iter()
                    .any(|a| a.id.starts_with("mostrador") && a.categorias.contains(&Categoria::Decoracion)),
                "{}: sin lugar para el cartel",
                b.id
            );
        }
    }

    #[test]
    fn ca_pap_01_carro_grande_con_todo_lo_de_las_papas() {
        let cat = catalogo_real();
        let mut c = cat.carrito_jugador.clone();
        c.base = "carro_grande".into();
        c.accesorios = [
            ("mostrador_izq", "freidora_doble"),
            ("mostrador_centro", "tabla_papas"),
            ("mostrador_der", "cartel_cerrado"),
            ("lateral", "estante_deposito"),
        ]
        .iter()
        .map(|(a, b)| (a.to_string(), b.to_string()))
        .collect();
        c.stock = [("lateral".to_string(), vec![Some("bolsa_papas".to_string()), Some("pack_cajitas".to_string())])]
            .into_iter()
            .collect();
        let ids: Vec<String> = cat.bloques.iter().map(|b| b.id.clone()).collect();
        let armado = armar(&c, &cat.bases, &cat.accesorios, &ids).expect("la config con papas debería ser válida");
        assert_eq!(armado.colocados.len(), 4);
    }
}
