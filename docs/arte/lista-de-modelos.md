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

Resumen: **107 modelos**. La etapa 1 tiene 29, y 23 de ellos (P1) reemplazan las piezas simples que el juego usa hoy.

---

## Etapa 1 · Prototipo (ya en el juego, hoy con piezas simples)

### Comida (`comida/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `pan_pancho` | Pan de pancho | 0,17 × 0,045 × 0,055 | 300 | PanCorteza, PanMiga | Pan abierto, como de panadería: cortado a lo largo casi hasta la base, con las mitades separadas y el fondo del corte en U para la salchicha. Origen al centro. Hecho por código: `tools/blender/modelos/pan_pancho.py` (280 tris). [Hoja de revisión](revisiones/pan_pancho.jpg). | P1 | En revisión |
| `salchicha` | Salchicha | Ø 0,022 × 0,15 | 200 | SalchichaCruda | Tipo viena: 8 lados, puntas redondeadas con un nudito, apenas curvada. Objeto `pieza_salchicha` (el color lo cambia la cocción). Hecho por código: `tools/blender/modelos/salchicha.py` (176 tris). [Hoja de revisión](revisiones/salchicha.jpg). | P1 | En revisión |
| `pancho` | Pancho armado | 0,17 × 0,045 × 0,055 | 600 | PanCorteza, PanMiga, SalchichaCruda | `pan_pancho` + `pieza_salchicha` bajo un objeto `pancho` (no es un modelo nuevo). La salchicha va **hundida** entre las dos mitades: centro a 0,004 m del centro del pan, así que el pancho mide lo mismo que el pan. Cuando el juego cargue los `.glb`, en `productos.ron` hay que pasar la salchicha de 0,024 a 0,004 y la colisión de 0,06 a 0,045 de alto. Hecho por código: `tools/blender/modelos/pancho.py` (456 tris). [Hoja de revisión](revisiones/pancho.jpg). | P1 | En revisión |
| `pan_pancho_cerrado` | Pan de pancho cerrado (entero, sin cortar) | 0,17 × 0,045 × 0,055 | 300 | PanCorteza | Mismo pan que `pan_pancho` (mismo largo y puntas) pero entero. ⚠ Uso a definir: por ejemplo, los panes dentro de la bolsa del depósito, que se abren al sacarlos. Hecho por código: `tools/blender/modelos/pan_pancho_cerrado.py` (196 tris). [Hoja de revisión](revisiones/pan_pancho_cerrado.jpg). | P2 | En revisión |

### Bloques de stock (`stock/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `bolsa_panes_12` | Bolsa de 12 panes | ≈ 0,19 × 0,11 × 0,36 | 400 | BolsaPlastica, BlancoCrema | Solo la bolsa transparente con su nudo; los panes de adentro los pone el código (REQ-DEP-03). Etiqueta chica de papel. | P1 | Pendiente |
| `caja_salchichas_12` | Bandeja de 12 salchichas | ≈ 0,17 × 0,06 × 0,16 | 300 | Carton, BolsaPlastica | Bandeja de cartón baja con film transparente encima. Las salchichas las pone el código. | P1 | Pendiente |

### Bases de carrito (`carritos/`)

Cada base: cuerpo pintado (`pieza_pintura`, color elegido por el jugador), mesada de acero que
sobresale 2 cm, zócalo, 4 ruedas, manija para empujar. Las posiciones de los anclajes de cada
`.ron` se marcan con *Empties* `punto_<anclaje>`.

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `barra_chica` | Barra chica | 1,6 × 0,95 × 0,7 | 3.000 | PinturaCarrito, Acero, Goma, PlasticoNegro | El carrito actual del jugador. Puertitas del lado del vendedor (+Y en Blender). | P1 | Pendiente |
| `barra_mediana` | Barra mediana | 2,4 × 0,95 × 0,8 | 3.000 | ídem | Mismo diseño que la chica, más larga: 3 puestos de mostrador. | P1 | Pendiente |
| `carro_grande` | Carro grande | 3,4 × 1,0 × 1,2 | 3.000 | ídem | Más robusto, con estante bajo y lugar para garrafa. | P1 | Pendiente |

