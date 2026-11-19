//! SPEC-029 · Pelar y cortar (REQ-FRE-01..03): un producto se prepara a mano con una
//! herramienta, una pasada por cada E; tras la última pasa a ser otro producto.
//! Qué herramienta, cuántas pasadas y qué sale, lo dicen los datos (`preparar` del producto).

use serde::Deserialize;

use crate::datos::DefProducto;

/// REQ-FRE-03: cómo se prepara un producto (campo `preparar` de `productos.ron`).
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Preparacion {
    /// Texto del cartel, ej. "Pelar papa".
    pub accion: String,
    /// Producto que hay que tener en la mano (`pelapapas`, `cuchillo`).
    pub herramienta: String,
    /// E que hacen falta.
    pub pasadas: u32,
    /// Producto que sale, en el mismo lugar.
    pub resultado: String,
}

/// Qué pasa al apretar E sobre un producto que se prepara.
#[derive(Debug, Clone, PartialEq)]
pub enum Pasada {
    /// REQ-FRE-03: sin la herramienta (o si alguien lo sostiene), nada.
    Nada,
    /// Una pasada más: quedan hechas estas.
    Avanza(u32),
    /// REQ-FRE-01, REQ-FRE-02: fue la última; se reemplaza por este producto.
    Lista(String),
}

impl Preparacion {
    fn tiene_herramienta(&self, en_mano: Option<&str>) -> bool {
        en_mano == Some(self.herramienta.as_str())
    }

    /// REQ-FRE-01..03: una E con `en_mano` sobre el producto con `hechas` pasadas.
    /// Solo cuenta si está apoyado (nadie lo sostiene).
    pub fn pasar(&self, hechas: u32, en_mano: Option<&str>, sostenido: bool) -> Pasada {
        if sostenido || !self.tiene_herramienta(en_mano) {
            return Pasada::Nada;
        }
        let hechas = hechas + 1;
        if hechas >= self.pasadas { Pasada::Lista(self.resultado.clone()) } else { Pasada::Avanza(hechas) }
    }

    /// REQ-FRE-01, REQ-FRE-03: cartel al mirar el producto: el avance con la herramienta
    /// («[E] Pelar papa (1/3)») o cuál hace falta («Necesitás el pelapapas»).
    /// `nombre_herramienta` es el nombre para mostrar de la herramienta.
    pub fn cartel(&self, hechas: u32, en_mano: Option<&str>, nombre_herramienta: &str) -> String {
        if self.tiene_herramienta(en_mano) {
            format!("[E] {} ({hechas}/{})", self.accion, self.pasadas)
        } else {
            format!("Necesitás el {nombre_herramienta}")
        }
    }
}

