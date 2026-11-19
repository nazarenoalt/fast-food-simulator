//! SPEC-028 · Dibuja el logo del carrito. Cada calcomanía es una lámina (QuadMesh) con una
//! imagen que arma una SubViewport: fondo, marcos, figura, guardas y el texto. Las reglas (texto
//! válido, acomodo, lugares) viven en `carrito_core::logo`.

use carrito_core::logo::{self as reglas, DisenoLogo, FormaLogo, LugarLogo, Rect};
use godot::classes::base_material_3d::{EmissionOperator, Feature, Flags, TextureFilter, TextureParam};
use godot::classes::geometry_instance_3d::ShadowCastingSetting;
use godot::classes::sub_viewport::UpdateMode;
use godot::classes::text_server::FontAntialiasing;
use godot::classes::viewport::DefaultCanvasItemTextureFilter;
use godot::classes::{
    FontFile, INode2D, ImageTexture, MeshInstance3D, Node2D, QuadMesh, RenderingServer, StandardMaterial3D,
    SubViewport, Texture2D, ViewportTexture,
};
use godot::prelude::*;

use crate::{formas, nocturno};

/// Alto en píxeles de la imagen de cada calcomanía (el ancho sale de la proporción del lugar).
const ALTO_PX: f32 = 128.0;
const ANCHO_MAX_PX: f32 = 2048.0;
/// REQ-LOG-06: brillo de noche de los lugares que brillan (como los carteles, REQ-MOD-07).
const BRILLO_NOCHE: f32 = 0.8;

fn color(c: [f32; 3]) -> Color {
    Color::from_rgb(c[0], c[1], c[2])
}

fn rect2(r: Rect) -> Rect2 {
    Rect2::new(Vector2::new(r.x, r.y), Vector2::new(r.ancho, r.alto))
}

/// REQ-LOG-04: la tipografía de los carteles, sin suavizado.
fn fuente() -> Option<Gd<FontFile>> {
    let mut f = try_load::<FontFile>(&format!("res://{}", reglas::FUENTE)).ok()?;
    f.set_antialiasing(FontAntialiasing::NONE);
    Some(f)
}

/// Puntos de una elipse inscripta en `r`.
fn elipse(r: Rect) -> PackedVector2Array {
    let (cx, cy, rx, ry) = (r.x + r.ancho / 2.0, r.y + r.alto / 2.0, r.ancho / 2.0, r.alto / 2.0);
    (0..64)
        .map(|i| {
            let a = i as f32 / 64.0 * std::f32::consts::TAU;
            Vector2::new(cx + rx * a.cos(), cy + ry * a.sin())
        })
        .collect()
}

fn achicar(r: Rect, d: f32) -> Rect {
    Rect { x: r.x + d, y: r.y + d, ancho: r.ancho - 2.0 * d, alto: r.alto - 2.0 * d }
}

/// El dibujo de un logo (va adentro de una SubViewport). REQ-LOG-01, REQ-LOG-02
#[derive(GodotClass)]
#[class(base=Node2D, no_init)]
pub struct DibujoLogo {
    base: Base<Node2D>,
    diseno: DisenoLogo,
    texto: String,
    ancho: f32,
    alto: f32,
    /// La fuente y la figura se guardan acá: si se soltaran al terminar `draw`, Godot las borraría
    /// antes de pintar (y saldrían rectángulos lisos).
    fuente: Option<Gd<FontFile>>,
    figura: Option<Gd<Texture2D>>,
    /// Material de la calcomanía que recibe la foto del dibujo, y cuadros que lleva esperando.
    destino: Option<Gd<StandardMaterial3D>>,
    cuadros: u32,
}

impl DibujoLogo {
    fn crear(diseno: DisenoLogo, texto: &str, ancho: f32, alto: f32) -> Gd<Self> {
        let figura = diseno
            .figura
            .as_ref()
            .and_then(|f| try_load::<Texture2D>(&format!("res://{}/{f}.png", reglas::CARPETA_FIGURAS)).ok());
        Gd::from_init_fn(|base| Self {
            base,
            diseno,
            texto: texto.to_string(),
            ancho,
            alto,
            fuente: fuente(),
            figura,
            destino: None,
            cuadros: 0,
        })
    }

