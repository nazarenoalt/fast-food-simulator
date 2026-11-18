//! SPEC-024 · Sonido: reglas puras de mezcla, variantes, distancia y ambiente.

use std::collections::HashMap;

use serde::Deserialize;

use crate::azar::Azar;
use crate::reloj::{PUESTA_SOL, SALIDA_SOL, suave};

/// Ids de los sonidos que usa el juego (`godot/data/sonidos.ron`). Un test verifica que existan.
pub mod ids {
    pub const PAJAROS: &str = "pajaros";
    pub const GRILLOS: &str = "grillos";
    pub const MURMULLO_PLAZA: &str = "murmullo_plaza";
    pub const VIENTO: &str = "viento";
    pub const LLUVIA: &str = "lluvia";
    pub const MUSICA: &str = "musica_tranquila";
    pub const HERVIDOR_INTERRUPTOR: &str = "hervidor_interruptor";
    pub const HERVIDOR_HIERVE: &str = "hervidor_hierve";
    pub const PLANCHA_INTERRUPTOR: &str = "plancha_interruptor";
    pub const PLANCHA_CHISPOROTEO: &str = "plancha_chisporroteo";
    pub const PARRILLA_BRASAS: &str = "parrilla_brasas";
    pub const PARRILLA_CARBON: &str = "parrilla_carbon";
    pub const HELADERA_PUERTA: &str = "heladera_puerta";
    pub const AGARRAR: &str = "agarrar";
    pub const SOLTAR: &str = "soltar";
    pub const TIRAR: &str = "tirar";
    pub const APOYAR: &str = "apoyar";
    pub const POMO: &str = "pomo";
    pub const PAQUETE_LLEGA: &str = "paquete_llega";
    pub const PAQUETE_GUARDADO: &str = "paquete_guardado";
    pub const SACAR_BOLSA: &str = "sacar_bolsa";
    pub const SACAR_CAJA: &str = "sacar_caja";
    pub const COBRO: &str = "cobro";
    pub const CAMPANITA: &str = "campanita";
    pub const PASOS_JUGADOR: &str = "pasos_jugador";
    pub const AUTO_PASA: &str = "auto_pasa";
    pub const PALOMA_ALETEO: &str = "paloma_aleteo";
    pub const TIENDA_ABRIR: &str = "tienda_abrir";
    /// Puerta de una base de carrito (REQ-CAR-13): no es la de la heladera.
    pub const CARRITO_PUERTA: &str = "carrito_puerta";

    /// Todos, para validar los datos.
    pub const TODOS: [&str; 29] = [
        PAJAROS,
        GRILLOS,
        MURMULLO_PLAZA,
        VIENTO,
        LLUVIA,
        MUSICA,
        HERVIDOR_INTERRUPTOR,
        HERVIDOR_HIERVE,
        PLANCHA_INTERRUPTOR,
        PLANCHA_CHISPOROTEO,
        PARRILLA_BRASAS,
        PARRILLA_CARBON,
        HELADERA_PUERTA,
        AGARRAR,
        SOLTAR,
        TIRAR,
        APOYAR,
        POMO,
        PAQUETE_LLEGA,
        PAQUETE_GUARDADO,
        SACAR_BOLSA,
        SACAR_CAJA,
        COBRO,
        CAMPANITA,
        PASOS_JUGADOR,
        AUTO_PASA,
        PALOMA_ALETEO,
        TIENDA_ABRIR,
        CARRITO_PUERTA,
    ];
}

/// REQ-SON-01
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
pub enum Bus {
    Ambiente,
    Efectos,
    Musica,
}

impl Bus {
    pub const TODOS: [Bus; 3] = [Bus::Ambiente, Bus::Efectos, Bus::Musica];

    /// Nombre del bus en Godot.
    pub fn nombre(self) -> &'static str {
        match self {
            Bus::Ambiente => "Ambiente",
            Bus::Efectos => "Efectos",
            Bus::Musica => "Música",
        }
    }
}

fn distancia_por_defecto() -> f32 {
    20.0
}

