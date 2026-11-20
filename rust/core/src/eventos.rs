//! SPEC-019 · Eventos de la plaza: semana, feria y partido (`eventos.ron`).

use serde::Deserialize;

use crate::azar::Azar;
use crate::plaza;
use crate::rutinas::Perfil;

/// REQ-EVE-01
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
pub enum DiaSemana {
    Lun,
    Mar,
    Mie,
    Jue,
    Vie,
    Sab,
    Dom,
}

impl DiaSemana {
    const ORDEN: [DiaSemana; 7] = [
        DiaSemana::Lun,
        DiaSemana::Mar,
        DiaSemana::Mie,
        DiaSemana::Jue,
        DiaSemana::Vie,
        DiaSemana::Sab,
        DiaSemana::Dom,
    ];

    /// REQ-EVE-01: "Sáb".
    pub fn texto(self) -> &'static str {
        match self {
            DiaSemana::Lun => "Lun",
            DiaSemana::Mar => "Mar",
            DiaSemana::Mie => "Mié",
            DiaSemana::Jue => "Jue",
            DiaSemana::Vie => "Vie",
            DiaSemana::Sab => "Sáb",
            DiaSemana::Dom => "Dom",
        }
    }
}

/// REQ-EVE-01: el día 1 es lunes.
pub fn dia_semana(dia: u32) -> DiaSemana {
    DiaSemana::ORDEN[((dia.max(1) - 1) % 7) as usize]
}

fn uno() -> f32 {
    1.0
}

/// REQ-EVE-02: un tramo horario de un evento.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Tramo {
    /// Nombre del tramo ("feria", "puestos", "previa", "partido", "festejo").
    pub id: String,
    /// Horas desde el comienzo del día del evento; `hasta` puede pasar de 24 (sigue al día
    /// siguiente).
    pub desde: f32,
    pub hasta: f32,
    #[serde(default = "uno")]
    pub gente: f32,
    #[serde(default = "uno")]
    pub clientes: f32,
    /// Perfiles que se suman a los de la franja, con su peso.
    #[serde(default)]
    pub perfiles: Vec<(Perfil, f32)>,
    /// REQ-EVE-07: chance de que alguien que llega lleve la camiseta de un equipo.
    #[serde(default)]
    pub camisetas: f32,
}

/// REQ-EVE-02
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Evento {
    pub id: String,
    /// REQ-EVE-03: texto del aviso ("feria en la plaza de 10 a 18").
    pub aviso: String,
    pub dias: Vec<DiaSemana>,
    pub tramos: Vec<Tramo>,
    /// REQ-EVE-07: colores de las camisetas de los equipos.
    #[serde(default)]
    pub equipos: Vec<[f32; 3]>,
}

impl Evento {
    pub(crate) fn validar(&self) -> Result<(), String> {
        if self.dias.is_empty() || self.tramos.is_empty() {
            return Err(format!("el evento \"{}\" no tiene días o tramos", self.id));
        }
        for t in &self.tramos {
            if !(0.0..48.0).contains(&t.desde) || t.hasta <= t.desde || t.hasta > 48.0 {
                return Err(format!("\"{}\": tramo \"{}\" con horas inválidas", self.id, t.id));
            }
            if t.camisetas > 0.0 && self.equipos.is_empty() {
                return Err(format!("\"{}\": hay camisetas pero no equipos", self.id));
            }
        }
        Ok(())
    }

    /// ¿Hay evento en este día de la semana?
    pub fn es_dia(&self, d: DiaSemana) -> bool {
        self.dias.contains(&d)
    }
}

/// Lo que cambian los eventos activos en un momento. REQ-EVE-04
#[derive(Debug, Clone, PartialEq)]
pub struct Modificador {
    pub gente: f32,
    pub clientes: f32,
    pub perfiles: Vec<(Perfil, f32)>,
    /// REQ-EVE-07: chance de camiseta y colores posibles.
    pub camisetas: f32,
    pub equipos: Vec<[f32; 3]>,
    /// Tramos activos como "evento/tramo" (ej. "feria/puestos", "partido/festejo").
    pub tramos: Vec<String>,
}

impl Default for Modificador {
    fn default() -> Self {
        Self {
            gente: 1.0,
            clientes: 1.0,
            perfiles: Vec::new(),
            camisetas: 0.0,
            equipos: Vec::new(),
            tramos: Vec::new(),
        }
    }
}

