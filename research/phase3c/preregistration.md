# Pre-registro de la fase 3c — Transferencia de configuraciones en COCO bbob-biobj

Fecha: 2026-10-26. Se fija **antes de cualquier ajuste y de la matriz de esta fase**.

**Lo único ejecutado hasta ahora:**
- el catálogo de los 165 problemas, con sus ideales y nadires verdaderos;
- la caracterización con MOLA, que no usa ningún dato de rendimiento;
- un piloto de diseño, descrito en el §2, cuyas ejecuciones no se reutilizan.

El análisis, `scripts/analyze_3c.py`, se sube con este documento y solo se ha probado con datos
sintéticos.

Corresponde al paso 2 del plan que el usuario aprobó el 2026-10-26 ("procede con todo").

## 1. Motivación

La fase 3 dio un resultado negativo (`research/phase3/report.md`):
- **G3 no se superó.**
- **Ningún método superó al generalista.**
- **El margen sobre él era mínimo:** 0.014 entre el SBS y el oráculo.

Los análisis a posteriori señalaron cuatro causas:
- 13 de los 37 problemas estaban saturados;
- el conjunto lo dominaban ZCAT y LZ09/UF;
- un generalista dominaba;
- la debilidad del paisaje era de fiabilidad (la cola de fallos grandes), no de señal.

Esta fase cambia cuatro cosas a la vez:
1. **Un benchmark con menos saturación y más variado:** COCO bbob-biobj, con D = 10.
2. **Una similitud conocida de antemano.** La misma función en otra instancia (cercana), otra función
   (intermedia) y otro grupo de funciones de bbob (lejana). Así el "cuándo" del título se convierte
   en una variable controlada.
3. **La referencia estándar de la configuración por instancia (ISAC, Hydra):** un generalista
   ajustado con irace sobre todo el conjunto de entrenamiento.
4. **Pre-registrar la regla de consenso** que la fase 3 identificó de forma exploratoria.

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Problemas | bbob-biobj de cocoex 2.8.2, D = 10, funciones 1–55 e instancias 1, 2 y 3: 165 problemas (`data/catalogue.json`) |
| Caja de búsqueda | [−5, 5]^10, la región de interés de bbob, donde están los óptimos de los dos componentes (comprobado en los 165 problemas). COCO declara [−100, 100]^10, pero casi todo ese volumen queda lejos del frente: un LHS de 200·D puntos describiría la zona lejana y NSGA-II gastaría el presupuesto en ella |
| Normalización | La de COCO (`data/tuning_bounds.json`). Ideal: (f1(x1*), f2(x2*)), a partir de los óptimos de los componentes. Nadir: `largest_fvalues_of_interest`, que coincide con (f1(x2*), f2(x1*)) en los 165 problemas. Punto de referencia 1.1 |
| Donantes, c*_P | Una por función, ajustada sobre la instancia 1 (55 problemas). irace 4.5, `maxExperiments = 20 000`, resto por defecto, semilla 9000 + función. Espacio invariante de NSGA-II de la fase 3 (`phase3/irace/parameters.txt`, población en [20, 200]), con NSGA-II por defecto como candidata inicial. Cada ejecución hace 20 000 evaluaciones con VAMOS 1.0.0 (`0a8bbb0`) y motor numpy |
| Generalistas | Mismo irace y mismo espacio, con varias instancias de irace (los problemas de entrenamiento). `gen_all` usa los 55 problemas de instancia 1 (semilla 9100). `gen_g<g>`, para g = 1…5, usa los problemas de instancia 1 sin ningún componente del grupo g: 36 en cada caso (semilla 9100 + g) |
| Grupos de bbob | 1 separables {f1, f2}; 2 condicionamiento moderado {f6, f8}; 3 mal condicionadas {f13, f14}; 4 multimodales con estructura global {f15, f17}; 5 multimodales con estructura débil {f20, f21} |
| Matriz | 55 c*_P, 6 generalistas, NSGA-II y MOEA/D por defecto (VAMOS `0a8bbb0`) e IBEA por defecto (VAMOS reparado, `c4569f25`): 64 configuraciones en los 165 problemas, con las semillas 5001–5010 y 20 000 evaluaciones |
| HVn | El de la fase 3: HV normalizado por el ideal y el nadir verdaderos, con referencia 1.1, dividido entre el HV de la unión de los frentes finales de la matriz en cada problema; media de las 10 semillas |
| Caracterización | MOLA 0.4.0, geometría `bound`, k = D, `objective_scaling = "sample"` como principal y `raw` como secundario. 5 muestras LHS por problema (semillas 1001–1005, n = 2 000). Cada problema de entrenamiento se representa por la media de sus muestras; el destino, por cada muestra por separado |