/// REQ-SON-02: un sonido definido en `godot/data/sonidos.ron`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefSonido {
    pub id: String,
    /// Archivos de `godot/audio/` (variantes). Pueden no existir todavía (REQ-SON-09).
    pub archivos: Vec<String>,
    pub bus: Bus,
    #[serde(default)]
    pub volumen_db: f32,
    /// Sale de un punto del mundo (3D) y se atenúa con la distancia. REQ-SON-04
    #[serde(default)]
    pub espacial: bool,
    #[serde(default = "distancia_por_defecto")]
    pub distancia_max: f32,
    #[serde(default)]
    pub bucle: bool,
    /// Segundos mínimos entre dos disparos. REQ-SON-03
    #[serde(default)]
    pub enfriamiento: f32,
}

/// Valida la lista de sonidos: ids únicos, con archivos .ogg y valores razonables.
pub fn validar(sonidos: &[DefSonido]) -> Result<(), String> {
    for (i, s) in sonidos.iter().enumerate() {
        if sonidos[..i].iter().any(|o| o.id == s.id) {
            return Err(format!("sonido repetido: \"{}\"", s.id));
        }
        if s.archivos.is_empty() {
            return Err(format!("\"{}\" no tiene archivos", s.id));
        }
        if let Some(a) = s.archivos.iter().find(|a| !a.ends_with(".ogg")) {
            return Err(format!("\"{}\": \"{a}\" no es .ogg", s.id));
        }
        if s.espacial && s.distancia_max <= 0.0 {
            return Err(format!("\"{}\" es espacial y necesita distancia_max > 0", s.id));
        }
        if s.enfriamiento < 0.0 {
            return Err(format!("\"{}\" tiene un enfriamiento negativo", s.id));
        }
    }
    Ok(())
}

/// REQ-SON-02: lee y valida `godot/data/sonidos.ron`.
pub fn cargar(texto: &str) -> Result<Vec<DefSonido>, crate::datos::ErrorDatos> {
    let sonidos: Vec<DefSonido> = crate::datos::parsear("sonidos.ron", texto)?;
    validar(&sonidos).map_err(|mensaje| crate::datos::ErrorDatos { archivo: "sonidos.ron".into(), mensaje })?;
    Ok(sonidos)
}

/// REQ-SON-01: volumen lineal (0 a 1) a decibeles; 0 es silencio.
pub fn lineal_a_db(v: f32) -> f32 {
    if v <= 0.0 { -80.0 } else { (20.0 * v.log10()).max(-80.0) }
}

/// REQ-SON-01: volumen general y por bus.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Mezcla {
    pub general: f32,
    pub ambiente: f32,
    pub efectos: f32,
    pub musica: f32,
    pub silenciado: bool,
}

impl Default for Mezcla {
    fn default() -> Self {
        Self { general: 1.0, ambiente: 0.8, efectos: 1.0, musica: 0.5, silenciado: false }
    }
}

impl Mezcla {
    pub fn volumen(&self, bus: Bus) -> f32 {
        match bus {
            Bus::Ambiente => self.ambiente,
            Bus::Efectos => self.efectos,
            Bus::Musica => self.musica,
        }
    }

    pub fn set_volumen(&mut self, bus: Bus, v: f32) {
        let v = v.clamp(0.0, 1.0);
        match bus {
            Bus::Ambiente => self.ambiente = v,
            Bus::Efectos => self.efectos = v,
            Bus::Musica => self.musica = v,
        }
    }

    /// dB del bus Master (el general, o silencio con M).
    pub fn db_master(&self) -> f32 {
        if self.silenciado { -80.0 } else { lineal_a_db(self.general.clamp(0.0, 1.0)) }
    }

    /// dB de un bus.
    pub fn db_bus(&self, bus: Bus) -> f32 {
        lineal_a_db(self.volumen(bus))
    }
}

/// REQ-SON-04: cuánto se oye un sonido espacial a `d` metros (1 pegado, 0 desde `max`).
pub fn ganancia_distancia(d: f32, max: f32) -> f32 {
    if max <= 0.0 || d >= max {
        return 0.0;
    }
    let f = 1.0 - d.max(0.0) / max;
    f * f
}

