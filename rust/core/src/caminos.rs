//! SPEC-013 · Red de caminos para peatones (plaza, veredas, sendas peatonales).

use crate::ciudad::{Edificio, SENDAS, Z_VEREDA_ENFRENTE};
use crate::plaza::{self, TipoProp};

/// Línea por donde camina la gente en la vereda del carrito.
pub const Z_VEREDA_PEATONES: f32 = -21.4;
pub const X_VEREDA_LATERAL: f32 = 29.0;
pub const Z_VEREDA_SUR: f32 = 29.0;
/// REQ-AMB-15: borde del mapa (REQ-MUN-01), donde la gente llega y se va.
pub const BORDE: f32 = plaza::TAMANO_TERRENO / 2.0 - 0.5;
/// Dónde está el carrito (centro de su base, sobre la vereda; ver `main.tscn`).
pub const PUNTO_CARRITO: [f32; 2] = [0.0, plaza::Z_VEREDA];
/// Margen para no contar como tapado algo que apenas roza la esquina de un edificio.
const MARGEN_TAPADO: f32 = 0.3;

/// ¿El segmento `a`→`b` pasa por el rectángulo `r` = `[x_min, z_min, x_max, z_max]`?
fn cruza(a: [f32; 2], b: [f32; 2], r: [f32; 4]) -> bool {
    let (mut t0, mut t1) = (0.0_f32, 1.0_f32);
    for eje in 0..2 {
        let d = b[eje] - a[eje];
        let (min, max) = (r[eje], r[eje + 2]);
        if d.abs() < 1e-6 {
            if a[eje] < min || a[eje] > max {
                return false;
            }
            continue;
        }
        let (mut u0, mut u1) = ((min - a[eje]) / d, (max - a[eje]) / d);
        if u0 > u1 {
            std::mem::swap(&mut u0, &mut u1);
        }
        t0 = t0.max(u0);
        t1 = t1.min(u1);
        if t0 > t1 {
            return false;
        }
    }
    true
}

/// REQ-AMB-15: ¿algún edificio tapa `punto` visto desde `ojo`? (en planta: los edificios
/// tienen al menos dos pisos, más altos que cualquier persona).
pub fn tapado(ojo: [f32; 2], punto: [f32; 2], edificios: &[Edificio]) -> bool {
    edificios.iter().any(|e| {
        let [x0, z0, x1, z1] = e.planta();
        let m = MARGEN_TAPADO;
        cruza(ojo, punto, [x0 + m, z0 + m, x1 - m, z1 - m])
    })
}

