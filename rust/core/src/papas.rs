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
            assert!(p.precio.is_none(), "{id}: suelta no se vende");
            // REQ-FRE-09: cortadas y fritas se cocinan en el aceite; la cruda y la pelada, no.
            let se_frie = matches!(id, "papa_cortada" | "papas_fritas");
            assert_eq!(p.coccion.is_some(), se_frie, "{id}");
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
    fn req_pap_02_cajita_y_pack() {
        let cat = catalogo_real();
        let cajita = cat.producto("cajita_papas").expect("falta cajita_papas");
        assert_eq!(cajita.modelo.as_deref(), Some("comida/cajita_papas"));
        assert_eq!(cat.bloque("pack_cajitas").expect("falta pack_cajitas").producto, "cajita_papas");
    }

    #[test]
    fn req_pap_03_bolsas_de_2_y_5_kg_que_entran_en_el_estante() {
        let cat = catalogo_real();
        assert!(cat.bloque("bolsa_papas").is_none(), "la bolsa de papel se reemplazó por las de arpillera");
        let papa = cat.producto("papa_cruda").unwrap();
        let [px, py, pz] = caja(&papa.colision);
        for (id, kg, unidades) in [("bolsa_papas_2kg", 2.0, 12), ("bolsa_papas_5kg", 5.0, 24)] {
            let b = cat.bloque(id).unwrap_or_else(|| panic!("falta {id}"));
            assert_eq!(b.producto, "papa_cruda");
            assert_eq!(b.modelo.as_deref(), Some(format!("stock/{id}").as_str()));
            assert_eq!(b.empaque, crate::deposito::Empaque::Bolsa);
            assert_eq!(b.capacidad(), unidades, "{id}");
            let peso = b.capacidad() as f32 * papa.masa;
            assert!((peso - kg).abs() <= 0.5, "{id}: {peso} kg");
            assert!(b.precio > 0.0);
            // Una papa entra en su lugar de la grilla y la bolsa en un lugar del estante.
            assert!(px <= b.separacion[0] && py <= b.separacion[1] && pz <= b.separacion[2], "{id}");
            let [x, y, z] = b.tamano();
            assert!(x <= 0.22 && y <= 0.3 && z <= 0.4, "{id} no entra en el estante: {x}×{y}×{z}");
        }
        // 25 papas no entran: a lo ancho caben 2, y 25 es impar.
        assert_eq!((0.22 / px) as u32, 2);
        let [x, y, z] = cat.bloque("pack_cajitas").unwrap().tamano();
        assert!(x <= 0.22 && y <= 0.3 && z <= 0.4);
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
        // El colador (su canasto) es más chico que la cuba (0,205 × 0,309 del modelo, REQ-FRE-04).
        let [cx, _, cz] = caja(&cat.producto("colador_freidora").unwrap().colision);
        assert!(cx + 0.01 <= 0.206 && cz + 0.01 <= 0.31);
    }

    #[test]
    fn req_pap_06_surtidos() {
        let cat = catalogo_real();
        let trae = |id: &str| match &accesorio(&cat, id).funcion {
            Some(f) => f.objetos_iniciales().iter().map(|o| o.producto.clone()).collect::<Vec<_>>(),
            None => panic!("{id} debería traer objetos"),
        };
        assert_eq!(trae("freidora"), vec!["colador_freidora"]);
        assert_eq!(trae("freidora_doble"), vec!["colador_freidora", "colador_freidora"]);
        let tabla = trae("tabla_papas");
        for p in ["cuchillo", "pelapapas", "papa_cruda"] {
            assert!(tabla.contains(&p.to_string()), "la tabla trae {p}");
        }
        assert_eq!(accesorio(&cat, "tabla_papas").categoria, Categoria::Equipamiento);
        assert_eq!(Funcion::Surtido { objetos: vec![] }.nombre(), "Surtido");
        // REQ-FRE-04: la freidora es una Freidora con sus cubas (la doble, dos).
        for (id, n) in [("freidora", 1), ("freidora_doble", 2)] {
            match &accesorio(&cat, id).funcion {
                Some(Funcion::Freidora { cubas, .. }) => assert_eq!(cubas.len(), n, "{id}"),
                otra => panic!("{id} debería ser Freidora, es {otra:?}"),
            }
        }
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
            &leer("logos.ron"),
        )
        .unwrap_err();
        assert!(e.mensaje.contains("fantasma") && e.mensaje.contains("\"x\""), "{}", e.mensaje);
    }

    #[test]
    fn req_pap_07_cartel_de_cerrado_colgado_de_una_pared_o_de_la_puerta() {
        let cat = catalogo_real();
        let c = accesorio(&cat, "cartel_cerrado");
        assert_eq!(c.categoria, Categoria::Cartel);
        assert_eq!(c.modelo.as_deref(), Some("accesorios/cartel_cerrado"));
        // Cuelga: el origen es el clavo y el tablero queda abajo; no choca.
        let tablero = c.forma.iter().max_by(|a, b| a.medidas[0].total_cmp(&b.medidas[0])).unwrap();
        assert!(tablero.pos[1] + tablero.medidas[1] / 2.0 < -0.05, "el tablero cuelga del clavo");
        assert!(c.forma.iter().all(|p| !p.colision));
        // Es el único Cartel: ninguna otra decoración cae en la pared.
        assert_eq!(cat.accesorios.iter().filter(|a| a.categoria == Categoria::Cartel).count(), 1);
        for b in &cat.bases {
            let a =
                b.anclajes.iter().find(|a| a.id == "cartel").unwrap_or_else(|| panic!("{}: sin anclaje cartel", b.id));
            assert_eq!(a.categorias, vec![Categoria::Cartel], "{}", b.id);
            assert_eq!(b.anclajes.iter().filter(|x| x.categorias.contains(&Categoria::Cartel)).count(), 1);
            // Adelante, centrado (en la base, o en la ventana y la fila: REQ-AMP-03) y mirando al
            // cliente (+Z), donde lo ven los de la fila.
            let centrado = a.pos[0].abs() < 1e-6 || (a.pos[0] - b.fila[0]).abs() < 1e-6;
            assert!(centrado && a.rot_y.abs() < 1e-6, "{}", b.id);
            assert!(a.pos[2] > b.profundidad / 2.0 && b.fila[2] > a.pos[2] + 0.3, "{}: adelante del carro", b.id);
            // Del canto del mostrador: el clavo entra en la losa (0,04 m abajo del mostrador).
            let clavo = a.pos[1] - 0.008;
            assert!(clavo < b.alto_mostrador && clavo > b.alto_mostrador - 0.04, "{}: {clavo}", b.id);
            // Delante del telón (si lo hay): el tablero (5 mm detrás del clavo) no lo atraviesa.
            if let Some(f) = b.anclajes.iter().find(|x| x.id == "frente") {
                assert!(a.pos[2] - 0.007 > f.pos[2] + 0.012 || f.pos[1] > a.pos[1], "{}: choca con el telón", b.id);
            }
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
            ("cartel", "cartel_cerrado"),
            ("lateral", "estante_deposito"),
        ]
        .iter()
        .map(|(a, b)| (a.to_string(), b.to_string()))
        .collect();
        c.stock =
            [("lateral".to_string(), vec![Some("bolsa_papas_5kg".to_string()), Some("pack_cajitas".to_string())])]
                .into_iter()
                .collect();
        let ids: Vec<String> = cat.bloques.iter().map(|b| b.id.clone()).collect();
        let armado = armar(&c, &cat.bases, &cat.accesorios, &ids).expect("la config con papas debería ser válida");
        assert_eq!(armado.colocados.len(), 4);
    }
}
