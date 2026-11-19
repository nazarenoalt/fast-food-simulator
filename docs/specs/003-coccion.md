# SPEC-003 · Cocción

Estado: **Implementada (etapa 1: hervidor)**

## Objetivo

Que la comida se cocine de forma creíble según la temperatura a la que está expuesta y el
tiempo, y que el jugador lo vea.

## Requisitos

### Temperatura de la comida
- **REQ-COC-01** Cada alimento cocinable tiene una temperatura propia (empieza a 20 °C,
  ambiente) y un "avance de cocción" que empieza en 0.
- **REQ-COC-02** La temperatura del alimento se acerca a la del entorno de forma gradual
  (ley de enfriamiento de Newton): `ΔT = (T_entorno − T) × k × Δt`, con `k` propio de cada alimento.
  Fuera de toda fuente de calor el entorno es el ambiente (20 °C).
- **REQ-COC-03** El avance de cocción solo crece cuando el alimento supera su temperatura
  mínima de cocción, y crece más rápido cuanto más caliente está: `Δavance = (T − T_min) × velocidad × Δt`.
  Nunca retrocede.

### Estados
- **REQ-COC-04** Estados según el avance: **Crudo** (< punto), **Cocido** (≥ punto),
  **Pasado** (≥ pasado). Un alimento cuya temperatura supera su temperatura de quemado pasa
  a **Quemado** cuando acumula suficiente tiempo por encima de ella; Quemado es definitivo.
- **REQ-COC-05** Salchicha en hervidor a 95 °C: pasa a Cocida entre 30 s y 90 s, y a Pasada
  después de 150 s. En agua nunca se quema.
- **REQ-COC-06** El color del alimento cambia de forma continua con el avance
  (salchicha: rosado → rojizo → marrón; quemado: casi negro).

### Hervidor
- **REQ-COC-07** El hervidor tiene agua con su propia temperatura (arranca a 20 °C).
  Encendido, el agua sube 1,5 °C por segundo hasta 95 °C. Apagado, se enfría gradualmente
  hacia el ambiente.
- **REQ-COC-08** Todo alimento cuyo cuerpo está dentro del volumen de agua del hervidor
  toma como temperatura de entorno la temperatura del agua.
- **REQ-COC-09** Se enciende/apaga con E. Una luz piloto roja indica que está encendido y el
  cartel muestra la temperatura del agua.
- **REQ-COC-10** Con un paquete en la mano de algo que se cocina entero (no por lados, como la
  salchicha), E sobre el hervidor vuelca todas sus unidades al agua: acostadas en filas a lo
  largo de la cuba (en capas si no entran), con la temperatura del paquete. El paquete se va.

## Criterios de aceptación

- **CA-COC-01** Enciendo el hervidor, tiro una salchicha, en menos de 2 minutos está Cocida y
  se ve más oscura.
- **CA-COC-02** Si la saco y la dejo afuera, deja de cocinarse (no cambia de estado).

## Fuera de alcance (próximas etapas)

- Plancha, parrilla con carbón, tostado de pan, vapor, nivel de agua que se evapora, grasa.

## Notas de diseño

- El modelo es el mismo para todas las fuentes de calor: cada una solo define "qué
  temperatura de entorno da". Plancha y parrilla se agregan sin cambiar `coccion.rs`.
- Valores iniciales de la salchicha (en `godot/data/productos.ron`): k = 0,06; T_min = 55 °C;
  velocidad = 0,0025; punto = 3; pasado = 13; quemado a 180 °C.
