//! SPEC-019 · Eventos de la plaza: semana, feria y partido (`eventos.ron`).

use serde::Deserialize;

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

/// REQ-EVE-01: el día 1 es viernes.
pub fn dia_semana(dia: u32) -> DiaSemana {
    DiaSemana::ORDEN[((dia.max(1) - 1 + 4) % 7) as usize]
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rutinas::tests::plaza_real;

    #[test]
    fn req_eve_01_el_dia_1_es_viernes() {
        assert_eq!(dia_semana(1), DiaSemana::Vie);
        assert_eq!(dia_semana(2), DiaSemana::Sab);
        assert_eq!(dia_semana(3), DiaSemana::Dom);
        assert_eq!(dia_semana(6), DiaSemana::Mie);
        assert_eq!(dia_semana(8), DiaSemana::Vie);
        assert_eq!(dia_semana(2).texto(), "Sáb");
    }

    #[test]
    fn req_eve_02_04_feria_el_fin_de_semana() {
        let p = plaza_real();
        // Viernes al mediodía: nada.
        assert_eq!(p.modificador(1, 12.0), Modificador::default());
        // Sábado al mediodía: feria con más gente y más clientes.
        let m = p.modificador(2, 12.0);
        assert!(m.activo("feria/feria") && m.activo("feria/puestos"), "{m:?}");
        assert_eq!((m.gente, m.clientes), (1.5, 1.3));
        assert!(m.perfiles.iter().any(|(p, _)| *p == Perfil::Familia));
        // Sábado a las 8: los puestos están, la feria todavía no empezó.
        let m = p.modificador(2, 8.0);
        assert!(m.activo("feria/puestos") && !m.activo("feria/feria"));
        assert_eq!(m.gente, 1.0);
        // Lunes: nada.
        assert!(p.modificador(4, 12.0).tramos.is_empty());
    }

    #[test]
    fn req_eve_02_04_partido_miercoles_y_domingo() {
        let p = plaza_real();
        let mie = 6;
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
        assert!(p.modificador(3, 22.0).activo("partido/partido"));
        // El día 1 a las 0:15 no hay "ayer".
        assert!(p.modificador(1, 0.25).tramos.is_empty());
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
