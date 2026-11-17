# Lista de modelos 3D

Todo lo que hay que modelar, ordenado por etapa de la [hoja de ruta](../hoja-de-ruta.md).
Cada modelo sigue la [guía de modelado](guia-modelado-3d.md).

**Cómo leer la tabla**

- **ID**: nombre del archivo (`<id>.glb`). Si ya existe en los datos (`godot/data/*.ron`), es el mismo id.
- **Medidas**: ancho × alto × profundidad en metros (X × Y × Z de Godot), tomadas de los datos
  o del código actual. "≈" = medida propuesta, a confirmar al modelar.
- **Tris**: tope de triángulos (sección 3.1 de la guía).
- **Prioridad**: **P1** = reemplaza algo que ya está en el juego · **P2** = hace falta para su etapa ·
  **P3** = suma variedad, se puede dejar para después.
- **Estado**: Pendiente → En progreso → En revisión → Hecho.
- ⚠ = objeto que **no** está en ninguna spec todavía; es una propuesta y se confirma al escribir la spec de su etapa.

Resumen: **119 modelos** (más los tamaños de techos y toldos). La etapa 1 tiene 29, y 23 de ellos (P1) reemplazan las piezas simples que el juego usa hoy.

---

## Etapa 1 · Prototipo (ya en el juego, hoy con piezas simples)

### Comida (`comida/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `pan_pancho` | Pan de pancho | 0,17 × 0,045 × 0,055 | 300 | PanCorteza, PanMiga | Pan abierto, como de panadería: cortado a lo largo casi hasta la base, con las mitades separadas y el fondo del corte en U para la salchicha. Origen al centro. Hecho por código: `tools/blender/modelos/pan_pancho.py` (280 tris). [Hoja de revisión](revisiones/pan_pancho.jpg). | P1 | Hecho |
| `salchicha` | Salchicha | Ø 0,022 × 0,15 | 200 | SalchichaCruda | Tipo viena: 8 lados, puntas redondeadas con un nudito, apenas curvada. Objeto `pieza_salchicha` (el color lo cambia la cocción). Hecho por código: `tools/blender/modelos/salchicha.py` (176 tris). [Hoja de revisión](revisiones/salchicha.jpg). | P1 | Hecho |
| `pancho` | Pancho armado | 0,17 × 0,045 × 0,055 | 600 | PanCorteza, PanMiga, SalchichaCruda | `pan_pancho` + `pieza_salchicha` bajo un objeto `pancho` (no es un modelo nuevo). La salchicha va **hundida** entre las dos mitades: centro a 0,004 m del centro del pan, así que el pancho mide lo mismo que el pan. Cuando el juego cargue los `.glb`, en `productos.ron` hay que pasar la salchicha de 0,024 a 0,004 y la colisión de 0,06 a 0,045 de alto. Hecho por código: `tools/blender/modelos/pancho.py` (456 tris). [Hoja de revisión](revisiones/pancho.jpg). | P1 | Hecho |
| `pan_pancho_cerrado` | Pan de pancho cerrado (entero, sin cortar) | 0,17 × 0,045 × 0,055 | 300 | PanCorteza | Mismo pan que `pan_pancho` (mismo largo y puntas) pero entero. ⚠ Uso a definir: por ejemplo, los panes dentro de la bolsa del depósito, que se abren al sacarlos. Hecho por código: `tools/blender/modelos/pan_pancho_cerrado.py` (196 tris). [Hoja de revisión](revisiones/pan_pancho_cerrado.jpg). | P2 | Hecho |

### Bloques de stock (`stock/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `bolsa_panes_12` | Bolsa de 12 panes | 0,19 × 0,108 × 0,429 (con nudo) | 400 | BolsaPlastica, BlancoCrema | Bolsa blanda transparente de sección rectangular redondeada, con la punta de adelante cerrada. Del lado del vendedor (−Z) se junta en un cuello con precinto de papel, nudo y copete, como hoy en el juego. Etiqueta chica de papel arriba. Los 12 panes los pone el código. Origen en el centro de la base del cuerpo (0,19 × 0,105 × 0,366); el nudo sobresale 6 cm hacia atrás. Sin colisión en el modelo: la arma el código con el tamaño de la grilla. Hecho por código: `tools/blender/modelos/bolsa_panes_12.py` (346 tris). [Hoja de revisión](revisiones/bolsa_panes_12.jpg). | P1 | Hecho |
| `caja_salchichas_12` | Bandeja de 12 salchichas | 0,172 × 0,051 × 0,168 | 300 | Carton, BolsaPlastica | Bandeja de cartón baja con esquinas redondeadas, paredes un poco abiertas y pestaña alrededor. El film transparente va pegado a la pestaña y estirado sobre las dos capas de salchichas. Las 12 salchichas las pone el código (las de abajo quedan 2 mm metidas en el fondo: si se quiere exacto, sumar 0,003 en Y para el empaque Bandeja). Sin colisión en el modelo, como la bolsa. Hecho por código: `tools/blender/modelos/caja_salchichas_12.py` (246 tris). [Hoja de revisión](revisiones/caja_salchichas_12.jpg). | P1 | Hecho |

### Bases de carrito (`carritos/`)