/// REQ-SON-03: variante al azar, distinta de la anterior si hay más de una.
pub fn elegir_variante(azar: &mut Azar, cantidad: usize, anterior: Option<usize>) -> usize {
    if cantidad <= 1 {
        return 0;
    }
    match anterior {
        Some(a) if a < cantidad => {
            let i = azar.entero(cantidad - 1);
            if i >= a { i + 1 } else { i }
        }
        _ => azar.entero(cantidad),
    }
}

/// REQ-SON-03: recuerda cuándo sonó cada sonido para respetar el enfriamiento.
#[derive(Debug, Default)]
pub struct Enfriador {
    ultimo: HashMap<String, f64>,
}

impl Enfriador {
    /// Si pasó el enfriamiento desde la última vez, anota `ahora` y devuelve true.
    pub fn disparar(&mut self, id: &str, ahora: f64, enfriamiento: f32) -> bool {
        if self.ultimo.get(id).is_some_and(|&t| ahora - t < enfriamiento as f64) {
            return false;
        }
        self.ultimo.insert(id.to_string(), ahora);
        true
    }
}

/// Lo que determina el ambiente. REQ-SON-05..07
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Entorno {
    /// Minuto del día, 0 ≤ minuto < 1440.
    pub minuto: f32,
    /// Peatones en la plaza.
    pub gente: u32,
    /// 0 a 1 (SPEC-023; hasta entonces 0).
    pub lluvia: f32,
    /// 0 a 1 (SPEC-023; hasta entonces 0).
    pub viento: f32,
}

/// Una capa de ambiente: qué sonido y cuánto (0 a 1).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Capa {
    pub id: &'static str,
    pub nivel: f32,
}

/// REQ-SON-05: 1 de día, 0 de noche, con un fundido de 30 min alrededor del sol.
pub fn nivel_dia(minuto: f32) -> f32 {
    let salida = SALIDA_SOL as f32;
    let puesta = PUESTA_SOL as f32;
    suave(salida - 15.0, salida + 15.0, minuto) * (1.0 - suave(puesta - 15.0, puesta + 15.0, minuto))
}

