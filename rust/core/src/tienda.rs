//! SPEC-017 · Tienda y modo armado: poner, mover, guardar y vender accesorios y bases.
//! Reglas puras; el nodo de Godot (`game/src/armado.rs`) las aplica al carrito.

use std::collections::BTreeMap;
use std::fmt;

use crate::carrito::{Accesorio, Anclaje, BaseCarrito, ConfigCarrito};
use crate::economia::{Caja, plata};

/// REQ-TIE-08: paleta fija y gratis.
pub const PALETA: [(&str, [f32; 3]); 10] = [
    ("Rojo", [0.78, 0.13, 0.10]),
    ("Naranja", [0.90, 0.45, 0.10]),
    ("Amarillo", [0.95, 0.75, 0.15]),
    ("Verde", [0.20, 0.55, 0.25]),
    ("Celeste", [0.35, 0.65, 0.85]),
    ("Azul", [0.12, 0.25, 0.60]),
    ("Violeta", [0.45, 0.25, 0.60]),
    ("Rosa", [0.90, 0.50, 0.65]),
    ("Blanco", [0.92, 0.91, 0.88]),
    ("Negro", [0.10, 0.10, 0.11]),
];

/// REQ-TIE-09: lo usado se vende a la mitad.
pub const FRACCION_VENTA: f32 = 0.5;

/// REQ-TIE-02, REQ-TIE-11: el accesorio entra en ese anclaje de esa base.
pub fn entra(acc: &Accesorio, base: &BaseCarrito, anclaje: &Anclaje) -> bool {
    anclaje.categorias.contains(&acc.categoria) && acc.bases.as_ref().is_none_or(|b| b.contains(&base.id))
}

