//! SPEC-028 · Logo del carrito: diseños, texto, lugares y cómo se acomoda el dibujo.
//! Reglas puras; el juego (`game/src/logo.rs`) dibuja la calcomanía.

use std::fmt;

use serde::Deserialize;

use crate::datos::Catalogo;
use crate::tienda::Armado;

/// REQ-LOG-03: largo máximo del texto, en caracteres.
pub const LARGO_MAX: usize = 18;
/// REQ-LOG-03: signos permitidos además de letras, números y espacio.
pub const SIGNOS: &str = ".,'-&!";
/// REQ-LOG-02: desde esta proporción (ancho / alto) el lugar es largo.
pub const PROPORCION_LARGA: f32 = 3.0;
/// REQ-LOG-05: la calcomanía va 2 mm delante de la superficie.
pub const SEPARACION: f32 = 0.002;
/// REQ-LOG-04: tipografía de los carteles pintados.
pub const FUENTE: &str = "fuentes/DejaVuSans-Bold.ttf";
/// REQ-LOG-01: carpeta de las figuras (dentro de `godot/`).
pub const CARPETA_FIGURAS: &str = "logos";

/// REQ-LOG-01
#[derive(Debug, Clone, PartialEq, Deserialize, Default)]
pub enum FormaLogo {
    #[default]
    Rectangulo,
    /// Óvalo centrado con los marcos como anillos y este relleno adentro.
    Ovalo { relleno: [f32; 3] },
}

/// Un diseño de logo (`godot/data/logos.ron`). REQ-LOG-01
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DisenoLogo {
    pub id: String,
    pub nombre: String,
    pub fondo: [f32; 3],
    /// De afuera hacia adentro.
    #[serde(default)]
    pub marcos: Vec<[f32; 3]>,
    #[serde(default)]
    pub forma: FormaLogo,
    /// Nombre del `.png` en `godot/logos/` (sin extensión).
    #[serde(default)]
    pub figura: Option<String>,
    pub texto: [f32; 3],
    #[serde(default)]
    pub sombra: Option<[f32; 3]>,
    #[serde(default)]
    pub mayusculas: bool,
    /// Colores de los tres anillos de cada guarda de filete (vacío: sin guardas).
    #[serde(default)]
    pub guardas: Vec<[f32; 3]>,
    #[serde(default)]
    pub subrayado: Option<[f32; 3]>,
}

impl DisenoLogo {
    /// Todos los colores que usa (para revisar que sean de la paleta).
    pub fn colores(&self) -> Vec<[f32; 3]> {
        let mut v = vec![self.fondo, self.texto];
        v.extend(&self.marcos);
        v.extend(&self.guardas);
        v.extend(self.sombra);
        v.extend(self.subrayado);
        if let FormaLogo::Ovalo { relleno } = self.forma {
            v.push(relleno);
        }
        v
    }

    /// El texto como se dibuja (en mayúsculas si el diseño lo pide).
    pub fn texto_a_mostrar(&self, texto: &str) -> String {
        if self.mayusculas { texto.to_uppercase() } else { texto.to_string() }
    }
}

/// Un lugar donde va una calcomanía con el logo, relativo a la base o al accesorio. REQ-LOG-05
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct LugarLogo {
    /// Nombre que ve el jugador (varios lugares pueden compartirlo).
    pub lugar: String,
    /// Centro de la calcomanía (ya separada de la superficie).
    pub pos: [f32; 3],
    /// Giro en Y, grados (0: mira a +Z).
    #[serde(default)]
    pub rot_y: f32,
    /// Ancho y alto, metros.
    pub tam: [f32; 2],
    #[serde(default)]
    pub brilla: bool,
}

/// El logo elegido. REQ-LOG-08, REQ-LOG-10
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Logo {
    pub diseno: String,
    pub texto: String,
    /// Lugares apagados (por nombre); el resto se ve.
    #[serde(default)]
    pub apagados: Vec<String>,
}

impl Logo {
    /// REQ-LOG-08
    pub fn prendido(&self, lugar: &str) -> bool {
        !self.apagados.iter().any(|a| a == lugar)
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum ErrorLogo {
    Vacio,
    Largo(usize),
    Caracter(char),
    DisenoInexistente(String),
    SinLogo,
}

impl fmt::Display for ErrorLogo {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ErrorLogo::Vacio => write!(f, "Escribí el nombre del puesto"),
            ErrorLogo::Largo(n) => write!(f, "El nombre tiene {n} caracteres: el máximo es {LARGO_MAX}"),
            ErrorLogo::Caracter(c) => write!(f, "El nombre no puede llevar \"{c}\""),
            ErrorLogo::DisenoInexistente(d) => write!(f, "No existe el diseño de logo \"{d}\""),
            ErrorLogo::SinLogo => write!(f, "Primero elegí un logo"),
        }
    }
}