Cada base: cuerpo pintado (`pieza_pintura`, color elegido por el jugador), mesada de acero que
sobresale 2 cm, zócalo, 4 ruedas, manija para empujar. Las posiciones de los anclajes de cada
`.ron` se marcan con *Empties* `punto_<anclaje>`.

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `barra_chica` | Barra chica | 1,6 × 0,95 × 0,7 | 3.000 | PinturaCarrito, Acero, Goma, PlasticoNegro, MetalOscuro | El carrito actual del jugador. Cuerpo pintado `pieza_pintura` (el juego lo tiñe), zócalo y cantoneras de acero, mesada de acero con esquinas redondeadas que sobresale 2 cm a los costados (5 cm hacia el cliente, como hoy en `carrito.rs`), 4 ruedas de goma con taza de acero y manija con puño negro del lado −X. 2 puertitas con tirador del lado del vendedor. *Empties* `punto_<anclaje>` en cada anclaje del `.ron`, más `punto_entrega` y `punto_fila`. Colisión `barra_chica-colonly` + `barra_chica_manija-colonly`. Origen en el centro del cuerpo, a nivel del piso. Hecho por código: `tools/blender/modelos/barra_chica.py` (1824 tris). [Hoja de revisión](revisiones/barra_chica.jpg). | P1 | Hecho |
| `barra_mediana` | Barra mediana | 2,4 × 0,95 × 0,8 | 3.000 | PinturaCarrito, Acero, Goma, PlasticoNegro, MetalOscuro | Mismo diseño que la chica (módulo `_base_carrito.py`), más larga: 3 puestos de mostrador y 3 puertitas del lado del vendedor. `pieza_pintura`, *Empties* `punto_<anclaje>` + `punto_entrega` y `punto_fila`, colisión `-colonly`. Hecho por código: `tools/blender/modelos/barra_mediana.py` (1912 tris). [Hoja de revisión](revisiones/barra_mediana.jpg). | P1 | Hecho |
| `carro_grande` | Carro grande | 3,4 × 1,0 × 1,2 | 3.000 | PinturaCarrito, Acero, Goma, PlasticoNegro, MetalOscuro | Más robusto que las barras: zócalo más alto, ruedas más anchas, manija más gruesa, 4 patas niveladoras y parantes de acero. Del lado del vendedor queda abierto bajo la mesada, con estante bajo, estante intermedio y, en la punta +X, el lugar para la garrafa (cincha y rejilla de ventilación). La garrafa no está: sería un modelo aparte. `pieza_pintura`, *Empties* `punto_<anclaje>` + `punto_entrega` y `punto_fila`, colisión `-colonly`. Hecho por código: `tools/blender/modelos/carro_grande.py` (2620 tris). [Hoja de revisión](revisiones/carro_grande.jpg). | P1 | Hecho |

### Accesorios (`accesorios/`, `cocina/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `hervidor_chico` | Hervidor baño maría | ≈ 0,40 × 0,20 × 0,30 (interior 0,36 × 0,18 × 0,26) | 1.500 | Acero, PlasticoNegro, PilotoApagado, Agua | Batea abierta de acero con esquinas redondeadas, reborde de 1 cm y manijas negras a los costados. Del lado del vendedor, frente de controles con la perilla negra (−X) y `pieza_piloto` (+X), a la altura de `hervidor.rs`. Interior exacto 0,36 × 0,18 × 0,26 con paredes de 0,012 (coinciden con la colisión del código). `pieza_agua` separada al 70 %, con el origen en el piso de la batea (el código puede cambiar el nivel escalando en Y). `punto_interior` en el centro del piso. Sin colisión propia: la arma el código con 5 cajas (una caja simple llenaría la batea). Medida total 0,452 × 0,192 × 0,344 con manijas y perilla. Hecho por código: `tools/blender/modelos/hervidor_chico.py` (928 tris). [Hoja de revisión](revisiones/hervidor_chico.jpg). | P1 | Hecho |
| `estante_deposito` | Estante de depósito | 0,53 × 1,01 × 0,41 | 1.000 | MetalOscuro, MaderaClara, Goma | Estante de ángulo ranurado: 4 parantes en L con regatones de goma, 3 tablas de madera (centradas a 0,35, 0,75 y 1,0 m) con un ángulo de apoyo adelante y atrás, y un travesaño abajo. Las tablas miden 0,51 × 0,39 para quedar adentro de los ángulos. *Empties* `punto_lugar_1..4` en los `lugares` de `accesorios.ron`. Colisión `-colonly`: las 7 cajas del dato. Hecho por código: `tools/blender/modelos/estante_deposito.py` (972 tris). [Hoja de revisión](revisiones/estante_deposito.jpg). | P1 | Hecho |
| `sombrilla` | Sombrilla de carrito | Ø 2,7 × 2,72 | 2.000 | Hierro, Acero, RojoAcento / BlancoCrema / AzulAcento | Base de hierro de 16 lados, caño de acero inclinado 15° y articulación arriba. Paño de 8 gajos con panza leve, faldón festoneado, varillas y tensores por debajo, centrado en x = 0,62 como el dato. **Un solo modelo:** `pieza_pano` tiene dos superficies (0 = gajos pares, 1 = impares); el `.glb` trae la roja (las dos en RojoAcento) y para la rayada el juego pone BlancoCrema en la 0 y AzulAcento en la 1. Origen en el centro de la base (anclaje `sombra`). Colisión `-colonly`: base y caño. Hecho por código: `tools/blender/modelos/sombrilla.py` (1460 tris). [Hoja de revisión](revisiones/sombrilla.jpg). | P1 | Hecho |
| `carpa_2x2` | Carpa 2 × 2 | 2,3 × 2,6 × 1,9 | 2.000 | Acero, PlasticoNegro, Lona | Carpa plegable: 4 patas telescópicas de acero con traba y pie negros, tijeras en X debajo del techo y escuadras en las esquinas. Techo de lona a dos aguas (cumbrera a lo largo de X) con el alero a 2,30 como el dato y faldón festoneado; la cumbrera llega a 2,60 (a dos aguas no entra en 2,36). Colisión `-colonly`: solo las patas. Hecho por código: `tools/blender/modelos/carpa_2x2.py` (1816 tris). [Hoja de revisión](revisiones/carpa_2x2.jpg). | P1 | Hecho |
| `telon_panchos` | Telón "Panchos" | 1,3 × 0,42 × 0,01 | 200 | Amarillo + cartel `T_telon_panchos` | Lona tensada de 1 cm, sin bisel. Las franjas rojas, "PANCHOS" con sombra crema entre dos guardas de filete simplificado y los ojales van en una imagen (solo colores de la paleta). Origen en el anclaje `frente`, como hoy (la lona va de 0,31 a 0,73 m). Sin colisión. Hecho por código: `tools/blender/modelos/telon_panchos.py` (12 tris). [Hoja de revisión](revisiones/telon_panchos.jpg). | P1 | Hecho |
| `cerco_bajo` | Cerco bajo de madera | 2,46 × 0,6 × 0,06 | 600 | Madera | 2 postes de 0,06 con punta en bisel y 2 travesaños de 0,06 × 0,04 a 0,25 y 0,5 m, encastrados entre los postes (en el dato los atraviesan y parpadearían). Colisión `-colonly`: una caja del tamaño total. ⚠ En el anclaje `frente` de las barras, el travesaño de abajo cruza las ruedas de adelante (pasa igual con las piezas simples de hoy): revisar el dato. Hecho por código: `tools/blender/modelos/cerco_bajo.py` (160 tris). [Hoja de revisión](revisiones/cerco_bajo.jpg). | P1 | Hecho |
| `foco_calido` | Foco colgante | Ø 0,07 × 0,38 | 300 | PlasticoNegro, LuzCalida | Lamparita colgando de su cable: florón arriba, cable negro de 6 lados, portalámparas y lamparita de pera como `pieza_lampara` (se prende y apaga). Origen arriba, en el punto de donde cuelga; `punto_luz` en el centro de la lamparita (0, −0,345, 0). Sin colisión. Cuando el juego lo cargue: subir el anclaje `luz_1` 0,345 m y poner la luz en `punto_luz`. Hecho por código: `tools/blender/modelos/foco_calido.py` (282 tris). [Hoja de revisión](revisiones/foco_calido.jpg). | P1 | Hecho |
| `pizarra_precios` | Pizarra de precios | 0,36 × 0,434 × 0,234 (con la pata) | 400 | Pizarra, Madera + cartel `T_pizarra_precios` | Pizarrita tipo atril: marco de madera inclinado 12°, pata trasera y repisita para la tiza. Lo escrito es una imagen (guía 4.5, solo colores de la paleta): "PANCHOS", un dibujito de pancho, "PANCHO $ 2500" y "CALENTITOS". El precio se lee de `productos.ron` al correr el script (si cambia, hay que volver a correrlo). Colisión `-colonly` inclinada como el marco. Hecho por código: `tools/blender/modelos/pizarra_precios.py` (194 tris). [Hoja de revisión](revisiones/pizarra_precios.jpg). | P1 | Hecho |
| `servilletero` | Servilletero | 0,12 × 0,11 × 0,08 | 300 | Acero, BlancoCrema | Servilletero de chapa de bar: base de acero y dos chapas paradas con esquinas redondeadas y una muesca en U. Entre las chapas, las servilletas paradas asomando 2 cm con tres dobleces. Colisión `servilletero-colonly` (una caja). Hecho por código: `tools/blender/modelos/servilletero.py` (270 tris). [Hoja de revisión](revisiones/servilletero.jpg). | P1 | Hecho |