/// De dónde sale lo que se pone. REQ-TIE-02
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Origen {
    Guardado,
    Tienda,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Opcion {
    pub accesorio: String,
    pub origen: Origen,
    /// 0 si está guardado.
    pub precio: f32,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ErrorArmado {
    Inexistente(String),
    AnclajeInexistente(String),
    NoEntra { accesorio: String, anclaje: String },
    Vacio(String),
    SinSaldo { falta: f32 },
    NoGuardado(String),
    /// REQ-TIE-05 / REQ-TIE-10: depósito con bloques.
    ConBloques(String),
    MismaBase,
}

impl fmt::Display for ErrorArmado {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use ErrorArmado::*;
        match self {
            Inexistente(id) => write!(f, "No existe \"{id}\""),
            AnclajeInexistente(a) => write!(f, "El carrito no tiene el lugar \"{a}\""),
            NoEntra { accesorio, anclaje } => write!(f, "\"{accesorio}\" no entra en \"{anclaje}\""),
            Vacio(a) => write!(f, "En \"{a}\" no hay nada"),
            SinSaldo { falta } => write!(f, "No te alcanza: faltan {}", plata(*falta)),
            NoGuardado(id) => write!(f, "No tenés \"{id}\" guardado"),
            ConBloques(a) => write!(f, "El depósito de \"{a}\" tiene mercadería: vacialo primero"),
            MismaBase => write!(f, "Ya estás usando esa base"),
        }
    }
}

/// Resultado de mover. REQ-TIE-04
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Movimiento {
    Simple,
    Intercambio,
}

/// Resultado de cambiar de base. REQ-TIE-10
#[derive(Debug, Clone, PartialEq)]
pub struct CambioBase {
    pub pagado: f32,
    /// Anclajes cuyos accesorios pasan a la base nueva.
    pub pasan: Vec<String>,
    /// (anclaje, accesorio) que se guardaron por no entrar.
    pub guardados: Vec<(String, String)>,
}

/// Lo guardado (puede haber repetidos). REQ-TIE-05, REQ-TIE-09
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Inventario {
    pub accesorios: Vec<String>,
    pub bases: Vec<String>,
}

fn sacar(lista: &mut Vec<String>, id: &str) -> bool {
    match lista.iter().position(|x| x == id) {
        Some(i) => {
            lista.remove(i);
            true
        }
        None => false,
    }
}

/// Estado del carrito del jugador que se cambia desde el juego.
#[derive(Debug, Clone, PartialEq)]
pub struct Armado {
    pub base: String,
    pub color: [f32; 3],
    /// anclaje → accesorio
    pub accesorios: BTreeMap<String, String>,
    pub inventario: Inventario,
}

impl Armado {
    pub fn desde_config(cfg: &ConfigCarrito, bases: &[BaseCarrito]) -> Self {
        let color = cfg.color.or_else(|| bases.iter().find(|b| b.id == cfg.base).map(|b| b.color)).unwrap_or([1.0; 3]);
        Self { base: cfg.base.clone(), color, accesorios: cfg.accesorios.clone(), inventario: Inventario::default() }
    }

    /// Config para volver a armar el carrito (sin stock: los bloques viven en los nodos).
    pub fn config(&self) -> ConfigCarrito {
        ConfigCarrito {
            base: self.base.clone(),
            color: Some(self.color),
            accesorios: self.accesorios.clone(),
            stock: BTreeMap::new(),
        }
    }

    fn base_def<'a>(&self, bases: &'a [BaseCarrito]) -> Result<&'a BaseCarrito, ErrorArmado> {
        bases.iter().find(|b| b.id == self.base).ok_or_else(|| ErrorArmado::Inexistente(self.base.clone()))
    }

    fn acc<'a>(id: &str, accesorios: &'a [Accesorio]) -> Result<&'a Accesorio, ErrorArmado> {
        accesorios.iter().find(|a| a.id == id).ok_or_else(|| ErrorArmado::Inexistente(id.to_string()))
    }

    /// REQ-TIE-02: lo que entra en un anclaje; primero lo guardado (sin repetir), después la tienda.
    pub fn opciones(&self, anclaje: &str, bases: &[BaseCarrito], accesorios: &[Accesorio]) -> Vec<Opcion> {
        let Ok(base) = self.base_def(bases) else { return Vec::new() };
        let Some(anc) = base.anclaje(anclaje) else { return Vec::new() };
        let mut v: Vec<Opcion> = Vec::new();
        for id in &self.inventario.accesorios {
            if v.iter().any(|o| &o.accesorio == id) {
                continue;
            }
            if let Some(a) = accesorios.iter().find(|a| &a.id == id).filter(|a| entra(a, base, anc)) {
                v.push(Opcion { accesorio: a.id.clone(), origen: Origen::Guardado, precio: 0.0 });
            }
        }
        for a in accesorios.iter().filter(|a| entra(a, base, anc)) {
            v.push(Opcion { accesorio: a.id.clone(), origen: Origen::Tienda, precio: a.precio });
        }
        v
    }

    /// REQ-TIE-02, REQ-TIE-03: pone un accesorio (si había otro, se guarda). Devuelve lo gastado.
    /// `con_bloques`: el accesorio que estaba es un depósito con mercadería.
    pub fn poner(
        &mut self,
        anclaje: &str,
        acc_id: &str,
        origen: Origen,
        con_bloques: bool,
        caja: &mut Caja,
        bases: &[BaseCarrito],
        accesorios: &[Accesorio],
    ) -> Result<f32, ErrorArmado> {
        let base = self.base_def(bases)?;
        let anc = base.anclaje(anclaje).ok_or_else(|| ErrorArmado::AnclajeInexistente(anclaje.to_string()))?;
        let acc = Self::acc(acc_id, accesorios)?;
        if !entra(acc, base, anc) {
            return Err(ErrorArmado::NoEntra { accesorio: acc.nombre.clone(), anclaje: anclaje.to_string() });
        }
        if self.accesorios.contains_key(anclaje) && con_bloques {
            return Err(ErrorArmado::ConBloques(anclaje.to_string()));
        }
        let gasto = match origen {
            Origen::Guardado => {
                if !self.inventario.accesorios.contains(&acc.id) {
                    return Err(ErrorArmado::NoGuardado(acc.id.clone()));
                }
                0.0
            }
            Origen::Tienda => {
                caja.pagar(acc.precio).map_err(|e| ErrorArmado::SinSaldo { falta: e.falta })?;
                acc.precio
            }
        };
        if origen == Origen::Guardado {
            sacar(&mut self.inventario.accesorios, &acc.id);
        }
        if let Some(viejo) = self.accesorios.insert(anclaje.to_string(), acc.id.clone()) {
            self.inventario.accesorios.push(viejo);
        }
        Ok(gasto)
    }

    /// REQ-TIE-05: guarda lo que hay en el anclaje. Devuelve el id guardado.
    pub fn guardar(&mut self, anclaje: &str, con_bloques: bool) -> Result<String, ErrorArmado> {
        if !self.accesorios.contains_key(anclaje) {
            return Err(ErrorArmado::Vacio(anclaje.to_string()));
        }
        if con_bloques {
            return Err(ErrorArmado::ConBloques(anclaje.to_string()));
        }
        let id = self.accesorios.remove(anclaje).expect("revisado arriba");
        self.inventario.accesorios.push(id.clone());
        Ok(id)
    }

    /// REQ-TIE-04: mueve al anclaje de destino; si está ocupado y los dos se aceptan, intercambia.
    pub fn mover(
        &mut self,
        desde: &str,
        hasta: &str,
        bases: &[BaseCarrito],
        accesorios: &[Accesorio],
    ) -> Result<Movimiento, ErrorArmado> {
        let base = self.base_def(bases)?;
        let a_id = self.accesorios.get(desde).cloned().ok_or_else(|| ErrorArmado::Vacio(desde.to_string()))?;
        let anc_desde = base.anclaje(desde).ok_or_else(|| ErrorArmado::AnclajeInexistente(desde.to_string()))?;
        let anc_hasta = base.anclaje(hasta).ok_or_else(|| ErrorArmado::AnclajeInexistente(hasta.to_string()))?;
        let a = Self::acc(&a_id, accesorios)?;
        if !entra(a, base, anc_hasta) {
            return Err(ErrorArmado::NoEntra { accesorio: a.nombre.clone(), anclaje: hasta.to_string() });
        }
        match self.accesorios.get(hasta).cloned() {
            None => {
                self.accesorios.remove(desde);
                self.accesorios.insert(hasta.to_string(), a_id);
                Ok(Movimiento::Simple)
            }
            Some(b_id) => {
                let b = Self::acc(&b_id, accesorios)?;
                if !entra(b, base, anc_desde) {
                    return Err(ErrorArmado::NoEntra { accesorio: b.nombre.clone(), anclaje: desde.to_string() });
                }
                self.accesorios.insert(desde.to_string(), b_id);
                self.accesorios.insert(hasta.to_string(), a_id);
                Ok(Movimiento::Intercambio)
            }
        }
    }

    /// REQ-TIE-09: vende un accesorio guardado. Devuelve lo cobrado.
    pub fn vender_accesorio(&mut self, id: &str, caja: &mut Caja, accesorios: &[Accesorio]) -> Result<f32, ErrorArmado> {
        let precio = Self::acc(id, accesorios)?.precio;
        if !sacar(&mut self.inventario.accesorios, id) {
            return Err(ErrorArmado::NoGuardado(id.to_string()));
        }
        let monto = precio * FRACCION_VENTA;
        caja.cobrar(monto);
        Ok(monto)
    }

    /// REQ-TIE-09: vende una base guardada. Devuelve lo cobrado.
    pub fn vender_base(&mut self, id: &str, caja: &mut Caja, bases: &[BaseCarrito]) -> Result<f32, ErrorArmado> {
        let precio = bases.iter().find(|b| b.id == id).ok_or_else(|| ErrorArmado::Inexistente(id.to_string()))?.precio;
        if !sacar(&mut self.inventario.bases, id) {
            return Err(ErrorArmado::NoGuardado(id.to_string()));
        }
        let monto = precio * FRACCION_VENTA;
        caja.cobrar(monto);
        Ok(monto)
    }

    /// REQ-TIE-10: cambia a otra base (comprada o guardada); la actual se guarda.
    /// `con_bloques`: anclajes cuyo depósito tiene mercadería.
    pub fn cambiar_base(
        &mut self,
        nueva: &str,
        caja: &mut Caja,
        bases: &[BaseCarrito],
        accesorios: &[Accesorio],
        con_bloques: &[String],
    ) -> Result<CambioBase, ErrorArmado> {
        if nueva == self.base {
            return Err(ErrorArmado::MismaBase);
        }
        let destino = bases.iter().find(|b| b.id == nueva).ok_or_else(|| ErrorArmado::Inexistente(nueva.to_string()))?;
        let mut pasan = Vec::new();
        let mut guardados = Vec::new();
        for (anc_id, acc_id) in &self.accesorios {
            let acc = Self::acc(acc_id, accesorios)?;
            if destino.anclaje(anc_id).is_some_and(|a| entra(acc, destino, a)) {
                pasan.push(anc_id.clone());
            } else if con_bloques.contains(anc_id) {
                return Err(ErrorArmado::ConBloques(anc_id.clone()));
            } else {
                guardados.push((anc_id.clone(), acc_id.clone()));
            }
        }
        let guardada = self.inventario.bases.contains(&destino.id);
        let pagado = if guardada { 0.0 } else { destino.precio };
        caja.pagar(pagado).map_err(|e| ErrorArmado::SinSaldo { falta: e.falta })?;
        if guardada {
            sacar(&mut self.inventario.bases, &destino.id);
        }
        self.inventario.bases.push(std::mem::replace(&mut self.base, destino.id.clone()));
        for (anc, acc) in &guardados {
            self.accesorios.remove(anc);
            self.inventario.accesorios.push(acc.clone());
        }
        Ok(CambioBase { pagado, pasan, guardados })
    }

    /// REQ-TIE-08
    pub fn pintar(&mut self, color: [f32; 3]) {
        self.color = color;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::datos::tests::catalogo_real;

    fn armado() -> (Armado, crate::datos::Catalogo) {
        let c = catalogo_real();
        (Armado::desde_config(&c.carrito_jugador, &c.bases), c)
    }

    fn caja(saldo: f32) -> Caja {
        Caja { saldo }
    }

    #[test]
    fn req_tie_02_opciones_guardado_primero_y_solo_lo_que_entra() {
        let (mut a, c) = armado();
        a.inventario.accesorios = vec!["sombrilla_rayada".into(), "sombrilla_rayada".into(), "plancha_chica".into()];
        let ops = a.opciones("sombra", &c.bases, &c.accesorios);
        assert_eq!(ops[0], Opcion { accesorio: "sombrilla_rayada".into(), origen: Origen::Guardado, precio: 0.0 });
        assert_eq!(ops.iter().filter(|o| o.origen == Origen::Guardado).count(), 1, "sin repetir ni la plancha");
        let base = c.bases.iter().find(|b| b.id == a.base).unwrap();
        let anc = base.anclaje("sombra").unwrap();
        for o in &ops {
            let acc = c.accesorios.iter().find(|x| x.id == o.accesorio).unwrap();
            assert!(entra(acc, base, anc));
        }
        assert!(ops.iter().any(|o| o.origen == Origen::Tienda && o.precio > 0.0));
    }

    #[test]
    fn req_tie_02_comprar_cobra_y_sin_saldo_rechaza() {
        let (mut a, c) = armado();
        a.accesorios.remove("sombra");
        let precio = c.accesorios.iter().find(|x| x.id == "sombrilla_roja").unwrap().precio;
        let mut k = caja(precio - 1.0);
        let e = a.poner("sombra", "sombrilla_roja", Origen::Tienda, false, &mut k, &c.bases, &c.accesorios);
        assert!(matches!(e, Err(ErrorArmado::SinSaldo { .. })));
        assert!(!a.accesorios.contains_key("sombra"));
        let mut k = caja(precio);
        let g = a.poner("sombra", "sombrilla_roja", Origen::Tienda, false, &mut k, &c.bases, &c.accesorios).unwrap();
        assert_eq!((g, k.saldo), (precio, 0.0));
        // Una plancha no va en el anclaje de la sombrilla.
        let e = a.poner("sombra", "plancha_chica", Origen::Tienda, false, &mut caja(1e9), &c.bases, &c.accesorios);
        assert!(matches!(e, Err(ErrorArmado::NoEntra { .. })));
    }

    #[test]
    fn req_tie_03_cambiar_guarda_el_anterior_y_lo_guardado_es_gratis() {
        let (mut a, c) = armado();
        a.inventario.accesorios.push("sombrilla_rayada".into());
        let mut k = caja(0.0);
        let g = a.poner("sombra", "sombrilla_rayada", Origen::Guardado, false, &mut k, &c.bases, &c.accesorios).unwrap();
        assert_eq!(g, 0.0);
        assert_eq!(a.accesorios["sombra"], "sombrilla_rayada");
        assert_eq!(a.inventario.accesorios, vec!["sombrilla_roja".to_string()]);
        let e = a.poner("sombra", "sombrilla_rayada", Origen::Guardado, false, &mut k, &c.bases, &c.accesorios);
        assert!(matches!(e, Err(ErrorArmado::NoGuardado(_))));
    }

    #[test]
    fn req_tie_04_mover_y_dar_intercambiar() {
        let (mut a, c) = armado();
        // Plancha del centro a la izquierda (donde está el hervidor): se intercambian.
        assert_eq!(a.mover("mostrador_centro", "mostrador_izq", &c.bases, &c.accesorios), Ok(Movimiento::Intercambio));
        assert_eq!(a.accesorios["mostrador_izq"], "plancha_chica");
        assert_eq!(a.accesorios["mostrador_centro"], "hervidor_chico");
        // A un lugar libre.
        a.accesorios.remove("luz_2");
        assert_eq!(a.mover("luz_1", "luz_2", &c.bases, &c.accesorios), Ok(Movimiento::Simple));
        assert!(!a.accesorios.contains_key("luz_1"));
        // La sombrilla no va en un mostrador.
        let antes = a.clone();
        assert!(matches!(a.mover("sombra", "mostrador_der", &c.bases, &c.accesorios), Err(ErrorArmado::NoEntra { .. })));
        assert_eq!(a, antes);
    }

    #[test]
    fn req_tie_05_guardar_y_deposito_con_bloques() {
        let (mut a, _) = armado();
        assert!(matches!(a.guardar("lateral", true), Err(ErrorArmado::ConBloques(_))));
        assert_eq!(a.guardar("sombra", false), Ok("sombrilla_roja".to_string()));
        assert!(a.inventario.accesorios.contains(&"sombrilla_roja".to_string()));
        assert!(matches!(a.guardar("sombra", false), Err(ErrorArmado::Vacio(_))));
    }

    #[test]
    fn req_tie_08_paleta_de_diez_colores_distintos() {
        assert_eq!(PALETA.len(), 10);
        for (i, a) in PALETA.iter().enumerate() {
            assert!(PALETA[i + 1..].iter().all(|b| b.1 != a.1 && b.0 != a.0));
        }
        let (mut a, _) = armado();
        a.pintar(PALETA[3].1);
        assert_eq!(a.config().color, Some(PALETA[3].1));
    }

    #[test]
    fn req_tie_09_vender_a_la_mitad() {
        let (mut a, c) = armado();
        a.guardar("sombra", false).unwrap();
        let precio = c.accesorios.iter().find(|x| x.id == "sombrilla_roja").unwrap().precio;
        let mut k = caja(0.0);
        assert_eq!(a.vender_accesorio("sombrilla_roja", &mut k, &c.accesorios), Ok(precio / 2.0));
        assert_eq!(k.saldo, precio / 2.0);
        assert!(matches!(a.vender_accesorio("sombrilla_roja", &mut k, &c.accesorios), Err(ErrorArmado::NoGuardado(_))));
        // Lo puesto no se vende.
        assert!(a.vender_accesorio("plancha_chica", &mut k, &c.accesorios).is_err());
    }

    #[test]
    fn req_tie_10_cambiar_de_base_pasa_lo_que_entra_y_guarda_el_resto() {
        let (mut a, c) = armado();
        assert_eq!(a.base, "barra_mediana");
        let grande = c.bases.iter().find(|b| b.id == "carro_grande").unwrap().precio;
        let mut k = caja(grande);
        let r = a.cambiar_base("carro_grande", &mut k, &c.bases, &c.accesorios, &[]).unwrap();
        assert_eq!((r.pagado, k.saldo), (grande, 0.0));
        assert!(r.guardados.is_empty(), "el carro grande tiene todos los anclajes de la mediana");
        assert_eq!(a.inventario.bases, vec!["barra_mediana".to_string()]);
        // Volver a la guardada es gratis; al kiosco no pasan la sombrilla ni la parrilla.
        let r = a.cambiar_base("barra_mediana", &mut k, &c.bases, &c.accesorios, &[]).unwrap();
        assert_eq!(r.pagado, 0.0);
        assert_eq!(a.inventario.bases, vec!["carro_grande".to_string()]);
        let kiosco = c.bases.iter().find(|b| b.id == "carro_kiosco").unwrap().precio;
        let antes = a.clone();
        let e = a.cambiar_base("carro_kiosco", &mut caja(kiosco), &c.bases, &c.accesorios, &["lateral".to_string()]);
        assert!(matches!(e, Err(ErrorArmado::ConBloques(_))), "el estante con mercadería no tiene lugar");
        assert_eq!(a, antes);
        let r = a.cambiar_base("carro_kiosco", &mut caja(kiosco), &c.bases, &c.accesorios, &[]).unwrap();
        assert!(r.guardados.iter().any(|(_, acc)| acc == "sombrilla_roja"));
        assert!(r.pasan.contains(&"mostrador_centro".to_string()));
        assert!(a.inventario.accesorios.contains(&"sombrilla_roja".to_string()));
        assert_eq!(a.cambiar_base("carro_kiosco", &mut k, &c.bases, &c.accesorios, &[]), Err(ErrorArmado::MismaBase));
    }

    #[test]
    fn req_tie_11_accesorio_limitado_a_bases() {
        let c = catalogo_real();
        let mut acc = c.accesorios.iter().find(|x| x.id == "sombrilla_roja").unwrap().clone();
        let chica = c.bases.iter().find(|b| b.id == "barra_chica").unwrap();
        let grande = c.bases.iter().find(|b| b.id == "carro_grande").unwrap();
        acc.bases = Some(vec!["barra_chica".into()]);
        assert!(entra(&acc, chica, chica.anclaje("sombra").unwrap()));
        assert!(!entra(&acc, grande, grande.anclaje("sombra").unwrap()));
    }
}