impl Modificador {
    /// ¿Está activo el tramo "evento/tramo"?
    pub fn activo(&self, evento_tramo: &str) -> bool {
        self.tramos.iter().any(|t| t == evento_tramo)
    }
}

/// REQ-EVE-02, REQ-EVE-04: combina los tramos activos el día `dia` (número de día de juego)
/// a la hora `hora` (0–24). Un tramo que pasa de las 24 sigue activo a la madrugada del día
/// siguiente. Los multiplicadores se multiplican entre sí.
pub fn modificador(eventos: &[Evento], dia: u32, hora: f32) -> Modificador {
    let mut m = Modificador::default();
    let hoy = dia_semana(dia);
    let ayer = dia_semana(if dia <= 1 { 7 } else { dia - 1 });
    for e in eventos {
        for t in &e.tramos {
            let activo = (e.es_dia(hoy) && (t.desde..t.hasta).contains(&hora))
                || (dia > 1 && e.es_dia(ayer) && (t.desde..t.hasta).contains(&(hora + 24.0)));
            if !activo {
                continue;
            }
            m.gente *= t.gente;
            m.clientes *= t.clientes;
            m.perfiles.extend(t.perfiles.iter().copied());
            if t.camisetas > m.camisetas {
                m.camisetas = t.camisetas;
                m.equipos = e.equipos.clone();
            }
            m.tramos.push(format!("{}/{}", e.id, t.id));
        }
    }
    m
}

/// REQ-EVE-03: hora del aviso de la mañana.
pub const HORA_AVISO: f32 = 7.0;

/// REQ-EVE-03: el aviso de la mañana con los eventos del día (o `None` si no hay ninguno).
/// "Hoy: feria en la plaza de 10 a 18 y juega el equipo del barrio a las 21".
pub fn aviso_del_dia(eventos: &[Evento], dia: u32) -> Option<String> {
    let hoy = dia_semana(dia);
    let avisos: Vec<String> = eventos.iter().filter(|e| e.es_dia(hoy)).map(|e| e.aviso.clone()).collect();
    if avisos.is_empty() { None } else { Some(format!("Hoy: {}", crate::aderezos::enumerar(&avisos))) }
}

/// REQ-EVE-07: con chance `m.camisetas`, el color de la camiseta de uno de los equipos.
pub fn camiseta(azar: &mut Azar, m: &Modificador) -> Option<[f32; 3]> {
    if m.equipos.is_empty() || !azar.chance(m.camisetas) {
        return None;
    }
    azar.elegir(&m.equipos).copied()
}

/// REQ-EVE-09: ¿esa remera es la camiseta de alguno de los equipos?
pub fn es_camiseta(remera: [f32; 3], m: &Modificador) -> bool {
    m.equipos.contains(&remera)
}

/// REQ-EVE-09: en el festejo, cada persona con camiseta que charla o espera salta, en
/// promedio, una vez cada `1 / SALTOS_POR_S` segundos, unos segundos cada vez y como mucho
/// `MAX_SALTOS` veces (para que la charla termine y el grupo se vaya).
pub const SALTOS_POR_S: f32 = 0.2;
pub const SEGUNDOS_SALTO: [f32; 2] = [1.5, 3.0];
pub const MAX_SALTOS: u32 = 4;

// ── Feria (REQ-EVE-05, REQ-EVE-06) ─────────────────────────────────

/// REQ-EVE-05: medidas de un puesto (m): ancho del frente y fondo.
pub const ANCHO_PUESTO: f32 = 2.4;
pub const FONDO_PUESTO: f32 = 1.4;
/// Dónde quedan: sobre el pasto entre el borde sur de la plaza y la vereda sur, mirando a la
/// plaza (y al carrito) y al camino del borde, por donde pasa la gente.
const Z_PUESTOS: f32 = plaza::LADO_PLAZA / 2.0 + 3.2;
const X_PUESTOS: [f32; 6] = [-13.0, -8.5, -4.0, 4.0, 8.5, 13.0];
const TOLDOS: [[f32; 3]; 6] =
    [[0.85, 0.15, 0.15], [0.1, 0.45, 0.8], [0.95, 0.7, 0.1], [0.15, 0.6, 0.3], [0.6, 0.2, 0.65], [0.95, 0.45, 0.1]];