### Accesorios (`accesorios/`, `cocina/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `hervidor_chico` | Hervidor baño maría | ≈ 0,40 × 0,20 × 0,30 (interior 0,36 × 0,18 × 0,26) | 1.500 | Acero, PlasticoNegro, PilotoApagado, Agua | Batea abierta. Perilla y `pieza_piloto` del lado del vendedor. `pieza_agua` separada. El interior tiene que medir exacto (física). | P1 | Pendiente |
| `estante_deposito` | Estante de depósito | 0,53 × 1,0 × 0,41 | 1.000 | MetalOscuro, MaderaClara | 4 parantes y 3 tablas (a 0,35, 0,75 y 1,0 m). *Empties* `punto_lugar_1..4` en los lugares de `accesorios.ron`. | P1 | Pendiente |
| `sombrilla` | Sombrilla de carrito | Ø 2,7 × 2,7 | 2.000 | Hierro, Acero, RojoAcento / BlancoCrema / AzulAcento | **Un solo modelo** para la roja y la rayada (cambia el material del paño). Base pesada, caño inclinado 15°, paño de 8 gajos con varillas. | P1 | Pendiente |
| `carpa_2x2` | Carpa 2 × 2 | 2,3 × 2,36 × 1,9 | 2.000 | Acero, Lona | 4 patas plegables, techo a dos aguas bajo con faldón. | P1 | Pendiente |
| `telon_panchos` | Telón "Panchos" | 1,3 × 0,42 × 0,01 | 200 | Amarillo, RojoAcento | Lona tensada con franjas y texto "PANCHOS" (cartel en imagen, guía 4.5). | P1 | Pendiente |
| `cerco_bajo` | Cerco bajo de madera | 2,46 × 0,6 × 0,06 | 600 | Madera | 2 postes y 2 travesaños, con puntas en bisel. | P1 | Pendiente |
| `foco_calido` | Foco colgante | ≈ Ø 0,08 × 0,38 | 300 | PlasticoNegro, LuzCalida | Cable + portalámparas + lamparita (`pieza_lampara`, emisión). Origen arriba. `punto_luz` en la lamparita. | P1 | Pendiente |
| `pizarra_precios` | Pizarra de precios | 0,36 × 0,44 × 0,04 | 400 | Pizarra, Madera | Tipo atril, inclinada 12°. Precios en imagen. | P1 | Pendiente |
| `servilletero` | Servilletero | 0,12 × 0,11 × 0,08 | 300 | Acero, BlancoCrema | Clásico de chapa con servilletas asomando. | P1 | Pendiente |

### Plaza (`plaza/`)

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `banco` | Banco de plaza | 1,6 × 0,8 × 0,6 | 800 | Madera, Hierro | Tablas de madera con respaldo y patas laterales de hierro. Asiento a 0,45 m. | P1 | Pendiente |
| `farol` | Farol de plaza | ≈ 0,5 × 3,9 × 0,5 | 800 | Hierro, LuzFarol | Columna con base decorada simple y farol con `pieza_lampara`. `punto_luz` a 3,62 m. | P1 | Pendiente |
| `fuente` | Fuente central | Ø 6,0 × 1,6 | 2.500 | Piedra, Agua | Pileta redonda, columna central y plato superior. `pieza_agua` separada. | P1 | Pendiente |
| `arbol_platano_a` | Árbol (plátano) A | ≈ 5 × 7 | 1.200 | Tronco, Hojas1/2/3 | Copa de 3–4 bollos facetados. | P1 | Pendiente |
| `arbol_platano_b` | Árbol (plátano) B | ≈ 4 × 6 | 1.200 | ídem | Variante más chica e inclinada. | P1 | Pendiente |
| `arbol_platano_c` | Árbol (plátano) C | ≈ 6 × 8 | 1.200 | ídem | Variante más grande. | P1 | Pendiente |
| `cordon_vereda` | Cordón de vereda (tramo) | 2,0 × 0,15 × 0,15 | 50 | Vereda | Tramo que se repite a lo largo de la calle. | P2 | Pendiente |
| `cantero` | Borde de cantero (tramo) | 2,0 × 0,1 × 0,1 | 50 | Piedra | Tramo para bordear el pasto de la plaza. | P3 | Pendiente |
| `arbol_jacaranda_a` | Árbol (jacarandá) A | ≈ 5 × 6 | 1.200 | Tronco, color lila *(agregar a la paleta)* | Toque de color en la plaza. | P3 | Pendiente |
| `arbol_jacaranda_b` | Árbol (jacarandá) B | ≈ 4 × 5 | 1.200 | ídem | Variante. | P3 | Pendiente |
| `arbusto` | Arbusto | ≈ 1,0 × 0,8 | 300 | Hojas1/2/3 | Para canteros. | P3 | Pendiente |

