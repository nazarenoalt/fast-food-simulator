//! SPEC-009 · Clientes: llegada, fila, pedido, paciencia y evaluación.

use crate::azar::Azar;
use crate::coccion::Punto;
use crate::tostado::EstadoPan;

pub const LUGARES_FILA: usize = 6; // REQ-CLI-03
pub const SEPARACION_FILA: f32 = 0.85;
pub const PACIENCIA_S: f32 = 150.0; // REQ-CLI-06
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

/// REQ-CLI-01: factor por el menú: × (1 + 0,15 × (productos del menú − 1)). Con uno solo, 1.
pub fn factor_menu(productos: usize) -> f32 {
    1.0 + 0.15 * (productos.max(1) - 1) as f32
}

/// REQ-ARR-05 (y REQ-CLI-01, REQ-CLI-03): la primera semana los clientes van subiendo. Devuelve
/// el factor de clientes y los lugares de la fila del día `dia` (el 1 es el primero).
pub fn rampa(dia: u32) -> (f32, usize) {
    match dia {
        0 | 1 => (0.3, 3),
        2 => (0.45, 4),
        3 => (0.6, 5),
        4 => (0.75, LUGARES_FILA),
        5 => (0.9, LUGARES_FILA),
        _ => (1.0, LUGARES_FILA),
    }
}

/// REQ-CLI-03: fila de hasta 6 personas (menos la primera semana, REQ-ARR-05). Guarda ids de
/// clientes en orden.
#[derive(Debug, Clone, PartialEq)]
pub struct Fila {
    ids: Vec<u64>,
    /// Lugares que tiene hoy (REQ-ARR-05).
    lugares: usize,
}

impl Default for Fila {
    fn default() -> Self {
        Self { ids: Vec::new(), lugares: LUGARES_FILA }
    }
}

impl Fila {
    /// REQ-ARR-05: cambia los lugares de la fila. Si ya hay más gente, nadie se va: solo no se
    /// suma nadie hasta que haya lugar.
    pub fn set_lugares(&mut self, lugares: usize) {
        self.lugares = lugares.clamp(1, LUGARES_FILA);
    }
    pub fn lugares(&self) -> usize {
        self.lugares
    }
    pub fn llena(&self) -> bool {
        self.ids.len() >= self.lugares
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

/// REQ-CLI-13: el `cartel_cerrado` está colgado (se lee «CERRADO») o descolgado (no se ve).
/// Arranca colgado; el clic con la mano libre o E en su zona lo alterna.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CartelCerrado {
    pub colgado: bool,
}

impl Default for CartelCerrado {
    fn default() -> Self {
        Self { colgado: true }
    }
}

impl CartelCerrado {
    pub fn alternar(&mut self) {
        self.colgado = !self.colgado;
    }

    /// Lo que dice el cartel de la mira. REQ-CLI-13
    pub fn accion(&self) -> &'static str {
        if self.colgado {
            "[Clic/E] Abrir el puesto (sacar el cartel)"
        } else {
            "[Clic/E] Cerrar el puesto (colgar el cartel)"
        }
    }

    /// REQ-CLI-13: descolgado, el cartel desaparece; su zona de uso queda en el frente.
    pub fn se_ve(&self) -> bool {
        self.colgado
    }
}

/// REQ-CLI-13: zona de uso del cartel (caja que solo ve la mira), relativa al clavo del anclaje
/// `cartel` (REQ-PAP-07): medidas y centro. Queda en el frente aunque el cartel esté descolgado,
/// para volver a colgarlo desde la vereda. Cubre el tablero (de 10 a 26 cm abajo del clavo) con
/// margen y sale 6 cm hacia la vereda, pero no sube más de 8 mm sobre el clavo: la mesada está
/// 12 mm arriba, así que no asoma sobre el mostrador ni le roba la mira a lo que está apoyado.
pub const ZONA_CARTEL_MEDIDAS: [f32; 3] = [0.40, 0.29, 0.08];
pub const ZONA_CARTEL_CENTRO: [f32; 3] = [0.0, -0.137, 0.02];

