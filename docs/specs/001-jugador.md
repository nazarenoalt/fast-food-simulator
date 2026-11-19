# SPEC-001 · Jugador

Estado: **Implementada (etapa 1)**

## Objetivo

Moverse en primera persona por el mundo: atender detrás del mostrador, salir del carrito
y caminar por la plaza.

## Requisitos

- **REQ-JUG-01** Movimiento en primera persona con W/A/S/D relativo a hacia dónde mira la cámara.
- **REQ-JUG-02** Mirar con el mouse. El ángulo vertical se limita a ±85° para no dar la vuelta.
- **REQ-JUG-03** Velocidad al caminar 3,5 m/s; con Shift (correr) 6 m/s.
- **REQ-JUG-04** Saltar con Espacio, solo si está apoyado en el piso. Gravedad del proyecto.
- **REQ-JUG-05** El cuerpo del jugador es una cápsula de 1,75 m de alto y 0,3 m de radio;
  la cámara está a 1,65 m del piso.
- **REQ-JUG-06** El jugador choca con el carrito, el mobiliario y el piso (no los atraviesa),
  y empuja suavemente los objetos sueltos con física al chocarlos.
- **REQ-JUG-07** Clic captura el mouse; Esc lo libera (para poder salir de la ventana).
- **REQ-JUG-08** El jugador aparece detrás del mostrador del carrito.
- **REQ-JUG-09** Camina por escalones de hasta 0,30 m sin saltar (el del food truck y el
  tráiler, SPEC-027): si choca de frente con un borde que se puede pisar, sube a ese nivel.

## Criterios de aceptación

- **CA-JUG-01** Puedo dar una vuelta completa alrededor del carrito y entrar de nuevo detrás del mostrador.
- **CA-JUG-02** Puedo caminar hasta la fuente del centro de la plaza.
- **CA-JUG-03** Si camino contra un pan que está en el piso, el pan se mueve.

## Fuera de alcance

- Agacharse, animaciones del cuerpo, manos visibles, joystick.

## Notas de diseño

- Se usa `CharacterBody3D` (control preciso) en vez de un cuerpo físico, como casi todos los
  juegos en primera persona. Por eso el empuje de objetos (REQ-JUG-06) se hace a mano
  aplicando un impulso a lo que toca.
