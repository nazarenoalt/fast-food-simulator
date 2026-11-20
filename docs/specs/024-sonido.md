# SPEC-024 · Sonido

Estado: **Implementada (lógica y nodos; faltan cargar los archivos de audio)**

## Objetivo

Un paisaje sonoro cálido y suave (estilo "cozy"): ambiente de plaza que cambia con la hora,
sonidos de cada acción y música tranquila opcional. El juego funciona igual sin audio.

## Requisitos

### Mezcla
- **REQ-SON-01** Hay tres buses: **Ambiente**, **Efectos** y **Música**, que salen al Master.
  Volumen general y por bus entre 0 y 1 (por defecto 1, 0,8, 1 y 0,5). En dB: `20·log10(v)`;
  con 0 el bus queda en silencio. Con la tecla M se silencia o se reactiva todo.
- **REQ-SON-02** `godot/data/sonidos.ron` define cada sonido: id, archivos (variantes), bus,
  volumen en dB, si es espacial (3D), distancia máxima, si hace bucle y enfriamiento en s.
  Agregar un sonido no requiere tocar código.
- **REQ-SON-03** Con varias variantes se elige una al azar sin repetir la anterior. Un mismo
  sonido no se dispara de nuevo antes de su enfriamiento.
- **REQ-SON-04** Un sonido espacial se oye cada vez menos con la distancia:
  `ganancia = (1 − d / distancia_max)²` (1 si d es 0, 0 desde la distancia máxima). Más lejos
  no se reproduce.

### Ambiente
- **REQ-SON-05** De día suenan pájaros y de noche grillos, con un fundido de 30 min alrededor
  de la salida y la puesta del sol (SPEC-007). Nunca suenan los dos a pleno.
- **REQ-SON-06** El murmullo de la plaza crece con la cantidad de gente (llega al máximo con
  20 peatones) y de noche baja a 40%.
- **REQ-SON-07** El viento suena siempre bajito (nivel 0,2) y sube con la intensidad de viento
  del clima. La lluvia suena solo si llueve. (El clima llega con SPEC-023; hasta entonces
  ambos valen 0.)

### Acciones
- **REQ-SON-08** Cada hecho del juego dispara su sonido: hervidor (interruptor y hervor
  mientras está prendido con agua), plancha (interruptor y chisporroteo mientras haya carne
  encima y la plancha esté caliente, más de 100 °C), parrilla (carbón al cargarla y brasas
  mientras esté prendida; se callan si se apaga sola sin carbón), heladera (puerta al abrir y
  al cerrar), agarrar, soltar, tirar y apoyar comida, pomo de aderezo, paquete que llega y que
  se guarda, sacar del depósito, cobro (una moneda, en cada venta), campanita de cliente que llega, pasos del jugador,
  autos que pasan cerca, aleteo de palomas. La lluvia queda en los datos, sin conectar.
- **REQ-SON-09** Un archivo que falta o la ausencia de audio nunca es un error: el sonido
  se omite y el juego sigue.
- **REQ-SON-10** Todo archivo de `godot/audio/` figura en `godot/audio/CREDITOS.md` con
  autor, enlace y licencia (CC0 o CC-BY). Sin crédito, no entra.

## Criterios de aceptación

- **CA-SON-01** Con audio, prendo el hervidor: se oye el interruptor y después el hervor.
- **CA-SON-02** A las 13:00 oigo pájaros y murmullo; a las 23:00, grillos y poco murmullo.
- **CA-SON-03** Sin audio (driver Dummy) los buses existen, un sonido se dispara sin fallar y
  M los silencia.

## Fuera de alcance

- Menú de opciones con deslizadores (llega con SPEC-022), sonido de la lluvia real (SPEC-023),
  voces, doblaje.

## Notas de diseño

- Los sonidos espaciales usan `AudioStreamPlayer3D`; interfaz y música, `AudioStreamPlayer`.
