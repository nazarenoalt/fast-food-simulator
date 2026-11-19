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
/// Porciones que entran en un colador (varias tandas). REQ-FRE-07
pub const PORCIONES_COLADOR: usize = 4;
/// Las porciones van en una grilla de 2 × 2: dos a lo ancho y dos a lo largo del canasto.
const COLUMNAS: usize = 2;
const FILAS: usize = PORCIONES_COLADOR / COLUMNAS;
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

/// REQ-FRE-07: el lugar de una porción en el canasto: centro (relativo al origen del colador)
/// y giro en Y (grados).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct LugarPorcion {
    pub pos: [f32; 3],
    pub giro_y: f32,
}

/// Medidas (ancho X, fondo Z) del cuarto del canasto que le toca a cada porción.
fn celda(canasto: [f32; 3]) -> [f32; 2] {
    [canasto[0] / COLUMNAS as f32, canasto[2] / FILAS as f32]
}

/// Centro (X, Z) del cuarto `i` del canasto: `i % 2` es la columna, `i / 2` la fila.
fn centro_celda(i: usize, canasto: [f32; 3]) -> [f32; 2] {
    let [cw, cd] = celda(canasto);
    let (col, fila) = ((i % COLUMNAS) as f32, (i / COLUMNAS) as f32);
    [-canasto[0] / 2.0 + cw * (col + 0.5), -canasto[2] / 2.0 + cd * (fila + 0.5)]
}

/// REQ-FRE-07: dónde va la porción `i` (0 a 3) dentro del canasto (medidas ancho, alto, fondo;
/// centrado en el origen del colador). Cada porción tiene su cuarto fijo (grilla de 2 × 2),
/// centrada en él, con su lado largo a lo largo del cuarto y apoyada en el piso: no se pisan, no
/// tocan las paredes y sacar una no mueve las demás. `porcion` son sus medidas (las de la
/// cortada o las de las fritas: el lugar es el mismo, solo cambia la altura).
pub fn lugar_en_colador(i: usize, canasto: [f32; 3], porcion: [f32; 3]) -> LugarPorcion {
    let [x, z] = centro_celda(i, canasto);
    let [cw, cd] = celda(canasto);
    let girada = (porcion[0] > porcion[2]) != (cw > cd);
    LugarPorcion {
        pos: [x, -canasto[1] / 2.0 + porcion[1] / 2.0 + HOLGURA, z],
        giro_y: if girada { 90.0 } else { 0.0 },
    }
}

/// Cuarto del canasto (0 a 3) en el que cae un punto (X, Z relativos al colador).
fn celda_de(punto: [f32; 2], canasto: [f32; 3]) -> usize {
    let [cw, cd] = celda(canasto);
    let col = ((punto[0] + canasto[0] / 2.0) / cw).floor().clamp(0.0, (COLUMNAS - 1) as f32) as usize;
    let fila = ((punto[1] + canasto[2] / 2.0) / cd).floor().clamp(0.0, (FILAS - 1) as f32) as usize;
    fila * COLUMNAS + col
}

/// REQ-FRE-07: en qué lugar libre va una porción nueva: el más cercano a donde toca la mira
/// (`cerca`, X y Z relativos al colador) o, sin mira, el primero libre. `None` si está lleno.
pub fn lugar_libre(ocupados: &[bool], cerca: Option<[f32; 2]>, canasto: [f32; 3]) -> Option<usize> {
    let libres = (0..PORCIONES_COLADOR).filter(|i| !ocupados.get(*i).copied().unwrap_or(false));
    match cerca {
        None => libres.min(),
        Some([px, pz]) => libres.min_by(|a, b| {
            let d = |i: usize| {
                let [x, z] = centro_celda(i, canasto);
                (x - px).powi(2) + (z - pz).powi(2)
            };
            d(*a).total_cmp(&d(*b))
        }),
    }
}