**Piloto de diseño.** NSGA-II por defecto, la c*_ZDT3 de la fase 3 y 6 configuraciones aleatorias,
en 8 funciones de la instancia 1, con 2 semillas y 20 000 evaluaciones.

| Dimensión | Problemas saturados (mejor − mediana < 0.01) | Diferencia media entre la mejor y la mediana |
|---|---|---|
| D = 5 | 7 de 8 | 0.010 |
| D = 10 | 3 de 8 | 0.048 |

En D = 10, la mediana por ejecución es 2.2 s y el máximo 40 s. Por eso se elige D = 10 y se mantienen
las 20 000 evaluaciones de las fases anteriores.

## 3. Particiones

La similitud entre el destino y los donantes disminuye de S1 a S2.

| Partición | Destinos | Entrenamiento (donantes) | Generalista |
|---|---|---|---|
| **S1, cercana** | Instancias 2 y 3 de cada función (110) | Los 55 problemas de instancia 1, incluida la función del destino | `gen_all` |
| S3, función fuera (secundaria) | Instancias 2 y 3 de la función f | Instancia 1 de las otras 54 funciones | — (`gen_all` vio f) |
| **S2, grupo fuera** | Las tres instancias de las 19 funciones con un componente en el grupo g | Instancia 1 de las 36 funciones sin componentes en g | `gen_g<g>` |

**Unidad de análisis: la función (55).**
- En S1 y S3, el valor de una función es la media sobre sus destinos y muestras.
- En S2, una función con componentes de dos grupos es destino en dos pliegues; su valor es la media
  sobre ambos.

## 4. Métodos (`analyze_3c.recommend`)

| Método | Elige |
|---|---|
| `sbs` | La candidata con mejor HVn medio sobre T |
| `random` | Valor esperado de un donante uniforme |
| `landscape_1nn` | c*_P del P más cercano, con distancia euclídea sobre las features escaladas de forma robusta (como en la fase 3) |
| `knn_selector` | La candidata con mejor HVn medio en los 3 problemas más cercanos |
| `consensus` | El SBS, salvo que la mejor candidata en los 3 problemas más cercanos le supere ahí en al menos 0.05. Son k = 3 y δ = 0.05, fijados en la exploración de la fase 3 (§11 de su informe) |
| `thesis_1nn`, `loss_predictor` | Como en la fase 3 |
| Referencias | `generalist` (el `gen_*` de la partición), `default` (NSGA-II por defecto), `oracle` (la mejor candidata) y `same_function` (la c*_P de la propia función, en S1) |

`metadata_1nn` no se usa: todos los problemas tienen D = 10 y las mismas cotas, así que los
metadatos no distinguen ninguno.

## 5. Puertas (análisis principal)

Son pruebas de Wilcoxon de rangos con signo, unilaterales, sobre las 55 funciones, con corrección de
Holm para las dos:
- **G4 (transferencia cercana, S1):** HVn(`landscape_1nn`) > HVn(`gen_all`).
- **G5 (transferencia lejana, S2):** HVn(`consensus`) > HVn(`gen_g<g>`).

Una puerta se supera si la diferencia media es positiva y el p ajustado por Holm es menor que 0.05.
Si no se supera, se informa como resultado negativo. No se cambian la representación, la distancia
ni los parámetros de la regla para repetir la prueba.

## 6. Análisis secundarios, descriptivos

- **HVn medio** por método y partición.
- **Pérdida frente al oráculo:** mediana, fracción mayor que 0.10 y media del peor 10 %.
- **Reconocimiento en S1:** fracción de destinos cuyo vecino por paisaje es la instancia 1 de su
  propia función.
- **Techo de la similitud perfecta:** `same_function` frente al generalista en S1.
- **Gradiente de similitud:** S1 → S3 → S2 para `landscape_1nn`, `consensus` y el SBS.
- **Estabilidad:** el donante de `landscape_1nn` en las 5 muestras.
- **Otras referencias:** el SBS, `knn_selector`, `thesis_1nn` y `loss_predictor` frente al
  generalista, así como MOEA/D e IBEA por defecto.
