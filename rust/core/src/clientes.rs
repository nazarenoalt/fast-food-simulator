//! SPEC-009 · Clientes: llegada, fila, pedido, paciencia y evaluación.

use crate::azar::Azar;
use crate::coccion::Punto;

pub const LUGARES_FILA: usize = 6; // REQ-CLI-03
pub const SEPARACION_FILA: f32 = 0.85;
pub const PACIENCIA_S: f32 = 100.0; // REQ-CLI-06
pub const PENALIDAD_RECHAZO_S: f32 = 20.0; // REQ-CLI-08
pub const PROPINA_MAX: f32 = 0.2; // REQ-CLI-09

/// REQ-CLI-01: factor por reputación (0 estrellas → 0,4; 5 estrellas → 1,6).
pub fn factor_reputacion(reputacion: f32) -> f32 {
    0.4 + 0.24 * reputacion.clamp(0.0, 5.0)
}

/// REQ-CLI-01: clientes esperados por hora de juego, según la hora (0–24) y la reputación.
pub fn tasa_clientes(hora: f32, reputacion: f32) -> f32 {
    let h = hora.rem_euclid(24.0);
    let campana = |centro: f32, ancho: f32| (-((h - centro) / ancho).powi(2)).exp();
    let base = if (7.0..23.5).contains(&h) {
        0.8
    } else if h < 7.0 {
        0.05
    } else {
        0.3
    };
    let picos = 2.2 * campana(13.0, 1.0) + 2.0 * campana(21.0, 1.1);
    (base + picos) * factor_reputacion(reputacion)
}

/// REQ-CLI-03: fila de hasta 6 personas. Guarda ids de clientes en orden.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Fila {
    ids: Vec<u64>,
}

