//! SPEC-029 · Freidora: aceite por cuba (fuente de calor), colador y papas que se fríen.

use crate::TEMP_AMBIENTE;
use crate::carrito::CubaFreidora;
use crate::coccion::Punto;
use crate::datos::DefProducto;

/// Temperatura máxima del aceite encendido (°C). REQ-FRE-04
pub const TEMP_MAX_ACEITE: f32 = 180.0;
/// Subida por segundo encendido (°C/s). REQ-FRE-04
pub const SUBIDA_POR_SEGUNDO: f32 = 2.5;
/// Qué tan rápido se enfría apagado (1/s): el aceite guarda más el calor que el agua. REQ-FRE-04
pub const K_ENFRIADO: f32 = 0.003;

/// REQ-FRE-04: el aceite de una cuba.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Aceite {
    pub temp: f32,
    pub encendida: bool,
}

impl Default for Aceite {
    fn default() -> Self {
        // REQ-FRE-04: arranca a 20 °C, apagada.
        Self { temp: TEMP_AMBIENTE, encendida: false }
    }
}

impl Aceite {
    /// REQ-FRE-05
    pub fn alternar(&mut self) {
        self.encendida = !self.encendida;
    }

    /// REQ-FRE-04
    pub fn paso(&mut self, dt: f32) {
        if self.encendida {
            self.temp = (self.temp + SUBIDA_POR_SEGUNDO * dt).min(TEMP_MAX_ACEITE);
        } else {
            self.temp += (TEMP_AMBIENTE - self.temp) * (K_ENFRIADO * dt).min(1.0);
        }
    }

    /// REQ-FRE-05: texto del cartel de la cuba (`n` = número de cuba, si hay más de una).
    pub fn cartel(&self, n: Option<usize>) -> String {
        let accion = if self.encendida { "Apagar" } else { "Encender" };
        let cuba = n.map(|i| format!(" {i}")).unwrap_or_default();
        format!("[E] {accion} freidora{cuba} — aceite a {:.0} °C", self.temp)
    }
}

/// REQ-FRE-06: el volumen de aceite de una cuba (centro y medidas), relativo al accesorio.
pub fn volumen_aceite(cuba: &CubaFreidora) -> ([f32; 3], [f32; 3]) {
    let [x, y, z] = cuba.centro;
    (([x, y + cuba.interior[1] / 2.0, z]), cuba.interior)
}

/// Producto que hace de colador. REQ-FRE-07
pub const COLADOR: &str = "colador_freidora";
/// Porciones que entran en un colador. REQ-FRE-07
pub const PORCIONES_COLADOR: usize = 2;
/// Lo que se pone en el colador: las papas cortadas o fritas. REQ-FRE-07
pub const VAN_AL_COLADOR: [&str; 2] = ["papa_cortada", "papas_fritas"];
/// Espacio entre el piso del canasto y lo que tiene adentro (m).
const HOLGURA: f32 = 0.004;

/// REQ-FRE-07
pub fn va_al_colador(producto: &str) -> bool {
    VAN_AL_COLADOR.contains(&producto)
}

/// REQ-FRE-07: por qué no se puede meter algo en el colador.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NoEntra {
    NoVa,
    Lleno,
}

impl NoEntra {
    pub fn mensaje(self) -> &'static str {
        match self {
            NoEntra::NoVa => "En el colador van papas",
            NoEntra::Lleno => "El colador está lleno",
        }
    }
}

/// REQ-FRE-07: si `producto` entra en un colador que ya tiene `porciones`.
pub fn puede_meter(producto: &str, porciones: usize) -> Result<(), NoEntra> {
    if !va_al_colador(producto) {
        Err(NoEntra::NoVa)
    } else if porciones >= PORCIONES_COLADOR {
        Err(NoEntra::Lleno)
    } else {
        Ok(())
    }
}

/// REQ-FRE-07: dónde va la porción `i` dentro del canasto (medidas ancho, alto, fondo; centrado
/// en el origen del colador): en fila a lo largo del fondo, apoyada en el piso.
pub fn lugar_en_colador(i: usize, canasto: [f32; 3], alto: f32) -> [f32; 3] {
    let n = PORCIONES_COLADOR as f32;
    let paso = canasto[2] / n;
    [0.0, -canasto[1] / 2.0 + alto / 2.0 + HOLGURA, (i as f32 - (n - 1.0) / 2.0) * paso]
}

/// REQ-FRE-08: altura del origen del colador (relativa al accesorio) en la cuba. Arriba es
/// donde lo apoya el modelo (`arriba`, el de los datos): el canasto encima del aceite. Abajo,
/// el canasto casi toca el piso de la cuba y queda dentro del aceite.
pub fn altura_colador(cuba: &CubaFreidora, canasto: [f32; 3], arriba: f32, abajo: bool) -> f32 {
    if abajo { cuba.centro[1] + canasto[1] / 2.0 + HOLGURA } else { arriba }
}

