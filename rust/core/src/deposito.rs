//! SPEC-004 · Depósito con comida visible.

use serde::Deserialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
pub enum Empaque {
    /// Bolsa de nylon transparente.
    Bolsa,
    /// Bandeja de cartón abierta con film.
    Bandeja,
}

/// Tipo de bloque (`godot/data/bloques.ron`). REQ-DEP-01
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefBloque {
    pub id: String,
    pub nombre: String,
    pub producto: String,
    /// (columnas en X, filas en Z, capas en Y). REQ-DEP-02
    pub grilla: [u32; 3],
    /// Distancia entre centros de unidades en (X, Y, Z), en metros.
    pub separacion: [f32; 3],
    pub empaque: Empaque,
    pub color_empaque: [f32; 3],
    pub precio: f32,
    /// REQ-MOD-01: modelo 3D del empaque (las unidades las sigue dibujando el código).
    #[serde(default)]
    pub modelo: Option<String>,
}

impl DefBloque {
    pub fn capacidad(&self) -> u32 {
        self.grilla[0] * self.grilla[1] * self.grilla[2]
    }

    /// Tamaño exterior del paquete (X, Y, Z).
    pub fn tamano(&self) -> [f32; 3] {
        [
            self.grilla[0] as f32 * self.separacion[0],
            self.grilla[2] as f32 * self.separacion[1],
            self.grilla[1] as f32 * self.separacion[2],
        ]
    }

    /// Posición del centro de la unidad `i` relativa a la base del paquete (centro abajo).
    /// Orden de llenado: capa de abajo primero; dentro de la capa, fila de adelante (+Z) primero.
    /// Así la última unidad es la de arriba y atrás (REQ-DEP-04).
    pub fn posicion_unidad(&self, i: u32) -> [f32; 3] {
        let [cols, filas, _capas] = self.grilla;
        let capa = i / (cols * filas);
        let resto = i % (cols * filas);
        let fila = resto / cols;
        let col = resto % cols;
        let [sx, sy, sz] = self.separacion;
        [
            (col as f32 - (cols as f32 - 1.0) / 2.0) * sx,
            capa as f32 * sy + sy / 2.0,
            // fila 0 = adelante (+Z), las siguientes hacia atrás (-Z)
            ((filas as f32 - 1.0) / 2.0 - fila as f32) * sz,
        ]
    }
}

/// Un bloque concreto en un depósito.
#[derive(Debug, Clone, PartialEq)]
pub struct Bloque {
    pub def: DefBloque,
    pub restantes: u32,
}

impl Bloque {
    pub fn lleno(def: DefBloque) -> Self {
        let restantes = def.capacidad();
        Self { def, restantes }
    }

    /// Un bloque empezado (ej. un paquete que se levantó del estante). REQ-DEP-09
    pub fn con_restantes(def: DefBloque, restantes: u32) -> Self {
        let restantes = restantes.min(def.capacidad());
        Self { def, restantes }
    }

    pub fn vacio(&self) -> bool {
        self.restantes == 0
    }

    /// Posiciones de las unidades que se dibujan. REQ-DEP-02, REQ-DEP-03
    pub fn posiciones_visibles(&self) -> Vec<[f32; 3]> {
        (0..self.restantes).map(|i| self.def.posicion_unidad(i)).collect()
    }

    /// Saca la última unidad. Devuelve el id del producto. REQ-DEP-04
    pub fn sacar(&mut self) -> Option<&str> {
        if self.restantes == 0 {
            return None;
        }
        self.restantes -= 1;
        Some(&self.def.producto)
    }
}