### Plaza (`plaza/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `banco` | Banco de plaza | 1,6 × 0,8 × 0,6 | 800 | Madera, Hierro | Tablas de madera (4 en el asiento, 3 en el respaldo inclinado 15°) sobre dos patas laterales de hierro con apoyabrazos. Asiento a 0,45 m (arriba de la tabla), frente hacia +Z como pide `plaza.rs`. Colisión `banco-colonly` (asiento) + `banco_respaldo-colonly`. Hecho por código: `tools/blender/modelos/banco.py` (748 tris). [Hoja de revisión](revisiones/banco.jpg). | P1 | Hecho |
| `farol` | Farol de plaza | 0,5 × 3,9 × 0,5 | 800 | Hierro, LuzFarol | Farola porteña de hierro: base torneada, columna apenas cónica con collar y farol de 4 caras con parantes, techo en pirámide con alero y remate. Vidrio = `pieza_lampara` (emisión), `punto_luz` a 3,62 m. Colisión de columna y base. Hecho por código: `tools/blender/modelos/farol.py` (576 tris). [Hoja de revisión](revisiones/farol.jpg). | P1 | Hecho |
| `fuente` | Fuente central | Ø 6,0 × 1,6 | 2.500 | Piedra, Agua | Pileta de piedra de Ø 6 m con borde con alero (0,51 m), pedestal, columna con capitel, plato de Ø 1,8 a 1,47 m y remate. Agua aparte en `pieza_agua` (pileta y plato). Sin cortina de agua cayendo: con transparencia parecía un tambor; si se quiere, va con partículas en Godot. Colisión de pileta y columna. Hecho por código: `tools/blender/modelos/fuente.py` (1516 tris). [Hoja de revisión](revisiones/fuente.jpg). | P1 | Hecho |
| `arbol_platano_a` | Árbol (plátano) A | 5 × 7 | 1.200 | Tronco, Hojas1/2/3 | Tronco de 6 caras, ramas que se ven entre los bollos y copa de 4 bollos facetados mezclando Hojas1/2/3, desde 2,85 m o más (se pasa caminando por abajo). Origen en la base del tronco. Colisión `-colonly` solo del tronco. Módulo común `_arbol.py`. Hecho por código: `tools/blender/modelos/arbol_platano_a.py` (396 tris). [Hoja de revisión](revisiones/arbol_platano_a.jpg). | P1 | Hecho |
| `arbol_platano_b` | Árbol (plátano) B | 4 × 6 | 1.200 | ídem | Variante más chica, inclinada 9° hacia +X, copa de 3 bollos. Origen en la base del tronco. Colisión del tronco inclinado. Hecho por código: `tools/blender/modelos/arbol_platano_b.py` (292 tris). [Hoja de revisión](revisiones/arbol_platano_b.jpg). | P1 | Hecho |
| `arbol_platano_c` | Árbol (plátano) C | 6 × 8 | 1.200 | ídem | Variante más grande, tronco más grueso, copa de 4 bollos más baja y extendida. La hoja muestra las tres variantes juntas. Hecho por código: `tools/blender/modelos/arbol_platano_c.py` (402 tris). [Hoja de revisión](revisiones/arbol_platano_c.jpg). | P1 | Hecho |
| `cordon_vereda` | Cordón de vereda (tramo) | 2,0 × 0,12 × 0,20 | 50 | Vereda | Tramo de 2 m con chaflán de 3 cm del lado de la calle (−Z) y 2 cm del lado de la vereda, sin cara de abajo. Medidas del juego actual (`plaza.rs`). Sin colisión, como hoy. Hecho por código: `tools/blender/modelos/cordon_vereda.py` (18 tris). [Hoja de revisión](revisiones/cordon_vereda.jpg). | P2 | Hecho |
| `cantero` | Borde de cantero (tramo) | 2,0 × 0,1 × 0,1 | 50 | Piedra | Tramo de 2 m de borde de piedra con chaflanes de 2 cm arriba, simétrico. Sin colisión. Hecho por código: `tools/blender/modelos/cantero.py` (18 tris). [Hoja de revisión](revisiones/cantero.jpg). | P3 | Hecho |
| `arbol_jacaranda_a` | Árbol (jacarandá) A | ≈ 5 × 6 | 1.200 | Tronco, color lila *(agregar a la paleta)* | Toque de color en la plaza. | P3 | Pendiente |
| `arbol_jacaranda_b` | Árbol (jacarandá) B | ≈ 4 × 5 | 1.200 | ídem | Variante. | P3 | Pendiente |
| `arbusto` | Arbusto | 1,0 × 0,8 × 0,64 | 300 | Hojas1/2/3 | 3 bollos facetados apoyados en el piso (sin cara de abajo), con los tres verdes mezclados. Sin colisión. Hecho por código: `tools/blender/modelos/arbusto.py` (134 tris). [Hoja de revisión](revisiones/arbusto.jpg). | P3 | Hecho |

