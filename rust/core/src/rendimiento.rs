//! SPEC-032 · Rendimiento: cuentas de los tiempos de cada cuadro (TASK-0255).
//!
//! El nodo de Godot (`game/rendimiento.rs`) solo junta los tiempos; acá se resumen. REQ-REN-05

/// Segundos de espera antes de medir. REQ-REN-03
pub const SEGUNDOS_ESPERA: f64 = 10.0;
/// Segundos de medición. REQ-REN-03
pub const SEGUNDOS_MEDICION: f64 = 60.0;
/// Parte de los cuadros más lentos que entra en el "1% bajo". REQ-REN-04
const PARTE_BAJA: f64 = 0.01;

/// Resumen de una medición. REQ-REN-04
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Resumen {
    /// Cuadros por segundo promedio (cuadros medidos / segundos medidos).
    pub prom_fps: f64,
    /// Promedio de fps del 1% de cuadros más lentos (al menos un cuadro).
    pub bajo_1_fps: f64,
    /// El cuadro más lento, en milisegundos.
    pub peor_ms: f64,
}

/// REQ-REN-04, REQ-REN-05: resume los tiempos de cada cuadro (en segundos). Los promedios de
/// fps se sacan como cuadros / tiempo total (así un cuadro lento pesa lo que dura).
/// `None` si no hay cuadros.
pub fn resumir(tiempos: &[f64]) -> Option<Resumen> {
    let validos: Vec<f64> = tiempos.iter().copied().filter(|t| t.is_finite() && *t > 0.0).collect();
    if validos.is_empty() {
        return None;
    }
    let fps = |ts: &[f64]| ts.len() as f64 / ts.iter().sum::<f64>();
    let mut lentos = validos.clone();
    lentos.sort_by(|a, b| b.total_cmp(a));
    let n_bajo = ((validos.len() as f64 * PARTE_BAJA).ceil() as usize).max(1);
    Some(Resumen { prom_fps: fps(&validos), bajo_1_fps: fps(&lentos[..n_bajo]), peor_ms: lentos[0] * 1000.0 })
}

/// REQ-REN-04: la línea que imprime la escena al terminar.
pub fn linea(r: &Resumen, dibujos: u64, personas: usize, autos: usize) -> String {
    format!(
        "RENDIMIENTO: prom {:.0} fps · 1% bajo {:.0} fps · peor cuadro {:.0} ms · {dibujos} dibujos · {personas} personas · {autos} autos",
        r.prom_fps, r.bajo_1_fps, r.peor_ms
    )
}

/// REQ-REN-03: en qué etapa está la medición a los `segundos` de arrancar (con los tiempos de
/// espera y medición dados, que la prueba puede acortar).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Etapa {
    Esperando,
    Midiendo,
    Terminada,
}

pub fn etapa(segundos: f64, espera: f64, medicion: f64) -> Etapa {
    if segundos < espera {
        Etapa::Esperando
    } else if segundos < espera + medicion {
        Etapa::Midiendo
    } else {
        Etapa::Terminada
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_ren_05_cuadros_parejos() {
        let r = resumir(&[1.0 / 60.0; 600]).unwrap();
        assert!((r.prom_fps - 60.0).abs() < 1e-6);
        assert!((r.bajo_1_fps - 60.0).abs() < 1e-6);
        assert!((r.peor_ms - 1000.0 / 60.0).abs() < 1e-6);
    }

    #[test]
    fn req_ren_05_un_por_ciento_bajo_y_peor_cuadro() {
        // 990 cuadros de 10 ms y 10 de 40 ms: el 1% más lento son los 10 de 40 ms.
        let mut t = vec![0.010; 990];
        t.extend([0.040; 10]);
        let r = resumir(&t).unwrap();
        assert!((r.prom_fps - 1000.0 / 10.3).abs() < 1e-6, "prom {}", r.prom_fps);
        assert!((r.bajo_1_fps - 25.0).abs() < 1e-6, "1% bajo {}", r.bajo_1_fps);
        assert!((r.peor_ms - 40.0).abs() < 1e-9);
        // Con pocos cuadros entra al menos uno en el 1% bajo.
        let r = resumir(&[0.010, 0.020, 0.050]).unwrap();
        assert!((r.bajo_1_fps - 20.0).abs() < 1e-6);
    }

    #[test]
    fn req_ren_05_sin_cuadros_no_hay_resumen() {
        assert_eq!(resumir(&[]), None);
        assert_eq!(resumir(&[0.0, f64::NAN]), None);
    }

    #[test]
    fn req_ren_04_linea() {
        let r = Resumen { prom_fps: 72.4, bajo_1_fps: 54.6, peor_ms: 31.2 };
        assert_eq!(
            linea(&r, 1900, 48, 6),
            "RENDIMIENTO: prom 72 fps · 1% bajo 55 fps · peor cuadro 31 ms · 1900 dibujos · 48 personas · 6 autos"
        );
    }

    #[test]
    fn req_ren_03_espera_10_s_y_mide_60_s() {
        assert_eq!(etapa(9.9, SEGUNDOS_ESPERA, SEGUNDOS_MEDICION), Etapa::Esperando);
        assert_eq!(etapa(10.0, SEGUNDOS_ESPERA, SEGUNDOS_MEDICION), Etapa::Midiendo);
        assert_eq!(etapa(69.9, SEGUNDOS_ESPERA, SEGUNDOS_MEDICION), Etapa::Midiendo);
        assert_eq!(etapa(70.0, SEGUNDOS_ESPERA, SEGUNDOS_MEDICION), Etapa::Terminada);
    }
}