    /// Le pasa una foto del dibujo (una textura común, en sRGB y con mipmaps) al material de la
    /// calcomanía y borra la SubViewport. Sin pantalla (`--headless`) no hay foto: queda la imagen
    /// de la SubViewport.
    fn sacar_foto(&mut self) {
        let Some(mut vp) = self.base().get_parent().and_then(|p| p.try_cast::<SubViewport>().ok()) else { return };
        let Some(mut img) = vp.get_texture().and_then(|t| t.get_image()).filter(|i| !i.is_empty()) else { return };
        img.generate_mipmaps();
        let Some(foto) = ImageTexture::create_from_image(&img) else { return };
        if let Some(mut m) = self.destino.take() {
            m.set_texture(TextureParam::ALBEDO, &foto);
            // Una textura hecha en el momento: Forward+ ya la lee como sRGB; el modo compatible
            // (OpenGL) no, y sin esto se ve lavada.
            let compatible = RenderingServer::singleton().get_current_rendering_method() == "gl_compatibility";
            m.set_flag(Flags::ALBEDO_TEXTURE_FORCE_SRGB, compatible);
            if m.get_feature(Feature::EMISSION) {
                m.set_texture(TextureParam::EMISSION, &foto);
            }
        }
        vp.queue_free();
    }

    /// REQ-LOG-02: el texto en un renglón, achicado hasta entrar en `r`.
    fn dibujar_texto(&mut self, r: Rect) {
        let Some(f) = self.fuente.clone() else { return };
        let d = self.diseno.clone();
        let texto = d.texto_a_mostrar(&self.texto);
        let mut tam = (r.alto * 0.8) as i32;
        while tam > 8 && f.get_string_size_ex(&texto).font_size(tam).done().x > r.ancho {
            tam -= 1;
        }
        let medida = f.get_string_size_ex(&texto).font_size(tam).done();
        let (sube, baja) = (f.get_ascent_ex().font_size(tam).done(), f.get_descent_ex().font_size(tam).done());
        let x = (r.x + (r.ancho - medida.x) / 2.0).round();
        let y = (r.y + (r.alto + sube - baja) / 2.0).round();
        let corrido = (tam as f32 / 16.0).max(1.0).round();
        let alto = self.alto;
        let mut yo = self.base_mut();
        if let Some(s) = d.sombra {
            yo.draw_string_ex(&f, Vector2::new(x + corrido, y + corrido), &texto)
                .font_size(tam)
                .modulate(color(s))
                .done();
        }
        yo.draw_string_ex(&f, Vector2::new(x, y), &texto).font_size(tam).modulate(color(d.texto)).done();
        if let Some(c) = d.subrayado {
            let ys = (y + baja * 0.6 + 2.0).min(alto - 3.0);
            let grueso = (alto * 0.03).max(2.0);
            yo.draw_line_ex(Vector2::new(x, ys), Vector2::new(x + medida.x, ys), color(c)).width(grueso).done();
        }
    }
}

#[godot_api]
impl INode2D for DibujoLogo {
    fn ready(&mut self) {
        let con_destino = self.destino.is_some();
        self.base_mut().set_process(con_destino);
    }

    /// La foto se saca dos cuadros después de dibujar (cuando la SubViewport ya pintó).
    fn process(&mut self, _delta: f64) {
        self.cuadros += 1;
        if self.cuadros >= 2 {
            self.base_mut().set_process(false);
            if godot::classes::DisplayServer::singleton().get_name() != "headless" {
                self.sacar_foto();
            }
        }
    }

    fn draw(&mut self) {
        let (w, h) = (self.ancho, self.alto);
        let d = self.diseno.clone();
        let a = reglas::acomodar(&d, w, h);
        let g = a.grosor_marco;
        let todo = Rect { x: 0.0, y: 0.0, ancho: w, alto: h };
        let figura = self.figura.clone();
        {
            let mut yo = self.base_mut();
            yo.draw_rect(rect2(todo), color(d.fondo));
            match (&d.forma, a.ovalo) {
                // Óvalo: los marcos como anillos y el relleno adentro.
                (FormaLogo::Ovalo { relleno }, Some(o)) => {
                    let mut r = o;
                    for c in &d.marcos {
                        yo.draw_colored_polygon(&elipse(r), color(*c));
                        r = achicar(r, g * 1.4);
                    }
                    yo.draw_colored_polygon(&elipse(r), color(*relleno));
                }
                _ => {
                    for (i, c) in d.marcos.iter().enumerate() {
                        let r = achicar(todo, i as f32 * g + g / 2.0);
                        yo.draw_rect_ex(rect2(r), color(*c)).filled(false).width(g).done();
                    }
                }
            }
            // La figura, con los píxeles de su imagen (sin suavizar).
            if let (Some(r), Some(t)) = (a.figura, &figura) {
                yo.draw_texture_rect(t, rect2(r), false);
            }
            // Guardas de filete: tres anillos corridos hacia afuera, a cada lado del texto.
            if let Some((izq, der)) = a.guardas {
                for (z, lado) in [(izq, -1.0), (der, 1.0)] {
                    let centro = Vector2::new(z.x + z.ancho / 2.0, z.y + z.alto / 2.0);
                    for (k, c) in d.guardas.iter().enumerate() {
                        let k = k as f32;
                        let radio = z.alto * (0.42 - 0.11 * k);
                        let c0 = centro + Vector2::new(lado * k * z.alto * 0.2, 0.0);
                        yo.draw_arc_ex(c0, radio, 0.0, std::f32::consts::TAU, 40, color(*c))
                            .width((h * 0.035).max(2.0))
                            .done();
                    }
                }
            }
        }
        self.dibujar_texto(a.texto);
    }
}

