# SPEC-014 · Plancha

Estado: **Borrador**

## Objetivo

Cocinar hamburguesas en una plancha: se cocinan **por lados** y hay que darlas vuelta.
Usa el mismo modelo de calor de [SPEC-003](003-coccion.md): la plancha solo define qué
temperatura le da a lo que la toca.

## Requisitos

### Plancha
- **REQ-PLA-01** La plancha es un accesorio del carrito (datos `.ron`). Se enciende y apaga
  con E; una luz piloto roja indica que está encendida y el cartel muestra su temperatura.
- **REQ-PLA-02** Encendida, sube 4 °C por segundo hasta 220 °C. Apagada, se enfría hacia el
  ambiente (20 °C) de forma gradual.
- **REQ-PLA-03** Un alimento apoyado sobre la plancha toma su temperatura como entorno solo
  en el lado que la toca; el otro lado toma la del ambiente.

### Hamburguesa
- **REQ-PLA-04** La hamburguesa tiene dos lados, cada uno con su propia temperatura y su
  avance de cocción (mismas fórmulas que REQ-COC-02 y REQ-COC-03). Empieza cruda de los dos.
- **REQ-PLA-05** El estado de la hamburguesa sale de sus dos lados: **Cruda** si alguno está
  crudo, **Cocida** si los dos están cocidos, **Pasada** si alguno está pasado, **Quemada**
  si alguno está quemado (definitivo). Cada lado se ve del color de su propio avance.
- **REQ-PLA-06** En una plancha a 200 °C cada lado queda Cocido entre 30 s y 90 s y Pasado
  después de 150 s. Un lado se quema si pasa 15 s sobre 200 °C de la propia carne.
- **REQ-PLA-07** E sobre una hamburguesa apoyada en la plancha la da vuelta (intercambia
  lados). También se da vuelta si el jugador la levanta y la apoya del otro lado.

## Criterios de aceptación

- **CA-PLA-01** Enciendo la plancha, apoyo una hamburguesa: crece el avance del lado de abajo
  y el de arriba sigue crudo.
- **CA-PLA-02** La doy vuelta a tiempo y a los pocos minutos está Cocida de los dos lados.
- **CA-PLA-03** Si me olvido, un lado se quema y el cliente la rechaza.

## Fuera de alcance

- Grasa, humo, espátula como herramienta, cocinar varias hamburguesas con contacto entre sí.

## Notas de diseño

- Es la misma idea que el hervidor: `coccion.rs` no cambia por fuente de calor. Lo nuevo es
  que un alimento puede tener más de un lado, cada uno con su estado térmico.
- Valores iniciales en `godot/data/productos.ron`: k = 0,10; T_min = 60 °C; velocidad = 0,0015;
  punto = 6; pasado = 14.
