# SPEC-032 · Rendimiento

Estado: **Aprobada (TASK-0250)**

## Objetivo

Medir siempre igual cuántos cuadros por segundo da el juego en el peor momento (plaza llena,
fila llena), para saber si anda bien en la PC del dueño (TASK-0255).

## Requisitos

- **REQ-REN-01** `tools/rendimiento.sh` (con `GODOT=`) abre `res://scenes/rendimiento.tscn` con
  ventana, sin `--headless` ni `--fixed-fps` y con vsync apagado.
- **REQ-REN-02** La escena es siempre la misma: sábado de la segunda semana a las 13:00, con
  feria (la plaza más llena), autos, la fila llena con 6 clientes y la cámara desde el
  mostrador mirando a la plaza. Usa el carrito con los cuatro equipos.
- **REQ-REN-03** Espera 10 s y después mide 60 s el tiempo de cada cuadro.
- **REQ-REN-04** Al terminar imprime una línea y se cierra:
  `RENDIMIENTO: prom 72 fps · 1% bajo 55 fps · peor cuadro 31 ms · 1900 dibujos · 48 personas · 6 autos`.
  "1% bajo" es el promedio de fps del 1% de cuadros más lentos.
- **REQ-REN-05** Las cuentas (promedio, 1% bajo, peor cuadro) están en `rust/core` con tests;
  el nodo de Godot solo junta los tiempos.
- **REQ-REN-06** Meta: promedio ≥ 60 fps y 1% bajo ≥ 45 fps a 1080p en la PC del dueño. No
  entra en `tools/verificar.sh`: necesita placa de video.

## Criterios de aceptación

- **CA-REN-01** Corro `tools/rendimiento.sh` en mi PC y en ~75 s sale la línea `RENDIMIENTO:`.

## Fuera de alcance

- Opciones de calidad gráfica (llegan con el menú, SPEC-022), medir memoria.

## Notas de diseño

- El sábado con feria es el momento con más gente (hasta ~42 personas, SPEC-019).
