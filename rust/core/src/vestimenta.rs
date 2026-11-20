//! SPEC-018 · Ropa según perfil y hora (REQ-RUT-10) y actividades según la hora (REQ-RUT-11).
//! (TASK-0507)

use std::sync::LazyLock;

use crate::peatones::{Paleta, Plan};
use crate::plaza::{TipoProp, distribucion};
use crate::reloj::Sol;
use crate::rutinas::Perfil;

/// REQ-RUT-10: de 7 a 20 se viste de día (manga corta, colores claros).
pub const DESDE_ROPA_DE_DIA: f32 = 7.0;
/// REQ-RUT-10: de 20 a 7 se viste de noche (campera o buzo, colores oscuros).
pub const DESDE_ROPA_DE_NOCHE: f32 = 20.0;
/// REQ-RUT-11: de 20 a 6 nadie trota.
pub const TROTE: [f32; 2] = [6.0, 20.0];
/// REQ-RUT-11: de 22 a 24 nadie pasea al perro.
pub const SIN_PERRO_DESDE: f32 = 22.0;
/// REQ-RUT-11: de noche solo se sientan a menos de esto de un farol (m).
pub const CERCA_DE_FAROL: f32 = 6.0;

type Color = [f32; 3];

/// Pieles y pelos: siempre variados, de día y de noche.
const PIELES: [Color; 6] = [
    [0.96, 0.8, 0.68],
    [0.87, 0.67, 0.5],
    [0.78, 0.58, 0.42],
    [0.66, 0.47, 0.33],
    [0.52, 0.36, 0.24],
    [0.38, 0.26, 0.18],
];
const PELOS: [Color; 8] = [
    [0.08, 0.06, 0.05],
    [0.3, 0.2, 0.1],
    [0.55, 0.4, 0.2],
    [0.85, 0.75, 0.5],
    [0.6, 0.6, 0.6],
    [0.6, 0.25, 0.1],
    [0.18, 0.11, 0.07],
    [0.92, 0.9, 0.86],
];

/// De día: remeras claras.
const REMERAS_DIA: [Color; 12] = [
    [0.95, 0.95, 0.92], // blanco
    [0.98, 0.85, 0.4],  // amarillo claro
    [0.6, 0.8, 0.95],   // celeste
    [0.95, 0.7, 0.75],  // rosa
    [0.7, 0.9, 0.6],    // verde claro
    [0.98, 0.75, 0.5],  // durazno
    [0.8, 0.7, 0.9],    // lila
    [0.85, 0.8, 0.6],   // beige
    [0.75, 0.77, 0.8],  // gris claro
    [0.5, 0.85, 0.8],   // aguamarina
    [0.95, 0.6, 0.45],  // coral
    [0.55, 0.7, 0.95],  // azul claro
];
const PANTALONES_DIA: [Color; 8] = [
    [0.35, 0.45, 0.6],  // jean
    [0.45, 0.55, 0.7],  // jean gastado
    [0.75, 0.68, 0.55], // beige
    [0.6, 0.55, 0.4],   // caqui
    [0.65, 0.66, 0.68], // gris claro
    [0.9, 0.88, 0.84],  // blanco
    [0.55, 0.58, 0.42], // verde oliva claro
    [0.25, 0.35, 0.55], // jean medio
];
const GORRAS_DIA: [Color; 7] = [
    [0.8, 0.15, 0.15],
    [0.12, 0.2, 0.5],
    [0.1, 0.1, 0.1],
    [0.95, 0.95, 0.95],
    [0.2, 0.5, 0.25],
    [0.95, 0.7, 0.1],
    [0.45, 0.6, 0.8],
];