/// REQ-LOG-03
pub fn permitido(c: char) -> bool {
    c.is_ascii_alphanumeric() || c == ' ' || SIGNOS.contains(c) || "áéíóúüñÁÉÍÓÚÜÑ".contains(c)
}

/// REQ-LOG-03: devuelve el texto sin los espacios de las puntas, o por qué no sirve.
pub fn validar_texto(texto: &str) -> Result<String, ErrorLogo> {
    let t = texto.trim();
    if t.is_empty() {
        return Err(ErrorLogo::Vacio);
    }
    if let Some(c) = t.chars().find(|c| !permitido(*c)) {
        return Err(ErrorLogo::Caracter(c));
    }
    let n = t.chars().count();
    if n > LARGO_MAX {
        return Err(ErrorLogo::Largo(n));
    }
    Ok(t.to_string())
}

/// Rectángulo en píxeles del dibujo (origen arriba a la izquierda).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Rect {
    pub x: f32,
    pub y: f32,
    pub ancho: f32,
    pub alto: f32,
}

impl Rect {
    pub fn adentro_de(&self, ancho: f32, alto: f32) -> bool {
        self.x >= 0.0 && self.y >= 0.0 && self.x + self.ancho <= ancho + 1e-3 && self.y + self.alto <= alto + 1e-3
    }
    pub fn se_pisa(&self, o: &Rect) -> bool {
        self.x < o.x + o.ancho && o.x < self.x + self.ancho && self.y < o.y + o.alto && o.y < self.y + self.alto
    }
}

/// Dónde va cada parte del dibujo. REQ-LOG-02
#[derive(Debug, Clone, PartialEq)]
pub struct Acomodo {
    pub largo: bool,
    /// Grosor de cada marco.
    pub grosor_marco: f32,
    pub ovalo: Option<Rect>,
    pub figura: Option<Rect>,
    pub texto: Rect,
    /// Zonas de las dos guardas (izquierda, derecha), si el diseño las tiene y el lugar es largo.
    pub guardas: Option<(Rect, Rect)>,
}

/// REQ-LOG-02: acomoda el diseño en un dibujo de `ancho` × `alto` píxeles.
pub fn acomodar(d: &DisenoLogo, ancho: f32, alto: f32) -> Acomodo {
    let largo = ancho >= alto * PROPORCION_LARGA;
    let grosor = (alto * 0.035).max(2.0);
    let m = d.marcos.len() as f32 * grosor + alto * 0.06;
    let adentro = Rect { x: m, y: m, ancho: ancho - 2.0 * m, alto: alto - 2.0 * m };
    let mut a = Acomodo { largo, grosor_marco: grosor, ovalo: None, figura: None, texto: adentro, guardas: None };
    if let FormaLogo::Ovalo { .. } = d.forma {
        // El óvalo, lo más ancho posible sin pasar de 2,6 veces su alto; el texto, adentro.
        let alto_o = alto - 2.0 * alto * 0.06;
        let ancho_o = (ancho - 2.0 * alto * 0.06).min(alto_o * 2.6);
        let o = Rect { x: (ancho - ancho_o) / 2.0, y: (alto - alto_o) / 2.0, ancho: ancho_o, alto: alto_o };
        a.texto = Rect { x: o.x + o.ancho * 0.13, y: o.y + o.alto * 0.22, ancho: o.ancho * 0.74, alto: o.alto * 0.56 };
        a.ovalo = Some(o);
        return a;
    }
    if d.figura.is_some() {
        if largo {
            let lado = adentro.alto * 0.9;
            let f = Rect { x: m + alto * 0.08, y: (alto - lado) / 2.0, ancho: lado, alto: lado };
            let x = f.x + f.ancho + alto * 0.12;
            a.texto = Rect { x, y: adentro.y, ancho: ancho - m - x, alto: adentro.alto };
            a.figura = Some(f);
        } else {
            let lado = adentro.alto * 0.58;
            let f = Rect { x: (ancho - lado) / 2.0, y: m, ancho: lado, alto: lado };
            let y = f.y + f.alto + adentro.alto * 0.04;
            a.texto = Rect { x: adentro.x, y, ancho: adentro.ancho, alto: alto - m - y };
            a.figura = Some(f);
        }
    } else if largo && !d.guardas.is_empty() {
        let zona = alto * 1.2;
        a.guardas = Some((
            Rect { x: m, y: adentro.y, ancho: zona, alto: adentro.alto },
            Rect { x: ancho - m - zona, y: adentro.y, ancho: zona, alto: adentro.alto },
        ));
        a.texto = Rect { x: m + zona, y: adentro.y, ancho: ancho - 2.0 * (m + zona), alto: adentro.alto };
    }
    if d.subrayado.is_some() {
        a.texto.alto *= 0.85; // lugar para la raya de abajo
    }
    a
}