/// REQ-FRE-08: qué porción se agarra mirando el colador: la del cuarto donde toca la mira
/// (`punto`, X y Z relativos al colador), si hay una. Si ese cuarto está vacío, `None` (se
/// agarra el colador).
pub fn porcion_apuntada(punto: [f32; 2], ocupados: &[bool], canasto: [f32; 3]) -> Option<usize> {
    let i = celda_de(punto, canasto);
    ocupados.get(i).copied().unwrap_or(false).then_some(i)
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

    fn caja(id: &str) -> [f32; 3] {
        match catalogo_real().producto(id).unwrap().colision {
            crate::datos::Colision::Caja { medidas } => medidas,
            _ => panic!("{id} es una caja"),
        }
    }

    /// Huella (mitades en X y Z) de una porción en su lugar, según el giro.
    fn huella(l: &LugarPorcion, porcion: [f32; 3]) -> [f32; 2] {
        if l.giro_y == 0.0 { [porcion[0] / 2.0, porcion[2] / 2.0] } else { [porcion[2] / 2.0, porcion[0] / 2.0] }
    }

    #[test]
    fn req_fre_07_entran_cuatro_porciones_de_papas() {
        for n in 0..4 {
            assert_eq!(puede_meter("papa_cortada", n), Ok(()), "{n}");
            assert_eq!(puede_meter("papas_fritas", n), Ok(()), "{n}");
        }
        assert_eq!(puede_meter("papa_cortada", 4), Err(NoEntra::Lleno), "la 5.ª no entra");
        assert_eq!(puede_meter("salchicha", 0), Err(NoEntra::NoVa));
        assert_eq!(NoEntra::Lleno.mensaje(), "El colador está lleno");
    }

    #[test]
    fn req_fre_07_las_cuatro_entran_en_el_canasto_sin_pisarse_ni_tocar_las_paredes() {
        let canasto = caja(COLADOR);
        // El canasto del modelo es de alambre: se deja 1 cm a las paredes y entre porciones.
        let margen = 0.01;
        for id in VAN_AL_COLADOR {
            let p = caja(id);
            let lugares: Vec<LugarPorcion> = (0..PORCIONES_COLADOR).map(|i| lugar_en_colador(i, canasto, p)).collect();
            for (i, l) in lugares.iter().enumerate() {
                let [hx, hz] = huella(l, p);
                assert!(l.pos[0].abs() + hx <= canasto[0] / 2.0 - margen, "{id} {i}: a lo ancho {l:?}");
                assert!(l.pos[2].abs() + hz <= canasto[2] / 2.0 - margen, "{id} {i}: a lo largo {l:?}");
                // Apoyada en el piso del canasto, sin asomar por arriba.
                let piso = l.pos[1] - p[1] / 2.0;
                assert!(piso > -canasto[1] / 2.0 && piso < -canasto[1] / 2.0 + 0.01, "{id} {i}: en el piso");
                assert!(l.pos[1] + p[1] / 2.0 < canasto[1] / 2.0, "{id} {i}: no asoma");
                for (j, m) in lugares.iter().enumerate().skip(i + 1) {
                    let [mx, mz] = huella(m, p);
                    let separadas_x = (l.pos[0] - m.pos[0]).abs() >= hx + mx + margen;
                    let separadas_z = (l.pos[2] - m.pos[2]).abs() >= hz + mz + margen;
                    assert!(separadas_x || separadas_z, "{id}: {i} y {j} se pisan");
                }
            }
        }
        // REQ-FRE-10: al freírse, la porción queda en el mismo lugar y con el mismo giro.
        for i in 0..PORCIONES_COLADOR {
            let a = lugar_en_colador(i, canasto, caja("papa_cortada"));
            let b = lugar_en_colador(i, canasto, caja("papas_fritas"));
            assert_eq!((a.pos[0], a.pos[2], a.giro_y), (b.pos[0], b.pos[2], b.giro_y), "{i}");
        }
        // Acostadas a lo largo del canasto (su lado largo con el del canasto).
        assert_eq!(lugar_en_colador(0, canasto, caja("papa_cortada")).giro_y, 90.0);
    }

    #[test]
    fn req_fre_07_cada_tanda_va_al_lugar_libre_mas_cercano_a_la_mira() {
        let canasto = caja(COLADOR);
        let p = caja("papa_cortada");
        let xz = |i: usize| {
            let l = lugar_en_colador(i, canasto, p);
            [l.pos[0], l.pos[2]]
        };
        assert_eq!(lugar_libre(&[false; 4], None, canasto), Some(0));
        assert_eq!(lugar_libre(&[true, false, false, false], None, canasto), Some(1));
        for i in 0..4 {
            assert_eq!(lugar_libre(&[false; 4], Some(xz(i)), canasto), Some(i), "apuntando al lugar {i}");
        }
        // Apuntando a un lugar ocupado, va al libre más cercano (el de al lado, no el de enfrente).
        assert_eq!(
            lugar_libre(&[true, false, false, false], Some(xz(0)), canasto).map(|i| i == 1 || i == 2),
            Some(true)
        );
        assert_eq!(lugar_libre(&[true; 4], Some(xz(0)), canasto), None, "lleno");
        // Sacar una deja su lugar libre y las otras no se mueven (cada lugar es fijo).
        assert_eq!(lugar_libre(&[true, true, false, true], None, canasto), Some(2));
    }

    #[test]
    fn req_fre_07_cada_porcion_se_frie_a_su_ritmo() {
        // Una tanda nueva arranca cruda mientras la otra sigue: cada una lleva su propia cocción.
        let p = perfil("papa_cortada");
        let (mut primera, mut segunda) = (EstadoCoccion::default(), EstadoCoccion::default());
        let mut t = 0.0;
        while primera.punto(&p) == Punto::Crudo {
            primera.paso(&p, 180.0, DT);
            if t >= 30.0 {
                segunda.paso(&p, 180.0, DT);
            }
            t += DT;
        }
        assert_eq!(segunda.punto(&p), Punto::Crudo, "la segunda (30 s después) sigue cruda a los {t:.0} s");
        assert!(segunda.avance > 0.0, "pero ya se está friendo");
        // Sacar la primera no frena a la segunda.
        while segunda.punto(&p) == Punto::Crudo {
            segunda.paso(&p, 180.0, DT);
            t += DT;
        }
        assert!(t < 200.0);
    }

    #[test]
    fn req_fre_08_se_agarra_la_porcion_del_cuarto_que_mira() {
        let canasto = caja(COLADOR);
        let p = caja("papas_fritas");
        let ocupados = [true, false, true, true];
        for i in 0..4 {
            let l = lugar_en_colador(i, canasto, p);
            // En el centro de la porción o cerca del borde de su cuarto: esa porción, si está.
            for (dx, dz) in [(0.0, 0.0), (0.03, -0.05), (-0.03, 0.05)] {
                let punto = [l.pos[0] + dx, l.pos[2] + dz];
                let esperado = ocupados[i].then_some(i);
                assert_eq!(porcion_apuntada(punto, &ocupados, canasto), esperado, "{i} {punto:?}");
            }
        }
        // Mirando el cuarto vacío (o el colador vacío) se agarra el colador.
        assert_eq!(porcion_apuntada([0.05, -0.07], &[false; 4], canasto), None);
        // Fuera del canasto (el borde o la pared), cuenta el cuarto más cercano.
        assert_eq!(porcion_apuntada([-0.2, 0.3], &[true; 4], canasto), Some(2));
    }

    #[test]
    fn req_fre_08_bajado_las_papas_quedan_en_el_aceite_y_subido_encima() {
        let cat = catalogo_real();
        let canasto = caja(COLADOR);
        let papa = caja("papas_fritas");
        let alto_papa = papa[1];
        for id in ["freidora", "freidora_doble"] {
            let f = cat.accesorios.iter().find(|a| a.id == id).unwrap().funcion.clone().unwrap();
            let Funcion::Freidora { cubas, objetos } = &f else { unreachable!() };
            for (c, o) in cubas.iter().zip(objetos) {
                let (centro, medidas) = volumen_aceite(c);
                let techo = centro[1] + medidas[1] / 2.0;
                let papa = |abajo: bool| {
                    altura_colador(c, canasto, o.pos[1], abajo) + lugar_en_colador(0, canasto, papa).pos[1]
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