/// REQ-SON-05, REQ-SON-06, REQ-SON-07: las capas del ambiente y su nivel.
pub fn capas_ambiente(e: &Entorno) -> [Capa; 5] {
    let dia = nivel_dia(e.minuto);
    let gente = (e.gente as f32 / 20.0).min(1.0);
    [
        Capa { id: ids::PAJAROS, nivel: dia },
        Capa { id: ids::GRILLOS, nivel: 1.0 - dia },
        Capa { id: ids::MURMULLO_PLAZA, nivel: gente * (0.4 + 0.6 * dia) },
        Capa { id: ids::VIENTO, nivel: 0.2 + 0.8 * e.viento.clamp(0.0, 1.0) },
        Capa { id: ids::LLUVIA, nivel: e.lluvia.clamp(0.0, 1.0) },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    fn def(id: &str) -> DefSonido {
        DefSonido {
            id: id.into(),
            archivos: vec!["a.ogg".into()],
            bus: Bus::Efectos,
            volumen_db: 0.0,
            espacial: false,
            distancia_max: 20.0,
            bucle: false,
            enfriamiento: 0.0,
        }
    }

    fn nivel(capas: &[Capa], id: &str) -> f32 {
        capas.iter().find(|c| c.id == id).unwrap().nivel
    }

    #[test]
    fn req_son_01_tres_buses_con_nombre() {
        let n: Vec<_> = Bus::TODOS.iter().map(|b| b.nombre()).collect();
        assert_eq!(n, vec!["Ambiente", "Efectos", "Música"]);
    }

    #[test]
    fn req_son_01_volumen_lineal_a_decibeles() {
        assert_eq!(lineal_a_db(1.0), 0.0);
        assert!((lineal_a_db(0.5) + 6.02).abs() < 0.01);
        assert_eq!(lineal_a_db(0.0), -80.0);
        assert_eq!(lineal_a_db(-1.0), -80.0);
    }

    #[test]
    fn req_son_01_volumenes_por_defecto_y_limites() {
        let mut m = Mezcla::default();
        assert_eq!((m.general, m.ambiente, m.efectos, m.musica), (1.0, 0.8, 1.0, 0.5));
        m.set_volumen(Bus::Musica, 3.0);
        assert_eq!(m.volumen(Bus::Musica), 1.0);
        m.set_volumen(Bus::Efectos, -1.0);
        assert_eq!(m.db_bus(Bus::Efectos), -80.0, "con 0 el bus queda en silencio");
    }

    #[test]
    fn req_son_01_silenciar_apaga_todo_y_reactivar_lo_devuelve() {
        let mut m = Mezcla { general: 0.5, ..Mezcla::default() };
        assert!((m.db_master() + 6.02).abs() < 0.01);
        m.silenciado = true;
        assert_eq!(m.db_master(), -80.0);
        m.silenciado = false;
        assert!((m.db_master() + 6.02).abs() < 0.01);
    }

    #[test]
    fn req_son_02_validacion_de_datos() {
        assert!(validar(&[def("a"), def("b")]).is_ok());
        assert!(validar(&[def("a"), def("a")]).unwrap_err().contains("repetido"));
        let mut sin = def("x");
        sin.archivos.clear();
        assert!(validar(&[sin]).is_err());
        let mut mp3 = def("x");
        mp3.archivos = vec!["x.mp3".into()];
        assert!(validar(&[mp3]).unwrap_err().contains(".ogg"));
        let mut lejos = def("x");
        lejos.espacial = true;
        lejos.distancia_max = 0.0;
        assert!(validar(&[lejos]).is_err());
    }

    fn sonidos_reales() -> Vec<DefSonido> {
        let ruta = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot/data/sonidos.ron");
        cargar(&std::fs::read_to_string(ruta).expect("sonidos.ron")).unwrap_or_else(|e| panic!("{e}"))
    }

    #[test]
    fn req_son_02_los_datos_del_juego_cargan_y_cubren_todos_los_ids() {
        let datos = sonidos_reales();
        for id in ids::TODOS {
            assert!(datos.iter().any(|s| s.id == id), "falta el sonido \"{id}\" en sonidos.ron");
        }
        assert_eq!(datos.len(), ids::TODOS.len(), "hay sonidos en los datos que el código no conoce");
    }

    #[test]
    fn req_son_02_ambiente_y_musica_son_de_fondo_y_las_acciones_efectos() {
        let datos = sonidos_reales();
        let de = |id: &str| datos.iter().find(|s| s.id == id).unwrap();
        for id in [ids::PAJAROS, ids::GRILLOS, ids::MURMULLO_PLAZA, ids::VIENTO, ids::LLUVIA] {
            assert_eq!((de(id).bus, de(id).bucle, de(id).espacial), (Bus::Ambiente, true, false), "{id}");
        }
        assert_eq!(de(ids::MUSICA).bus, Bus::Musica);
        assert!(de(ids::HERVIDOR_HIERVE).espacial && de(ids::HERVIDOR_HIERVE).bucle);
        assert!(de(ids::CAMPANITA).espacial && de(ids::CAMPANITA).enfriamiento > 0.0);
        assert!(de(ids::AGARRAR).archivos.len() > 1, "variantes para no repetir");
    }

    #[test]
    fn req_son_03_la_variante_nunca_repite_la_anterior() {
        let mut azar = Azar::new(3);
        let mut anterior = None;
        let mut vistas = [0; 4];
        for _ in 0..2000 {
            let i = elegir_variante(&mut azar, 4, anterior);
            assert!(i < 4);
            assert_ne!(Some(i), anterior);
            vistas[i] += 1;
            anterior = Some(i);
        }
        assert!(vistas.iter().all(|&n| n > 300), "todas salen: {vistas:?}");
        assert_eq!(elegir_variante(&mut azar, 1, Some(0)), 0);
        assert_eq!(elegir_variante(&mut azar, 0, None), 0);
    }

    #[test]
    fn req_son_03_el_enfriamiento_evita_repetir_seguido() {
        let mut e = Enfriador::default();
        assert!(e.disparar("campanita", 10.0, 2.0));
        assert!(!e.disparar("campanita", 11.0, 2.0));
        assert!(e.disparar("otro", 11.0, 2.0), "cada sonido tiene el suyo");
        assert!(e.disparar("campanita", 12.0, 2.0));
        assert!(e.disparar("sin_enfriamiento", 12.0, 0.0));
        assert!(e.disparar("sin_enfriamiento", 12.0, 0.0));
    }

    #[test]
    fn req_son_04_ganancia_baja_con_la_distancia() {
        assert_eq!(ganancia_distancia(0.0, 20.0), 1.0);
        assert!((ganancia_distancia(10.0, 20.0) - 0.25).abs() < 1e-6);
        assert_eq!(ganancia_distancia(20.0, 20.0), 0.0);
        assert_eq!(ganancia_distancia(50.0, 20.0), 0.0, "más lejos no se oye");
        assert!(ganancia_distancia(5.0, 20.0) > ganancia_distancia(6.0, 20.0));
    }

    #[test]
    fn req_son_05_de_dia_pajaros_y_de_noche_grillos() {
        let dia = capas_ambiente(&Entorno { minuto: 13.0 * 60.0, gente: 0, lluvia: 0.0, viento: 0.0 });
        assert_eq!(nivel(&dia, ids::PAJAROS), 1.0);
        assert_eq!(nivel(&dia, ids::GRILLOS), 0.0);
        let noche = capas_ambiente(&Entorno { minuto: 23.0 * 60.0, gente: 0, lluvia: 0.0, viento: 0.0 });
        assert_eq!(nivel(&noche, ids::PAJAROS), 0.0);
        assert_eq!(nivel(&noche, ids::GRILLOS), 1.0);
    }

    #[test]
    fn req_son_05_fundido_de_30_minutos_y_nunca_los_dos_a_pleno() {
        let salida = SALIDA_SOL as f32;
        assert_eq!(nivel_dia(salida - 15.0), 0.0);
        assert!((nivel_dia(salida) - 0.5).abs() < 1e-3);
        assert_eq!(nivel_dia(salida + 15.0), 1.0);
        let puesta = PUESTA_SOL as f32;
        assert_eq!(nivel_dia(puesta - 15.0), 1.0);
        assert!((nivel_dia(puesta) - 0.5).abs() < 1e-3);
        assert_eq!(nivel_dia(puesta + 15.0), 0.0);
        for m in 0..1440 {
            let c = capas_ambiente(&Entorno { minuto: m as f32, gente: 5, lluvia: 0.0, viento: 0.0 });
            let (p, g) = (nivel(&c, ids::PAJAROS), nivel(&c, ids::GRILLOS));
            assert!(p + g <= 1.0 + 1e-5, "a las {m} suenan los dos ({p}, {g})");
        }
    }

    #[test]
    fn req_son_06_murmullo_segun_la_gente_y_baja_de_noche() {
        let e = |gente, minuto| Entorno { minuto, gente, lluvia: 0.0, viento: 0.0 };
        let m = |gente, minuto| nivel(&capas_ambiente(&e(gente, minuto)), ids::MURMULLO_PLAZA);
        assert_eq!(m(0, 780.0), 0.0);
        assert!((m(10, 780.0) - 0.5).abs() < 1e-5);
        assert_eq!(m(20, 780.0), 1.0);
        assert_eq!(m(60, 780.0), 1.0, "tope en 20 peatones");
        assert!((m(20, 23.0 * 60.0) - 0.4).abs() < 1e-5, "de noche, 40%");
    }

    #[test]
    fn req_son_07_viento_siempre_bajito_y_lluvia_solo_si_llueve() {
        let e = |viento, lluvia| Entorno { minuto: 780.0, gente: 0, lluvia, viento };
        let c = capas_ambiente(&e(0.0, 0.0));
        assert!((nivel(&c, ids::VIENTO) - 0.2).abs() < 1e-6);
        assert_eq!(nivel(&c, ids::LLUVIA), 0.0);
        let c = capas_ambiente(&e(1.0, 0.7));
        assert_eq!(nivel(&c, ids::VIENTO), 1.0);
        assert!((nivel(&c, ids::LLUVIA) - 0.7).abs() < 1e-6);
    }
}
