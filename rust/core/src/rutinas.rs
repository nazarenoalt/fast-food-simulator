//! SPEC-018 · Rutinas de la plaza: agenda por franja horaria y perfiles de la gente.
//!
//! La agenda (`agenda.ron`) dice cuánta gente hay en cada franja y qué perfiles llegan.
//! Los eventos (SPEC-019, `eventos.ron`) la modifican; los habituales (SPEC-030) tienen
//! sus nombres en `habituales.ron`.

use serde::Deserialize;

use crate::azar::Azar;
use crate::datos::{ErrorDatos, parsear};
use crate::eventos::{Evento, Modificador};
use crate::peatones::Plan;

/// REQ-RUT-03: la agenda mira 45 minutos adelante (en horas).
pub const ADELANTO_H: f32 = 0.75;

/// REQ-RUT-02: quién es cada persona. Decide su velocidad, paciencia, grupo y actividades.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
pub enum Perfil {
    Paseante,
    Corredor,
    Paseador,
    AlTrabajo,
    Jubilado,
    Oficinista,
    Familia,
    Adolescente,
    Nocturno,
    Pareja,
    Trasnochado,
}

impl Perfil {
    pub const TODOS: [Perfil; 11] = [
        Perfil::Paseante,
        Perfil::Corredor,
        Perfil::Paseador,
        Perfil::AlTrabajo,
        Perfil::Jubilado,
        Perfil::Oficinista,
        Perfil::Familia,
        Perfil::Adolescente,
        Perfil::Nocturno,
        Perfil::Pareja,
        Perfil::Trasnochado,
    ];
}

fn uno() -> f32 {
    1.0
}

fn solo() -> [usize; 2] {
    [1, 1]
}

/// REQ-RUT-02: cómo es y qué hace un perfil.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefPerfil {
    pub perfil: Perfil,
    /// m/s, mínimo y máximo.
    pub velocidad: [f32; 2],
    /// REQ-RUT-04: multiplica la paciencia de REQ-CLI-06 cuando es cliente.
    #[serde(default = "uno")]
    pub paciencia: f32,
    /// Personas que llegan juntas (mínimo y máximo).
    #[serde(default = "solo")]
    pub grupo: [usize; 2],
    /// Actividades posibles con su peso (REQ-AMB-05).
    pub planes: Vec<(Plan, f32)>,
    /// Segundos que se queda quieto (sentado o charlando), mínimo y máximo.
    #[serde(default)]
    pub quieto: Option<[f32; 2]>,
}

/// REQ-RUT-01: una franja horaria de la agenda.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Franja {
    /// Horas (0–24); `desde` incluida, `hasta` no.
    pub desde: f32,
    pub hasta: f32,
    /// Cuánta gente anda por la plaza.
    pub gente: usize,
    /// Perfiles que llegan, con su peso.
    pub perfiles: Vec<(Perfil, f32)>,
}

/// REQ-RUT-01
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Agenda {
    pub perfiles: Vec<DefPerfil>,
    pub franjas: Vec<Franja>,
}

/// Sortea un elemento según los pesos (suma > 0).
pub fn sortear<T: Copy>(azar: &mut Azar, opciones: &[(T, f32)]) -> Option<T> {
    let total: f32 = opciones.iter().map(|(_, p)| p.max(0.0)).sum();
    if total <= 0.0 {
        return None;
    }
    let mut r = azar.real() * total;
    for (t, p) in opciones {
        r -= p.max(0.0);
        if r < 0.0 {
            return Some(*t);
        }
    }
    opciones.iter().rev().find(|(_, p)| *p > 0.0).map(|(t, _)| *t)
}

impl Agenda {
    /// REQ-RUT-01: la franja de una hora (0–24).
    pub fn franja(&self, hora: f32) -> &Franja {
        let h = hora.rem_euclid(24.0);
        self.franjas.iter().find(|f| (f.desde..f.hasta).contains(&h)).unwrap_or(&self.franjas[0])
    }

    /// REQ-RUT-03: la franja que manda ahora (la de dentro de 45 min).
    pub fn franja_adelantada(&self, hora: f32) -> &Franja {
        self.franja(hora + ADELANTO_H)
    }

    /// REQ-RUT-01, REQ-RUT-03, REQ-EVE-04: cuánta gente tiene que haber en la plaza.
    pub fn cantidad_objetivo(&self, hora: f32, m: &Modificador) -> usize {
        (self.franja_adelantada(hora).gente as f32 * m.gente).round() as usize
    }

