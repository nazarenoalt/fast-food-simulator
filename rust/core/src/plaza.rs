//! SPEC-008 · Distribución fija de la plaza.
//!
//! Coordenadas del mundo: la plaza está centrada en (0, 0). Norte = -Z, este = +X.
//! La calle y la vereda corren por el lado norte; el carrito queda en la vereda.

pub const TAMANO_TERRENO: f32 = 120.0; // REQ-MUN-01
pub const LADO_PLAZA: f32 = 40.0; // REQ-MUN-02
pub const ANCHO_CAMINO: f32 = 3.0;
/// Centro de la vereda (en Z) donde va el carrito. REQ-MUN-03
pub const Z_VEREDA: f32 = -23.0;
pub const ANCHO_VEREDA: f32 = 4.0;
pub const Z_CALLE: f32 = -29.0;
pub const ANCHO_CALLE: f32 = 8.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TipoProp {
    Banco,
    Arbol,
    Farol,
    Fuente,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Prop {
    pub tipo: TipoProp,
    pub x: f32,
    pub z: f32,
    /// Giro en Y, grados.
    pub rot_y: f32,
}

/// REQ-MUN-02, REQ-MUN-05: misma distribución siempre (sin azar).
pub fn distribucion() -> Vec<Prop> {
    let mut v = vec![Prop { tipo: TipoProp::Fuente, x: 0.0, z: 0.0, rot_y: 0.0 }];
    let medio = LADO_PLAZA / 2.0;

    // Bancos a los costados de los dos caminos en cruz, mirando al camino.
    for &d in &[7.0_f32, 13.0] {
        for &s in &[-1.0_f32, 1.0] {
            v.push(Prop { tipo: TipoProp::Banco, x: s * d, z: 2.6, rot_y: 180.0 });
            v.push(Prop { tipo: TipoProp::Banco, x: s * d, z: -2.6, rot_y: 0.0 });
            v.push(Prop { tipo: TipoProp::Banco, x: 2.6, z: s * d, rot_y: -90.0 });
            v.push(Prop { tipo: TipoProp::Banco, x: -2.6, z: s * d, rot_y: 90.0 });
        }
    }

    // Árboles en los cuatro cuadrantes, en una grilla con corrimiento fijo.
    for &sx in &[-1.0_f32, 1.0] {
        for &sz in &[-1.0_f32, 1.0] {
            for (i, &(a, b)) in
                [(6.5, 6.5), (12.0, 7.0), (7.0, 12.5), (15.5, 15.0), (11.5, 16.5), (16.5, 10.5)].iter().enumerate()
            {
                let corr = (i as f32 * 0.37).sin() * 0.8;
                v.push(Prop { tipo: TipoProp::Arbol, x: sx * (a + corr), z: sz * (b - corr), rot_y: i as f32 * 47.0 });
            }
        }
    }

    // Faroles: en el anillo de la fuente, en los caminos y sobre la vereda.
    for &(x, z) in &[(4.0, 4.0), (-4.0, 4.0), (4.0, -4.0), (-4.0, -4.0)] {
        v.push(Prop { tipo: TipoProp::Farol, x, z, rot_y: 0.0 });
    }
    for &d in &[10.0_f32, 17.0] {
        for &s in &[-1.0_f32, 1.0] {
            v.push(Prop { tipo: TipoProp::Farol, x: s * d, z: 1.8, rot_y: 0.0 });
            v.push(Prop { tipo: TipoProp::Farol, x: 1.8, z: s * d, rot_y: 0.0 });
        }
    }
    for &x in &[-medio, -medio / 2.0, medio / 2.0, medio] {
        v.push(Prop { tipo: TipoProp::Farol, x: x + 3.0, z: Z_VEREDA - 1.5, rot_y: 0.0 });
    }
    v
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_mun_01_terreno() {
        assert_eq!(TAMANO_TERRENO, 120.0);
    }

    #[test]
    fn req_mun_02_plaza_con_todo() {
        let d = distribucion();
        for t in [TipoProp::Fuente, TipoProp::Banco, TipoProp::Arbol, TipoProp::Farol] {
            assert!(d.iter().any(|p| p.tipo == t), "falta {t:?}");
        }
        let medio = LADO_PLAZA / 2.0;
        for p in d.iter().filter(|p| p.tipo != TipoProp::Farol) {
            assert!(p.x.abs() <= medio && p.z.abs() <= medio, "{p:?} fuera de la plaza");
        }
        // Los árboles no caen sobre los caminos en cruz.
        for p in d.iter().filter(|p| p.tipo == TipoProp::Arbol) {
            assert!(p.x.abs() > ANCHO_CAMINO && p.z.abs() > ANCHO_CAMINO, "árbol en el camino: {p:?}");
        }
    }

    #[test]
    fn req_mun_02_bancos_miran_al_camino() {
        // El frente del banco (eje +Z local girado) apunta hacia el camino más cercano.
        for p in distribucion().iter().filter(|p| p.tipo == TipoProp::Banco) {
            let (s, c) = p.rot_y.to_radians().sin_cos();
            let (fx, fz) = (s, c);
            let hacia_camino = if p.x.abs() < p.z.abs() { (-p.x.signum(), 0.0) } else { (0.0, -p.z.signum()) };
            assert!(fx * hacia_camino.0 + fz * hacia_camino.1 > 0.9, "banco {p:?} no mira al camino");
        }
    }

    #[test]
    fn req_mun_03_vereda_y_calle_fuera_de_la_plaza() {
        assert!(Z_VEREDA + ANCHO_VEREDA / 2.0 <= -LADO_PLAZA / 2.0);
        assert!(Z_CALLE + ANCHO_CALLE / 2.0 <= Z_VEREDA - ANCHO_VEREDA / 2.0);
    }

    #[test]
    fn req_mun_05_siempre_igual() {
        assert_eq!(distribucion(), distribucion());
    }
}