impl Fila {
    pub fn llena(&self) -> bool {
        self.ids.len() >= LUGARES_FILA
    }
    pub fn len(&self) -> usize {
        self.ids.len()
    }
    pub fn is_empty(&self) -> bool {
        self.ids.is_empty()
    }
    /// Devuelve el lugar asignado, o `None` si está llena.
    pub fn unirse(&mut self, id: u64) -> Option<usize> {
        if self.llena() || self.ids.contains(&id) {
            return None;
        }
        self.ids.push(id);
        Some(self.ids.len() - 1)
    }
    /// Al salir uno, los de atrás avanzan.
    pub fn salir(&mut self, id: u64) {
        self.ids.retain(|&x| x != id);
    }
    pub fn lugar(&self, id: u64) -> Option<usize> {
        self.ids.iter().position(|&x| x == id)
    }
    pub fn primero(&self) -> Option<u64> {
        self.ids.first().copied()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Pedido {
    pub producto: String,
    pub aderezos: Vec<String>,
}

/// REQ-CLI-04: un producto del menú y de 0 a 2 aderezos disponibles (25% sin aderezos).
pub fn generar_pedido(azar: &mut Azar, menu: &[String], aderezos: &[String]) -> Pedido {
    let producto = azar.elegir(menu).cloned().unwrap_or_default();
    let mut elegidos = Vec::new();
    if !aderezos.is_empty() && !azar.chance(0.25) {
        let cuantos = if aderezos.len() >= 2 && azar.chance(0.5) { 2 } else { 1 };
        let mut disponibles = aderezos.to_vec();
        for _ in 0..cuantos {
            let i = azar.entero(disponibles.len());
            elegidos.push(disponibles.remove(i));
        }
    }
    Pedido { producto, aderezos: elegidos }
}

/// Paciencia de un cliente. REQ-CLI-06
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Paciencia {
    pub restante: f32,
}

impl Default for Paciencia {
    fn default() -> Self {
        Self { restante: PACIENCIA_S }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Animo {
    Contento,
    Impaciente,
    Enojado,
}

impl Paciencia {
    /// Avanza `dt` segundos. Mientras está en la fila sin haber pedido baja a mitad de
    /// velocidad. Devuelve `true` si se agotó.
    pub fn paso(&mut self, dt: f32, ya_pidio: bool) -> bool {
        let factor = if ya_pidio { 1.0 } else { 0.5 };
        self.restante = (self.restante - dt * factor).max(0.0);
        self.restante <= 0.0
    }
    pub fn penalizar(&mut self, s: f32) {
        self.restante = (self.restante - s).max(0.0);
    }
    /// Cuánto de la paciencia ya gastó (0 a 1).
    pub fn usada(&self) -> f32 {
        1.0 - self.restante / PACIENCIA_S
    }
    /// REQ-CLI-05: verde, amarillo, rojo.
    pub fn animo(&self) -> Animo {
        match self.usada() {
            u if u < 0.5 => Animo::Contento,
            u if u < 0.8 => Animo::Impaciente,
            _ => Animo::Enojado,
        }
    }
}

/// Lo que se le entregó al cliente.
#[derive(Debug, Clone, PartialEq)]
pub struct Entregado {
    pub producto: String,
    /// Punto de cocción de la parte cocinada (la salchicha del pancho), si tiene.
    pub punto: Option<Punto>,
    pub aderezos: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rechazo {
    OtroProducto,
    Crudo,
    Quemado,
}

impl Rechazo {
    pub fn frase(self) -> &'static str {
        match self {
            Rechazo::OtroProducto => "¡Esto no es lo que pedí!",
            Rechazo::Crudo => "¡Está cruda!",
            Rechazo::Quemado => "¡Está quemada!",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Evaluacion {
    pub estrellas: f32,
    pub pago: f32,
    pub propina: f32,
}

/// REQ-CLI-08, REQ-CLI-09
pub fn evaluar(
    pedido: &Pedido,
    entregado: &Entregado,
    precio: f32,
    paciencia_usada: f32,
) -> Result<Evaluacion, Rechazo> {
    if entregado.producto != pedido.producto {
        return Err(Rechazo::OtroProducto);
    }
    match entregado.punto {
        Some(Punto::Crudo) => return Err(Rechazo::Crudo),
        Some(Punto::Quemado) => return Err(Rechazo::Quemado),
        _ => {}
    }
    let faltan = pedido.aderezos.iter().filter(|a| !entregado.aderezos.contains(a)).count() as f32;
    let sobran = entregado.aderezos.iter().filter(|a| !pedido.aderezos.contains(a)).count() as f32;
    let pasado = if entregado.punto == Some(Punto::Pasado) { 1.5 } else { 0.0 };
    let espera = 1.5 * paciencia_usada.clamp(0.0, 1.0);
    let estrellas = (5.0 - faltan - 0.5 * sobran - pasado - espera).clamp(1.0, 5.0);
    let propina = precio * PROPINA_MAX * ((estrellas - 3.0) / 2.0).max(0.0);
    Ok(Evaluacion { estrellas, pago: precio, propina })
}

/// "★★★★☆"
pub fn estrellas_texto(e: f32) -> String {
    let llenas = e.round().clamp(0.0, 5.0) as usize;
    "★".repeat(llenas) + &"☆".repeat(5 - llenas)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pedido(ad: &[&str]) -> Pedido {
        Pedido { producto: "pancho".into(), aderezos: ad.iter().map(|s| s.to_string()).collect() }
    }
    fn entregado(punto: Punto, ad: &[&str]) -> Entregado {
        Entregado {
            producto: "pancho".into(),
            punto: Some(punto),
            aderezos: ad.iter().map(|s| s.to_string()).collect(),
        }
    }

    #[test]
    fn req_cli_01_tasa_segun_hora_y_reputacion() {
        assert!(tasa_clientes(4.0, 3.0) < 0.1);
        assert!(tasa_clientes(13.0, 3.0) > tasa_clientes(10.0, 3.0) * 2.0);
        assert!(tasa_clientes(21.0, 3.0) > tasa_clientes(17.0, 3.0) * 2.0);
        assert!((factor_reputacion(0.0) - 0.4).abs() < 1e-6);
        assert!((factor_reputacion(5.0) - 1.6).abs() < 1e-6);
        assert!(tasa_clientes(13.0, 5.0) > tasa_clientes(13.0, 1.0));
    }

    #[test]
    fn req_cli_03_fila_de_seis_que_avanza() {
        let mut f = Fila::default();
        for id in 0..6 {
            assert_eq!(f.unirse(id), Some(id as usize));
        }
        assert!(f.llena());
        assert_eq!(f.unirse(99), None);
        f.salir(0);
        assert_eq!(f.primero(), Some(1));
        assert_eq!(f.lugar(5), Some(4));
        assert!(!f.llena());
    }

    #[test]
    fn req_cli_04_pedido_con_0_a_2_aderezos_disponibles() {
        let mut azar = Azar::new(1);
        let menu = vec!["pancho".to_string()];
        let ad: Vec<String> = ["mostaza", "ketchup", "mayonesa"].iter().map(|s| s.to_string()).collect();
        let mut sin = 0;
        for _ in 0..2000 {
            let p = generar_pedido(&mut azar, &menu, &ad);
            assert_eq!(p.producto, "pancho");
            assert!(p.aderezos.len() <= 2);
            assert!(p.aderezos.iter().all(|a| ad.contains(a)));
            let mut u = p.aderezos.clone();
            u.dedup();
            assert_eq!(u.len(), p.aderezos.len(), "sin repetidos");
            if p.aderezos.is_empty() {
                sin += 1;
            }
        }
        assert!((400..600).contains(&sin), "25% sin aderezos: {sin}");
        // Sin aderecera, nunca pide aderezos.
        assert!(generar_pedido(&mut azar, &menu, &[]).aderezos.is_empty());
    }

    #[test]
    fn req_cli_05_06_paciencia_y_animo() {
        let mut p = Paciencia::default();
        assert_eq!(p.animo(), Animo::Contento);
        p.paso(10.0, false);
        assert_eq!(p.restante, 95.0, "en la fila baja a la mitad");
        p.paso(45.0, true);
        assert_eq!(p.animo(), Animo::Impaciente);
        p.paso(30.0, true);
        assert_eq!(p.animo(), Animo::Enojado);
        assert!(p.paso(100.0, true));
    }

    #[test]
    fn req_cli_08_rechazos() {
        let ped = pedido(&["mostaza"]);
        assert_eq!(evaluar(&ped, &entregado(Punto::Crudo, &["mostaza"]), 2500.0, 0.0), Err(Rechazo::Crudo));
        assert_eq!(evaluar(&ped, &entregado(Punto::Quemado, &["mostaza"]), 2500.0, 0.0), Err(Rechazo::Quemado));
        let otro = Entregado { producto: "salchicha".into(), punto: Some(Punto::Cocido), aderezos: vec![] };
        assert_eq!(evaluar(&ped, &otro, 2500.0, 0.0), Err(Rechazo::OtroProducto));
        let mut pac = Paciencia::default();
        pac.penalizar(PENALIDAD_RECHAZO_S);
        assert_eq!(pac.restante, 80.0);
    }

    #[test]
    fn req_cli_08_estrellas() {
        let ped = pedido(&["mostaza", "ketchup"]);
        let perfecto = evaluar(&ped, &entregado(Punto::Cocido, &["ketchup", "mostaza"]), 2500.0, 0.0).unwrap();
        assert_eq!(perfecto.estrellas, 5.0);
        let falta = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza"]), 2500.0, 0.0).unwrap();
        assert_eq!(falta.estrellas, 4.0);
        let sobra = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza", "ketchup", "mayonesa"]), 2500.0, 0.0).unwrap();
        assert_eq!(sobra.estrellas, 4.5);
        let pasado = evaluar(&ped, &entregado(Punto::Pasado, &["mostaza", "ketchup"]), 2500.0, 0.0).unwrap();
        assert_eq!(pasado.estrellas, 3.5);
        let lento = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza", "ketchup"]), 2500.0, 1.0).unwrap();
        assert_eq!(lento.estrellas, 3.5);
        let todo_mal = evaluar(&ped, &entregado(Punto::Pasado, &["mayonesa"]), 2500.0, 1.0).unwrap();
        assert_eq!(todo_mal.estrellas, 1.0);
    }

    #[test]
    fn req_cli_09_pago_y_propina() {
        let ped = pedido(&[]);
        let e5 = evaluar(&ped, &entregado(Punto::Cocido, &[]), 2500.0, 0.0).unwrap();
        assert_eq!((e5.pago, e5.propina), (2500.0, 500.0));
        let e3 = evaluar(&ped, &entregado(Punto::Pasado, &[]), 2500.0, 0.0).unwrap();
        assert_eq!(e3.estrellas, 3.5);
        assert!((e3.propina - 125.0).abs() < 1e-3);
        let e_baja = evaluar(&ped, &entregado(Punto::Pasado, &["x"]), 2500.0, 0.5).unwrap();
        assert_eq!(e_baja.propina, 0.0);
    }

    #[test]
    fn req_cli_10_texto_de_estrellas() {
        assert_eq!(estrellas_texto(4.4), "★★★★☆");
        assert_eq!(estrellas_texto(1.0), "★☆☆☆☆");
    }
}
