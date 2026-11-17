# SPEC-013 · Ambientación

Estado: **Implementada (etapa 2)**

## Objetivo

Que el lugar se sienta vivo: una ciudad alrededor, gente haciendo su vida, autos, palomas,
nubes y un cielo con sol y luna.

## Requisitos

### Ciudad
- **REQ-AMB-01** Una fila de edificios del otro lado de la calle (frente al carrito) y
  edificios rodeando la plaza por los otros tres lados, con vereda. Alturas de 2 a 7 pisos,
  anchos y colores variados, locales en planta baja con toldo.
- **REQ-AMB-02** Ventanas en las fachadas que miran a la plaza. De noche algunas se prenden
  (siempre las mismas en cada partida).
- **REQ-AMB-03** La distribución de la ciudad es fija y repetible (generada con semilla).

### Gente
- **REQ-AMB-04** Peatones que siguen la red de caminos de la plaza y las veredas, eligiendo
  destinos al azar. La cantidad depende de la hora (mucha de día, poca de madrugada).
- **REQ-AMB-05** Actividades además de caminar: sentarse un rato en un banco, quedarse
  charlando de a dos (con gestos), trotar, pasear el perro.
- **REQ-AMB-06** Los peatones tienen ropa y tono de piel variados, y animación simple de
  caminar (piernas y brazos).
- **REQ-AMB-07** La red de caminos está conectada: desde cualquier punto se puede llegar a
  cualquier otro.

### Movimiento
- **REQ-AMB-08** Autos que circulan por la calle en los dos sentidos (mano derecha), con
  velocidades distintas. Frenan si hay un auto, un peatón o el jugador adelante en su carril.
  Hay dos sendas peatonales para cruzar a la vereda de enfrente.
- **REQ-AMB-09** Los autos tienen faros y luces traseras que se prenden de noche.
- **REQ-AMB-10** Palomas en la plaza que picotean el piso y salen volando si el jugador se
  acerca a menos de 3,5 m; después vuelven a bajar en otro lugar.

### Cielo
- **REQ-AMB-11** Nubes que se mueven despacio con el viento y cruzan el cielo; de día son
  blancas (anaranjadas al atardecer) y de noche oscuras.
- **REQ-AMB-12** El sol se ve como un disco en el cielo; de noche se ve la luna.

## Criterios de aceptación

- **CA-AMB-01** Parado detrás del mostrador veo edificios, autos pasando, nubes moviéndose y
  gente en la plaza.
- **CA-AMB-02** Corro hacia unas palomas y salen volando.

## Fuera de alcance

- Que los peatones esquiven al jugador con inteligencia (lo atraviesan), semáforos, lluvia,
  interiores de edificios.