Piso, pasto, caminos, vereda y calle **no se modelan**: son superficies planas con color que arma el código.

---

## Etapa 2 · Rutina de venta

La etapa 2 ya está programada (SPEC-009 a SPEC-013). Esta tabla se rehízo mirando lo que el juego
dibuja de verdad con piezas simples. Cambios respecto de la versión anterior: los tres pomos son
**un solo modelo** (`pomo_aderezo`, el juego le pone el color); la `caja_reparto` no va (el pedido
llega como el bloque de stock mismo, `paquete.rs`); `cliente_base` pasa a la etapa 3 (los clientes
son los peatones); la plata, la servilleta, el papel y la camioneta no están en el juego y bajan a P3.

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `pomo_aderezo` | Pomo de aderezo (mostaza, ketchup, mayonesa) | Ø 0,056 × 0,235 | 500 | PlasticoClaro, Amarillo | Pomo de plástico translúcido con tapa a rosca y pico. Un solo modelo para los tres aderezos: el juego pinta `pieza_tapa` y `pieza_relleno` con el color de `aderezos.ron` y achica el relleno (origen en su base, se escala en Y) a medida que se usa. Colisión `-colonly`. Hecho por código: `tools/blender/modelos/pomo_aderezo.py` (436 tris). [Hoja de revisión](revisiones/pomo_aderezo.jpg). | P2 | En progreso |
| `aderecera_tres` | Aderecera de tres pomos | 0,30 × 0,085 × 0,10 | 1.000 | Acero | Soporte de acero en U con bandeja de tres agujeros, abierto adelante y atrás para ver el nivel. Origen en el anclaje; base en z = −0,22 como el dato. *Empties* `punto_pomo_1..3`. Colisión `-colonly` solo de la base (la bandeja de arriba no tapa la mira a los pomos). Los pomos los pone el código. Hecho por código: `tools/blender/modelos/aderecera_tres.py` (426 tris). [Hoja de revisión](revisiones/aderecera_tres.jpg). | P2 | Hecho |
| `repuesto_aderezo` | Repuesto de aderezo | Ø 0,078 × 0,19 | 400 | Amarillo, BlancoCrema, PlasticoNegro | Botella petisa de medio kilo con etiqueta lisa (texto pendiente, nombre inventado) y tapa negra. Un modelo para los tres repuestos: el juego pinta `pieza_cuerpo`. Hecho por código: `tools/blender/modelos/repuesto_aderezo.py` (324 tris). [Hoja de revisión](revisiones/repuesto_aderezo.jpg). | P2 | Hecho |
| `pack_repuestos` | Pack de 2 repuestos | 0,188 × 0,194 × 0,098 | 400 | Carton, PlasticoClaro | Bandeja de cartón con film termocontraíble: el empaque de los tres `pack_*` (las botellas las pone el código). Pared de 0,05 (no 0,45 × alto, para no tapar la etiqueta). Sin colisión en el modelo, como los otros bloques. Hecho por código: `tools/blender/modelos/pack_repuestos.py` (364 tris). [Hoja de revisión](revisiones/pack_repuestos.jpg). | P3 | En progreso |
| `bandeja_entrega` | Bandeja de entrega del carrito | 0,30 × 0,02 × 0,228 | 400 | RojoAcento | Bandeja roja de plástico con borde en los cuatro lados, en el punto `entrega` de cada base. Colisión `-colonly` del piso (hoy la comida se hunde 8 mm). Hecho por código: `tools/blender/modelos/bandeja_entrega.py` (238 tris). [Hoja de revisión](revisiones/bandeja_entrega.jpg). | P2 | Hecho |
| `pallet` | Pallet del proveedor | 0,80 × 0,12 × 0,60 | 800 | MaderaClara, Madera | Pallet de tacos (3 tablas abajo, 9 tacos, 5 tablas arriba) donde el proveedor deja los paquetes. Colisión `-colonly`: una caja. Hecho por código: `tools/blender/modelos/pallet.py` (706 tris). [Hoja de revisión](revisiones/pallet.jpg). | P3 | Hecho |
| `chorrito_aderezo` | Chorrito de aderezo | 0,152 × 0,006 × 0,021 | 300 | color del aderezo (en el archivo, Amarillo) | Hilo ondulado que se apoya sobre la salchicha (`pieza_chorrito`, el juego le pone el color). En el `pancho` modelado va a y = 0,0152, +0,003 por cada aderezo extra (hoy el código lo pone a 0,037). 6 lados (excepción de cables). Hecho por código: `tools/blender/modelos/chorrito_aderezo.py` (216 tris). [Hoja de revisión](revisiones/chorrito_aderezo.jpg). | P2 | Hecho |
| `caja_dinero` | Caja de dinero | ≈ 0,30 × 0,10 × 0,25 | 500 | MetalOscuro, Acero | No está en el juego (la plata es solo el número del HUD). Caja metálica con tapa (`pieza_tapa`). | P3 | Pendiente |
| `billete` | Billete | 0,15 × 0,002 × 0,065 | 20 | color por valor *(agregar a la paleta)* | No está en el juego. Un modelo, distinto material por valor. Diseño inventado. | P3 | Pendiente |
| `moneda` | Moneda | Ø 0,024 × 0,003 | 40 | Acero | No está en el juego. 12 lados. | P3 | Pendiente |
| `servilleta` | Servilleta | 0,15 × 0,003 × 0,15 | 20 | BlancoCrema | No está en el juego (SPEC-009 entrega en la bandeja). | P3 | Pendiente |
| `papel_envoltorio` | Papel para envolver | ≈ 0,20 × 0,005 × 0,20 | 50 | BlancoCrema | ⚠ No está en el juego. | P3 | Pendiente |
| `camioneta_proveedor` | Camioneta del proveedor | ≈ 1,9 × 2,0 × 4,8 | 3.000 | colores de la paleta | ⚠ Hoy el proveedor no se ve: el pedido aparece en el pallet. | P3 | Pendiente |

