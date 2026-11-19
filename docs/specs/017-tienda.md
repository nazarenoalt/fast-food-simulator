# SPEC-017 · Tienda y modo armado

Estado: **Implementada (etapa 4, primera parte)**

## Objetivo

Armar el carrito desde el juego: comprar accesorios y bases, ponerlos, moverlos, guardarlos,
venderlos y cambiar el color, sin tocar archivos. Usa los anclajes de SPEC-006.

## Requisitos

### Modo armado
- **REQ-TIE-01** Con B se entra y se sale del modo armado. Los anclajes del carrito se ven
  como marcas (verde: libre; celeste: ocupado); la que miro se resalta y un cartel dice su
  nombre, qué tiene y qué categorías acepta. En el modo armado no se agarra ni se usa nada.
- **REQ-TIE-02** Clic en un anclaje libre abre la lista de lo que entra ahí (categoría
  permitida y base admitida, REQ-TIE-11): primero lo guardado, gratis; después la tienda,
  con precio. Elegir uno lo pone al instante. Comprar resta de la caja (REQ-ECO-02: si no
  alcanza, se rechaza con aviso) y suma a los gastos del día (REQ-ECO-05).
- **REQ-TIE-03** Clic en un anclaje ocupado ofrece: **Mover**, **Guardar** o cambiarlo por
  otro de la lista (el que estaba se guarda).
- **REQ-TIE-04** Mover: el siguiente clic elige el anclaje de destino. Si está libre y lo
  acepta, el accesorio va ahí; si está ocupado y los dos se aceptan mutuamente, se
  intercambian. El accesorio se mueve con todo su estado (agua, temperatura, carbón, bloques
  del depósito). Clic en otro lado o B cancela.
- **REQ-TIE-05** Guardar manda el accesorio al inventario. Un depósito con bloques no se
  puede guardar (aviso: vacialo primero). La comida suelta que estaba encima queda donde está.
- **REQ-TIE-06** Al poner, sacar o mover equipos se actualiza lo que el carrito puede
  cocinar: los clientes nuevos piden según eso (REQ-CLI-04); los que ya pidieron no cambian.

### Panel del carrito
- **REQ-TIE-07** En el modo armado, Tab abre el panel del carrito con tres partes: Color,
  Bases e Inventario. Con el panel abierto el mouse queda libre.
- **REQ-TIE-08** Color: una paleta fija de 10 colores, gratis; elegir uno pinta el carrito al
  instante (REQ-CAR-09, REQ-MOD-05).
- **REQ-TIE-09** Inventario: los accesorios y bases guardados; cualquiera se puede **vender**
  a la mitad de su precio (suma a la caja y a los ingresos del día).
- **REQ-TIE-10** Bases: la lista de bases con su precio. Comprar una, o elegir una guardada
  (gratis), la pone en lugar de la actual, que se guarda. Cada accesorio pasa al anclaje
  con el mismo id en la base nueva si ahí se acepta; los demás se guardan. No se puede
  cambiar si un depósito con bloques no tiene lugar en la base nueva.

### Datos
- **REQ-TIE-11** Un accesorio puede limitar en qué bases entra (`bases`, lista de ids; si
  falta, entra en todas). Así cada tamaño de techo o toldo va solo en la base de su ancho.
- **REQ-TIE-12** Se suman como accesorios los modelos ya hechos (SPEC-025): techos plano, a
  dos aguas y curvo y marquesina (en tres tamaños, uno por barra o carro), telones de hamburguesas y choripán, cerco de metal, cartel luminoso,
  pizarra grande, maceta, mesa alta y banqueta.
- **REQ-TIE-13** Categoría nueva **Mobiliario** (REQ-CAR-04): cosas de piso para los clientes
  (mesa alta, banqueta, maceta, pizarra grande). Solo la aceptan los anclajes de piso al
  costado o adelante del carrito (`lateral`, `lateral_izq`, `cerco`).

## Criterios de aceptación

- **CA-TIE-01** Aprieto B, miro el anclaje del techo de la barra mediana, compro un techo
  plano mediano: aparece, y la caja baja su precio.
- **CA-TIE-02** Muevo la plancha del mostrador del centro al de la izquierda con una
  hamburguesa cocinándose: la plancha sigue caliente en su lugar nuevo.
- **CA-TIE-03** Guardo la sombrilla y la vendo desde el inventario: recupero la mitad.
- **CA-TIE-04** Saco la plancha: los clientes nuevos dejan de pedir hamburguesa.

## Fuera de alcance

- Guardar la partida (lo comprado se pierde al cerrar: SPEC-022, etapa 7b). Segunda parte
  de la etapa 4 (food truck, tráiler, alacenas, toldos y guirnaldas): [SPEC-027](027-ampliaciones.md).
  Precios definitivos (etapa 6b).

## Notas de diseño

- Decisiones del dueño: modo armado que también mueve; lo sacado se guarda y se puede vender a
  la mitad; la base vieja se guarda; paleta gratis.
- Precios de bases y accesorios: los de los `.ron`, provisorios hasta el balance.