/// Una SubViewport que dibuja el logo una vez, y su imagen.
pub fn imagen(d: &DisenoLogo, texto: &str, ancho: f32, alto: f32) -> (Gd<SubViewport>, Gd<ViewportTexture>) {
    imagen_para(d, texto, ancho, alto, None)
}

/// Como `imagen`; si hay `destino`, después le pasa una foto del dibujo y se borra.
fn imagen_para(
    d: &DisenoLogo,
    texto: &str,
    ancho: f32,
    alto: f32,
    destino: Option<Gd<StandardMaterial3D>>,
) -> (Gd<SubViewport>, Gd<ViewportTexture>) {
    let mut vp = SubViewport::new_alloc();
    vp.set_size(Vector2i::new(ancho as i32, alto as i32));
    vp.set_disable_3d(true);
    vp.set_transparent_background(false);
    vp.set_default_canvas_item_texture_filter(DefaultCanvasItemTextureFilter::NEAREST);
    vp.set_update_mode(UpdateMode::ONCE);
    let mut dibujo = DibujoLogo::crear(d.clone(), texto, ancho, alto);
    dibujo.bind_mut().destino = destino;
    vp.add_child(&dibujo);
    let tex = vp.get_texture().expect("una SubViewport siempre tiene imagen");
    (vp, tex)
}

/// REQ-LOG-05: la calcomanía de un lugar (2 mm delante de la superficie, ya puesto en `pos`).
/// Si el lugar brilla, de noche brilla con su mismo dibujo (REQ-LOG-06).
pub fn calcomania(l: &LugarLogo, d: &DisenoLogo, texto: &str) -> Gd<MeshInstance3D> {
    let ancho = (ALTO_PX * l.tam[0] / l.tam[1]).round().clamp(32.0, ANCHO_MAX_PX);
    let mut malla = QuadMesh::new_gd();
    malla.set_size(Vector2::new(l.tam[0], l.tam[1]));
    let mut mat = StandardMaterial3D::new_gd();
    let (vp, tex) = imagen_para(d, texto, ancho, ALTO_PX, Some(mat.clone()));
    mat.set_texture(TextureParam::ALBEDO, &tex);
    mat.set_texture_filter(TextureFilter::LINEAR_WITH_MIPMAPS);
    // Hasta la foto, la imagen de la SubViewport (en sRGB, como un .png: sin esto se ve lavada).
    mat.set_flag(Flags::ALBEDO_TEXTURE_FORCE_SRGB, true);
    mat.set_roughness(0.7);
    if l.brilla {
        mat.set_feature(Feature::EMISSION, true);
        mat.set_emission(Color::WHITE);
        mat.set_texture(TextureParam::EMISSION, &tex);
        // Blanco × dibujo: brilla con sus colores. Con el operador por defecto (sumar) sería
        // blanco + dibujo, y de noche se vería lavado, casi blanco.
        mat.set_emission_operator(EmissionOperator::MULTIPLY);
        nocturno::registrar(mat.clone(), BRILLO_NOCHE);
    }
    let mut mi = MeshInstance3D::new_alloc();
    mi.set_name(&format!("Logo_{}", l.lugar));
    mi.set_mesh(&malla);
    mi.set_material_override(&mat);
    mi.set_cast_shadows_setting(ShadowCastingSetting::OFF);
    mi.set_position(formas::v3(l.pos));
    mi.set_rotation_degrees(Vector3::new(0.0, l.rot_y, 0.0));
    mi.add_child(&vp);
    mi
}
