//! SPEC-001 · Cómo se mueve el jugador: arranque y frenado suaves y balanceo de la cámara.
//! Velocidades horizontales como `[x, z]` (m/s).

/// REQ-JUG-02: radianes que gira la vista por cada píxel que se mueve el mouse.
pub const SENSIBILIDAD: f32 = 0.0018;
/// REQ-JUG-04: velocidad con que sale el salto (m/s): sube ~0,6 m con la gravedad de 9,8.
pub const VEL_SALTO: f32 = 3.5;
/// REQ-JUG-10: en el piso, cuánto cambia la velocidad por segundo al acelerar y al frenar (m/s²).
pub const ACELERACION: f32 = 12.0;
pub const FRENADO: f32 = 16.0;
/// REQ-JUG-10: en el aire, casi no se puede cambiar el rumbo (m/s²).
pub const ACELERACION_AIRE: f32 = 3.0;
/// REQ-JUG-10: balanceo de la cámara al caminar: alto (m), pasos por segundo a `VEL_REFERENCIA`
/// y tiempo en volver al centro al parar (s).
pub const BALANCEO_ALTO: f32 = 0.02;
pub const PASOS_POR_SEGUNDO: f32 = 2.0;
pub const VEL_REFERENCIA: f32 = 3.5;
pub const BALANCEO_VUELTA: f32 = 0.2;

/// REQ-JUG-10: la velocidad horizontal `actual` va hacia la `pedida`, sin pasarse. En el piso
/// acelera con `ACELERACION` y frena (pide menos, o para el otro lado) con `FRENADO`; en el
/// aire, con `ACELERACION_AIRE`.
pub fn acercar_velocidad(actual: [f32; 2], pedida: [f32; 2], en_piso: bool, dt: f32) -> [f32; 2] {
    let largo = |v: [f32; 2]| (v[0] * v[0] + v[1] * v[1]).sqrt();
    let frena = largo(pedida) < largo(actual) || actual[0] * pedida[0] + actual[1] * pedida[1] < 0.0;
    let a = match (en_piso, frena) {
        (false, _) => ACELERACION_AIRE,
        (true, true) => FRENADO,
        (true, false) => ACELERACION,
    };
    let d = [pedida[0] - actual[0], pedida[1] - actual[1]];
    let falta = largo(d);
    let paso = a * dt;
    if falta <= paso {
        return pedida;
    }
    [actual[0] + d[0] / falta * paso, actual[1] + d[1] / falta * paso]
}

/// REQ-JUG-10: balanceo de la cámara al caminar.
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Balanceo {
    /// Pasos dados, sin la parte entera (cada paso es una subida y bajada de la cámara).
    pub fase: f32,
    /// Alto actual del balanceo (m): va hacia el que corresponde a la velocidad.
    pub alto: f32,
}