/// De noche: camperas y buzos oscuros.
const CAMPERAS_NOCHE: [Color; 12] = [
    [0.12, 0.12, 0.14], // negro
    [0.15, 0.2, 0.35],  // azul marino
    [0.3, 0.32, 0.35],  // gris oscuro
    [0.35, 0.12, 0.15], // bordó
    [0.15, 0.3, 0.2],   // verde oscuro
    [0.35, 0.25, 0.18], // marrón
    [0.3, 0.18, 0.35],  // violeta oscuro
    [0.1, 0.25, 0.3],   // petróleo
    [0.35, 0.33, 0.22], // oliva
    [0.22, 0.22, 0.25], // grafito
    [0.45, 0.2, 0.1],   // óxido
    [0.2, 0.15, 0.3],   // berenjena
];
const PANTALONES_NOCHE: [Color; 6] = [
    [0.1, 0.12, 0.2],   // jean oscuro
    [0.15, 0.15, 0.17], // negro
    [0.2, 0.2, 0.22],   // gris carbón
    [0.25, 0.22, 0.18], // marrón oscuro
    [0.12, 0.18, 0.3],  // azul
    [0.22, 0.25, 0.2],  // verde oscuro
];
const GORROS_NOCHE: [Color; 4] = [[0.1, 0.1, 0.1], [0.15, 0.2, 0.35], [0.35, 0.12, 0.15], [0.3, 0.32, 0.35]];

/// Oficinistas: camisa clara y pantalón oscuro, sin gorra.
const CAMISAS: [Color; 5] = [
    [0.97, 0.97, 0.95], // blanco
    [0.92, 0.91, 0.86], // hueso
    [0.72, 0.85, 0.95], // celeste
    [0.82, 0.9, 0.97],  // celeste pálido
    [0.8, 0.81, 0.83],  // gris claro
];
const PANTALONES_OFICINA: [Color; 5] = [
    [0.1, 0.12, 0.2],   // azul marino
    [0.15, 0.15, 0.17], // negro
    [0.25, 0.26, 0.28], // gris oscuro
    [0.2, 0.16, 0.12],  // marrón oscuro
    [0.12, 0.15, 0.25], // azul
];

/// Salida nocturna: colores fuertes.
const FUERTES: [Color; 9] = [
    [0.85, 0.1, 0.15],  // rojo
    [0.1, 0.3, 0.9],    // azul eléctrico
    [0.1, 0.7, 0.3],    // verde
    [0.85, 0.15, 0.6],  // fucsia
    [0.95, 0.45, 0.05], // naranja
    [0.95, 0.8, 0.1],   // amarillo
    [0.5, 0.15, 0.8],   // violeta
    [0.05, 0.65, 0.7],  // turquesa
    [0.7, 0.05, 0.3],   // magenta oscuro
];

/// Corredores: ropa deportiva de colores vivos y calzas.
const DEPORTIVAS: [Color; 8] = [
    [0.85, 0.95, 0.1], // amarillo flúor
    [0.95, 0.4, 0.1],  // naranja
    [0.1, 0.75, 0.9],  // cian
    [0.95, 0.2, 0.55], // fucsia
    [0.4, 0.9, 0.2],   // lima
    [0.9, 0.15, 0.15], // rojo
    [0.2, 0.4, 0.95],  // azul
    [0.6, 0.2, 0.9],   // violeta
];
const CALZAS: [Color; 5] = [[0.1, 0.1, 0.12], [0.2, 0.22, 0.3], [0.15, 0.2, 0.4], [0.4, 0.42, 0.45], [0.25, 0.12, 0.3]];
const VISERAS: [Color; 4] = [[0.95, 0.95, 0.95], [0.1, 0.1, 0.1], [0.95, 0.4, 0.1], [0.1, 0.75, 0.9]];

/// REQ-RUT-10: ¿a esa hora se viste de día (7 a 20)?
pub fn ropa_de_dia(hora: f32) -> bool {
    (DESDE_ROPA_DE_DIA..DESDE_ROPA_DE_NOCHE).contains(&hora.rem_euclid(24.0))
}

fn paleta_con(remeras: &[Color], pantalones: &[Color], gorras: &[Color], chance_gorra: f32, manga: bool) -> Paleta {
    Paleta {
        pieles: PIELES.to_vec(),
        remeras: remeras.to_vec(),
        pantalones: pantalones.to_vec(),
        pelos: PELOS.to_vec(),
        gorras: gorras.to_vec(),
        chance_gorra,
        altura: [1.55, 1.9],
        manga_larga: if manga { 1.0 } else { 0.0 },
    }
}