    /// REQ-RUT-01, REQ-RUT-02, REQ-EVE-02: el perfil de alguien que llega ahora.
    pub fn sortear_perfil(&self, azar: &mut Azar, hora: f32, m: &Modificador) -> Perfil {
        let mut opciones = self.franja_adelantada(hora).perfiles.clone();
        opciones.extend(m.perfiles.iter().copied());
        sortear(azar, &opciones).unwrap_or(Perfil::Paseante)
    }

    /// REQ-RUT-02
    pub fn def(&self, p: Perfil) -> &DefPerfil {
        self.perfiles.iter().find(|d| d.perfil == p).unwrap_or(&self.perfiles[0])
    }

    /// REQ-RUT-02: la actividad de alguien de ese perfil.
    pub fn sortear_plan(&self, azar: &mut Azar, p: Perfil) -> Plan {
        sortear(azar, &self.def(p).planes).unwrap_or(Plan::Pasear)
    }

    /// REQ-RUT-02: cuántos llegan juntos.
    pub fn tamano_grupo(&self, azar: &mut Azar, p: Perfil) -> usize {
        let [a, b] = self.def(p).grupo;
        a + azar.entero(b.saturating_sub(a) + 1)
    }

    pub fn velocidad(&self, azar: &mut Azar, p: Perfil) -> f32 {
        let [a, b] = self.def(p).velocidad;
        azar.rango(a, b)
    }

    /// Segundos quieto (sentado o charlando).
    pub fn quieto(&self, azar: &mut Azar, p: Perfil) -> f32 {
        let [a, b] = self.def(p).quieto.unwrap_or([20.0, 70.0]);
        azar.rango(a, b)
    }

    /// REQ-RUT-04: factor de paciencia del perfil.
    pub fn paciencia(&self, p: Perfil) -> f32 {
        self.def(p).paciencia
    }

    fn validar(&self) -> Result<(), String> {
        for p in Perfil::TODOS {
            if !self.perfiles.iter().any(|d| d.perfil == p) {
                return Err(format!("falta el perfil {p:?}"));
            }
        }
        for d in &self.perfiles {
            if d.planes.is_empty() || d.grupo[0] == 0 || d.grupo[0] > d.grupo[1] {
                return Err(format!("perfil {:?} sin planes o con grupo inválido", d.perfil));
            }
        }
        // Las franjas cubren el día entero, en orden y sin huecos.
        let mut h = 0.0;
        for f in &self.franjas {
            if f.desde != h || f.hasta <= f.desde || f.perfiles.is_empty() {
                return Err(format!("franja {}–{} mal armada (se esperaba desde {h})", f.desde, f.hasta));
            }
            h = f.hasta;
        }
        if h != 24.0 {
            return Err("las franjas no llegan a las 24".into());
        }
        Ok(())
    }
}

/// REQ-HAB-01: nombres para los habituales.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ArchivoHabituales {
    pub nombres: Vec<String>,
}

/// Todo lo de la plaza que viene de datos.
#[derive(Debug, Clone, PartialEq)]
pub struct DatosPlaza {
    pub agenda: Agenda,
    pub eventos: Vec<Evento>,
    pub habituales: ArchivoHabituales,
}

impl DatosPlaza {
    /// REQ-EVE-02, REQ-EVE-04: lo que cambian los eventos activos ese día y hora.
    pub fn modificador(&self, dia: u32, hora: f32) -> Modificador {
        crate::eventos::modificador(&self.eventos, dia, hora)
    }
}