impl Armado {
    /// REQ-LOG-07: pone (o cambia) el logo. Los lugares apagados siguen apagados (REQ-LOG-08).
    pub fn poner_logo(&mut self, diseno: &str, texto: &str, cat: &Catalogo) -> Result<(), ErrorLogo> {
        if cat.diseno(diseno).is_none() {
            return Err(ErrorLogo::DisenoInexistente(diseno.to_string()));
        }
        let texto = validar_texto(texto)?;
        let apagados = self.logo.take().map(|l| l.apagados).unwrap_or_default();
        self.logo = Some(Logo { diseno: diseno.to_string(), texto, apagados });
        Ok(())
    }

    /// REQ-LOG-07, REQ-LOG-09
    pub fn sacar_logo(&mut self) {
        self.logo = None;
    }

    /// REQ-LOG-07: prende o apaga un lugar. Devuelve si quedó prendido.
    pub fn alternar_lugar(&mut self, lugar: &str) -> Result<bool, ErrorLogo> {
        let logo = self.logo.as_mut().ok_or(ErrorLogo::SinLogo)?;
        if logo.prendido(lugar) {
            logo.apagados.push(lugar.to_string());
            Ok(false)
        } else {
            logo.apagados.retain(|a| a != lugar);
            Ok(true)
        }
    }

    /// REQ-LOG-06, REQ-LOG-07: nombres de los lugares del carrito actual (base y accesorios
    /// puestos), sin repetir.
    pub fn lugares_logo(&self, cat: &Catalogo) -> Vec<String> {
        let mut v: Vec<String> = Vec::new();
        let base = cat.bases.iter().find(|b| b.id == self.base).map(|b| &b.logos[..]).unwrap_or_default();
        let puestos = self.accesorios.values().filter_map(|id| cat.accesorios.iter().find(|a| &a.id == id));
        for l in base.iter().chain(puestos.flat_map(|a| a.logos.iter())) {
            if !v.contains(&l.lugar) {
                v.push(l.lugar.clone());
            }
        }
        v
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::datos::tests::catalogo_real;
    use std::path::PathBuf;

    fn raiz() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
    }

    /// Colores de `tools/arte/paleta.json`, de 0 a 1.
    fn paleta() -> Vec<[f32; 3]> {
        let texto = std::fs::read_to_string(raiz().join("tools/arte/paleta.json")).unwrap();
        let v: serde_json::Value = serde_json::from_str(&texto).unwrap();
        let mut colores = Vec::new();
        for g in v["grupos"].as_array().unwrap() {
            for m in g["materiales"].as_array().unwrap() {
                let h = m["hex"].as_str().unwrap();
                let c = |i: usize| u8::from_str_radix(&h[i..i + 2], 16).unwrap() as f32 / 255.0;
                colores.push([c(1), c(3), c(5)]);
            }
        }
        colores
    }

    #[test]
    fn req_log_01_seis_disenos_con_colores_de_la_paleta_y_figuras_en_disco() {
        let c = catalogo_real();
        let nombres: Vec<&str> = c.logos.iter().map(|d| d.nombre.as_str()).collect();
        assert_eq!(nombres, ["Óvalo", "Filete", "Pancho", "Hamburguesa", "Estrella", "Pizarrón"]);
        let pal = paleta();
        for d in &c.logos {
            for col in d.colores() {
                let en_paleta = pal.iter().any(|p| (0..3).all(|i| (p[i] - col[i]).abs() < 0.003));
                assert!(en_paleta, "{}: el color {col:?} no es de la paleta", d.id);
            }
            if let Some(f) = &d.figura {
                let ruta = raiz().join("godot").join(CARPETA_FIGURAS).join(format!("{f}.png"));
                assert!(ruta.exists(), "{}: falta la figura {}", d.id, ruta.display());
            }
            assert!(d.guardas.is_empty() || d.guardas.len() == 3, "{}: las guardas llevan 3 colores", d.id);
        }
        assert!(c.logos.iter().any(|d| matches!(d.forma, FormaLogo::Ovalo { .. })));
        assert!(c.logos.iter().any(|d| d.mayusculas && !d.guardas.is_empty()), "el filete");
    }