/// Desde dónde se mira en el carrito (para los tests): el mostrador y un poco alrededor.
#[cfg(test)]
pub(crate) fn ojos_carrito() -> Vec<[f32; 2]> {
    let [cx, cz] = PUNTO_CARRITO;
    [-2.5, 0.0, 2.5].iter().flat_map(|&dx| [-1.5, 0.0, 1.5].map(|dz| [cx + dx, cz + dz])).collect()
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum TipoNodo {
    Paso,
    /// Lugar en un banco; `rot_y` = hacia dónde mira sentado.
    Asiento {
        rot_y: f32,
    },
    /// Donde la gente aparece o desaparece (puertas, extremos del mapa).
    Salida,
    /// Lugar para quedarse charlando.
    Charla,
}

#[derive(Debug, Clone, Default)]
pub struct Red {
    pub pos: Vec<[f32; 2]>,
    pub tipo: Vec<TipoNodo>,
    pub vecinos: Vec<Vec<usize>>,
}

impl Red {
    fn nodo(&mut self, x: f32, z: f32, tipo: TipoNodo) -> usize {
        if let Some(i) = self.pos.iter().position(|p| (p[0] - x).abs() < 0.05 && (p[1] - z).abs() < 0.05) {
            if tipo != TipoNodo::Paso {
                self.tipo[i] = tipo;
            }
            return i;
        }
        self.pos.push([x, z]);
        self.tipo.push(tipo);
        self.vecinos.push(Vec::new());
        self.pos.len() - 1
    }

    fn unir(&mut self, a: usize, b: usize) {
        if a != b && !self.vecinos[a].contains(&b) {
            self.vecinos[a].push(b);
            self.vecinos[b].push(a);
        }
    }

    fn linea(&mut self, puntos: &[(f32, f32)], tipo: impl Fn(usize) -> TipoNodo) {
        let ids: Vec<_> = puntos.iter().enumerate().map(|(i, &(x, z))| self.nodo(x, z, tipo(i))).collect();
        for w in ids.windows(2) {
            self.unir(w[0], w[1]);
        }
    }

    fn distancia(&self, a: usize, b: usize) -> f32 {
        let (p, q) = (self.pos[a], self.pos[b]);
        (p[0] - q[0]).hypot(p[1] - q[1])
    }

    pub fn mas_cercano(&self, x: f32, z: f32) -> usize {
        (0..self.pos.len())
            .min_by(|&a, &b| {
                let da = (self.pos[a][0] - x).hypot(self.pos[a][1] - z);
                let db = (self.pos[b][0] - x).hypot(self.pos[b][1] - z);
                da.total_cmp(&db)
            })
            .unwrap_or(0)
    }

    /// Nodo de tipo `Paso` más cercano (para enganchar asientos y lugares de charla).
    fn paso_mas_cercano(&self, x: f32, z: f32) -> usize {
        (0..self.pos.len())
            .filter(|&i| self.tipo[i] == TipoNodo::Paso)
            .min_by(|&a, &b| {
                let da = (self.pos[a][0] - x).hypot(self.pos[a][1] - z);
                let db = (self.pos[b][0] - x).hypot(self.pos[b][1] - z);
                da.total_cmp(&db)
            })
            .unwrap()
    }

    pub fn de_tipo(&self, f: impl Fn(&TipoNodo) -> bool) -> Vec<usize> {
        (0..self.pos.len()).filter(|&i| f(&self.tipo[i])).collect()
    }

    /// Camino más corto (Dijkstra). Incluye origen y destino.
    pub fn camino(&self, desde: usize, hasta: usize) -> Option<Vec<usize>> {
        let n = self.pos.len();
        let mut dist = vec![f32::INFINITY; n];
        let mut previo = vec![usize::MAX; n];
        let mut hecho = vec![false; n];
        dist[desde] = 0.0;
        for _ in 0..n {
            let u = (0..n).filter(|&i| !hecho[i]).min_by(|&a, &b| dist[a].total_cmp(&dist[b]))?;
            if dist[u].is_infinite() {
                return None;
            }
            if u == hasta {
                break;
            }
            hecho[u] = true;
            for &v in &self.vecinos[u] {
                let d = dist[u] + self.distancia(u, v);
                if d < dist[v] {
                    dist[v] = d;
                    previo[v] = u;
                }
            }
        }
        if dist[hasta].is_infinite() {
            return None;
        }
        let mut camino = vec![hasta];
        while let Some(&u) = camino.last() {
            if u == desde {
                break;
            }
            camino.push(previo[u]);
        }
        camino.reverse();
        Some(camino)
    }
}

/// REQ-AMB-04, REQ-AMB-07
pub fn red() -> Red {
    use TipoNodo::*;
    let mut r = Red::default();
    let b = plaza::LADO_PLAZA / 2.0 + 0.5; // borde de baldosas: 20.5
    let tramos = [-b, -17.0, -13.0, -10.0, -7.0, -4.5];
    let espejo = |v: &[f32]| v.iter().map(|x| -x).rev().collect::<Vec<_>>();

    // Caminos en cruz y anillo alrededor de la fuente.
    for lado in [tramos.to_vec(), espejo(&tramos)] {
        r.linea(&lado.iter().map(|&x| (x, 0.0)).collect::<Vec<_>>(), |_| Paso);
        r.linea(&lado.iter().map(|&z| (0.0, z)).collect::<Vec<_>>(), |_| Paso);
    }
    let anillo: Vec<_> = (0..=8)
        .map(|i| {
            let a = (i % 8) as f32 * std::f32::consts::FRAC_PI_4;
            ((4.5 * a.cos() * 10.0).round() / 10.0, (4.5 * a.sin() * 10.0).round() / 10.0)
        })
        .collect();
    r.linea(&anillo, |_| Paso);

    // Borde de la plaza.
    let lado = [-b, -10.0, 0.0, 10.0, b];
    for s in [-b, b] {
        r.linea(&lado.iter().map(|&x| (x, s)).collect::<Vec<_>>(), |_| Paso);
        r.linea(&lado.iter().map(|&z| (s, z)).collect::<Vec<_>>(), |_| Paso);
    }

    // Vereda del carrito y vereda de enfrente. REQ-AMB-15: sin salidas a la vista (ni en las
    // puntas ni en las puertas); se sale por el borde del mapa, detrás de los edificios.
    let xs = [-50.0, -42.0, -34.0, -29.0, -25.0, -17.0, -8.0, 0.0, 8.0, 17.0, 25.0, 29.0, 34.0, 42.0, 50.0];
    r.linea(&xs.iter().map(|&x| (x, Z_VEREDA_PEATONES)).collect::<Vec<_>>(), |_| Paso);
    r.linea(&xs.iter().map(|&x| (x, Z_VEREDA_ENFRENTE)).collect::<Vec<_>>(), |_| Paso);
    // Sendas peatonales.
    for x in SENDAS {
        r.linea(&[(x, Z_VEREDA_PEATONES), (x, Z_VEREDA_ENFRENTE)], |_| Paso);
    }
    // Veredas laterales y sur.
    let zs = [Z_VEREDA_PEATONES, -12.0, 0.0, 10.0, 20.0, Z_VEREDA_SUR];
    for s in [-X_VEREDA_LATERAL, X_VEREDA_LATERAL] {
        r.linea(&zs.iter().map(|&z| (s, z)).collect::<Vec<_>>(), |_| Paso);
    }
    let xs_sur = [-45.0, -X_VEREDA_LATERAL, -20.0, -10.0, 0.0, 10.0, 20.0, X_VEREDA_LATERAL, 45.0];
    r.linea(&xs_sur.iter().map(|&x| (x, Z_VEREDA_SUR)).collect::<Vec<_>>(), |_| Paso);

    // REQ-AMB-15: salidas en el borde del mapa, detrás de los edificios (no se ven desde el
    // carrito). Seis, tres por lado.
    let salida_al_final = |n: usize| move |i: usize| if i + 1 == n { Salida } else { Paso };
    for s in [-1.0_f32, 1.0] {
        // Desde la punta de la vereda del carrito, por detrás de la primera casa del costado.
        r.linea(&[(s * 50.0, Z_VEREDA_PEATONES), (s * 55.0, -15.0), (s * BORDE, -5.0)], salida_al_final(3));
        // Por el pasaje entre los edificios del costado y los del sur…
        r.linea(&[(s * 45.0, Z_VEREDA_SUR), (s * 52.0, Z_VEREDA_SUR), (s * BORDE, Z_VEREDA_SUR)], salida_al_final(3));
        // …y hacia el fondo, por detrás de la fila sur.
        r.linea(&[(s * 52.0, Z_VEREDA_SUR), (s * 52.0, BORDE)], salida_al_final(2));
    }

    // Conexiones plaza ↔ veredas.
    let conectar = |r: &mut Red, a: (f32, f32), c: (f32, f32)| {
        let (i, j) = (r.nodo(a.0, a.1, Paso), r.nodo(c.0, c.1, Paso));
        r.unir(i, j);
    };
    conectar(&mut r, (0.0, -b), (0.0, Z_VEREDA_PEATONES));
    conectar(&mut r, (-b, -b), (-17.0, Z_VEREDA_PEATONES));
    conectar(&mut r, (b, -b), (17.0, Z_VEREDA_PEATONES));
    conectar(&mut r, (b, 0.0), (X_VEREDA_LATERAL, 0.0));
    conectar(&mut r, (-b, 0.0), (-X_VEREDA_LATERAL, 0.0));
    conectar(&mut r, (0.0, b), (0.0, Z_VEREDA_SUR));

    // Asientos en los bancos, enganchados al camino.
    for p in plaza::distribucion().iter().filter(|p| p.tipo == TipoProp::Banco) {
        let (s, c) = p.rot_y.to_radians().sin_cos();
        let (x, z) = (p.x + s * 0.12, p.z + c * 0.12);
        let paso = r.paso_mas_cercano(x, z);
        let a = r.nodo(x, z, Asiento { rot_y: p.rot_y });
        r.unir(a, paso);
    }
    // Lugares para charlar.
    for &(x, z) in &[(8.5, -1.0), (-8.5, 1.0), (1.0, 15.0), (-1.0, -15.0), (15.0, 0.9), (-15.0, -0.9)] {
        let paso = r.paso_mas_cercano(x, z);
        let c = r.nodo(x, z, Charla);
        r.unir(c, paso);
    }
    r
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ciudad;

    #[test]
    fn req_amb_07_todo_conectado() {
        let r = red();
        assert!(r.pos.len() > 80);
        // Desde el nodo 0 se llega a todos.
        let mut visto = vec![false; r.pos.len()];
        let mut pila = vec![0];
        while let Some(u) = pila.pop() {
            if !std::mem::replace(&mut visto[u], true) {
                pila.extend(&r.vecinos[u]);
            }
        }
        let sueltos: Vec<_> = (0..r.pos.len()).filter(|&i| !visto[i]).map(|i| r.pos[i]).collect();
        assert!(sueltos.is_empty(), "nodos sin conexión: {sueltos:?}");
    }

    #[test]
    fn req_amb_04_destinos_y_caminos() {
        let r = red();
        let salidas = r.de_tipo(|t| *t == TipoNodo::Salida);
        let asientos = r.de_tipo(|t| matches!(t, TipoNodo::Asiento { .. }));
        let charlas = r.de_tipo(|t| *t == TipoNodo::Charla);
        assert!(salidas.len() >= 6 && asientos.len() == 16 && charlas.len() == 6);
        let c = r.camino(salidas[0], asientos[3]).expect("camino");
        assert_eq!(c.first(), Some(&salidas[0]));
        assert_eq!(c.last(), Some(&asientos[3]));
        // Cada paso del camino es entre vecinos.
        for w in c.windows(2) {
            assert!(r.vecinos[w[0]].contains(&w[1]));
        }
    }

    #[test]
    fn req_amb_08_se_cruza_por_la_senda() {
        let r = red();
        let a = r.mas_cercano(0.0, Z_VEREDA_PEATONES);
        let b = r.mas_cercano(0.0, Z_VEREDA_ENFRENTE);
        let c = r.camino(a, b).unwrap();
        // Todo tramo que cruza la calle lo hace por una senda.
        for w in c.windows(2) {
            let (p, q) = (r.pos[w[0]], r.pos[w[1]]);
            if (p[1] - q[1]).abs() > 5.0 {
                assert!(SENDAS.contains(&p[0]) && p[0] == q[0], "cruza fuera de la senda: {p:?} → {q:?}");
            }
        }
    }

    #[test]
    fn req_amb_15_tapado_por_edificios() {
        let e = ciudad::edificios();
        let ojo = PUNTO_CARRITO;
        assert!(!tapado(ojo, [0.0, 0.0], &e), "la fuente se ve");
        assert!(!tapado(ojo, [X_VEREDA_LATERAL, 10.0], &e), "la vereda lateral se ve");
        assert!(!tapado(ojo, [40.0, Z_VEREDA_PEATONES], &e), "la vereda del carrito se ve");
        assert!(tapado(ojo, [0.0, -55.0], &e), "detrás de la fila de enfrente no se ve");
        assert!(tapado(ojo, [55.0, 10.0], &e), "detrás de la fila del este no se ve");
    }

    #[test]
    fn req_amb_15_salidas_en_el_borde_fuera_de_la_vista() {
        let r = red();
        let e = ciudad::edificios();
        let salidas = r.de_tipo(|t| *t == TipoNodo::Salida);
        assert!(salidas.len() >= 4);
        for &s in &salidas {
            let p = r.pos[s];
            assert!(p[0].abs().max(p[1].abs()) >= BORDE - 0.01, "salida {p:?} lejos del borde");
            assert!(p[0].abs().max(p[1].abs()) <= plaza::TAMANO_TERRENO / 2.0, "salida {p:?} fuera del terreno");
            // La salida y los últimos 5 m de camino hasta ella no se ven desde el carrito.
            for &v in &r.vecinos[s] {
                let q = r.pos[v];
                let largo = (q[0] - p[0]).hypot(q[1] - p[1]);
                for k in 0..=10 {
                    let d = largo.min(5.0) * k as f32 / 10.0;
                    let punto = [p[0] + (q[0] - p[0]) / largo * d, p[1] + (q[1] - p[1]) / largo * d];
                    for ojo in ojos_carrito() {
                        assert!(tapado(ojo, punto, &e), "se ve {punto:?} (camino a la salida {p:?}) desde {ojo:?}");
                    }
                }
            }
        }
    }

    #[test]
    fn req_amb_15_nadie_aparece_en_la_plaza_ni_en_la_vereda() {
        let r = red();
        let medio = plaza::LADO_PLAZA / 2.0;
        for s in r.de_tipo(|t| *t == TipoNodo::Salida) {
            let [x, z] = r.pos[s];
            // Ni en la plaza, ni en sus veredas (las de los cuatro lados y la de enfrente).
            assert!(x.abs() > X_VEREDA_LATERAL + 15.0 || z.abs() > medio + 25.0, "salida en la vereda: {:?}", r.pos[s]);
            let d = (x - PUNTO_CARRITO[0]).hypot(z - PUNTO_CARRITO[1]);
            assert!(d > 50.0, "salida a {d:.0} m del carrito");
        }
    }

    #[test]
    fn req_cli_02_desde_las_salidas_se_llega_a_la_fila() {
        let r = red();
        let fila = r.mas_cercano(0.2, -22.0);
        for s in r.de_tipo(|t| *t == TipoNodo::Salida) {
            assert!(r.camino(s, fila).is_some());
        }
    }
}
