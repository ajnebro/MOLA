# Informe de la fase 3c — Transferencia en COCO bbob-biobj (puertas G4 y G5)

Fecha: 2026-11-09 · Rama `research/phase3` · MOLA 0.4.0 · VAMOS 1.0.0 (`0a8bbb0`, motor numpy), más
IBEA reparado (VAMOS `c4569f25`, PR #115) · Pre-registro: `preregistration.md`, con sus enmiendas 1
(configuraciones aleatorias), 2 (control positivo) y 3 (réplica de G7), todas anteriores a la matriz.

## 1. Resultado

**G4 y G5 no se superan.** Son resultados negativos pre-registrados. En las dos particiones, el
recomendador queda por debajo del generalista de irace, no por encima.

| Puerta (55 funciones) | Comparación | Diferencia media | Mediana | Victorias / derrotas | p bruto | p de Holm |
|---|---|---|---|---|---|---|
| G4 (S1, misma función) | `landscape_1nn` − `gen_all` | −0.0032 | −0.0004 | 15 / 40 | 0.997 | 1.0 |
| G5 (S2, grupo fuera) | `consensus` − `gen_g<g>` | −0.0005 | −0.0002 | 19 / 36 | 0.843 | 1.0 |

**Lo que más pesa:** en bbob-biobj apenas hay margen para transferir. Entre el SBS y el donante
oráculo hay 0.007 de HVn en las tres particiones. Ni siquiera la configuración ajustada para la
propia función supera al SBS de forma apreciable (§3.1).

| HVn medio sobre funciones | S1 | S3 | S2 |
|---|---|---|---|
| Donante oráculo (referencia) | 0.978 | 0.978 | 0.977 |
| Misma función (techo de la similitud perfecta) | 0.972 | — | — |
| `knn_selector` | 0.972 | 0.970 | 0.964 |
| **SBS** (= `consensus`) | **0.972** | **0.972** | **0.970** |
| Generalista de irace | 0.968 (`gen_all`) | — | 0.971 (`gen_g<g>`) |
| `landscape_1nn` (G4) | 0.965 | 0.964 | 0.959 |
| `loss_predictor` | 0.965 | 0.964 | 0.964 |
| `thesis_1nn` | 0.963 | 0.961 | 0.959 |
| Donante aleatorio | 0.961 | 0.961 | 0.960 |
| NSGA-II por defecto | 0.960 | 0.960 | 0.961 |
| Configuración aleatoria del espacio (enmienda 1, media) | 0.934 | 0.934 | 0.935 |

Las particiones van de más a menos similitud: S1 deja la instancia 1 de la función destino entre
los donantes; S3 deja fuera la función; S2 deja fuera todas las funciones con un componente del grupo
de bbob.

## 2. Qué se hizo

| Etapa | Resultado | Fichero |
|---|---|---|
| Ajuste | 61 ejecuciones de irace 4.5 (55 por función, sobre la instancia 1, y 6 generalistas), cada una con 19 993–20 000 experimentos, 10–22 iteraciones y 2 256–3 833 configuraciones. En NicoVM del 2026-10-26 21:12 al 2026-11-08 16:48 UTC, con una parada (§5) | `data/tuned_configs.json` |
| Matriz | 55 c*_f, 6 generalistas y NSGA-II y MOEA/D por defecto: 10 395 pares × 10 semillas en 4.4 h. IBEA por defecto (VAMOS `c4569f25`): 165 pares, 49 s. Las 37 configuraciones aleatorias: 6 105 pares, 1.5 h | `data/matrix_fronts_SHA256SUMS`, `data/evaluation_runs*.csv` |
| G4 y G5 | `analyze_3c.py`, sin cambios | `data/gates.json`, `data/transfer_summary.json`, `data/transfer_long.csv`, `data/hvn.csv` |
| Enmienda 1 | `random_configs_3c.py`, sin cambios | `data/random_configs_summary.json`, `data/random_configs_hvn.csv` |
| Enmienda 2 | `positive_control_3c.py`, sin cambios | `data/positive_control.json` |
| Enmienda 3 | `research/phase4/scripts/analyze_g7_3c.py`, sin cambios | `research/phase4/data/g7_3c.json`, `research/phase4/data/g7_3c_long.csv` |
| Análisis secundarios del §6 | `secondary_3c.py`, escrito después de ver G4 y G5 (§5) | `data/secondary.json` |

Los 16 665 frentes se copiaron de NicoVM a `C:\tmp\mola-phase3c\matrix\fronts`; sus SHA-256 coinciden
con los de NicoVM.

## 3. Hallazgos

### 3.1 Casi no hay margen para transferir

- **Del SBS al oráculo hay 0.007.** Es lo máximo que puede ganar cualquier recomendador que elija un
  donante, y el oráculo además se beneficia de elegir el máximo de 55 medias con ruido.
- **El techo de la similitud perfecta es casi nulo.** En S1, la c*_f de la propia función destino
  (ajustada en la instancia 1, aplicada a las instancias 2 y 3):

  | Comparación en S1 (55 funciones) | Media | Mediana | Victorias / derrotas | p bilateral |
  |---|---|---|---|---|
  | Misma función − `gen_all` | +0.0035 | +0.0007 | 40 / 15 | 0.001 |
  | Misma función − SBS | +0.0002 | +0.0010 | 41 / 13 | 0.006 |
  | SBS − `gen_all` | +0.0033 | −0.0002 | 22 / 33 | 0.39 |

  La propia configuración gana a menudo, pero por muy poco, y a veces pierde mucho: la media del
  peor 10 % de sus pérdidas frente al oráculo es 0.039, frente a 0.026 del SBS. En la fase 3 la
  propia c*_Q superaba al SBS en 0.023.
- **La c*_f de la propia función es el mejor donante en 15 de los 110 destinos de S1.**
- **Las configuraciones ajustadas sí difieren entre sí** en cada destino: entre la mejor y la peor
  hay una mediana de 0.044 (percentil 90: 0.145). Pero el SBS está siempre cerca de la mejor.
- **La mitad de los destinos de S1 están casi saturados:** en 55 de 110, el oráculo supera a NSGA-II
  por defecto en menos de 0.01.
- **El ruido de una celda de la matriz** (error estándar de su HVn sobre las 10 semillas) tiene
  mediana 0.0014 y percentil 90 0.012 en las c*_f. Es del mismo orden que las diferencias entre
  métodos por destino, aunque la media sobre 55 funciones las estime con más precisión.

### 3.2 El paisaje reconoce la función a veces, y lo paga con colas

- **Reconocimiento en S1:** el vecino por paisaje es la instancia 1 de la propia función en el
  29.6 % de las muestras destino. Por azar sería el 1.8 % (1 de 55).
- **Estabilidad:** el donante de `landscape_1nn` es el mismo en las 5 muestras para el 24.5 % de los
  destinos en S1, el 21.8 % en S3 y el 35.1 % en S2.
- **Colas:**

  | Pérdida frente al oráculo | S1 | S3 | S2 |
  |---|---|---|---|
  | `landscape_1nn`, fracción > 0.10 | 2.4 % | 2.4 % | 4.4 % |
  | `knn_selector`, fracción > 0.10 | 0.2 % | 0.7 % | 1.5 % |
  | SBS y generalistas, fracción > 0.10 | 0 % | 0 % | 0 % |
  | `landscape_1nn`, media del peor 10 % | 0.077 | 0.080 | 0.103 |
  | `knn_selector`, media del peor 10 % | 0.033 | 0.046 | 0.068 |
  | SBS, media del peor 10 % | 0.026 | 0.025 | 0.027 |
  | Generalista, media del peor 10 % | 0.043 | — | 0.032 |

- **Gradiente de similitud S1 → S3 → S2:** `landscape_1nn` baja de 0.965 a 0.964 y a 0.959;
  `knn_selector`, de 0.972 a 0.970 y a 0.964; el SBS apenas se mueve (0.972, 0.972, 0.970).
- **Mediana de la pérdida frente al oráculo** en S1: 0.0023 `knn_selector`, 0.0027 SBS, 0.0028
  `gen_all`, 0.0029 `landscape_1nn`. Como en la fase 3, el vecino por paisaje tiene una mediana
  competitiva y una cola que hunde su media.

### 3.3 La regla de consenso nunca se activa

`consensus` se aparta del SBS en el 0 % de las muestras, en las tres particiones y en los tres
presupuestos. Su umbral, δ = 0.05, es siete veces el hueco entero entre el SBS y el oráculo. G5 ha
comparado, por tanto, el SBS con los generalistas por grupo.

### 3.4 Los generalistas

- **c*_f32 es el SBS** en S1, en 54 de los 55 pliegues de S3 (en el otro, c*_f34) y en 4 de los 5 de
  S2 (en el del grupo 4, c*_f20). Es NSGA-II con población 143, `offspring_ratio` 0.5, selección
  SUS, cruce BLX-α y mutación polinómica enlazada.
- **`gen_all`, ajustado por irace sobre las 55 instancias 1, queda por debajo del SBS en media**
  (0.968 frente a 0.972), aunque gana en 33 de las 55 funciones. Sus pérdidas se concentran en
  pocas funciones.
- **Los generalistas por grupo de S2 empatan con el SBS** (0.971 frente a 0.970; 36 victorias del
  generalista de 55, p bilateral 0.31).
- **Sobre los 165 problemas, la mejor configuración es `gen_g5`** (HVn medio 0.973), seguida de
  c*_f32 (0.972).
- **Las 61 configuraciones son variadas:** 22 son de estado estacionario (`offspring_ratio` 0), 27
  tienen población de 190 o más, y el cruce va de difuso (16) a BLX-α (14), aritmético (12) y SBX
  (11). La selección es SUS en 38. No hay un generalista tan dominante como c*_ZDT3 en la fase 3: el
  margen es pequeño para todas.

### 3.5 Otras distancias y presupuestos (§6, descriptivos)

| `landscape_1nn` con | S1 | S3 | S2 |
|---|---|---|---|
| Euclídea (pre-registrada) | 0.965 | 0.964 | 0.959 |
| L1 | 0.966 | 0.963 | 0.959 |
| PCA blanqueada | 0.964 | 0.962 | 0.957 |
| Rangos | 0.965 | 0.962 | 0.958 |
| Euclídea, features con objetivos sin escalar | 0.967 | 0.965 | 0.959 |

Ninguna distancia alcanza al generalista ni al SBS.

| Presupuesto | SBS (S1) | `gen_all` | `landscape_1nn` − `gen_all` (S1) | `consensus` − `gen_g<g>` (S2) |
|---|---|---|---|---|
| 5 000 | 0.956 | 0.951 | −0.0056 (15 / 40) | +0.0028 (40 / 15, p bilateral 0.026) |
| 10 000 | 0.966 | 0.963 | −0.0045 (13 / 42) | −0.0008 (23 / 32) |
| 20 000 (G4, G5) | 0.972 | 0.968 | −0.0032 (15 / 40) | −0.0005 (19 / 36) |

Con 5 000 evaluaciones, el SBS (que es `consensus`) supera a los generalistas por grupo. Es
descriptivo: las configuraciones se ajustaron para 20 000.

### 3.6 Enmienda 1: configuraciones aleatorias del espacio

Las 37 configuraciones aleatorias de la fase 3 tienen un HVn medio de 0.934 (mediana 0.942), y el
11–12 % pierden más de 0.10 frente al oráculo. Ajustar importa: cualquier c*_f, elegida al azar,
llega a 0.961, y el SBS a 0.972. Lo que apenas importa es cuál de las ajustadas se usa.

### 3.7 Enmienda 3: réplica de G7

La política π₀.₀₅ transfiere con `knn_selector` si s₁ ≥ 0.05, y si no recurre al generalista de la
partición.

- **Cobertura, tal como se declaró antes de la matriz:** transfiere en el 96.9 % de las muestras en
  S1, el 88.9 % en S2 y el 95.6 % en S3 (se esperaba 97, 89 y 96 %). La distancia mediana al problema
  de entrenamiento más cercano es de 0.80, 0.91 y 0.83 unidades de ruido.
- **Condiciones de G7:**

  | Partición | 1. No inferioridad (margen 0.005) | 2. Cola reducida a la mitad frente a `knn_selector` |
  |---|---|---|
  | S1 | Sí: +0.0035, p = 5.6·10⁻¹⁰ | No: 0.18 % frente a 0.18 % |
  | S3 | Sí: +0.0002, p = 2.7·10⁻⁷ | No: 0.73 % frente a 0.73 % |
  | S2 | No: −0.0055, p = 0.070 | No: 1.26 % frente a 1.54 % |

  G7 no se replica en ninguna partición. Como se anticipó, π casi nunca se abstiene, así que se
  comporta como `knn_selector`.

### 3.8 Enmienda 2: control positivo

Medias sobre funciones. El hueco cerrado es (método − SBS) / (VBS − SBS); con huecos tan pequeños
es inestable, así que el hueco absoluto va al lado.

| Protocolo | Vecino de la misma función | Selección entre los 3 por defecto: VBS − SBS | Mejor selector (hueco cerrado) | Transferencia: oráculo − SBS | `knn_selector` (hueco cerrado) | `landscape_1nn` (hueco cerrado) |
|---|---|---|---|---|---|---|
| `rows` (MO-ELA) | 41.6 % | 0.0022 | `rf_regr`, +30 % | 0.0065 | +22 % | −64 % |
| `instance_out` | 27.2 % | 0.0023 | ninguno; `rf_regr` −32 % | 0.0065 | −7 % | −75 % |
| `function_out` | 0 % | 0.0023 | ninguno; `rf_regr` −48 % | 0.0067 | −27 % | −87 % |
| `group_out` | 0 % | 0.0023 | ninguno; `rf_regr` −68 % | 0.0070 | −116 % | −135 % |

- **Entre los algoritmos por defecto casi no hay nada que elegir:** el SBS queda a 0.0022 del VBS y a
  menos de 0.01 de él en el 95.8 % de las filas.
- **El protocolo con fuga ayuda poco, porque no hay hueco.** Con la partición por filas, el mejor
  selector cierra el 30 % de un hueco de 0.0022, y `knn_selector` el 22 % de uno de 0.0065. En la
  fase 3 las mismas features cerraban el 79–98 % (§12 de su informe).
- **Fuera de la fila, nada supera al SBS,** como en la fase 3. La caída es monótona de `rows` a
  `group_out` en las dos tareas.
- El control no puede repetir aquí el contraste de la fase 3 entre protocolos: la similitud se
  reconoce (el vecino más cercano es de la misma función en el 42 % de las filas con `rows`), pero
  reconocerla vale como mucho unas milésimas de HVn.

## 4. Interpretación (a posteriori, no pre-registrada)

- **G4 y G5 fallan sobre todo porque no hay nada que transferir.** El diseño suponía que, con la
  similitud controlada, el donante de la misma función sería claramente mejor que un generalista. No
  lo es: en bbob-biobj con D = 10 y 20 000 evaluaciones, las configuraciones ajustadas por irace son
  casi intercambiables en media, y el SBS queda a 0.007 del oráculo.
- **Es la misma lección de la fase 3, más extrema.** Allí el SBS dejaba un margen de 0.014 y la propia
  c*_Q ganaba 0.023; aquí, 0.007 y 0.0002. Con portafolios ajustados por irace, la recuperación de un
  solo donante añade varianza (colas) sin añadir media.
- **Las features distinguen las funciones por encima del azar, pero no de forma fiable.** Encuentran
  la propia función en el 30 % de las muestras (azar: 1.8 %), y el donante cambia entre muestras del
  mismo problema en tres de cada cuatro destinos. Esto concuerda con la expectativa declarada en la
  enmienda 3: la distancia al vecino más cercano está dentro del ruido de remuestreo.
- **El control positivo no contradice la fase 3, pero aquí no puede confirmarla.** El orden de los
  protocolos se repite: solo la partición por filas cierra algo de hueco, y todo lo demás pierde
  frente al SBS. Pero el hueco es de milésimas, así que bbob-biobj con D = 10 y 20 000 evaluaciones no
  sirve para mostrar el éxito con fuga de la literatura. MO-ELA cerró el 45 % en las funciones de BBOB
  biobjetivo, con otros presupuestos, dimensiones y portafolio.
- **Un generalista ajustado no es siempre el mejor generalista.** `gen_all` queda por debajo de la
  mejor c*_f, y `gen_g5`, ajustado sin las funciones del grupo 5, es la mejor configuración sobre los
  165 problemas. Puede reflejar que 20 000 experimentos repartidos entre 55 instancias convergen menos
  que 20 000 sobre una sola, pero no se ha comprobado.

## 5. Desviaciones

1. **Parada y reanudación.** El 2026-10-28 a las 17:03 UTC se paró la campaña, a petición del
   usuario, para liberar NicoVM (`STOPPED-20261028.txt`). Se reanudó el 2026-11-02 a las 16:10 UTC
   desde los `irace.Rdata` de cada ajuste.
2. **f20 se repitió desde cero.** Su instantánea no tenía ningún experimento completo, y la
   recuperación falló. Se repitió solo, con el mismo escenario y la misma semilla, el 2026-11-08 de
   16:12 a 16:48 UTC, con 31 procesos en lugar de 6. El estado fallido está en
   `irace/f20/failed-recovery-20261102/` de NicoVM.
3. **Servidor de evaluación sustituido a media campaña (2026-11-07, 18:15 UTC).** El nuevo lleva el
   arreglo del `import numba` (`1ea590e`), idéntico bit a bit, sin parar irace. numba no se instaló
   porque cambia la secuencia aleatoria del SBX de estado estacionario
   (`scripts/check_numba_sbx.py`).
4. **Un fallo de `common.instantiate()` ralentizó la campaña.** Añadía una entrada a `sys.path` en
   cada experimento COCO, y con el `import numba` fallido de VAMOS cada generación de estado
   estacionario se hacía más lenta con los días. Solo afectó a la velocidad. Se corrigió después de la
   campaña (`6846f21`).
5. **Coste.** El ajuste ocupó unas 188 h de NicoVM, frente a las 70 h estimadas, por el fallo
   anterior. La matriz tardó 4.4 h, frente a las 5 h estimadas, más 1.5 h de las configuraciones
   aleatorias.
6. **scikit-learn 1.9.0** en lugar de la 1.9.1 que fija `positive_control_3c.py`. Solo afecta a los
   bosques aleatorios del control positivo, que es exploratorio.
7. **`secondary_3c.py` se escribió después de ver G4 y G5.** Cubre los análisis del §6 que
   `analyze_3c.py` no calcula: la media del peor 10 %, el techo de la similitud perfecta, las
   distancias alternativas y los presupuestos de 5 000 y 10 000. Añade el error estándar por semilla,
   que no estaba en el §6.

## 6. Qué no se debe afirmar

- **Que las features no reconocen los problemas.** Reconocen la función 16 veces más que el azar;
  lo que no hacen es elegir un donante mejor que el SBS, que aquí casi no tiene margen.
- **Que la similitud de paisaje no sirve para transferir en general.** Lo que se ha visto vale para
  NSGA-II ajustado con irace en bbob-biobj, con D = 10 y 20 000 evaluaciones, donde las
  configuraciones ajustadas son casi intercambiables.
- **Que el SBS es mejor que `gen_all`.** La diferencia media es +0.0033, pero la mediana es negativa
  y la prueba bilateral no es significativa (p = 0.39); es una comparación descriptiva.
- **Que la regla de consenso funciona con 5 000 evaluaciones.** Ahí `consensus` es el SBS, y la
  comparación es descriptiva.