    #[test]
    fn req_log_02_largo_figura_al_costado_y_chico_figura_arriba() {
        let c = catalogo_real();
        for d in &c.logos {
            for (w, h) in [(768.0, 128.0), (1536.0, 128.0), (270.0, 128.0), (200.0, 128.0)] {
                let a = acomodar(d, w, h);
                assert_eq!(a.largo, w >= h * PROPORCION_LARGA);
                assert!(a.texto.adentro_de(w, h) && a.texto.ancho > 0.0 && a.texto.alto > h * 0.2, "{} {w}", d.id);
                if let Some(f) = a.figura {
                    assert!(f.adentro_de(w, h) && !f.se_pisa(&a.texto), "{} {w}: figura y texto", d.id);
                    if a.largo {
                        assert!(f.x + f.ancho <= a.texto.x, "largo: la figura a la izquierda");
                    } else {
                        assert!(f.y + f.alto <= a.texto.y, "chico: la figura arriba");
                    }
                }
                match a.guardas {
                    Some((i, dr)) => {
                        assert!(a.largo, "{}: sin guardas en lo chico", d.id);
                        assert!(!i.se_pisa(&a.texto) && !dr.se_pisa(&a.texto) && dr.adentro_de(w, h));
                    }
                    None => assert!(!a.largo || d.guardas.is_empty() || d.figura.is_some()),
                }
                if let Some(o) = a.ovalo {
                    assert!(o.adentro_de(w, h) && a.texto.x >= o.x && a.texto.x + a.texto.ancho <= o.x + o.ancho);
                }
            }
        }
    }

    #[test]
    fn req_log_03_texto_de_1_a_18_caracteres_permitidos() {
        assert_eq!(validar_texto("  Panchos El Tano "), Ok("Panchos El Tano".into()));
        assert_eq!(validar_texto("Ñoño & Güemes!"), Ok("Ñoño & Güemes!".into()));
        assert_eq!(validar_texto("Lo de Tito, 1-2 '."), Ok("Lo de Tito, 1-2 '.".into()));
        assert_eq!(validar_texto("áéíóú ÁÉÍÓÚ ü"), Ok("áéíóú ÁÉÍÓÚ ü".into()));
        assert_eq!(validar_texto("   "), Err(ErrorLogo::Vacio));
        assert_eq!(validar_texto("abcdefghijklmnopqrs"), Err(ErrorLogo::Largo(19)));
        assert_eq!(validar_texto("ñññññññññññññññññ!"), Ok("ñññññññññññññññññ!".into()), "18 con ñ");
        assert_eq!(validar_texto("mail@puesto"), Err(ErrorLogo::Caracter('@')));
        assert_eq!(validar_texto("dos\nrenglones"), Err(ErrorLogo::Caracter('\n')));
        assert!(validar_texto("Pancho🌭").is_err());
        let d = catalogo_real().logos.into_iter().find(|d| d.mayusculas).unwrap();
        assert_eq!(d.texto_a_mostrar("lo de ñato"), "LO DE ÑATO");
    }

    #[test]
    fn req_log_04_la_fuente_esta_en_el_proyecto() {
        assert!(raiz().join("godot").join(FUENTE).exists());
        assert!(raiz().join("godot/fuentes/LICENCIA-DejaVu.txt").exists(), "con su licencia");
    }