/// REQ-RUT-10: de qué paleta se viste alguien de ese perfil a esa hora (0–24).
/// De 7 a 20, manga corta y colores claros; de 20 a 7, campera o buzo de manga larga y
/// colores oscuros. Oficinistas con camisa clara y pantalón oscuro; nocturnos con colores
/// fuertes; corredores con ropa deportiva; trasnochados y nocturnos siempre abrigados.
/// REQ-AMB-16 vale dentro de cada paleta (ver tests).
pub fn paleta(perfil: Perfil, hora: f32) -> Paleta {
    let dia = ropa_de_dia(hora);
    match perfil {
        Perfil::Oficinista => paleta_con(&CAMISAS, &PANTALONES_OFICINA, &[], 0.0, !dia),
        Perfil::Corredor => paleta_con(&DEPORTIVAS, &CALZAS, &VISERAS, 0.4, !dia),
        Perfil::Nocturno => {
            paleta_con(&FUERTES, &PANTALONES_NOCHE, &[FUERTES[0], FUERTES[1], [0.1, 0.1, 0.1]], 0.3, true)
        }
        Perfil::Trasnochado => paleta_con(&CAMPERAS_NOCHE, &PANTALONES_NOCHE, &GORROS_NOCHE, 0.3, true),
        _ if dia => paleta_con(&REMERAS_DIA, &PANTALONES_DIA, &GORRAS_DIA, 0.3, false),
        _ => paleta_con(&CAMPERAS_NOCHE, &PANTALONES_NOCHE, &GORROS_NOCHE, 0.25, true),
    }
}

/// REQ-RUT-11: ¿alguien de ese perfil puede hacer esa actividad a esa hora?
/// De 20 a 6 nadie trota; de 22 a 24 nadie pasea al perro (de madrugada sí).
/// (Que después de las 21 no haya chicos lo resuelven los grupos, TASK-0503.)
pub fn plan_permitido(_perfil: Perfil, plan: Plan, hora: f32) -> bool {
    let h = hora.rem_euclid(24.0);
    match plan {
        Plan::Trotar => (TROTE[0]..TROTE[1]).contains(&h),
        Plan::PasearPerro => h < SIN_PERRO_DESDE,
        _ => true,
    }
}

/// Posiciones (x, z) de los faroles de la plaza y la vereda (REQ-MUN-02).
pub fn faroles() -> &'static [[f32; 2]] {
    static FAROLES: LazyLock<Vec<[f32; 2]>> =
        LazyLock::new(|| distribucion().iter().filter(|p| p.tipo == TipoProp::Farol).map(|p| [p.x, p.z]).collect());
    &FAROLES
}

/// REQ-DIA-06: ¿a esa hora (0–24) es de noche (sol a menos de 3° sobre el horizonte)?
pub fn es_de_noche(hora: f32) -> bool {
    Sol::en(hora.rem_euclid(24.0) as f64 * 60.0).es_de_noche()
}

