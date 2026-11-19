# SPEC-029 · Preparar y freír papas

Estado: **Aprobada**

## Objetivo

Que las papas de la [SPEC-026](026-papas.md) se preparen a mano (pelar, cortar), se frían en
aceite caliente con el colador y se vendan en cajita. Usa el modelo de calor de la
[SPEC-003](003-coccion.md); los pedidos y el cobro, la [SPEC-009](009-clientes.md).

## Requisitos

### Pelar y cortar
- **REQ-FRE-01** Pelar: con el `pelapapas` en la mano y la mira en una `papa_cruda` apoyada
  (nadie la sostiene), cada E es una pasada; a la 3.ª la papa pasa a `papa_pelada` en el mismo
  lugar. El cartel muestra el avance («[E] Pelar papa (1/3)»).
- **REQ-FRE-02** Cortar: igual con el `cuchillo` sobre una `papa_pelada`, 4 pasadas: sale una
  `papa_cortada` (una porción de bastones, la de una cajita).
- **REQ-FRE-03** La herramienta, las pasadas y el resultado salen de los datos del producto.
  Sin la herramienta, E no hace nada y el cartel dice cuál hace falta. Las pasadas hechas
  quedan en la papa aunque se la mueva.

### Aceite
- **REQ-FRE-04** La función **Freidora** tiene una cuba (la doble, dos), cada una con su
  aceite: arranca a 20 °C; encendida sube 2,5 °C/s hasta 180 °C; apagada se enfría de a poco
  hacia el ambiente.
- **REQ-FRE-05** E sobre una cuba la enciende o la apaga; cada cuba tiene su luz piloto y su
  cartel con la temperatura del aceite. Las dos cubas de la doble no dependen una de otra.
- **REQ-FRE-06** Todo alimento dentro del volumen de aceite de una cuba toma la temperatura
  del aceite como entorno (como el agua, REQ-COC-08). La freidora sigue trayendo sus
  coladores (REQ-PAP-06).

### Colador
- **REQ-FRE-07** Con papas (cortadas o fritas) en la mano, colocar sobre el colador las deja
  adentro. Caben 2 porciones; lleno, el cartel lo dice y se apoya como siempre.
- **REQ-FRE-08** E sobre un colador puesto en una cuba lo baja (el canasto queda dentro del
  aceite) o lo sube (encima del aceite, escurriendo). Arranca arriba. Lo que tiene adentro se
  mueve con él; las papas se sacan agarrándolas.

### Cocción
- **REQ-FRE-09** La `papa_cortada` se cocina (REQ-COC-01 a 04). En aceite a 180 °C queda
  Cocida entre 60 s y 120 s, Pasada entre 130 s y 180 s, y Quemada después de 200 s, siempre
  después de pasarse. El color cambia de forma continua: pálido → dorado → marrón → casi negro.
- **REQ-FRE-10** Al quedar Cocida, la `papa_cortada` se reemplaza por `papas_fritas` en el
  mismo lugar, con la misma temperatura, avance y estado, y se sigue cocinando igual.

### Cajita
- **REQ-FRE-11** Combinación (REQ-ARM-01): `cajita_papas` (base) + `papas_fritas`
  (agregado) = `papas_en_cajita`, que conserva la cocción de las papas. Se vende a $8
  (REQ-ECO-07), admite ketchup y mayonesa y requiere Freidora (REQ-CLI-04).

## Criterios de aceptación

- **CA-FRE-01** Con la `tabla_papas`: pelo la papa con 3 E y la corto con 4.
- **CA-FRE-02** Prendo la freidora, en ~1 min llega a 180 °C, meto la porción en el colador, lo
  bajo y en menos de 2 min salen papas fritas doradas.
- **CA-FRE-03** Las pongo en una cajita, la apoyo en la bandeja y el cliente que pidió papas
  paga $8.

## Fuera de alcance

- Que el aceite se enfríe al meter papas frías, que se gaste o se ensucie; sal; combos de
  varios productos.

## Notas de diseño

- 1 papa = 1 porción = 1 cajita: la bolsa de 5 kg ($18) rinde 24 cajitas.
- Pelar y cortar con E (pasadas) y no con tiempo: se siente como trabajo y no hay que esperar.
- La papa cortada cambia de modelo al freírse porque las fritas son torcidas y doradas
  (REQ-PAP-01); el color sigue saliendo del avance.
- El colador es la manera cómoda de sacar todo junto, pero tirar papas a la cuba también fríe.