/// Un depósito: lugares fijos para bloques. REQ-DEP-07
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Deposito {
    pub lugares: Vec<Option<Bloque>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrorDeposito {
    LugarInexistente(usize),
    LugarOcupado(usize),
}

impl Deposito {
    pub fn con_lugares(n: usize) -> Self {
        Self { lugares: vec![None; n] }
    }

    /// REQ-DEP-07: no se puede poner en un lugar ocupado.
    pub fn poner(&mut self, lugar: usize, bloque: Bloque) -> Result<(), ErrorDeposito> {
        match self.lugares.get_mut(lugar) {
            None => Err(ErrorDeposito::LugarInexistente(lugar)),
            Some(Some(_)) => Err(ErrorDeposito::LugarOcupado(lugar)),
            Some(l) => {
                *l = Some(bloque);
                Ok(())
            }
        }
    }

    /// Saca una unidad del bloque en `lugar`. Si queda vacío, libera el lugar. REQ-DEP-06
    pub fn sacar(&mut self, lugar: usize) -> Option<String> {
        let slot = self.lugares.get_mut(lugar)?;
        let bloque = slot.as_mut()?;
        let producto = bloque.sacar()?.to_string();
        if bloque.vacio() {
            *slot = None;
        }
        Some(producto)
    }

    pub fn unidades_de(&self, producto: &str) -> u32 {
        self.lugares.iter().flatten().filter(|b| b.def.producto == producto).map(|b| b.restantes).sum()
    }
}

#[cfg(test)]
pub(crate) fn bolsa_panes() -> DefBloque {
    DefBloque {
        id: "bolsa_panes_12".into(),
        nombre: "bolsa de panes".into(),
        producto: "pan_pancho".into(),
        grilla: [1, 6, 2],
        separacion: [0.18, 0.047, 0.058],
        empaque: Empaque::Bolsa,
        color_empaque: [0.9, 0.9, 0.95],
        precio: 6.0,
        modelo: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_dep_09_un_bloque_levantado_conserva_sus_unidades() {
        let b = Bloque::con_restantes(bolsa_panes(), 7);
        assert_eq!(b.restantes, 7);
        assert_eq!(b.posiciones_visibles().len(), 7);
        assert_eq!(Bloque::con_restantes(bolsa_panes(), 99).restantes, 12, "no pasa la capacidad");
    }

    #[test]
    fn req_dep_01_capacidad_por_grilla() {
        assert_eq!(bolsa_panes().capacidad(), 12);
        assert_eq!(Bloque::lleno(bolsa_panes()).restantes, 12);
    }

    #[test]
    fn req_dep_02_cada_unidad_en_su_lugar_dentro_del_paquete() {
        let d = bolsa_panes();
        let t = d.tamano();
        let mut vistas = std::collections::HashSet::new();
        for i in 0..d.capacidad() {
            let p = d.posicion_unidad(i);
            assert!(p[0].abs() <= t[0] / 2.0 + 1e-5);
            assert!(p[1] > 0.0 && p[1] < t[1]);
            assert!(p[2].abs() <= t[2] / 2.0 + 1e-5);
            // Ninguna unidad ocupa el lugar de otra.
            assert!(vistas.insert(p.map(|v| (v * 1000.0).round() as i32)));
        }
    }

    #[test]
    fn req_dep_03_visibles_igual_a_restantes() {
        let mut b = Bloque::lleno(bolsa_panes());
        for esperado in (0..12).rev() {
            b.sacar();
            assert_eq!(b.posiciones_visibles().len() as u32, esperado);
            assert_eq!(b.restantes, esperado);
        }
        assert_eq!(b.sacar(), None);
    }

    #[test]
    fn req_dep_04_saca_la_de_arriba_y_atras_primero() {
        let d = bolsa_panes();
        let mut b = Bloque::lleno(d.clone());
        let antes = b.posiciones_visibles();
        b.sacar();
        let despues = b.posiciones_visibles();
        let sacada = antes.iter().find(|p| !despues.contains(p)).unwrap();
        let max_y = antes.iter().map(|p| p[1]).fold(f32::MIN, f32::max);
        let min_z = antes.iter().filter(|p| p[1] == max_y).map(|p| p[2]).fold(f32::MAX, f32::min);
        assert_eq!(sacada[1], max_y, "primero la capa de arriba");
        assert_eq!(sacada[2], min_z, "y dentro de ella la fila de atrás");
    }

    #[test]
    fn req_dep_06_bloque_vacio_libera_el_lugar() {
        let mut dep = Deposito::con_lugares(2);
        dep.poner(0, Bloque::lleno(bolsa_panes())).unwrap();
        for _ in 0..12 {
            assert_eq!(dep.sacar(0).as_deref(), Some("pan_pancho"));
        }
        assert!(dep.lugares[0].is_none());
        assert_eq!(dep.sacar(0), None);
    }

    #[test]
    fn req_dep_07_lugares_fijos_y_no_ocupados() {
        let mut dep = Deposito::con_lugares(1);
        dep.poner(0, Bloque::lleno(bolsa_panes())).unwrap();
        assert_eq!(dep.poner(0, Bloque::lleno(bolsa_panes())), Err(ErrorDeposito::LugarOcupado(0)));
        assert_eq!(dep.poner(5, Bloque::lleno(bolsa_panes())), Err(ErrorDeposito::LugarInexistente(5)));
        assert_eq!(dep.unidades_de("pan_pancho"), 12);
    }
}