impl Balanceo {
    /// Avanza `dt` caminando a `velocidad` (m/s, horizontal). Devuelve cuánto sube (o baja, si
    /// es negativo) la cámara (m). En el aire o quieto vuelve al centro en `BALANCEO_VUELTA`.
    pub fn paso(&mut self, velocidad: f32, en_piso: bool, dt: f32) -> f32 {
        let v = if en_piso { velocidad.max(0.0) } else { 0.0 };
        let objetivo = BALANCEO_ALTO * (v / VEL_REFERENCIA).min(1.0);
        let cambio = BALANCEO_ALTO / BALANCEO_VUELTA * dt;
        self.alto =
            if objetivo > self.alto { (self.alto + cambio).min(objetivo) } else { (self.alto - cambio).max(objetivo) };
        self.fase = (self.fase + PASOS_POR_SEGUNDO * v / VEL_REFERENCIA * dt).fract();
        self.alto * (self.fase * std::f32::consts::TAU).sin()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DT: f32 = 1.0 / 60.0;

    #[test]
    fn req_jug_02_y_req_jug_04_sensibilidad_y_salto() {
        assert_eq!(SENSIBILIDAD, 0.0018);
        let alto = VEL_SALTO * VEL_SALTO / (2.0 * 9.8);
        assert!((alto - 0.6).abs() < 0.03, "sube ~0,6 m: {alto}");
    }

    #[test]
    fn req_jug_10_arranca_de_a_poco_con_12_m_s2() {
        let v = acercar_velocidad([0.0, 0.0], [3.5, 0.0], true, DT);
        assert!((v[0] - 12.0 * DT).abs() < 1e-5, "el primer cuadro: {v:?}");
        let mut v = [0.0, 0.0];
        let mut t = 0.0;
        while v[0] < 3.5 {
            v = acercar_velocidad(v, [3.5, 0.0], true, DT);
            t += DT;
        }
        assert!((t - 3.5 / 12.0).abs() < 2.0 * DT, "llega a 3,5 m/s en ~0,29 s: {t}");
        assert_eq!(v, [3.5, 0.0], "sin pasarse");
    }

    #[test]
    fn req_jug_10_frena_con_16_m_s2_y_en_el_aire_con_3() {
        let v = acercar_velocidad([3.5, 0.0], [0.0, 0.0], true, DT);
        assert!((3.5 - v[0] - 16.0 * DT).abs() < 1e-5, "frena: {v:?}");
        let v = acercar_velocidad([3.5, 0.0], [-3.5, 0.0], true, DT);
        assert!((3.5 - v[0] - 16.0 * DT).abs() < 1e-5, "darse vuelta también es frenar: {v:?}");
        let v = acercar_velocidad([0.0, 0.0], [0.0, 3.5], false, DT);
        assert!((v[1] - 3.0 * DT).abs() < 1e-5, "en el aire: {v:?}");
        let v = acercar_velocidad([3.5, 0.0], [0.0, 0.0], false, DT);
        assert!((3.5 - v[0] - 3.0 * DT).abs() < 1e-5, "en el aire casi no frena: {v:?}");
    }

    #[test]
    fn req_jug_10_balanceo_de_2_cm_y_2_pasos_por_segundo() {
        let mut b = Balanceo::default();
        let (mut max, mut min) = (0.0f32, 0.0f32);
        let mut subidas = 0;
        let mut antes = 0.0;
        // 0,5 s para tomar el alto y después 2 s caminando a 3,5 m/s.
        for i in 0..150 {
            let y = b.paso(3.5, true, DT);
            if i >= 30 {
                max = max.max(y);
                min = min.min(y);
                if antes < 0.0 && y >= 0.0 {
                    subidas += 1;
                }
            }
            antes = y;
        }
        assert!((max - 0.02).abs() < 0.001 && (min + 0.02).abs() < 0.001, "2 cm: {min} a {max}");
        assert!((3..=5).contains(&subidas), "2 pasos por segundo en 2 s: {subidas}");
        // Más lento, más chico.
        let mut lento = Balanceo::default();
        let mut max_lento = 0.0f32;
        for _ in 0..240 {
            max_lento = max_lento.max(lento.paso(1.75, true, DT));
        }
        assert!((max_lento - 0.01).abs() < 0.001, "a 1,75 m/s, 1 cm: {max_lento}");
    }

    #[test]
    fn req_jug_10_al_parar_vuelve_al_centro_en_0_2_s() {
        let mut b = Balanceo::default();
        for _ in 0..80 {
            b.paso(3.5, true, DT);
        }
        let mut y = 1.0;
        for _ in 0..12 {
            y = b.paso(0.0, true, DT);
        }
        assert!(y.abs() < 1e-6, "en 0,2 s está en el centro: {y}");
        let mut aire = Balanceo { fase: 0.25, alto: BALANCEO_ALTO };
        for _ in 0..12 {
            y = aire.paso(3.5, false, DT);
        }
        assert!(y.abs() < 1e-6, "en el aire no se balancea: {y}");
    }
}
