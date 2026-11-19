# Cómo se juega

## Controles
| Tecla | Acción |
|---|---|
| W A S D | Moverse |
| Mouse | Mirar |
| Shift | Correr |
| Espacio | Saltar |
| Clic izquierdo | Agarrar (comida, paquetes y bolsas, también del estante) / colocar lo que tenés en la mano donde apunta la cruz blanca |
| Clic derecho | Tirar lo que tenés en la mano hacia la cruz |
| E | Usar: prender el hervidor, la plancha o la parrilla, abrir y cerrar la heladera, la puerta del carrito (carro grande, kiosco, food truck y tráiler) o las puertas y cajones de las alacenas, dar vuelta una hamburguesa, un chorizo o un pan, sacar del depósito, volcar todas las salchichas de un paquete en el hervidor (con el paquete en la mano), poner aderezo (con la comida en la mano), recargar un pomo (con el repuesto en la mano), echar carbón en la parrilla (con la bolsa en la mano) |
| Tab | Panel del proveedor (comprar mercadería) |
| B | Modo armado: poner, mover, guardar y vender accesorios; con Tab adentro, color, bases e inventario ([SPEC-017](specs/017-tienda.md), [SPEC-027](specs/027-ampliaciones.md)) |
| T | Tiempo ×30 (para ver el atardecer rápido) |
| C | Traer un cliente al instante (para probar) |
| M | Silenciar o reactivar todo el sonido |
| Esc | Soltar el mouse |

## Atender a un cliente
1. E sobre el hervidor para prenderlo.
2. E sobre el paquete de salchichas del estante y hacé clic apuntando al agua. O agarrá el
   paquete entero (clic) y apretá E sobre el hervidor: caen todas las salchichas de una.
3. Esperá a que esté cocida (el cartel lo dice y cambia de color).
4. Sacá un pan de la bolsa, dejalo en la mesada, agarrá la salchicha, apuntá la cruz al pan
   y hacé clic: la salchicha va arriba del pan y se arma el pancho.
5. Con el pancho en la mano, mirá un pomo y apretá E para ponerle el aderezo que pidió el
   cliente (está en el globo sobre su cabeza).
6. Dejá el pancho en la **bandeja roja**: el cliente lo agarra, paga y se va comiendo.

## Cuando se acaba algo
Tab abre el proveedor. Lo que comprás llega en una hora de juego a un pallet al lado del
carrito; llevá el paquete a un lugar libre del estante (apuntá ahí y hacé clic) y queda guardado.

## Mover cosas
Lo que agarrás queda en tu mano, abajo a la derecha. Con algo en la mano aparece una cruz
blanca en el centro: donde apunta es donde va a quedar al hacer clic (el cartel dice qué va a
pasar). Los paquetes, cajas y bolsas de papas del estante también se agarran con clic y se
llevan a cualquier lado; dejalos en un lugar libre y se vuelven a guardar.

## Agregar contenido sin tocar código
- **Un carrito nuevo:** copiá un archivo de `godot/data/carritos/` y cambiale id, medidas y anclajes.
- **Un accesorio:** agregalo en `godot/data/accesorios.ron` (categoría, forma, función).
- **Tu carrito:** editá `godot/data/carrito_jugador.ron` (base, color, anclajes, stock inicial).
  Si algo no encaja, el juego muestra el error arriba del carrito.
- **Papas fritas** ([SPEC-026](specs/026-papas.md)): ya están `freidora` y `freidora_doble`
  (traen su colador) y `tabla_papas` (cuchillo, pelapapas y una papa) para los anclajes de
  mostrador, `cartel_cerrado` para el anclaje `cartel` (cuelga adelante, del canto del
  mostrador), y las bolsas de papas de 2 y 5 kg y `pack_cajitas` en el proveedor. Freír viene después.

## Armar el carrito
- **Food truck y tráiler** (panel de bases, Tab en el modo armado): arrancás afuera, adelante;
  dá la vuelta, abrí la puerta con E y subí el escalón. Atendés por la ventana.
- **Alacenas** en los huecos de abajo de la mesada (bahías): guardan mercadería; puertas y
  cajones se abren con E. **Toldos** en el frente; **guirnaldas** solo con un techo puesto.
- Hay cosas que no van juntas (la sombrilla con un techo, el toldo con la carpa): el juego avisa.

## Otros platos
- **Hamburguesa:** E sobre la plancha para prenderla, apoyá una hamburguesa y dale vuelta con
  E antes de que se pase. Se cocina el lado que toca la plancha. Se sirve sola, sin aderezos.
- **Choripán:** cargá carbón (bolsa en la mano y E sobre la parrilla; entran hasta 3 kg) y
  prendela con E. Apoyá un chorizo y dalo vuelta. Tostá el pan de choripán por una cara como
  mínimo, sin quemarlo, y soltá el chorizo cocido encima: se arma el choripán. Va con
  chimichurri o mostaza. El carbón se gasta mientras está prendida: comprá más con Tab.
- **Heladera:** la carne **cruda** se echa a perder si queda tibia (se pone verdosa y el cartel
  avisa). Guardala en la heladera con la puerta cerrada (E la abre y la cierra). Los paquetes de
  carne del proveedor vienen fríos y se calientan si los dejás en el estante. Lo que ya está
  listo (un pancho, un choripán, una hamburguesa cocida de los dos lados) no se pudre.
- Cada cliente pide un plato del menú; solo piden lo que tu carrito puede cocinar.
## Sonido
El juego suena con ambiente que cambia con la hora (pájaros de día, grillos de noche, murmullo
de la plaza) y con cada acción. Los archivos van en `godot/audio/` (`.ogg`) y se declaran en
`godot/data/sonidos.ron`; lista y créditos en `godot/audio/CREDITOS.md`. Sin archivos, el
juego funciona igual, en silencio.