---

## Etapa 3 · Plaza viva (NPCs)

### Personajes (`personajes/`)

Todos comparten esqueleto humanoide y animaciones (guía 5.5). La variedad sale de combinar
cuerpo + cabeza + pelo + ropa + accesorio, y de cambiar colores.

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `cliente_base` | Cliente (cuerpo base) | ≈ 0,5 × 1,75 × 0,3 | 3.000 | ropa *(agregar a la paleta)* | Los clientes son los peatones (`peaton.rs`): es el mismo personaje base que los NPC (pasó de la etapa 2). | P2 | Pendiente |
| `persona_adulto_a` | Adulto, contextura A | alto ≈ 1,75 | 3.000 | piel, ropa | Cuerpo base con ropa por partes (remera, pantalón, zapatillas). | P2 | Pendiente |
| `persona_adulto_b` | Adulto, contextura B | alto ≈ 1,65 | 3.000 | ídem | Otra contextura y altura. | P2 | Pendiente |
| `persona_mayor` | Persona mayor | alto ≈ 1,65 | 3.000 | ídem | Postura un poco encorvada. | P2 | Pendiente |
| `persona_chico` | Chico / chica | alto ≈ 1,20 | 2.500 | ídem | Para la agenda "jugar". | P2 | Pendiente |
| `pelos_set` | Set de peinados | — | 300 c/u | colores de pelo | 6 a 8 peinados intercambiables. | P2 | Pendiente |
| `accesorios_persona` | Gorra, mochila, bolso, anteojos | — | 300 c/u | paleta | Para variar NPCs. | P3 | Pendiente |
| `vendedor` | Personaje del jugador (brazos) | — | 1.500 | piel, ropa | ⚠ Solo si se decide mostrar las manos en primera persona. | P3 | Pendiente |
| `perro` | Perro de plaza | ≈ 0,3 × 0,5 × 0,8 | 1.500 | Tronco, BlancoCrema | ⚠ Toque de vida en la plaza. | P3 | Pendiente |
| `paloma` | Paloma | ≈ 0,1 × 0,15 × 0,25 | 300 | grises | ⚠ Bandada que se acerca a las migas. | P3 | Pendiente |

