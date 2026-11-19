# SPEC-019 · Eventos de la plaza

Estado: **Aprobada (etapa 5)**

## Objetivo

Días distintos: los fines de semana hay feria y dos veces por semana juega el equipo del
barrio, con camisetas, plaza vacía durante el partido y festejo después.

## Requisitos

- **REQ-EVE-01** Semana de 7 días: el día 1 es viernes. La pantalla muestra el día de la
  semana al lado de la hora (ej. "Sáb 10:30").
- **REQ-EVE-02** Los eventos están en `godot/data/eventos.ron`: días de la semana, tramos
  horarios (pueden pasar las 24:00, que cuentan en el día siguiente) y, por tramo,
  multiplicador de gente, de clientes y perfiles que se suman a la franja.
- **REQ-EVE-03** A las 7:00 (o al empezar la partida, si ya pasó) sale un aviso con los
  eventos del día (ej. "Hoy: feria en la plaza de 10 a 18").
- **REQ-EVE-04** La gente de REQ-RUT-01 y la tasa de clientes de REQ-CLI-01 se multiplican
  por los del tramo activo (1 si no hay ninguno).

### Feria
- **REQ-EVE-05** Sábados y domingos: 6 puestos con toldo de colores (piezas simples, con
  colisión) en el lado de la plaza opuesto al carrito, sin tapar caminos. Están de 6 a 22
  (nadie los ve aparecer de día) y tienen un vendedor detrás de 10 a 18.
- **REQ-EVE-06** De 10 a 18: gente ×1,5, se suman familias y jubilados, y algunos paseantes
  se paran 1–3 min frente a un puesto. Clientes ×1,3.

### Partido
- **REQ-EVE-07** Miércoles y domingos, partido a las 21. De 18 a 21 la mitad de la gente que
  llega lleva la camiseta de uno de los dos equipos (colores en `eventos.ron`).
- **REQ-EVE-08** De 21 a 23 (durante el partido) gente y clientes ×0,3.
- **REQ-EVE-09** De 23 a 0:30, festejo: llegan grupos de 3–4 con camiseta que saltan y
  levantan los brazos. Clientes ×2.

## Criterios de aceptación

- **CA-EVE-01** El sábado a las 12 veo los puestos con vendedores y más gente que el viernes.
- **CA-EVE-02** El miércoles a las 20 veo camisetas; a las 22 la plaza está casi vacía; a
  las 23:30 hay grupos festejando y la fila se llena.

## Fuera de alcance

- Sonido del festejo (bocinazos, cantos), comprar en los puestos, otros eventos.

## Notas de diseño

- Día 1 viernes: el primer sábado llega a los ~7 min reales de partida.
- Los multiplicadores se componen con la agenda (SPEC-018) y la reputación (REQ-CLI-01).