/// REQ-CLI-12 (y REQ-CLI-03): ¿se suma a la fila un cliente nuevo que llega solo? No si la fila
/// está llena ni con el cartel de cerrado colgado. Sin cartel (`None`) o descolgado, está
/// abierto. (La tecla C de REQ-CLI-11 no pasa por acá: trae clientes igual.)
pub fn llegan_clientes(fila: &Fila, cartel: Option<CartelCerrado>) -> bool {
    !fila.llena() && cartel.is_none_or(|c| !c.colgado)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Pedido {
    pub producto: String,
    pub aderezos: Vec<String>,
}

/// Un producto del menú con los aderezos que admite (SPEC-012). REQ-CLI-04
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ItemMenu {
    pub producto: String,
    pub aderezos: Vec<String>,
}

/// REQ-CLI-04: un producto del menú (todos con la misma chance) y de 0 a 2 aderezos que ese
/// producto admite y el carrito tiene disponibles (25% sin aderezos).
pub fn generar_pedido(azar: &mut Azar, menu: &[ItemMenu], disponibles: &[String]) -> Pedido {
    let Some(item) = azar.elegir(menu) else { return Pedido { producto: String::new(), aderezos: Vec::new() } };
    let mut posibles: Vec<String> = item.aderezos.iter().filter(|a| disponibles.contains(a)).cloned().collect();
    let mut elegidos = Vec::new();
    if !posibles.is_empty() && !azar.chance(0.25) {
        let cuantos = if posibles.len() >= 2 && azar.chance(0.5) { 2 } else { 1 };
        for _ in 0..cuantos {
            let i = azar.entero(posibles.len());
            elegidos.push(posibles.remove(i));
        }
    }
    Pedido { producto: item.producto.clone(), aderezos: elegidos }
}

/// Paciencia de un cliente. REQ-CLI-06
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Paciencia {
    pub restante: f32,
    /// Con cuánta empezó (REQ-RUT-04, REQ-HAB-06: el perfil y los habituales la cambian).
    pub total: f32,
}

impl Default for Paciencia {
    fn default() -> Self {
        Self { restante: PACIENCIA_S, total: PACIENCIA_S }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Animo {
    Contento,
    Impaciente,
    Enojado,
}

impl Paciencia {
    /// REQ-RUT-04, REQ-HAB-06: la paciencia de REQ-CLI-06 multiplicada por `factor`.
    pub fn con_factor(factor: f32) -> Self {
        let total = PACIENCIA_S * factor.max(0.1);
        Self { restante: total, total }
    }

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
        1.0 - self.restante / self.total
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
    /// Estado del pan, si el producto lleva pan tostado (choripán). REQ-PAR-07
    pub pan: Option<EstadoPan>,
    /// Frescura de la carne en % (SPEC-016), si es perecedera. REQ-HEL-04
    pub frescura: Option<f32>,
    pub aderezos: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rechazo {
    OtroProducto,
    Crudo,
    Quemado,
    PanBlando,
    PanQuemado,
    EchadaAPerder,
}

impl Rechazo {
    /// REQ-CLI-08: dice por qué, concordando con lo que se entregó (`producto` es su id).
    pub fn frase(self, producto: &str) -> &'static str {
        match (self, producto) {
            (Rechazo::OtroProducto, _) => "¡Esto no es lo que pedí!",
            (Rechazo::Crudo, "pancho") => "¡La salchicha está cruda!",
            (Rechazo::Crudo, "choripan") => "¡El chorizo está crudo!",
            (Rechazo::Crudo, "papas_en_cajita") => "¡Están crudas!",
            (Rechazo::Crudo, _) => "¡Está cruda!",
            (Rechazo::Quemado, "pancho") => "¡La salchicha está quemada!",
            (Rechazo::Quemado, "choripan") => "¡El chorizo está quemado!",
            (Rechazo::Quemado, "papas_en_cajita") => "¡Están quemadas!",
            (Rechazo::Quemado, _) => "¡Está quemada!",
            (Rechazo::PanBlando, _) => "¡El pan está blando!",
            (Rechazo::PanQuemado, _) => "¡El pan está quemado!",
            (Rechazo::EchadaAPerder, _) => "¡Esto está echado a perder!",
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
    // REQ-HEL-04: carne echada a perder, rechazada.
    if entregado.frescura.is_some_and(|f| f <= 0.0) {
        return Err(Rechazo::EchadaAPerder);
    }
    match entregado.punto {
        Some(Punto::Crudo) => return Err(Rechazo::Crudo),
        Some(Punto::Quemado) => return Err(Rechazo::Quemado),
        _ => {}
    }
    // REQ-PAR-07: el pan del choripán tiene que estar tostado.
    match entregado.pan {
        Some(EstadoPan::Blando) => return Err(Rechazo::PanBlando),
        Some(EstadoPan::Quemado) => return Err(Rechazo::PanQuemado),
        _ => {}
    }
    let faltan = pedido.aderezos.iter().filter(|a| !entregado.aderezos.contains(a)).count() as f32;
    let sobran = entregado.aderezos.iter().filter(|a| !pedido.aderezos.contains(a)).count() as f32;
    let pasado = if entregado.punto == Some(Punto::Pasado) { 1.5 } else { 0.0 };
    // REQ-HEL-07: carne con frescura dudosa descuenta una estrella aunque esté bien cocida.
    let dudosa = if entregado.frescura.is_some_and(|f| f < crate::heladera::FRESCURA_DUDOSA) { 1.0 } else { 0.0 };
    let espera = 1.5 * paciencia_usada.clamp(0.0, 1.0);
    let estrellas = (5.0 - faltan - 0.5 * sobran - pasado - dudosa - espera).clamp(1.0, 5.0);
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
            pan: None,
            frescura: None,
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
    fn req_cli_01_factor_por_menu() {
        assert_eq!(factor_menu(1), 1.0);
        assert!((factor_menu(2) - 1.15).abs() < 1e-6);
        assert!((factor_menu(4) - 1.45).abs() < 1e-6);
        // Sin menú no baja de 1 (no hay productos de menos).
        assert_eq!(factor_menu(0), 1.0);
    }

    #[test]
    fn req_arr_05_cli_03_rampa_de_la_primera_semana() {
        let esperado = [(1, 0.3, 3), (2, 0.45, 4), (3, 0.6, 5), (4, 0.75, 6), (5, 0.9, 6), (6, 1.0, 6), (7, 1.0, 6)];
        for (dia, factor, lugares) in esperado {
            let (f, l) = rampa(dia);
            assert!((f - factor).abs() < 1e-6, "día {dia}: ×{f}");
            assert_eq!(l, lugares, "día {dia}");
        }
        for dia in 8..40 {
            assert_eq!(rampa(dia), (1.0, LUGARES_FILA), "día {dia}");
        }
    }

    #[test]
    fn req_arr_05_cli_03_la_fila_respeta_los_lugares_del_dia() {
        let mut f = Fila::default();
        f.set_lugares(rampa(1).1);
        for id in 0..3 {
            assert_eq!(f.unirse(id), Some(id as usize));
        }
        assert!(f.llena());
        assert_eq!(f.unirse(3), None, "el día 1 la fila tiene 3 lugares");
        assert!(!llegan_clientes(&f, None));
        // Al día siguiente hay un lugar más.
        f.set_lugares(rampa(2).1);
        assert!(!f.llena());
        assert_eq!(f.unirse(3), Some(3));
        assert!(f.llena());
        // Si los lugares bajan con gente de más, nadie se va pero no entra nadie.
        f.set_lugares(3);
        assert_eq!(f.len(), 4);
        assert_eq!(f.unirse(9), None);
        f.salir(0);
        f.salir(1);
        assert!(!f.llena());
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

    fn item(p: &str, ad: &[&str]) -> ItemMenu {
        ItemMenu { producto: p.into(), aderezos: ad.iter().map(|s| s.to_string()).collect() }
    }

    #[test]
    fn req_cli_04_pedido_con_0_a_2_aderezos_disponibles() {
        let mut azar = Azar::new(1);
        let menu = vec![item("pancho", &["mostaza", "ketchup", "mayonesa"])];
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
    fn req_cli_04_menu_de_varios_productos_con_sus_aderezos() {
        let mut azar = Azar::new(7);
        let menu = vec![
            item("pancho", &["mostaza", "papas_pay"]),
            item("hamburguesa", &[]),
            item("choripan", &["chimichurri", "mostaza"]),
        ];
        let disponibles: Vec<String> =
            ["mostaza", "papas_pay", "chimichurri", "ketchup"].iter().map(|s| s.to_string()).collect();
        let (mut p, mut h, mut c) = (0, 0, 0);
        for _ in 0..3000 {
            let ped = generar_pedido(&mut azar, &menu, &disponibles);
            let admitidos = &menu.iter().find(|i| i.producto == ped.producto).unwrap().aderezos;
            assert!(ped.aderezos.iter().all(|a| admitidos.contains(a)), "{ped:?}");
            match ped.producto.as_str() {
                "pancho" => p += 1,
                "hamburguesa" => {
                    h += 1;
                    assert!(ped.aderezos.is_empty(), "la hamburguesa no lleva aderezos");
                }
                _ => c += 1,
            }
        }
        for n in [p, h, c] {
            assert!((850..1150).contains(&n), "reparto parejo: {p}/{h}/{c}");
        }
        // Un aderezo que el carrito no tiene no se pide aunque el producto lo admita.
        let sin_chimi: Vec<String> = vec!["mostaza".into()];
        for _ in 0..500 {
            assert!(!generar_pedido(&mut azar, &menu, &sin_chimi).aderezos.contains(&"chimichurri".to_string()));
        }
    }

    #[test]
    fn req_cli_05_06_paciencia_y_animo() {
        let mut p = Paciencia::default();
        assert_eq!(p.total, 150.0, "REQ-CLI-06: 150 s");
        assert_eq!(p.animo(), Animo::Contento);
        p.paso(10.0, false);
        assert_eq!(p.restante, 145.0, "en la fila baja a la mitad");
        p.paso(70.0, true);
        assert_eq!(p.animo(), Animo::Impaciente);
        p.paso(45.0, true);
        assert_eq!(p.animo(), Animo::Enojado);
        assert!(!p.paso(29.0, true));
        assert!(p.paso(1.0, true), "se agota a los 150 s");
    }

    #[test]
    fn req_cli_08_rechazos() {
        let ped = pedido(&["mostaza"]);
        assert_eq!(evaluar(&ped, &entregado(Punto::Crudo, &["mostaza"]), 10.0, 0.0), Err(Rechazo::Crudo));
        assert_eq!(evaluar(&ped, &entregado(Punto::Quemado, &["mostaza"]), 10.0, 0.0), Err(Rechazo::Quemado));
        let otro = Entregado {
            producto: "salchicha".into(),
            punto: Some(Punto::Cocido),
            pan: None,
            frescura: None,
            aderezos: vec![],
        };
        assert_eq!(evaluar(&ped, &otro, 10.0, 0.0), Err(Rechazo::OtroProducto));
        let mut pac = Paciencia::default();
        pac.penalizar(PENALIDAD_RECHAZO_S);
        assert_eq!(pac.restante, 130.0);
    }

    #[test]
    fn req_par_07_choripan_con_pan_blando_o_quemado_se_rechaza() {
        let ped = Pedido { producto: "choripan".into(), aderezos: vec![] };
        let choripan = |punto, pan| Entregado {
            producto: "choripan".into(),
            punto: Some(punto),
            pan: Some(pan),
            frescura: None,
            aderezos: vec![],
        };
        assert_eq!(evaluar(&ped, &choripan(Punto::Cocido, EstadoPan::Blando), 12.0, 0.0), Err(Rechazo::PanBlando));
        assert_eq!(evaluar(&ped, &choripan(Punto::Cocido, EstadoPan::Quemado), 12.0, 0.0), Err(Rechazo::PanQuemado));
        assert_eq!(evaluar(&ped, &choripan(Punto::Crudo, EstadoPan::Tostado), 12.0, 0.0), Err(Rechazo::Crudo));
        assert_eq!(evaluar(&ped, &choripan(Punto::Quemado, EstadoPan::Tostado), 12.0, 0.0), Err(Rechazo::Quemado));
    }

    #[test]
    fn req_par_07_choripan_con_chorizo_cocido_y_pan_tostado_se_acepta() {
        let ped = Pedido { producto: "choripan".into(), aderezos: vec![] };
        let e = Entregado {
            producto: "choripan".into(),
            punto: Some(Punto::Cocido),
            pan: Some(EstadoPan::Tostado),
            frescura: None,
            aderezos: vec![],
        };
        assert!(evaluar(&ped, &e, 12.0, 0.0).is_ok());
    }

    #[test]
    fn req_cli_08_estrellas() {
        let ped = pedido(&["mostaza", "ketchup"]);
        let perfecto = evaluar(&ped, &entregado(Punto::Cocido, &["ketchup", "mostaza"]), 10.0, 0.0).unwrap();
        assert_eq!(perfecto.estrellas, 5.0);
        let falta = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza"]), 10.0, 0.0).unwrap();
        assert_eq!(falta.estrellas, 4.0);
        let sobra = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza", "ketchup", "mayonesa"]), 10.0, 0.0).unwrap();
        assert_eq!(sobra.estrellas, 4.5);
        let pasado = evaluar(&ped, &entregado(Punto::Pasado, &["mostaza", "ketchup"]), 10.0, 0.0).unwrap();
        assert_eq!(pasado.estrellas, 3.5);
        let lento = evaluar(&ped, &entregado(Punto::Cocido, &["mostaza", "ketchup"]), 10.0, 1.0).unwrap();
        assert_eq!(lento.estrellas, 3.5);
        let todo_mal = evaluar(&ped, &entregado(Punto::Pasado, &["mayonesa"]), 10.0, 1.0).unwrap();
        assert_eq!(todo_mal.estrellas, 1.0);
    }

    #[test]
    fn req_cli_09_pago_y_propina() {
        let ped = pedido(&[]);
        let e5 = evaluar(&ped, &entregado(Punto::Cocido, &[]), 10.0, 0.0).unwrap();
        assert_eq!((e5.pago, e5.propina), (10.0, 2.0));
        let e3 = evaluar(&ped, &entregado(Punto::Pasado, &[]), 10.0, 0.0).unwrap();
        assert_eq!(e3.estrellas, 3.5);
        assert!((e3.propina - 0.5).abs() < 1e-3);
        let e_baja = evaluar(&ped, &entregado(Punto::Pasado, &["x"]), 10.0, 0.5).unwrap();
        assert_eq!(e_baja.propina, 0.0);
    }

    fn papas(punto: Punto, ad: &[&str]) -> Entregado {
        Entregado {
            producto: "papas_en_cajita".into(),
            punto: Some(punto),
            pan: None,
            frescura: None,
            aderezos: ad.iter().map(|s| s.to_string()).collect(),
        }
    }

    #[test]
    fn req_cli_08_la_frase_concuerda() {
        assert_eq!(Rechazo::Crudo.frase("papas_en_cajita"), "¡Están crudas!");
        assert_eq!(Rechazo::Crudo.frase("choripan"), "¡El chorizo está crudo!");
        assert_eq!(Rechazo::Quemado.frase("pancho"), "¡La salchicha está quemada!");
        assert_eq!(Rechazo::Crudo.frase("hamburguesa"), "¡Está cruda!");
    }

    #[test]
    fn req_rut_04_paciencia_con_factor() {
        // REQ-CLI-06 con los perfiles de agenda.ron: oficinista ×0,8 → 120 s, jubilado ×1,2 → 180 s.
        let mut p = Paciencia::con_factor(0.8);
        assert_eq!(p.restante, 120.0);
        assert!((Paciencia::con_factor(1.2).total - 180.0).abs() < 1e-4);
        p.paso(60.0, true);
        assert!((p.usada() - 0.5).abs() < 1e-5);
        assert_eq!(Paciencia::default().total, PACIENCIA_S);
    }

    #[test]
    fn req_cli_08_fre_11_papas_crudas_o_quemadas_se_rechazan() {
        let ped = Pedido { producto: "papas_en_cajita".into(), aderezos: vec!["ketchup".into()] };
        assert_eq!(evaluar(&ped, &papas(Punto::Crudo, &["ketchup"]), 8.0, 0.0), Err(Rechazo::Crudo));
        assert_eq!(evaluar(&ped, &papas(Punto::Quemado, &["ketchup"]), 8.0, 0.0), Err(Rechazo::Quemado));
        // Un pancho no es lo que pidió.
        assert_eq!(evaluar(&ped, &entregado(Punto::Cocido, &["ketchup"]), 8.0, 0.0), Err(Rechazo::OtroProducto));
    }

    #[test]
    fn req_cli_08_09_fre_11_papas_cocidas_y_pasadas() {
        let ped = Pedido { producto: "papas_en_cajita".into(), aderezos: vec!["ketchup".into(), "mayonesa".into()] };
        let bien = evaluar(&ped, &papas(Punto::Cocido, &["mayonesa", "ketchup"]), 8.0, 0.0).unwrap();
        assert_eq!(bien.estrellas, 5.0);
        // REQ-CLI-09: $8 más el 20% de propina con 5 estrellas.
        assert_eq!(bien.pago, 8.0);
        assert!((bien.propina - 1.6).abs() < 1e-4);
        // −1,5 si están pasadas.
        let pasadas = evaluar(&ped, &papas(Punto::Pasado, &["ketchup", "mayonesa"]), 8.0, 0.0).unwrap();
        assert_eq!(pasadas.estrellas, 3.5);
        let sin_mayonesa = evaluar(&ped, &papas(Punto::Pasado, &["ketchup"]), 8.0, 0.0).unwrap();
        assert_eq!(sin_mayonesa.estrellas, 2.5);
        assert_eq!(sin_mayonesa.propina, 0.0);
    }

    #[test]
    fn req_cli_12_con_el_cartel_colgado_no_llegan_clientes_nuevos() {
        let mut fila = Fila::default();
        fila.unirse(1);
        // Sin cartel, abierto.
        assert!(llegan_clientes(&fila, None));
        // Colgado: no se suma nadie, pero el que estaba sigue en la fila.
        let colgado = CartelCerrado::default();
        assert!(!llegan_clientes(&fila, Some(colgado)));
        assert_eq!(fila.primero(), Some(1));
        // Descolgado: abierto otra vez.
        assert!(llegan_clientes(&fila, Some(CartelCerrado { colgado: false })));
        // REQ-CLI-03: con la fila llena no llega nadie, aunque esté abierto.
        for id in 2..=LUGARES_FILA as u64 {
            fila.unirse(id);
        }
        assert!(!llegan_clientes(&fila, None));
    }

    #[test]
    fn req_cli_13_el_cartel_arranca_colgado_y_se_alterna_desapareciendo() {
        let mut c = CartelCerrado::default();
        assert!(c.colgado && c.se_ve());
        assert_eq!(c.accion(), "[Clic/E] Abrir el puesto (sacar el cartel)");
        // Descolgado: abierto y no se ve.
        c.alternar();
        assert!(!c.colgado && !c.se_ve());
        assert_eq!(c.accion(), "[Clic/E] Cerrar el puesto (colgar el cartel)");
        c.alternar();
        assert!(c.colgado && c.se_ve());
    }

    #[test]
    fn req_cli_13_la_zona_del_cartel_se_toca_desde_la_vereda_sin_tapar_el_mostrador() {
        use crate::datos::tests::catalogo_real;
        let cat = catalogo_real();
        let [mx, my, mz] = ZONA_CARTEL_MEDIDAS;
        let [cx, cy, cz] = ZONA_CARTEL_CENTRO;
        // Cubre el tablero del cartel (REQ-PAP-07), relativo al clavo.
        let cartel = cat.accesorios.iter().find(|a| a.id == "cartel_cerrado").unwrap();
        let tablero = cartel.forma.iter().max_by(|a, b| a.medidas[0].total_cmp(&b.medidas[0])).unwrap();
        for i in 0..3 {
            let (m, c) = (ZONA_CARTEL_MEDIDAS[i], ZONA_CARTEL_CENTRO[i]);
            assert!(tablero.pos[i] - tablero.medidas[i] / 2.0 >= c - m / 2.0, "eje {i}");
            assert!(tablero.pos[i] + tablero.medidas[i] / 2.0 <= c + m / 2.0, "eje {i}");
        }
        assert!(mx >= 0.36 && my >= 0.25, "cómoda de tocar");
        for b in &cat.bases {
            let a = b.anclaje("cartel").unwrap();
            // No asoma sobre la mesada (ni sobre la bandeja, que está apoyada en ella).
            let arriba = a.pos[1] + cy + my / 2.0;
            assert!(arriba < b.alto_mostrador, "{}: la zona asoma sobre el mostrador ({arriba})", b.id);
            assert!(b.entrega[1] >= b.alto_mostrador - 1e-4, "{}: la bandeja está sobre la mesada", b.id);
            // Sale hacia la vereda, delante del carro.
            assert!(a.pos[2] + cz + mz / 2.0 > b.profundidad / 2.0, "{}", b.id);
            // Desde el primer lugar de la fila, con los ojos a 1,65 m (REQ-JUG-05), está a mano
            // (la mira llega a 2,5 m, REQ-INT-01), con margen.
            let centro = [a.pos[0] + cx, a.pos[1] + cy, a.pos[2] + cz];
            let ojos = [b.fila[0], 1.65, b.fila[2]];
            let d = (0..3).map(|i| (centro[i] - ojos[i]).powi(2)).sum::<f32>().sqrt();
            assert!(d < 1.5, "{}: lejos de la vereda ({d})", b.id);
        }
    }

    #[test]
    fn req_cli_10_texto_de_estrellas() {
        assert_eq!(estrellas_texto(4.4), "★★★★☆");
        assert_eq!(estrellas_texto(1.0), "★☆☆☆☆");
    }
}
