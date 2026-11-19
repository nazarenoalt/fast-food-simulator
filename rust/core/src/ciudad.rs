//! SPEC-013 · Ciudad alrededor de la plaza y nubes (datos repetibles con semilla).
//!
//! Coordenadas: norte = -Z, este = +X. La plaza está centrada en (0, 0).

use crate::azar::Azar;

pub const SEMILLA_CIUDAD: u64 = 2024;
pub const ALTO_PB: f32 = 3.6;
pub const ALTO_PISO: f32 = 3.0;
pub const ANCHO_VENTANA: f32 = 1.6;

/// Fachada de la fila norte (enfrente del carrito, cruzando la calle).
pub const Z_FACHADA_NORTE: f32 = -37.0;
pub const Z_VEREDA_ENFRENTE: f32 = -35.0;
/// Líneas de fachada de los otros tres lados.
pub const X_FACHADA_ESTE: f32 = 31.0;
pub const Z_FACHADA_SUR: f32 = 31.0;

#[derive(Debug, Clone, PartialEq)]
pub struct Edificio {
    /// Centro de la planta.
    pub x: f32,
    pub z: f32,
    /// Largo de la fachada y profundidad.
    pub ancho: f32,
    pub fondo: f32,
    /// Hacia dónde mira la fachada (giro en Y, grados; 0 = mira a +Z).
    pub rot_y: f32,
    pub pisos: u32,
    pub color: [f32; 3],
    /// Local en planta baja con toldo de este color.
    pub toldo: Option<[f32; 3]>,
    /// Columnas de ventanas por piso.
    pub columnas: u32,
    /// Qué ventanas se prenden de noche, piso por piso (de abajo hacia arriba), sin planta baja.
    pub encendidas: Vec<bool>,
}

impl Edificio {
    pub fn alto(&self) -> f32 {
        ALTO_PB + (self.pisos.saturating_sub(1)) as f32 * ALTO_PISO
    }

    /// Planta en el piso: `[x_min, z_min, x_max, z_max]` (las fachadas giran de a 90°).
    pub fn planta(&self) -> [f32; 4] {
        let girado = (self.rot_y.abs() - 90.0).abs() < 1.0;
        let (mx, mz) = if girado { (self.fondo, self.ancho) } else { (self.ancho, self.fondo) };
        [self.x - mx / 2.0, self.z - mz / 2.0, self.x + mx / 2.0, self.z + mz / 2.0]
    }
}

const COLORES_FACHADA: [[f32; 3]; 8] = [
    [0.86, 0.8, 0.68],
    [0.75, 0.55, 0.45],
    [0.62, 0.66, 0.7],
    [0.9, 0.88, 0.82],
    [0.7, 0.42, 0.32],
    [0.55, 0.6, 0.5],
    [0.82, 0.72, 0.55],
    [0.5, 0.5, 0.55],
];
const COLORES_TOLDO: [[f32; 3]; 5] =
    [[0.75, 0.1, 0.1], [0.1, 0.35, 0.65], [0.15, 0.5, 0.25], [0.85, 0.55, 0.1], [0.3, 0.3, 0.32]];

/// Una fila de edificios pegados sobre una línea de fachada.
fn fila(azar: &mut Azar, inicio: (f32, f32), rot_y: f32, largo: f32, pisos: (u32, u32), v: &mut Vec<Edificio>) {
    let r = rot_y.to_radians();
    let a = (r.cos(), -r.sin()); // a lo largo de la fachada
    let f = (r.sin(), r.cos()); // hacia donde mira
    let mut u = 0.0;
    while u < largo - 4.0 {
        let ancho = azar.rango(6.0, 12.0).min(largo - u);
        let fondo = azar.rango(9.0, 14.0);
        let p = pisos.0 + azar.entero((pisos.1 - pisos.0 + 1) as usize) as u32;
        let columnas = ((ancho - 1.0) / (ANCHO_VENTANA + 0.4)).floor().max(1.0) as u32;
        let encendidas = (0..(p - 1) * columnas).map(|_| azar.chance(0.35)).collect();
        let toldo = if azar.chance(0.6) { azar.elegir(&COLORES_TOLDO).copied() } else { None };
        let centro_u = u + ancho / 2.0;
        v.push(Edificio {
            x: inicio.0 + a.0 * centro_u - f.0 * fondo / 2.0,
            z: inicio.1 + a.1 * centro_u - f.1 * fondo / 2.0,
            ancho,
            fondo,
            rot_y,
            pisos: p,
            color: *azar.elegir(&COLORES_FACHADA).unwrap(),
            toldo,
            columnas,
            encendidas,
        });
        u += ancho;
    }
}