/// REQ-FRE-10: en qué se convierte el alimento al llegar a este punto (la papa cortada, en
/// papas fritas al quedar Cocida). La regla está en los datos (`al_cocerse`).
pub fn reemplazo_al_cocerse(def: &DefProducto, punto: Punto) -> Option<&str> {
    match punto {
        Punto::Crudo => None,
        _ => def.al_cocerse.as_deref(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::carrito::Funcion;
    use crate::coccion::{EstadoCoccion, PerfilCoccion};
    use crate::datos::tests::catalogo_real;

    const DT: f32 = 1.0 / 60.0;

    fn perfil(id: &str) -> PerfilCoccion {
        catalogo_real().producto(id).and_then(|p| p.coccion.clone()).unwrap_or_else(|| panic!("{id} se cocina"))
    }

    fn cubas(id: &str) -> Vec<CubaFreidora> {
        let cat = catalogo_real();
        match &cat.accesorios.iter().find(|a| a.id == id).unwrap().funcion {
            Some(Funcion::Freidora { cubas, .. }) => cubas.clone(),
            otra => panic!("{id} es {otra:?}"),
        }
    }

    #[test]
    fn req_fre_04_arranca_a_20_y_sube_2_5_por_segundo_hasta_180() {
        let mut a = Aceite::default();
        assert_eq!(a.temp, 20.0);
        assert!(!a.encendida);
        a.alternar();
        a.paso(10.0);
        assert!((a.temp - 45.0).abs() < 1e-4);
        // De 20 a 180 °C tarda ~64 s (CA-FRE-02: «en ~1 min llega a 180 °C»).
        let mut t = 10.0;
        while a.temp < TEMP_MAX_ACEITE {
            a.paso(DT);
            t += DT;
        }
        assert!((t - 64.0).abs() < 0.5, "{t}");
        for _ in 0..100 {
            a.paso(1.0);
        }
        assert_eq!(a.temp, 180.0);
    }

    #[test]
    fn req_fre_04_apagada_se_enfria_de_a_poco_hacia_el_ambiente() {
        let mut a = Aceite { temp: 180.0, encendida: false };
        a.paso(1.0);
        assert!(a.temp < 180.0 && a.temp > 179.0);
        for _ in 0..20_000 {
            a.paso(1.0);
        }
        assert!((a.temp - 20.0).abs() < 0.5);
    }

    #[test]
    fn req_fre_05_cada_cuba_se_prende_sola_y_tiene_su_cartel() {
        let mut cubas = [Aceite::default(), Aceite::default()];
        cubas[1].alternar();
        for c in &mut cubas {
            c.paso(4.0);
        }
        assert_eq!(cubas[0].temp, 20.0);
        assert_eq!(cubas[1].temp, 30.0);
        assert_eq!(cubas[0].cartel(None), "[E] Encender freidora — aceite a 20 °C");
        assert_eq!(cubas[1].cartel(Some(2)), "[E] Apagar freidora 2 — aceite a 30 °C");
    }

    #[test]
    fn req_fre_06_el_volumen_de_aceite_llena_la_cuba_hasta_el_nivel() {
        for id in ["freidora", "freidora_doble"] {
            for c in cubas(id) {
                let (centro, medidas) = volumen_aceite(&c);
                assert_eq!(medidas, c.interior);
                assert!((centro[1] - medidas[1] / 2.0 - c.centro[1]).abs() < 1e-6, "{id}: parte del piso");
            }
        }
        // REQ-FRE-06: la freidora sigue trayendo un colador por cuba.
        let cat = catalogo_real();
        for id in ["freidora", "freidora_doble"] {
            let f = cat.accesorios.iter().find(|a| a.id == id).unwrap().funcion.clone().unwrap();
            let Funcion::Freidora { cubas, objetos } = &f else { unreachable!() };
            assert_eq!(objetos.iter().filter(|o| o.producto == COLADOR).count(), cubas.len(), "{id}");
        }
    }

    #[test]
    fn req_fre_07_entran_dos_porciones_de_papas() {
        assert_eq!(puede_meter("papa_cortada", 0), Ok(()));
        assert_eq!(puede_meter("papas_fritas", 1), Ok(()));
        assert_eq!(puede_meter("papa_cortada", 2), Err(NoEntra::Lleno));
        assert_eq!(puede_meter("salchicha", 0), Err(NoEntra::NoVa));
        assert_eq!(NoEntra::Lleno.mensaje(), "El colador está lleno");
        // Las dos porciones entran en el canasto sin pisarse ni salirse.
        let cat = catalogo_real();
        let canasto = match cat.producto(COLADOR).unwrap().colision {
            crate::datos::Colision::Caja { medidas } => medidas,
            _ => panic!("el colador es una caja"),
        };
        for id in VAN_AL_COLADOR {
            let [x, y, z] = match cat.producto(id).unwrap().colision {
                crate::datos::Colision::Caja { medidas } => medidas,
                _ => panic!("{id} es una caja"),
            };
            let a = lugar_en_colador(0, canasto, y);
            let b = lugar_en_colador(1, canasto, y);
            assert!((b[2] - a[2]).abs() >= z && (a[2] - z / 2.0) >= -canasto[2] / 2.0, "{id}: a lo largo");
            assert!(x <= canasto[0] && a[1] - y / 2.0 >= -canasto[1] / 2.0, "{id}: adentro");
        }
    }

    #[test]
    fn req_fre_08_bajado_las_papas_quedan_en_el_aceite_y_subido_encima() {
        let cat = catalogo_real();
        let canasto = match cat.producto(COLADOR).unwrap().colision {
            crate::datos::Colision::Caja { medidas } => medidas,
            _ => panic!(),
        };
        let alto_papa = 0.034;
        for id in ["freidora", "freidora_doble"] {
            let f = cat.accesorios.iter().find(|a| a.id == id).unwrap().funcion.clone().unwrap();
            let Funcion::Freidora { cubas, objetos } = &f else { unreachable!() };
            for (c, o) in cubas.iter().zip(objetos) {
                let (centro, medidas) = volumen_aceite(c);
                let techo = centro[1] + medidas[1] / 2.0;
                let papa = |abajo: bool| {
                    altura_colador(c, canasto, o.pos[1], abajo) + lugar_en_colador(0, canasto, alto_papa)[1]
                };
                // Abajo, la papa entera dentro del aceite; arriba (como viene), entera encima.
                assert!(papa(true) + alto_papa / 2.0 < techo && papa(true) - alto_papa / 2.0 > c.centro[1], "{id}");
                assert!(papa(false) - alto_papa / 2.0 > techo, "{id}: arriba escurre");
                assert_eq!(altura_colador(c, canasto, o.pos[1], false), o.pos[1], "arranca arriba, donde lo trae");
            }
        }
    }

    /// Simula en aceite a `temp` hasta llegar al punto pedido. Pasa a papas fritas al quedar
    /// Cocida (REQ-FRE-10), con el perfil de las fritas.
    fn segundos_hasta(temp: f32, objetivo: Punto, max_s: f32) -> Option<f32> {
        let cat = catalogo_real();
        let mut def = cat.producto("papa_cortada").unwrap();
        let mut e = EstadoCoccion::default();
        let mut t = 0.0;
        while t < max_s {
            let p = def.coccion.as_ref().unwrap();
            e.paso(p, temp, DT);
            t += DT;
            let punto = e.punto(p);
            if let Some(otro) = reemplazo_al_cocerse(def, punto) {
                def = cat.producto(otro).unwrap();
            }
            if punto == objetivo {
                return Some(t);
            }
        }
        None
    }

    #[test]
    fn req_fre_09_papas_en_aceite_a_180() {
        let cocida = segundos_hasta(180.0, Punto::Cocido, 600.0).expect("nunca se cocinó");
        assert!((60.0..=120.0).contains(&cocida), "cocida a los {cocida} s");
        let pasada = segundos_hasta(180.0, Punto::Pasado, 600.0).expect("nunca se pasó");
        assert!((130.0..=180.0).contains(&pasada), "pasada a los {pasada} s");
        let quemada = segundos_hasta(180.0, Punto::Quemado, 900.0).expect("nunca se quemó");
        assert!(quemada > 200.0 && quemada > pasada, "quemada a los {quemada} s");
        // Con el aceite más frío no se quema (y siempre después de pasarse).
        for t in [140.0, 160.0, 170.0] {
            let q = segundos_hasta(t, Punto::Quemado, 900.0);
            let p = segundos_hasta(t, Punto::Pasado, 900.0);
            assert!(q.is_none() || q > p, "{t} °C");
        }
    }

    #[test]
    fn req_fre_09_color_palido_dorado_marron_casi_negro() {
        let p = perfil("papa_cortada");
        let brillo = |c: [f32; 3]| c[0] + c[1] + c[2];
        let mut e = EstadoCoccion::default();
        let palido = e.color(&p);
        e.avance = p.punto;
        let dorado = e.color(&p);
        e.avance = (p.punto + p.pasado) / 2.0;
        let medio = e.color(&p);
        e.avance = p.pasado;
        let marron = e.color(&p);
        e.quemado = true;
        let negro = e.color(&p);
        assert!(brillo(palido) > brillo(dorado) && brillo(dorado) > brillo(medio) && brillo(medio) > brillo(marron));
        assert!(brillo(negro) < 0.4, "casi negro");
        // Dorado: más rojo que azul; pálido: más claro.
        assert!(dorado[0] - dorado[2] > 0.5 && palido[2] > dorado[2]);
    }

    #[test]
    fn req_fre_10_la_cortada_se_vuelve_fritas_al_quedar_cocida_y_sigue_igual() {
        let cat = catalogo_real();
        let cortada = cat.producto("papa_cortada").unwrap();
        let fritas = cat.producto("papas_fritas").unwrap();
        assert_eq!(reemplazo_al_cocerse(cortada, Punto::Crudo), None);
        assert_eq!(reemplazo_al_cocerse(cortada, Punto::Cocido), Some("papas_fritas"));
        assert_eq!(reemplazo_al_cocerse(fritas, Punto::Cocido), None, "las fritas ya no cambian");
        // Mismo perfil: con el mismo estado sigue cocinándose y se ve igual.
        assert_eq!(cortada.coccion, fritas.coccion);
        assert!(!fritas.por_lados && !cortada.por_lados);
    }
}