/// REQ-EVE-05: un puesto de la feria. Su frente (mostrador) mira hacia +Z local, girado
/// `rot_y` grados en Y.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Puesto {
    pub x: f32,
    pub z: f32,
    pub rot_y: f32,
    /// Color del toldo (a rayas con blanco).
    pub toldo: [f32; 3],
}

impl Puesto {
    /// Hacia dónde mira el frente (en planta).
    pub fn frente_dir(&self) -> [f32; 2] {
        let (s, c) = self.rot_y.to_radians().sin_cos();
        [s, c]
    }

    fn corrido(&self, d: f32) -> [f32; 2] {
        let f = self.frente_dir();
        [self.x + f[0] * d, self.z + f[1] * d]
    }

    /// REQ-EVE-06: dónde se para quien mira el puesto (en el camino, frente al mostrador).
    pub fn frente(&self) -> [f32; 2] {
        self.corrido(FONDO_PUESTO / 2.0 + 1.3)
    }

    /// REQ-EVE-05: dónde está el vendedor (adentro, detrás del mostrador).
    pub fn vendedor(&self) -> [f32; 2] {
        self.corrido(-0.35)
    }

    /// Por dónde entra y sale el vendedor (detrás del puesto, del lado de la vereda sur).
    pub fn atras(&self) -> [f32; 2] {
        self.corrido(-(FONDO_PUESTO / 2.0 + 2.1))
    }

    /// Planta del puesto: `[x_min, z_min, x_max, z_max]` (los puestos están derechos o
    /// girados 180°).
    pub fn planta(&self) -> [f32; 4] {
        let (a, f) = (ANCHO_PUESTO / 2.0, FONDO_PUESTO / 2.0);
        let girado = (self.rot_y.rem_euclid(180.0) - 90.0).abs() < 45.0;
        let (dx, dz) = if girado { (f, a) } else { (a, f) };
        [self.x - dx, self.z - dz, self.x + dx, self.z + dz]
    }
}

/// REQ-EVE-05: los 6 puestos, siempre en el mismo lugar: del lado de la plaza opuesto al
/// carrito (que está sobre la vereda norte), mirando a la plaza.
pub fn puestos_feria() -> Vec<Puesto> {
    X_PUESTOS.iter().zip(TOLDOS).map(|(&x, toldo)| Puesto { x, z: Z_PUESTOS, rot_y: 180.0, toldo }).collect()
}

/// REQ-EVE-06: chance de que un paseante que pasa frente a un puesto se pare a mirarlo (una
/// sola vez cada uno) y cuánto se queda: 1–3 min de juego.
pub const CHANCE_PARAR_EN_PUESTO: f32 = 0.45;
pub const MINUTOS_EN_PUESTO: [f32; 2] = [1.0, 3.0];
/// Qué tan cerca del frente de un puesto hay que pasar para que cuente (m).
const CERCA_DEL_PUESTO: f32 = 1.6;

/// REQ-EVE-06: el puesto frente al que está `pos`, si hay uno.
pub fn puesto_cercano(puestos: &[Puesto], pos: [f32; 2]) -> Option<usize> {
    puestos.iter().position(|p| {
        let f = p.frente();
        (f[0] - pos[0]).abs() < ANCHO_PUESTO / 2.0 + 0.3 && (f[1] - pos[1]).abs() < CERCA_DEL_PUESTO
    })
}