/// REQ-AMB-01, REQ-AMB-03
pub fn edificios() -> Vec<Edificio> {
    let mut azar = Azar::new(SEMILLA_CIUDAD);
    let mut v = Vec::new();
    fila(&mut azar, (-60.0, Z_FACHADA_NORTE), 0.0, 120.0, (2, 7), &mut v);
    fila(&mut azar, (45.0, Z_FACHADA_SUR), 180.0, 90.0, (2, 5), &mut v);
    fila(&mut azar, (X_FACHADA_ESTE, -20.0), -90.0, 46.0, (2, 5), &mut v);
    fila(&mut azar, (-X_FACHADA_ESTE, 26.0), 90.0, 46.0, (2, 5), &mut v);
    v
}

// ── Calle ─────────────────────────────────────────────────────────────
// Los autos están en `autos.rs` (REQ-AMB-08, REQ-AMB-17).

/// Sendas peatonales (x).
pub const SENDAS: [f32; 2] = [-25.0, 25.0];

// ── Nubes ─────────────────────────────────────────────────────────────

pub const VIENTO: [f32; 2] = [2.5, 0.8]; // m/s (x, z)
pub const LIMITE_NUBES: f32 = 420.0;

#[derive(Debug, Clone, PartialEq)]
pub struct Nube {
    pub x: f32,
    pub z: f32,
    pub altura: f32,
    /// (desplazamiento, radio) de cada bola de la nube.
    pub bolas: Vec<([f32; 3], f32)>,
}

/// REQ-AMB-11
pub fn nubes() -> Vec<Nube> {
    let mut azar = Azar::new(SEMILLA_CIUDAD + 2);
    (0..16)
        .map(|_| {
            let n = 4 + azar.entero(4);
            let largo = azar.rango(30.0, 60.0);
            let bolas = (0..n)
                .map(|i| {
                    let t = i as f32 / (n - 1) as f32 - 0.5;
                    let r = azar.rango(9.0, 17.0) * (1.0 - t.abs());
                    ([t * largo, azar.rango(-2.0, 4.0), azar.rango(-6.0, 6.0)], r.max(6.0))
                })
                .collect();
            Nube {
                x: azar.rango(-LIMITE_NUBES, LIMITE_NUBES),
                z: azar.rango(-LIMITE_NUBES, LIMITE_NUBES),
                altura: azar.rango(90.0, 140.0),
                bolas,
            }
        })
        .collect()
}

pub fn envolver_nube(v: f32) -> f32 {
    if v > LIMITE_NUBES {
        v - 2.0 * LIMITE_NUBES
    } else if v < -LIMITE_NUBES {
        v + 2.0 * LIMITE_NUBES
    } else {
        v
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::plaza;

    #[test]
    fn req_amb_01_edificios_alrededor_variados() {
        let e = edificios();
        assert!(e.len() > 25);
        // Fila de enfrente: del otro lado de la calle, mirando a la plaza.
        let norte: Vec<_> = e.iter().filter(|b| b.rot_y == 0.0).collect();
        assert!(norte.len() >= 10);
        const { assert!(Z_FACHADA_NORTE < plaza::Z_CALLE - plaza::ANCHO_CALLE / 2.0) };
        for b in &norte {
            assert!(b.z + b.fondo / 2.0 <= Z_FACHADA_NORTE + 0.01, "{b:?}");
        }
        // Los otros tres lados.
        for rot in [180.0, -90.0, 90.0] {
            assert!(e.iter().any(|b| b.rot_y == rot), "falta el lado {rot}");
        }
        let pisos: std::collections::HashSet<_> = e.iter().map(|b| b.pisos).collect();
        assert!(pisos.len() >= 4 && e.iter().all(|b| (2..=7).contains(&b.pisos)));
        assert!(e.iter().any(|b| b.toldo.is_some()) && e.iter().any(|b| b.toldo.is_none()));
        // Ningún edificio pisa la plaza.
        for b in &e {
            assert!(b.x.abs() > plaza::LADO_PLAZA / 2.0 + 5.0 || b.z.abs() > plaza::LADO_PLAZA / 2.0 + 5.0, "{b:?}");
        }
    }

    #[test]
    fn req_amb_02_algunas_ventanas_se_prenden() {
        let e = edificios();
        let total: usize = e.iter().map(|b| b.encendidas.len()).sum();
        let prendidas = e.iter().flat_map(|b| &b.encendidas).filter(|x| **x).count();
        assert!(total > 200);
        let f = prendidas as f32 / total as f32;
        assert!((0.25..0.45).contains(&f), "{f}");
        for b in &e {
            assert_eq!(b.encendidas.len() as u32, (b.pisos - 1) * b.columnas);
        }
    }

    #[test]
    fn req_amb_03_ciudad_repetible() {
        assert_eq!(edificios(), edificios());
        assert_eq!(nubes(), nubes());
    }

    #[test]
    fn req_amb_11_nubes_altas_que_se_mueven() {
        let n = nubes();
        assert!(n.len() >= 10);
        assert!(n.iter().all(|c| c.altura >= 80.0 && !c.bolas.is_empty()));
        assert!(VIENTO[0].hypot(VIENTO[1]) > 0.5);
        assert_eq!(envolver_nube(LIMITE_NUBES + 5.0), -LIMITE_NUBES + 5.0);
    }
}