pub fn cargar_plaza(agenda: &str, eventos: &str, habituales: &str) -> Result<DatosPlaza, ErrorDatos> {
    let error = |archivo: &str, mensaje: String| ErrorDatos { archivo: archivo.into(), mensaje };
    let agenda: Agenda = parsear("agenda.ron", agenda)?;
    agenda.validar().map_err(|m| error("agenda.ron", m))?;
    let eventos: Vec<Evento> = parsear("eventos.ron", eventos)?;
    for e in &eventos {
        e.validar().map_err(|m| error("eventos.ron", m))?;
    }
    let habituales: ArchivoHabituales = parsear("habituales.ron", habituales)?;
    if habituales.nombres.len() < 8 {
        return Err(error("habituales.ron", "hacen falta al menos 8 nombres (REQ-HAB-01)".into()));
    }
    Ok(DatosPlaza { agenda, eventos, habituales })
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;

    fn leer(nombre: &str) -> String {
        let p = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data").join(nombre);
        std::fs::read_to_string(&p).unwrap_or_else(|e| panic!("{nombre}: {e}"))
    }

    /// Los archivos reales del juego.
    pub(crate) fn plaza_real() -> DatosPlaza {
        cargar_plaza(&leer("agenda.ron"), &leer("eventos.ron"), &leer("habituales.ron"))
            .unwrap_or_else(|e| panic!("{e}"))
    }

    fn mayoria(f: &Franja) -> Perfil {
        f.perfiles.iter().max_by(|a, b| a.1.total_cmp(&b.1)).unwrap().0
    }

    #[test]
    fn req_rut_01_franjas_de_la_agenda() {
        let a = plaza_real().agenda;
        let gente: Vec<usize> = [3.0, 7.0, 10.0, 13.0, 15.0, 17.0, 22.0].iter().map(|h| a.franja(*h).gente).collect();
        assert_eq!(gente, [3, 12, 18, 28, 16, 28, 20]);
        assert_eq!(mayoria(a.franja(13.0)), Perfil::Oficinista);
        assert_eq!(mayoria(a.franja(17.0)), Perfil::Familia);
        assert_eq!(mayoria(a.franja(22.0)), Perfil::Nocturno);
    }

    #[test]
    fn req_amb_04_rut_03_mas_gente_de_dia_y_se_adelanta() {
        let a = plaza_real().agenda;
        let m = Modificador::default();
        assert!(a.cantidad_objetivo(3.0, &m) < 5);
        assert!(a.cantidad_objetivo(13.0, &m) > 20);
        assert!(a.cantidad_objetivo(23.0, &m) < a.cantidad_objetivo(13.0, &m));
        // A las 11:20 ya sale la gente del mediodía (28); a las 11:00 todavía no.
        assert_eq!(a.cantidad_objetivo(11.0, &m), 18);
        assert_eq!(a.cantidad_objetivo(11.0 + 20.0 / 60.0, &m), 28);
        // Y los perfiles que llegan son los de la franja que viene.
        let mut azar = Azar::new(4);
        let n = (0..400).filter(|_| a.sortear_perfil(&mut azar, 11.5, &m) == Perfil::Oficinista).count();
        assert!(n > 150, "{n}");
    }

    #[test]
    fn req_amb_05_rut_02_cada_perfil_con_sus_actividades() {
        let a = plaza_real().agenda;
        let mut azar = Azar::new(5);
        let planes: std::collections::HashSet<_> = Perfil::TODOS
            .iter()
            .flat_map(|p| (0..60).map(|_| format!("{:?}", a.sortear_plan(&mut azar, *p))).collect::<Vec<_>>())
            .collect();
        assert_eq!(planes.len(), 5, "{planes:?}");
        assert!(a.velocidad(&mut azar, Perfil::Corredor) > a.velocidad(&mut azar, Perfil::Jubilado));
        assert_eq!(a.sortear_plan(&mut azar, Perfil::Corredor), Plan::Trotar);
        assert_eq!(a.sortear_plan(&mut azar, Perfil::Paseador), Plan::PasearPerro);
        for _ in 0..30 {
            let g = a.tamano_grupo(&mut azar, Perfil::Nocturno);
            assert!((3..=4).contains(&g), "{g}");
        }
        assert_eq!(a.tamano_grupo(&mut azar, Perfil::Pareja), 2);
    }

    #[test]
    fn req_rut_04_paciencia_por_perfil() {
        let a = plaza_real().agenda;
        assert_eq!(a.paciencia(Perfil::Oficinista), 0.8);
        assert_eq!(a.paciencia(Perfil::Jubilado), 1.2);
        for p in Perfil::TODOS.iter().filter(|p| !matches!(p, Perfil::Oficinista | Perfil::Jubilado)) {
            assert_eq!(a.paciencia(*p), 1.0, "{p:?}");
        }
    }

    #[test]
    fn la_agenda_tiene_que_estar_bien_armada() {
        let mal = r#"(perfiles: [], franjas: [])"#;
        let e = cargar_plaza(mal, "[]", r#"(nombres: [])"#).unwrap_err();
        assert!(e.mensaje.contains("falta el perfil"), "{e}");
    }

    #[test]
    fn sortear_respeta_los_pesos() {
        let mut azar = Azar::new(1);
        let n = (0..1000).filter(|_| sortear(&mut azar, &[(1, 3.0), (2, 1.0), (3, 0.0)]) == Some(1)).count();
        assert!((650..850).contains(&n), "{n}");
        assert_eq!(sortear::<u8>(&mut azar, &[]), None);
    }
}