- **Distancias alternativas** (L1, PCA blanqueada y rangos) y las features con objetivos sin
  escalar, presentadas como exploración.
- **Presupuestos de 5 000 y 10 000 evaluaciones**, solo descriptivos, porque las configuraciones se
  ajustaron para 20 000.

## 7. Recursos y ejecución

- **Ajuste:** 61 ejecuciones de irace (55 por problema y 6 generalistas) en NicoVM, con el servidor
  persistente de la fase 3 (31 procesos, `nice 19`) y `irace/launch.sh`. Estimación: unas 70 h.
- **Matriz:** `scripts/evaluate_3c.py`, 64 × 165 × 10 ejecuciones, unas 5 h. IBEA va aparte, con el
  VAMOS reparado.
- **Uso de NicoVM:** se lanza solo cuando está libre, con todos los núcleos menos uno.
- **Cualquier desviación** de este documento se registra en el informe de la fase.

## 8. Enmienda 1 (2026-10-27): referencia de configuraciones aleatorias del espacio

**Cuándo.** La pidió el usuario el 2026-10-27 para la tabla comparativa. Se registra mientras dura la
campaña de irace, antes de que exista ninguna c*_P, matriz o análisis de esta fase.

**Qué se añade.** Una referencia descriptiva, como la del §10 del informe de la fase 3:
- **Configuraciones:** las 37 que se muestrearon allí del mismo espacio invariante
  (`phase3/data/random_configs.json`, semilla 20261026).
- **Ejecución:** en los 165 problemas, con las semillas 5001–5010 y 20 000 evaluaciones
  (`evaluate_3c.py` con `PHASE3C_CONFIGS=random`).
- **Puntuación:** con el HVn de la matriz. No entran en la unión de frentes que lo normaliza, así que
  no cambian ningún otro valor ni las puertas.

**Qué se informa** (`scripts/random_configs_3c.py`): por partición, la media y la mediana de las
configuraciones aleatorias junto a los métodos, y la fracción de configuraciones aleatorias que
pierden más de 0.10 frente al oráculo.

**Lo que no cambia:** las puertas G4 y G5, los métodos y las particiones.

## 9. Enmienda 2 (2026-10-27): control positivo con cuatro protocolos, exploratorio

**Cuándo.** Se registra durante la campaña de irace, antes de que exista ninguna c*_P, matriz o
análisis de esta fase. Sigue al control positivo de la fase 3 (`phase3/report.md`, §12) y al punto
L2 de `plan.md`, §10.4.

**Por qué.** En la fase 3, la selección con features solo funcionó cuando el problema destino estaba
en el entrenamiento:
- con la partición por filas de MO-ELA, las features cerraron el 79–98 % del hueco;
- con el problema fuera, ningún selector superó al SBS.

En bbob-biobj la similitud se conoce, así que se puede medir la caída entre los dos casos.

**Qué se añade** (`scripts/positive_control_3c.py`). Dos tareas sobre las mismas filas y particiones:
- **selección entre NSGA-II, MOEA/D e IBEA por defecto,** con `sbs`, `nn1`, `knn3`, `rf_class` y
  `rf_regr`;
- **transferencia entre las c*_f** de las funciones presentes en el entrenamiento, con `sbs`,
  `landscape_1nn`, `knn_selector` y el oráculo.

Se aplican cuatro protocolos, de más a menos fuga:

| Protocolo | Entrenamiento | Equivale a |
|---|---|---|
| `rows` | 80/20 aleatorio de las 825 filas, 100 veces, semilla 20261027 | MO-ELA |
| `instance_out` | Todo salvo el problema destino; las otras instancias de su función se quedan | Los hermanos de Liefooghe 2021 |
| `function_out` | Todo salvo las tres instancias de la función destino | S3 |
| `group_out` | Los cinco pliegues por grupo de bbob | S2 |

**Qué se informa:** la media sobre funciones de:
- el HVn;
- el hueco cerrado, junto al hueco absoluto;
- el acierto (a menos de 0.01 del VBS);
- la fracción de filas cuyo vecino más cercano es de la misma función.

**Lo que no cambia:** las puertas G4 y G5, los métodos y las particiones de los §3–5.