Piso, pasto, caminos, vereda y calle **no se modelan**: son superficies planas con color que arma el código.

---

## Etapa 2 · Rutina de venta

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
| `caja_dinero` | Caja de dinero | ≈ 0,30 × 0,10 × 0,25 | 500 | MetalOscuro, Acero | Caja metálica con tapa (tapa como `pieza_tapa`, se abre). | P2 | Pendiente |
| `billete` | Billete | 0,15 × 0,002 × 0,065 | 20 | color por valor *(agregar a la paleta)* | Un modelo, distinto material por valor. Diseño inventado. | P2 | Pendiente |
| `moneda` | Moneda | Ø 0,024 × 0,003 | 40 | Acero | 12 lados. | P3 | Pendiente |
| `pomo_mostaza` | Pomo de mostaza | Ø 0,06 × 0,20 | 300 | Amarillo, PlasticoNegro | Pomo apretable con pico. Marca inventada. | P2 | Pendiente |
| `pomo_ketchup` | Pomo de kétchup | Ø 0,06 × 0,20 | 300 | RojoAcento, PlasticoNegro | Mismo modelo que la mostaza, otro material. | P2 | Pendiente |
| `pomo_mayonesa` | Pomo de mayonesa | Ø 0,06 × 0,20 | 300 | BlancoCrema, PlasticoNegro | Ídem. | P2 | Pendiente |
| `chorrito_aderezo` | Chorrito de aderezo | ≈ 0,15 × 0,01 × 0,02 | 100 | color del aderezo | Línea en zigzag que se pone arriba del pancho. | P2 | Pendiente |
| `servilleta` | Servilleta | 0,15 × 0,003 × 0,15 | 20 | BlancoCrema | Para envolver o entregar. | P3 | Pendiente |
| `papel_envoltorio` | Papel para envolver | ≈ 0,20 × 0,005 × 0,20 | 50 | BlancoCrema | ⚠ Si la spec de clientes pide entregar envuelto. | P3 | Pendiente |
| `caja_reparto` | Caja de reparto del proveedor | ≈ 0,50 × 0,35 × 0,40 | 200 | Carton | Caja con la que llegan los bloques (SPEC 011). | P2 | Pendiente |
| `camioneta_proveedor` | Camioneta del proveedor | ≈ 1,9 × 2,0 × 4,8 | 3.000 | colores de la paleta | ⚠ Depende de cómo llegue el proveedor (a pie, en moto, en camioneta). | P3 | Pendiente |
| `cliente_base` | Cliente (cuerpo base) | ≈ 0,5 × 1,75 × 0,3 | 3.000 | ropa *(agregar a la paleta)* | Ver etapa 3: es el mismo personaje base que los NPC. | P2 | Pendiente |

---

## Etapa 3 · Plaza viva (NPCs)

### Personajes (`personajes/`)

Todos comparten esqueleto humanoide y animaciones (guía 5.5). La variedad sale de combinar
cuerpo + cabeza + pelo + ropa + accesorio, y de cambiar colores.

| ID | Objeto | Medidas | Tris | Materiales | Notas | Prio. | Estado |
|---|---|---|---|---|---|---|---|
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
| `toldo_rayado` | Toldo rebatible | ≈ 1,6 × 0,4 × 0,8 | 800 | Acero, RojoAcento, BlancoCrema | Nueva categoría o variante de Carpa. | P2 | Pendiente |
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
2. ✔ **Comida de la etapa 1** (`pan_pancho`, `pan_pancho_cerrado`, `salchicha`, `pancho`), en revisión: chicos, rápidos y se ven de cerca; definen el "sabor" del estilo.
3. **`barra_chica` + `hervidor_chico`**: lo que el jugador ve todo el tiempo.
4. Resto de accesorios de la etapa 1.
5. Plaza de la etapa 1 (banco, farol, árboles, fuente).
6. Después, cada etapa a medida que se escriben sus specs.
