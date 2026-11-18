# Cómo se juega

## Controles
| Tecla | Acción |
|---|---|
| W A S D | Moverse |
| Mouse | Mirar |
| Shift | Correr |
| Espacio | Saltar |
| Clic izquierdo | Agarrar / soltar |
| Clic derecho | Tirar lo que tenés en la mano |
| E | Usar: prender el hervidor, sacar del depósito, poner aderezo (con el pancho en la mano), recargar un pomo (con el repuesto en la mano) |
| Tab | Panel del proveedor (comprar mercadería) |
| T | Tiempo ×30 (para ver el atardecer rápido) |
| C | Traer un cliente al instante (para probar) |
| M | Silenciar o reactivar todo el sonido |
| Esc | Soltar el mouse |

## Atender a un cliente
1. E sobre el hervidor para prenderlo.
2. E sobre el paquete de salchichas del estante y soltá la salchicha en el agua.
3. Esperá a que esté cocida (el cartel lo dice y cambia de color).
4. Sacá un pan de la bolsa, dejalo en la mesada y soltá la salchicha encima: se arma el pancho.
5. Con el pancho en la mano, mirá un pomo y apretá E para ponerle el aderezo que pidió el
   cliente (está en el globo sobre su cabeza).
6. Dejá el pancho en la **bandeja roja**: el cliente lo agarra, paga y se va comiendo.

## Cuando se acaba algo
Tab abre el proveedor. Lo que comprás llega en una hora de juego a un pallet al lado del
carrito; llevá el paquete a un lugar libre del estante y queda guardado.

## Agregar contenido sin tocar código
- **Un carrito nuevo:** copiá un archivo de `godot/data/carritos/` y cambiale id, medidas y anclajes.
- **Un accesorio:** agregalo en `godot/data/accesorios.ron` (categoría, forma, función).
- **Tu carrito:** editá `godot/data/carrito_jugador.ron` (base, color, anclajes, stock inicial).
  Si algo no encaja, el juego muestra el error arriba del carrito.

## Sonido
El juego suena con ambiente que cambia con la hora (pájaros de día, grillos de noche, murmullo
de la plaza) y con cada acción. Los archivos van en `godot/audio/` (`.ogg`) y se declaran en
`godot/data/sonidos.ron`; lista y créditos en `godot/audio/CREDITOS.md`. Sin archivos, el
juego funciona igual, en silencio.