/// REQ-EVE-06: segundos reales que se queda mirando (1 min de juego = 1 s real a velocidad
/// normal, REQ-DIA-01).
pub fn segundos_en_puesto(azar: &mut Azar) -> f32 {
    let minutos = azar.rango(MINUTOS_EN_PUESTO[0], MINUTOS_EN_PUESTO[1]);
    minutos / crate::reloj::Reloj::default().minutos_por_segundo as f32
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rutinas::tests::plaza_real;

    #[test]
    fn req_eve_01_el_dia_1_es_lunes() {
        assert_eq!(dia_semana(1), DiaSemana::Lun);
        assert_eq!(dia_semana(2), DiaSemana::Mar);
        assert_eq!(dia_semana(3), DiaSemana::Mie);
        assert_eq!(dia_semana(5), DiaSemana::Vie);
        assert_eq!(dia_semana(6), DiaSemana::Sab);
        assert_eq!(dia_semana(7), DiaSemana::Dom);
        assert_eq!(dia_semana(8), DiaSemana::Lun);
        assert_eq!(dia_semana(6).texto(), "Sáb");
    }

    #[test]
    fn req_eve_02_04_feria_el_fin_de_semana() {
        let p = plaza_real();
        // Viernes al mediodía: nada.
        assert_eq!(p.modificador(5, 12.0), Modificador::default());
        // Sábado al mediodía: feria con más gente y más clientes.
        let m = p.modificador(6, 12.0);
        assert!(m.activo("feria/feria") && m.activo("feria/puestos"), "{m:?}");
        assert_eq!((m.gente, m.clientes), (1.5, 1.3));
        assert!(m.perfiles.iter().any(|(p, _)| *p == Perfil::Familia));
        // Sábado a las 8: los puestos están, la feria todavía no empezó.
        let m = p.modificador(6, 8.0);
        assert!(m.activo("feria/puestos") && !m.activo("feria/feria"));
        assert_eq!(m.gente, 1.0);
        // Lunes: nada.
        assert!(p.modificador(1, 12.0).tramos.is_empty());
    }

    #[test]
    fn req_eve_02_04_07_08_09_partido_miercoles_y_domingo() {
        let p = plaza_real();
        let mie = 3;
        let m = p.modificador(mie, 19.0);
        assert!(m.activo("partido/previa"));
        assert_eq!(m.camisetas, 0.5);
        assert_eq!(m.equipos.len(), 2);
        let m = p.modificador(mie, 22.0);
        assert_eq!((m.gente, m.clientes), (0.3, 0.3));
        let m = p.modificador(mie, 23.5);
        assert!(m.activo("partido/festejo"));
        assert_eq!(m.clientes, 2.0);
        // El festejo sigue a las 0:15 del jueves y termina a las 0:30.
        assert!(p.modificador(mie + 1, 0.25).activo("partido/festejo"));
        assert!(!p.modificador(mie + 1, 0.6).activo("partido/festejo"));
        // Domingo también.
        assert!(p.modificador(7, 22.0).activo("partido/partido"));
        // El festejo del domingo sigue a las 0:15 del lunes siguiente (día 8).
        assert!(p.modificador(8, 0.25).activo("partido/festejo"));
        // El día 1 (lunes) a las 0:15 no hay "ayer": la partida no viene de un domingo.
        assert!(p.modificador(1, 0.25).tramos.is_empty());
    }

    #[test]
    fn req_eve_03_aviso_del_dia() {
        let p = plaza_real();
        assert_eq!(aviso_del_dia(&p.eventos, 1), None, "lunes sin eventos");
        assert_eq!(aviso_del_dia(&p.eventos, 5), None, "viernes sin eventos");
        assert_eq!(aviso_del_dia(&p.eventos, 6).as_deref(), Some("Hoy: feria en la plaza de 10 a 18"));
        assert_eq!(aviso_del_dia(&p.eventos, 3).as_deref(), Some("Hoy: juega el equipo del barrio a las 21"));
        // Domingo: los dos juntos.
        assert_eq!(
            aviso_del_dia(&p.eventos, 7).as_deref(),
            Some("Hoy: feria en la plaza de 10 a 18 y juega el equipo del barrio a las 21")
        );
    }

    #[test]
    fn req_eve_07_la_mitad_con_camiseta() {
        let p = plaza_real();
        let m = p.modificador(3, 19.0);
        let mut azar = Azar::new(5);
        let con: Vec<[f32; 3]> = (0..1000).filter_map(|_| camiseta(&mut azar, &m)).collect();
        assert!((420..580).contains(&con.len()), "{}", con.len());
        assert!(con.iter().all(|c| m.equipos.contains(c) && es_camiseta(*c, &m)));
        assert!(m.equipos.iter().all(|e| con.contains(e)), "salen los dos equipos");
        // Sin partido, nadie.
        let m = p.modificador(1, 19.0);
        assert!((0..100).all(|_| camiseta(&mut azar, &m).is_none()));
    }

    /// Distancia de un punto a un rectángulo `[x_min, z_min, x_max, z_max]` (0 si está adentro).
    fn dist_rect(p: [f32; 2], r: [f32; 4]) -> f32 {
        let dx = (r[0] - p[0]).max(p[0] - r[2]).max(0.0);
        let dz = (r[1] - p[1]).max(p[1] - r[3]).max(0.0);
        dx.hypot(dz)
    }

    /// Distancia mínima de un segmento a un rectángulo (muestreando el segmento).
    fn dist_segmento_rect(a: [f32; 2], b: [f32; 2], r: [f32; 4]) -> f32 {
        (0..=200)
            .map(|i| {
                let t = i as f32 / 200.0;
                dist_rect([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], r)
            })
            .fold(f32::MAX, f32::min)
    }

    #[test]
    fn req_eve_05_seis_puestos_lejos_del_carrito_sin_tapar_nada() {
        use crate::caminos::{self, PUNTO_CARRITO};
        let puestos = puestos_feria();
        assert_eq!(puestos.len(), 6);
        let red = caminos::red();
        let props = plaza::distribucion();
        for (i, p) in puestos.iter().enumerate() {
            let r = p.planta();
            // Del lado opuesto al carrito.
            assert!(p.z.signum() != PUNTO_CARRITO[1].signum() && p.z > plaza::LADO_PLAZA / 2.0, "{p:?}");
            // El frente mira a la plaza (hacia el carrito).
            assert!(p.frente_dir()[1] < -0.9, "{p:?}");
            // No pisa ningún camino de la red (ni de cerca), ni el lugar del vendedor.
            for (u, vecinos) in red.vecinos.iter().enumerate() {
                for &v in vecinos {
                    let d = dist_segmento_rect(red.pos[u], red.pos[v], r);
                    assert!(d > 1.0, "el puesto {i} tapa el camino {:?}–{:?} ({d})", red.pos[u], red.pos[v]);
                }
            }
            // Ni muebles de la plaza (bancos, árboles, faroles, fuente).
            for m in &props {
                assert!(dist_rect([m.x, m.z], r) > 1.5, "el puesto {i} pisa {m:?}");
            }
            // Ni la vereda sur.
            assert!(r[3] < caminos::Z_VEREDA_SUR - 2.0 && p.atras()[1] < caminos::Z_VEREDA_SUR - 2.0);
            // Ni a otro puesto.
            for q in &puestos[i + 1..] {
                let s = q.planta();
                assert!(r[2] + 1.0 < s[0] || s[2] + 1.0 < r[0], "{p:?} y {q:?} pegados");
            }
            // El vendedor queda adentro y quien mira, afuera, cerca del camino del borde.
            assert!(dist_rect(p.vendedor(), r) == 0.0);
            assert!(dist_rect(p.frente(), r) > 1.0);
            let f = p.frente();
            let cerca = red.pos.iter().any(|n| (n[1] - f[1]).abs() < 1.0 && (n[0] - f[0]).abs() < 12.0);
            assert!(cerca, "frente al puesto {i} no pasa ningún camino");
        }
    }

    #[test]
    fn req_eve_06_quien_pasa_frente_a_un_puesto() {
        let puestos = puestos_feria();
        let f = puestos[2].frente();
        assert_eq!(puesto_cercano(&puestos, f), Some(2));
        // Pasando por el camino del borde de la plaza, frente al puesto.
        assert_eq!(puesto_cercano(&puestos, [puestos[4].x + 0.5, plaza::LADO_PLAZA / 2.0 + 0.5]), Some(4));
        // Lejos, en el medio de la plaza o entre dos puestos, no.
        assert_eq!(puesto_cercano(&puestos, [0.0, 0.0]), None);
        assert_eq!(puesto_cercano(&puestos, [0.0, f[1]]), None);
        let mut azar = Azar::new(3);
        for _ in 0..100 {
            let s = segundos_en_puesto(&mut azar);
            assert!((1.0..=3.0).contains(&s), "{s}");
        }
    }

    #[test]
    fn eventos_mal_armados() {
        let e = Evento {
            id: "x".into(),
            aviso: String::new(),
            dias: vec![DiaSemana::Lun],
            tramos: vec![Tramo {
                id: "t".into(),
                desde: 5.0,
                hasta: 4.0,
                gente: 1.0,
                clientes: 1.0,
                perfiles: vec![],
                camisetas: 0.0,
            }],
            equipos: vec![],
        };
        assert!(e.validar().is_err());
    }
}