    #[test]
    fn req_log_05_06_lugares_de_las_bases_y_los_accesorios() {
        let c = catalogo_real();
        let lugares = |id: &str| -> Vec<(String, bool)> {
            let base = c.bases.iter().find(|b| b.id == id).map(|b| b.logos.clone());
            let acc = c.accesorios.iter().find(|a| a.id == id).map(|a| a.logos.clone());
            base.or(acc).unwrap().into_iter().map(|l| (l.lugar, l.brilla)).collect()
        };
        for id in ["barra_chica", "barra_mediana", "carro_grande"] {
            assert_eq!(lugares(id), vec![("Costados".into(), false); 2], "{id}");
        }
        assert_eq!(lugares("carro_kiosco"), vec![("Óvalos".into(), true); 5]);
        let ft = lugares("food_truck");
        assert_eq!(ft.iter().filter(|l| l.0 == "Costados").count(), 2);
        assert!(ft.iter().any(|l| l.0 == "Atrás") && ft.iter().all(|l| !l.1));
        let tr = lugares("trailer");
        assert!(tr.contains(&("Costado".into(), false)) && tr.contains(&("Atrás".into(), false)));
        for t in ["chico", "mediano", "grande"] {
            assert_eq!(lugares(&format!("marquesina_{t}")), vec![("Marquesina".into(), true)]);
        }
        assert_eq!(lugares("cartel_luminoso"), vec![("Cartel luminoso".into(), true)]);
        for a in c.accesorios.iter().filter(|a| a.categoria == crate::carrito::Categoria::Telon) {
            assert!(a.logos.is_empty(), "{}: los telones no llevan logo", a.id);
        }
        // Cada calcomanía, dentro de su base (vista desde arriba) y de un tamaño razonable.
        for b in &c.bases {
            for l in &b.logos {
                assert!(l.tam[0] > 0.2 && l.tam[1] > 0.1 && l.tam[0] < b.ancho, "{}: {:?}", b.id, l.tam);
                assert!(l.pos[0].abs() <= b.ancho / 2.0 + 0.25 && l.pos[2].abs() <= b.profundidad / 2.0 + 0.25);
            }
        }
    }

    #[test]
    fn req_log_07_08_poner_cambiar_apagar_y_sacar() {
        let c = catalogo_real();
        let mut a = Armado::desde_config(&c.carrito_jugador, &c.bases);
        a.sacar_logo();
        assert_eq!(a.alternar_lugar("Costados"), Err(ErrorLogo::SinLogo));
        assert_eq!(a.poner_logo("no_existe", "Hola", &c), Err(ErrorLogo::DisenoInexistente("no_existe".into())));
        a.poner_logo("estrella", " Panchos El Tano ", &c).unwrap();
        assert_eq!(a.logo.as_ref().unwrap().texto, "Panchos El Tano");
        assert_eq!(a.alternar_lugar("Costados"), Ok(false));
        assert!(!a.logo.as_ref().unwrap().prendido("Costados") && a.logo.as_ref().unwrap().prendido("Marquesina"));
        // Un texto que no sirve no cambia nada (REQ-LOG-03).
        let antes = a.clone();
        assert_eq!(a.poner_logo("filete", "@@@", &c), Err(ErrorLogo::Caracter('@')));
        assert_eq!(a, antes);
        // Cambiar diseño o texto mantiene lo apagado (REQ-LOG-08).
        a.poner_logo("filete", "Otro nombre", &c).unwrap();
        assert!(!a.logo.as_ref().unwrap().prendido("Costados"));
        assert_eq!(a.alternar_lugar("Costados"), Ok(true));
        assert_eq!(a.config().logo, a.logo, "el logo pasa a la config");
        a.sacar_logo();
        assert_eq!(a.logo, None);
    }

    #[test]
    fn req_log_07_lugares_del_carrito_actual() {
        let c = catalogo_real();
        let mut a = Armado::desde_config(&c.carrito_jugador, &c.bases);
        a.base = "barra_chica".into();
        a.accesorios.clear();
        assert_eq!(a.lugares_logo(&c), vec!["Costados".to_string()]);
        a.accesorios.insert("techo".into(), "marquesina_chico".into());
        a.accesorios.insert("mostrador_der".into(), "cartel_luminoso".into());
        let l = a.lugares_logo(&c);
        assert_eq!(l.len(), 3);
        assert!(l.contains(&"Marquesina".to_string()) && l.contains(&"Cartel luminoso".to_string()));
        a.accesorios.remove("techo");
        assert!(!a.lugares_logo(&c).contains(&"Marquesina".to_string()), "sacar la marquesina saca su lugar");
    }

    #[test]
    fn req_log_10_logo_de_arranque_validado_al_cargar() {
        let cfg = |logo: &str| format!("(base: \"barra_chica\", accesorios: {{}}, logo: {logo})");
        let cargar = |logo: &str| crate::datos::tests::catalogo_con_jugador(&cfg(logo));
        assert!(cargar("None").is_ok());
        let ok = cargar("Some((diseno: \"pancho\", texto: \"El Tano\", apagados: [\"Costados\"]))").unwrap();
        let logo = ok.carrito_jugador.logo.unwrap();
        assert!(!logo.prendido("Costados"));
        let e = cargar("Some((diseno: \"nada\", texto: \"El Tano\"))").unwrap_err();
        assert!(e.to_string().contains("carrito_jugador.ron") && e.to_string().contains("nada"), "{e}");
        let e = cargar("Some((diseno: \"pancho\", texto: \"#\"))").unwrap_err();
        assert!(e.to_string().contains('#'), "{e}");
    }
}
