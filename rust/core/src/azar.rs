//! Números al azar con semilla (repetibles). Sin dependencias externas.

#[derive(Debug, Clone)]
pub struct Azar(u64);

impl Azar {
    pub fn new(semilla: u64) -> Self {
        // Mezcla la semilla para que semillas parecidas den secuencias distintas.
        let mut s = semilla.wrapping_add(0x9E37_79B9_7F4A_7C15);
        s = (s ^ (s >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        s = (s ^ (s >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        Self((s ^ (s >> 31)) | 1)
    }

    /// xorshift64*
    pub fn siguiente(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    /// Real en [0, 1).
    pub fn real(&mut self) -> f32 {
        (self.siguiente() >> 40) as f32 / (1u64 << 24) as f32
    }

    pub fn rango(&mut self, a: f32, b: f32) -> f32 {
        a + (b - a) * self.real()
    }

    /// Entero en [0, n).
    pub fn entero(&mut self, n: usize) -> usize {
        if n == 0 { 0 } else { (self.siguiente() % n as u64) as usize }
    }

    pub fn chance(&mut self, p: f32) -> bool {
        self.real() < p
    }

    pub fn elegir<'a, T>(&mut self, v: &'a [T]) -> Option<&'a T> {
        if v.is_empty() { None } else { v.get(self.entero(v.len())) }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repetible_y_en_rango() {
        let mut a = Azar::new(7);
        let mut b = Azar::new(7);
        for _ in 0..1000 {
            let x = a.real();
            assert_eq!(x, b.real());
            assert!((0.0..1.0).contains(&x));
            assert!(a.entero(5) < 5);
            b.entero(5);
        }
        assert_ne!(Azar::new(1).siguiente(), Azar::new(2).siguiente());
    }

    #[test]
    fn distribucion_razonable() {
        let mut a = Azar::new(3);
        let n = 20_000;
        let si = (0..n).filter(|_| a.chance(0.25)).count() as f32 / n as f32;
        assert!((si - 0.25).abs() < 0.02, "{si}");
    }
}