/// REQ-RUT-11: ¿se puede sentar alguien en el asiento de la red que está en `asiento` (x, z)
/// a esa hora? De noche (REQ-DIA-06), solo a menos de 6 m de un farol; de día, en todos.
pub fn asiento_permitido(asiento: [f32; 2], hora: f32) -> bool {
    !es_de_noche(hora) || faroles().iter().any(|f| (f[0] - asiento[0]).hypot(f[1] - asiento[1]) < CERCA_DE_FAROL)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::azar::Azar;
    use crate::caminos::{TipoNodo, red};
    use crate::peatones::{Apariencia, MEMORIA_IDAS, Variedad, apariencia_de};

    const HORAS: [f32; 8] = [2.0, 6.5, 8.0, 13.0, 17.5, 19.9, 21.0, 23.5];

    fn luminancia(c: Color) -> f32 {
        0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    }

    fn saturacion(c: Color) -> f32 {
        let max = c[0].max(c[1]).max(c[2]);
        let min = c[0].min(c[1]).min(c[2]);
        (max - min) / max
    }

    /// Los perfiles que se visten "como todos" (sin ropa propia del perfil).
    fn comunes() -> impl Iterator<Item = Perfil> {
        Perfil::TODOS
            .into_iter()
            .filter(|p| !matches!(p, Perfil::Oficinista | Perfil::Corredor | Perfil::Nocturno | Perfil::Trasnochado))
    }

    fn vestidos(perfil: Perfil, hora: f32, n: usize) -> Vec<Apariencia> {
        let mut a = Azar::new(10);
        let p = paleta(perfil, hora);
        (0..n).map(|_| apariencia_de(&mut a, &p)).collect()
    }

    #[test]
    fn req_rut_10_de_dia_manga_corta_y_colores_claros() {
        for perfil in comunes() {
            for hora in [7.0, 9.0, 13.0, 17.5, 19.9] {
                let p = paleta(perfil, hora);
                assert_eq!(p.manga_larga, 0.0, "{perfil:?} a las {hora}");
                assert!(p.remeras.iter().all(|c| luminancia(*c) >= 0.5), "{perfil:?} a las {hora}: remera oscura");
                assert!(vestidos(perfil, hora, 30).iter().all(|a| !a.manga_larga));
            }
        }
    }

    #[test]
    fn req_rut_10_de_noche_manga_larga_y_colores_oscuros() {
        for perfil in comunes().chain([Perfil::Trasnochado]) {
            for hora in [20.0, 22.5, 0.5, 3.0, 6.9] {
                let p = paleta(perfil, hora);
                assert_eq!(p.manga_larga, 1.0, "{perfil:?} a las {hora}");
                assert!(p.remeras.iter().all(|c| luminancia(*c) <= 0.36), "{perfil:?} a las {hora}: campera clara");
                assert!(p.pantalones.iter().all(|c| luminancia(*c) <= 0.3), "{perfil:?} a las {hora}");
                assert!(vestidos(perfil, hora, 30).iter().all(|a| a.manga_larga));
            }
        }
        // De día los pantalones son más claros que de noche.
        let media = |v: &[Color]| v.iter().map(|c| luminancia(*c)).sum::<f32>() / v.len() as f32;
        assert!(
            media(&paleta(Perfil::Paseante, 13.0).pantalones) > media(&paleta(Perfil::Paseante, 22.0).pantalones) + 0.2
        );
        // Trasnochados y nocturnos, siempre abrigados.
        for hora in HORAS {
            assert_eq!(paleta(Perfil::Trasnochado, hora).manga_larga, 1.0);
            assert_eq!(paleta(Perfil::Nocturno, hora).manga_larga, 1.0);
        }
    }

    #[test]
    fn req_rut_10_oficinista_con_camisa_clara_y_pantalon_oscuro() {
        for hora in HORAS {
            let p = paleta(Perfil::Oficinista, hora);
            assert!(p.remeras.iter().all(|c| luminancia(*c) >= 0.75), "camisa clara a las {hora}");
            assert!(p.pantalones.iter().all(|c| luminancia(*c) <= 0.3), "pantalón oscuro a las {hora}");
            assert!(vestidos(Perfil::Oficinista, hora, 30).iter().all(|a| a.gorra.is_none()), "sin gorra");
            assert_eq!(p.manga_larga, if ropa_de_dia(hora) { 0.0 } else { 1.0 }, "a las {hora}");
        }
    }

    #[test]
    fn req_rut_10_nocturnos_fuertes_y_corredores_deportivos() {
        for hora in HORAS {
            let n = paleta(Perfil::Nocturno, hora);
            assert!(n.remeras.iter().all(|c| saturacion(*c) >= 0.6), "nocturno con color fuerte");
            let c = paleta(Perfil::Corredor, hora);
            assert!(c.remeras.iter().all(|r| saturacion(*r) >= 0.6 && luminancia(*r) >= 0.25), "corredor vivo");
            assert_eq!(c.manga_larga, if ropa_de_dia(hora) { 0.0 } else { 1.0 });
        }
    }

    /// REQ-AMB-16 dentro de una paleta: 32 presentes (26 + 6 en la fila) que se van renovando
    /// y las últimas 30 idas; nadie repite a nadie y se diferencia en dos rasgos o más.
    fn sin_repetir_con(paleta: &Paleta, semilla: u64) {
        let mut a = Azar::new(semilla);
        let mut v = Variedad::default();
        let mut historia: Vec<Apariencia> = Vec::new();
        let mut presentes: Vec<u64> = Vec::new();
        let mut idas: Vec<u64> = Vec::new();
        for id in 0..300_u64 {
            if presentes.len() >= 26 + 6 {
                let sale = presentes.remove(0);
                v.se_fue(sale);
                idas.push(sale);
            }
            let nueva = v.nueva_con(&mut a, id, paleta);
            for otro in presentes.iter().chain(idas.iter().rev().take(MEMORIA_IDAS)) {
                let d = nueva.diferencias(&historia[*otro as usize]);
                assert!(d >= 2, "la {id} se parece mucho a la {otro} ({d} rasgos)");
            }
            historia.push(nueva);
            presentes.push(id);
            assert!(v.sin_repetir());
        }
    }

    #[test]
    fn req_rut_10_variedad_suficiente_en_cada_paleta() {
        for (i, perfil) in Perfil::TODOS.into_iter().enumerate() {
            for hora in [3.0, 13.0, 22.0] {
                let p = paleta(perfil, hora);
                assert!(p.pieles.len() >= 6 && p.pelos.len() >= 8, "{perfil:?}: pieles y pelos variados");
                assert!(p.remeras.len() >= 5 && p.pantalones.len() >= 5, "{perfil:?}: ropa variada");
                sin_repetir_con(&p, i as u64 * 31 + hora as u64);
            }
        }
    }

    #[test]
    fn req_rut_11_de_20_a_6_nadie_trota() {
        for perfil in Perfil::TODOS {
            for hora in [20.0, 21.5, 23.9, 0.0, 3.0, 5.9] {
                assert!(!plan_permitido(perfil, Plan::Trotar, hora), "{perfil:?} trota a las {hora}");
            }
            for hora in [6.0, 8.0, 13.0, 19.9] {
                assert!(plan_permitido(perfil, Plan::Trotar, hora), "{perfil:?} no trota a las {hora}");
            }
            for plan in [Plan::Pasear, Plan::Sentarse, Plan::Charlar] {
                assert!(HORAS.iter().all(|h| plan_permitido(perfil, plan, *h)));
            }
        }
    }

    #[test]
    fn req_rut_11_de_22_a_24_nadie_pasea_al_perro() {
        for hora in [22.0, 23.0, 23.99] {
            assert!(!plan_permitido(Perfil::Paseador, Plan::PasearPerro, hora), "perro a las {hora}");
        }
        // De madrugada y el resto del día, sí.
        for hora in [0.0, 2.0, 5.5, 8.0, 13.0, 21.9] {
            assert!(plan_permitido(Perfil::Paseador, Plan::PasearPerro, hora), "sin perro a las {hora}");
        }
    }

    #[test]
    fn req_rut_11_de_noche_solo_asientos_cerca_de_un_farol() {
        assert!(es_de_noche(22.0) && es_de_noche(3.0) && !es_de_noche(13.0));
        assert!(!faroles().is_empty());
        let lejos = [10.0, 10.0]; // en el pasto, lejos de todo farol
        assert!(faroles().iter().all(|f| (f[0] - lejos[0]).hypot(f[1] - lejos[1]) >= CERCA_DE_FAROL));
        assert!(!asiento_permitido(lejos, 22.0) && !asiento_permitido(lejos, 3.0));
        assert!(asiento_permitido(lejos, 13.0), "de día, todos");
        let cerca = [faroles()[0][0] + 2.0, faroles()[0][1]];
        assert!(asiento_permitido(cerca, 22.0));

        // En la red real: de día todos los asientos; de noche, solo los cercanos a un farol,
        // y queda al menos alguno.
        let r = red();
        let asientos: Vec<[f32; 2]> =
            r.de_tipo(|t| matches!(t, TipoNodo::Asiento { .. })).into_iter().map(|i| r.pos[i]).collect();
        assert!(!asientos.is_empty());
        assert!(asientos.iter().all(|a| asiento_permitido(*a, 13.0)));
        let de_noche: Vec<_> = asientos.iter().filter(|a| asiento_permitido(**a, 22.0)).collect();
        assert!(!de_noche.is_empty(), "de noche no queda ningún asiento");
        for a in &de_noche {
            assert!(faroles().iter().any(|f| (f[0] - a[0]).hypot(f[1] - a[1]) < CERCA_DE_FAROL));
        }
    }
}