### Plaza (`plaza/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `tacho_basura` | Tacho de basura | Ø 0,45 × 0,9 | 500 | Hierro, MetalOscuro | Típico de plaza, sobre poste. | P2 | Pendiente |
| `hamaca` | Hamacas | ≈ 3,0 × 2,4 × 1,5 | 1.500 | Hierro, Madera, RojoAcento | Para la actividad "jugar". | P2 | Pendiente |
| `tobogan` | Tobogán | ≈ 0,8 × 2,0 × 3,5 | 1.500 | Hierro, AzulAcento, Amarillo | Ídem. | P2 | Pendiente |
| `subibaja` | Subibaja | ≈ 0,4 × 0,8 × 3,0 | 600 | Hierro, Amarillo | Ídem. | P3 | Pendiente |
| `mesa_ajedrez` | Mesa de ajedrez con bancos | ≈ 1,6 × 0,75 × 1,6 | 1.200 | Piedra | Para la actividad "charlar / jugar". | P3 | Pendiente |
| `bebedero` | Bebedero | ≈ 0,4 × 1,0 × 0,4 | 400 | Piedra, Acero | ⚠ | P3 | Pendiente |
| `pelota` | Pelota de fútbol | Ø 0,22 | 300 | BlancoCrema, PlasticoNegro | Con física. | P3 | Pendiente |
| `bicicleta` | Bicicleta | ≈ 0,6 × 1,0 × 1,7 | 1.500 | Hierro, colores | ⚠ Estacionada o en uso. | P3 | Pendiente |
| `cartel_plaza` | Cartel con el nombre de la plaza | ≈ 1,2 × 2,0 × 0,1 | 300 | Hierro, BlancoCrema | Nombre inventado. | P3 | Pendiente |

---

## Etapa 4 · Los tres productos

### Comida (`comida/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `medallon` | Medallón de hamburguesa | Ø 0,11 × 0,012 | 200 | CarneCruda *(agregar)* | `pieza_carne`: el color lo cambia la cocción. Bordes irregulares. | P2 | Pendiente |
| `pan_hamburguesa_abajo` | Pan de hamburguesa (base) | Ø 0,11 × 0,03 | 200 | PanCorteza, PanMiga | | P2 | Pendiente |
| `pan_hamburguesa_arriba` | Pan de hamburguesa (tapa) | Ø 0,11 × 0,045 | 250 | PanCorteza, PanMiga | Domo con semillas pintadas (color, no geometría). | P2 | Pendiente |
| `feta_queso` | Feta de queso | 0,09 × 0,003 × 0,09 | 40 | Amarillo | Esquinas caídas al derretirse (dos versiones o deformación). | P3 | Pendiente |
| `hoja_lechuga` | Hoja de lechuga | ≈ 0,10 × 0,01 × 0,10 | 100 | verde claro *(agregar)* | ⚠ Si hay ingredientes extra. | P3 | Pendiente |
| `rodaja_tomate` | Rodaja de tomate | Ø 0,07 × 0,008 | 80 | rojo tomate *(agregar)* | ⚠ Ídem. | P3 | Pendiente |
| `hamburguesa` | Hamburguesa armada | Ø 0,11 × 0,09 | 600 | — | Combinación de las piezas (no es modelo nuevo). | P2 | Pendiente |
| `chorizo` | Chorizo | Ø 0,03 × 0,14 | 250 | CarneCruda | Con atado en las puntas. Abierto en mariposa: segunda versión. | P2 | Pendiente |
| `pan_frances` | Pan francés | 0,16 × 0,06 × 0,08 | 300 | PanCorteza, PanMiga | Con cortes diagonales arriba. Para el choripán. | P2 | Pendiente |
| `choripan` | Choripán armado | 0,16 × 0,07 × 0,08 | 600 | — | Combinación de piezas. | P2 | Pendiente |
| `chimichurri` | Frasco de chimichurri | Ø 0,08 × 0,12 | 400 | vidrio, verde *(agregar)* | ⚠ Aderezo típico del choripán. | P3 | Pendiente |

### Equipos (`cocina/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `plancha` | Plancha a gas | ≈ 0,60 × 0,25 × 0,45 | 1.500 | Acero, MetalOscuro, PlasticoNegro, PilotoApagado | Superficie plana con canaleta para grasa, perillas al frente del vendedor. | P2 | Pendiente |
| `parrilla_carbon` | Parrilla con carbón | ≈ 0,70 × 0,35 × 0,45 | 1.500 | MetalOscuro, Hierro | Batea para carbón y parrilla de varillas (16–20 varillas). | P2 | Pendiente |
| `carbon_brasa` | Brasas de carbón (montón) | ≈ 0,5 × 0,08 × 0,35 | 500 | negro / brasa *(agregar emisión)* | `pieza_brasa` con emisión que cambia según el fuego. | P2 | Pendiente |
| `tostador` | Tostador de pan | ≈ 0,40 × 0,20 × 0,30 | 1.000 | Acero, PlasticoNegro | Para "pan tostado" de la hoja de ruta. | P2 | Pendiente |
| `heladera` | Heladera / conservadora | ≈ 0,60 × 0,85 × 0,55 | 1.000 | BlancoCrema, Acero, PlasticoNegro | Puerta como `pieza_puerta`. Lugares de depósito con `punto_lugar_N`. | P2 | Pendiente |
| `garrafa` | Garrafa de gas | Ø 0,30 × 0,55 | 600 | color garrafa *(agregar)* | Para la plancha. | P2 | Pendiente |
| `espatula` | Espátula | 0,30 × 0,03 × 0,10 | 200 | Acero, PlasticoNegro | Se agarra con la mano. | P2 | Pendiente |
| `pinza` | Pinza de parrilla | 0,30 × 0,03 × 0,05 | 200 | Acero, PlasticoNegro | Ídem. | P2 | Pendiente |
| `tabla_picar` | Tabla de picar | 0,35 × 0,02 × 0,25 | 100 | MaderaClara | | P3 | Pendiente |