/// REQ-FRE-03: al cargar, la herramienta y el resultado de cada preparación existen y hay al
/// menos una pasada. Devuelve el mensaje de error con los ids.
pub fn validar(productos: &[DefProducto]) -> Result<(), String> {
    let existe = |id: &str| productos.iter().any(|p| p.id == id);
    for p in productos {
        let Some(prep) = &p.preparar else { continue };
        if !existe(&prep.herramienta) {
            return Err(format!("\"{}\" se prepara con la herramienta inexistente \"{}\"", p.id, prep.herramienta));
        }
        if !existe(&prep.resultado) {
            return Err(format!("\"{}\" se prepara en el producto inexistente \"{}\"", p.id, prep.resultado));
        }
        if prep.pasadas == 0 {
            return Err(format!("\"{}\" se prepara con 0 pasadas", p.id));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::datos::tests::catalogo_real;

    fn prep(id: &str) -> Preparacion {
        catalogo_real().producto(id).and_then(|p| p.preparar.clone()).unwrap_or_else(|| panic!("{id} se prepara"))
    }

    /// Aprieta E `n` veces con `en_mano`, como el jugador; devuelve lo último que pasó.
    fn apretar(p: &Preparacion, hechas: &mut u32, en_mano: Option<&str>, n: u32) -> Pasada {
        let mut ultima = Pasada::Nada;
        for _ in 0..n {
            ultima = p.pasar(*hechas, en_mano, false);
            if let Pasada::Avanza(h) = ultima {
                *hechas = h;
            }
        }
        ultima
    }

    #[test]
    fn req_fre_01_tres_pasadas_de_pelapapas_pelan_la_papa() {
        let p = prep("papa_cruda");
        let mut hechas = 0;
        assert_eq!(p.cartel(hechas, Some("pelapapas"), "pelapapas"), "[E] Pelar papa (0/3)");
        assert_eq!(apretar(&p, &mut hechas, Some("pelapapas"), 1), Pasada::Avanza(1));
        assert_eq!(p.cartel(hechas, Some("pelapapas"), "pelapapas"), "[E] Pelar papa (1/3)");
        assert_eq!(apretar(&p, &mut hechas, Some("pelapapas"), 1), Pasada::Avanza(2));
        assert_eq!(apretar(&p, &mut hechas, Some("pelapapas"), 1), Pasada::Lista("papa_pelada".into()));
    }

    #[test]
    fn req_fre_01_si_alguien_la_sostiene_no_se_pela() {
        let p = prep("papa_cruda");
        assert_eq!(p.pasar(2, Some("pelapapas"), true), Pasada::Nada);
    }

    #[test]
    fn req_fre_02_cuatro_pasadas_de_cuchillo_cortan_la_papa_pelada() {
        let p = prep("papa_pelada");
        let mut hechas = 0;
        assert_eq!(apretar(&p, &mut hechas, Some("cuchillo"), 3), Pasada::Avanza(3));
        assert_eq!(p.cartel(hechas, Some("cuchillo"), "cuchillo"), "[E] Cortar papa (3/4)");
        assert_eq!(apretar(&p, &mut hechas, Some("cuchillo"), 1), Pasada::Lista("papa_cortada".into()));
        // Lo que sale ya no se prepara más (se fríe: REQ-FRE-09).
        let cat = catalogo_real();
        assert!(cat.producto("papa_cortada").unwrap().preparar.is_none());
    }

    #[test]
    fn req_fre_03_sin_la_herramienta_no_pasa_nada_y_el_cartel_dice_cual() {
        let p = prep("papa_cruda");
        for en_mano in [None, Some("cuchillo"), Some("salchicha")] {
            assert_eq!(p.pasar(1, en_mano, false), Pasada::Nada, "{en_mano:?}");
            assert_eq!(p.cartel(1, en_mano, "pelapapas"), "Necesitás el pelapapas");
        }
        // El pelapapas no corta: la pelada pide el cuchillo.
        assert_eq!(prep("papa_pelada").pasar(0, Some("pelapapas"), false), Pasada::Nada);
    }

    #[test]
    fn req_fre_03_las_pasadas_hechas_se_conservan() {
        // Las pasadas son del producto (no del lugar ni de la herramienta): con una herramienta
        // equivocada en el medio, se sigue desde donde quedó.
        let p = prep("papa_cruda");
        let mut hechas = 0;
        apretar(&p, &mut hechas, Some("pelapapas"), 2);
        apretar(&p, &mut hechas, Some("cuchillo"), 5);
        assert_eq!(hechas, 2);
        assert_eq!(apretar(&p, &mut hechas, Some("pelapapas"), 1), Pasada::Lista("papa_pelada".into()));
    }

    #[test]
    fn req_fre_03_herramienta_y_resultado_salen_de_los_datos() {
        let cruda = prep("papa_cruda");
        assert_eq!((cruda.herramienta.as_str(), cruda.pasadas), ("pelapapas", 3));
        let pelada = prep("papa_pelada");
        assert_eq!((pelada.herramienta.as_str(), pelada.pasadas), ("cuchillo", 4));
        assert!(validar(&catalogo_real().productos).is_ok());
    }

    #[test]
    fn req_fre_03_herramienta_o_resultado_inexistente_da_error_con_los_ids() {
        let mut productos = catalogo_real().productos;
        let papa = productos.iter_mut().find(|p| p.id == "papa_cruda").unwrap();
        papa.preparar.as_mut().unwrap().herramienta = "rallador".into();
        let e = validar(&productos).unwrap_err();
        assert!(e.contains("\"papa_cruda\"") && e.contains("\"rallador\""), "{e}");

        let mut productos = catalogo_real().productos;
        let papa = productos.iter_mut().find(|p| p.id == "papa_pelada").unwrap();
        papa.preparar.as_mut().unwrap().resultado = "pure".into();
        let e = validar(&productos).unwrap_err();
        assert!(e.contains("\"papa_pelada\"") && e.contains("\"pure\""), "{e}");

        // Y la carga del catálogo falla con ese mensaje.
        let dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data");
        let leer = |n: &str| std::fs::read_to_string(dir.join(n)).unwrap();
        let prod = leer("productos.ron").replacen("herramienta: \"pelapapas\"", "herramienta: \"rallador\"", 1);
        assert_ne!(prod, leer("productos.ron"));
        let e = crate::datos::cargar_catalogo(&prod, "[]", "[]", &[], "", &leer("aderezos.ron"), "[]").unwrap_err();
        assert!(e.archivo == "productos.ron" && e.mensaje.contains("rallador"), "{e}");
    }
}