### Bloques de stock (`stock/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `caja_medallones_12` | Caja de medallones | ≈ 0,24 × 0,08 × 0,24 | 300 | Carton, BolsaPlastica | Separadores de papel entre capas. | P2 | Pendiente |
| `bolsa_panes_hamburguesa_6` | Bolsa de panes de hamburguesa | ≈ 0,24 × 0,10 × 0,36 | 400 | BolsaPlastica, BlancoCrema | Mismo estilo que la bolsa de panes de pancho. | P2 | Pendiente |
| `bandeja_chorizos_6` | Bandeja de chorizos | ≈ 0,20 × 0,05 × 0,16 | 300 | Carton, BolsaPlastica | Mismo estilo que la de salchichas. | P2 | Pendiente |
| `bolsa_panes_frances_6` | Bolsa de pan francés | ≈ 0,20 × 0,10 × 0,35 | 400 | papel madera *(agregar)* | Bolsa de papel de panadería. | P2 | Pendiente |
| `bolsa_carbon` | Bolsa de carbón | ≈ 0,35 × 0,50 × 0,15 | 300 | papel madera, PlasticoNegro | | P2 | Pendiente |

---

## Etapa 5 · Carritos y mejoras

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `food_truck` | Base con interior caminable | ≈ 2,2 × 2,6 × 4,5 | 5.000 | PinturaCarrito, Acero, Goma, PlasticoNegro | Excede el tope de bases: se pide excepción al hacer la spec. Ventana de atención con toldo. | P2 | Pendiente |
| `trailer` | Base remolque | ≈ 2,0 × 2,3 × 3,0 | 4.000 | ídem | ⚠ Mencionado como "remolque" en SPEC-006 (fuera de alcance). | P3 | Pendiente |
| `cartel_luminoso` | Cartel luminoso | ≈ 0,8 × 0,3 × 0,1 | 400 | MetalOscuro, emisión | Texto en imagen con emisión de noche. | P2 | Pendiente |
| `guirnalda_luces` | Guirnalda de lamparitas | ≈ 2,0 × 0,3 | 600 | PlasticoNegro, LuzCalida | Cable con 8–10 lamparitas. | P2 | Pendiente |
| `banqueta` | Banqueta alta | Ø 0,35 × 0,75 | 400 | Acero, PinturaCarrito | Para que los clientes coman. | P2 | Pendiente |
| `mesa_alta` | Mesa alta redonda | Ø 0,6 × 1,1 | 500 | Acero, MaderaClara | | P3 | Pendiente |
| `maceta` | Maceta con planta | Ø 0,3 × 0,5 | 400 | Carton (terracota) *(agregar)*, Hojas | Decoración. | P3 | Pendiente |
| `telon_hamburguesas` | Telón "Hamburguesas" | 1,3 × 0,42 × 0,01 | 200 | Amarillo, RojoAcento | Mismo modelo que `telon_panchos`, otra imagen. | P3 | Pendiente |
| `telon_choripan` | Telón "Choripán" | 1,3 × 0,42 × 0,01 | 200 | ídem | Ídem. | P3 | Pendiente |
| `pizarra_grande` | Pizarra de menú grande | ≈ 0,6 × 0,9 × 0,05 | 400 | Pizarra, Madera | | P3 | Pendiente |
| `cerco_metal` | Cerco de metal | 2,46 × 0,9 × 0,05 | 600 | Hierro | Variante del cerco. | P3 | Pendiente |
| `heladera_bebidas` | Heladera exhibidora de bebidas | ≈ 0,6 × 1,8 × 0,6 | 1.500 | BlancoCrema, vidrio, emisión | ⚠ Si se agregan bebidas. | P3 | Pendiente |

### Alacenas bajo mesada (`accesorios/`)

⚠ Pedido nuevo: depósitos de metal que se **encastran** debajo de la mesada, del lado del vendedor, y forman parte del carrito (como los muebles bajo mesada de los food trucks). Cada base tiene huecos de medida estándar ("bahías": 2 en la barra chica, 3 en la mediana, 4 en el carro grande) con un *Empty* `punto_bahia_<n>`; lo que hoy tapa el hueco (las puertitas) pasa a ser `pieza_tapa_bahia_<n>`, que el juego esconde cuando hay una alacena. Todas las alacenas miden lo mismo, así entran en cualquier bahía de cualquier carrito. Puertas `pieza_puerta_<n>` y cajones `pieza_cajon_<n>` aparte (se abren), lugares de depósito `punto_lugar_<n>` adentro. **Para que el juego las use hace falta una spec** (anclajes `bahia_<n>` en los `.ron` de carritos, categoría Depósito).

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `alacena_puertas` | Alacena de 2 puertas | ≈ medida de bahía | 1.000 | Acero, PlasticoNegro, MetalOscuro | 2 puertas batientes con tirador y un estante adentro. | P2 | Pendiente |
| `alacena_cajones` | Cajonera de 3 cajones | ídem | 1.000 | ídem | 3 cajones con tirador corrido. | P2 | Pendiente |
| `alacena_abierta` | Alacena abierta | ídem | 1.000 | ídem | Sin puertas, 2 estantes a la vista. | P3 | Pendiente |
| `alacena_mixta` | Alacena puerta + cajones | ídem | 1.000 | ídem | 1 puerta y una columna de 2–3 cajones. | P3 | Pendiente |

### Techos y toldos para los carritos (`accesorios/`)

⚠ Pedido nuevo. Se enganchan en el anclaje `techo` (categoría Carpa, como `carpa_2x2`) o en el `frente` (toldos). Los techos van sobre parantes propios y tienen que cubrir la mesada: como las bases miden distinto, cada techo tiene **tres tamaños** con sufijo `_chico` (barra chica, ≈ 1,7 m de ancho), `_mediano` (barra mediana, ≈ 2,5 m) y `_grande` (carro grande, ≈ 3,5 m); la tabla da el chico. Lona y chapa sin colisión; parantes con `-colonly`. Colores por material (guía 4.2, regla 5): el paño o la chapa como `pieza_` con superficies para las rayas, como `pieza_pano` de la sombrilla. **Para que el juego los use hace falta una spec** (tamaños por base y la categoría Toldo, si se separa de Carpa).

**A futuro, tamaño dinámico:** más adelante el juego podría estirar techos y toldos a cualquier ancho. Para no tener que rehacerlos, se arman desde ya con un script **parametrizado por ancho** (los tres tamaños salen del mismo código) y, dentro del `.glb`, separados en **punta izquierda + tramo del medio + punta derecha** (`pieza_punta_izq`, `pieza_tramo`, `pieza_punta_der`), con el tramo del medio hecho de forma que se pueda estirar o repetir a lo largo de X sin deformar las rayas ni los festones (las rayas van a lo largo de Z, o el tramo mide un múltiplo del ancho de una raya).

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `techo_plano` | Techo plano de chapa sobre 4 caños | ≈ 1,7 × 2,3 × 1,0 | 1.500 | MetalOscuro, Acero, PinturaCarrito | Chapa plana con borde pintado y un faldón al frente (como el carrito de la foto de referencia). 4 caños de acero desde el piso o desde la mesada. Tubo de luz debajo (`punto_luz`). Tres tamaños. | P2 | Pendiente |
| `techo_dos_aguas` | Techo de chapa a dos aguas | ≈ 1,8 × 2,5 × 1,1 | 1.500 | MetalOscuro, Acero, PinturaCarrito | Chapa a dos aguas con alero, estilo puesto de feria. Tres tamaños. | P3 | Pendiente |
| `techo_curvo` | Techo curvo de chapa | ≈ 1,8 × 2,4 × 1,1 | 1.500 | MetalOscuro, Acero, PinturaCarrito | Chapa curva en arco, estilo food truck clásico. Tres tamaños. | P3 | Pendiente |
| `toldo_rayado` | Toldo rebatible | ≈ 1,6 × 0,4 × 0,8 | 800 | Acero, RojoAcento, BlancoCrema | Lona rayada sobre brazos articulados, inclinada hacia el cliente. Tres tamaños. | P2 | Pendiente |
| `toldo_enrollable` | Toldo enrollable con faldón | ≈ 1,6 × 0,5 × 1,0 | 800 | Acero, PlasticoNegro, RojoAcento / BlancoCrema / AzulAcento | Caja de enrollado pegada al techo o a los parantes, lona desplegada con faldón festoneado y manivela. Tres tamaños. | P2 | Pendiente |
| `toldo_frente` | Toldito fijo de frente | ≈ 1,6 × 0,3 × 0,4 | 400 | Acero, RojoAcento / BlancoCrema | Alerito corto sobre el mostrador, del lado del cliente, sin parantes (va en el anclaje `frente` o colgado de la mesada). Tres tamaños. | P3 | Pendiente |
| `marquesina` | Techo con cartel al frente | ≈ 1,7 × 2,4 × 1,0 | 1.500 | MetalOscuro, Acero, Amarillo, LuzCalida | Techo plano con un cartel frontal grande (texto en imagen, guía 4.5) y lamparitas de emisión. Tres tamaños. | P3 | Pendiente |

---

## Etapa 6 · Pulido (ciudad alrededor)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `fachada_casa_a` | Fachada de casa chorizo | ≈ 9 × 6 × 1 | 2.000 | colores de fachada *(agregar)* | Edificios bajos de barrio frente a la plaza. | P2 | Pendiente |
| `fachada_casa_b` | Fachada con negocio en planta baja | ≈ 9 × 7 × 1 | 2.000 | ídem | Kiosco / almacén con cortina metálica. | P2 | Pendiente |
| `fachada_edificio` | Edificio de departamentos | ≈ 9 × 18 × 1 | 2.000 | ídem | Balcones simples. | P3 | Pendiente |
| `auto_a` | Auto (sedán) | ≈ 1,8 × 1,45 × 4,5 | 2.500 | colores de autos *(agregar)* | Diseño genérico, sin marca. | P3 | Pendiente |
| `auto_b` | Auto (chico) | ≈ 1,7 × 1,5 × 3,8 | 2.500 | ídem | | P3 | Pendiente |
| `colectivo` | Colectivo | ≈ 2,5 × 3,0 × 12 | 3.000 | ídem | ⚠ Pasa por la calle. | P3 | Pendiente |
| `semaforo` | Semáforo | ≈ 0,4 × 3,5 × 0,4 | 500 | Hierro, emisión | | P3 | Pendiente |
| `parada_colectivo` | Parada de colectivo | ≈ 2,5 × 2,5 × 1,2 | 800 | Hierro, vidrio | | P3 | Pendiente |
| `charco` | Charco | ≈ 1,0 × 0,005 × 0,7 | 30 | Agua | Para el clima con lluvia. | P3 | Pendiente |
| `paraguas` | Paraguas (NPC) | Ø 1,0 × 0,9 | 400 | colores | Para NPCs cuando llueve. | P3 | Pendiente |

---

## Orden sugerido para empezar

1. ✔ **Biblioteca** (`materiales.blend`, `referencias.blend`) — sin esto no hay coherencia.
2. ✔ **Comida de la etapa 1** (`pan_pancho`, `pan_pancho_cerrado`, `salchicha`, `pancho`), hecha: chicos, rápidos y se ven de cerca; definen el "sabor" del estilo.
3. ✔ **`barra_chica` + `hervidor_chico`**: lo que el jugador ve todo el tiempo.
4. ✔ Resto de accesorios de la etapa 1.
5. ✔ Plaza de la etapa 1 (banco, farol, árboles, fuente). Faltan los jacarandás (necesitan un color lila en la paleta).
6. Después, cada etapa a medida que se escriben sus specs.
