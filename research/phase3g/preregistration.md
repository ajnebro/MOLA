# Pre-registro de la fase 3g — La recomendación frente a un generalista ajustado con irace

Fecha: 2026-10-31. Se fija **antes de ejecutar ningún ajuste de esta fase**. Corresponde a la
decisión D11 del usuario (`research/decisions/decisions.md`).

El análisis, `scripts/analyze_3g.py`, se sube con este documento. Solo se ha probado con frentes
sintéticos: copias de frentes de la matriz de la fase 3 renombradas como generalistas.

## 1. Motivación

En la fase 3 la referencia era el SBS: la mejor de las 37 configuraciones ajustadas por problema,
de media sobre el entrenamiento. El SBS depende de qué problemas hay en el portafolio. En casi todos
los pliegues salió c*_ZDT3.

La referencia estándar de la configuración por instancia es otra: un generalista ajustado sobre
todo el entrenamiento, como la configuración R de ISAC, la primera de Hydra o la "robusta" de
Belkhir et al. Este estudio la añade a la fase 3, con su misma matriz, sus particiones y sus
métodos.

**Lo que ya se sabe:**
- `knn_selector` queda por debajo del SBS (LOGO, −0.018; LOFO, −0.047).
- `knn_selector` supera a NSGA-II por defecto y al donante al azar (`research/phase3/report.md`).

**Lo que no se sabe:** el rendimiento del generalista irace, que es lo que este pre-registro fija
antes de conocerlo.

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Problemas | Los 37 de desarrollo de la fase 3 (`common.pilot_problems()`). Los 17 reservados no se tocan |
| Generalistas | `gen_lofo_<familia>`, uno por familia excluida, con irace sobre los problemas de desarrollo de las otras cuatro familias: `dtlz` (32 problemas), `lz09uf` (22), `rerwa` (34), `zcat` (27) y `zdt` (33). Además, `gen_all`, sobre los 37, solo para la evaluación final con los reservados. Listas y semillas en `data/generalist_tasks.json` |
| irace | 4.5, `maxExperiments = 20 000`, resto por defecto. Semillas 8100 (`gen_all`) y 8101–8105. El espacio invariante de NSGA-II de la fase 3 (`phase3/irace/parameters.txt`), NSGA-II por defecto como candidata inicial, el mismo *target runner* y las mismas cotas de normalización (`phase3/data/tuning_bounds.json`). Cada ejecución hace 20 000 evaluaciones con VAMOS 1.0.0 (`0a8bbb0`) y motor numpy |
| Evaluación | Cada generalista en los 37 problemas, con las semillas 5001–5010 y 20 000 evaluaciones (`scripts/evaluate_3g.py`) |
| HVn | El de la matriz de la fase 3, normalizado por la unión de los frentes finales de sus 40 configuraciones. Los generalistas no entran en esa unión, así que ningún valor de la fase 3 cambia |
| Métodos | Los de `analyze_transfer.recommend`, sin cambios. Se añaden tres (§4) |
| Ejecución | En NicoVM, cuando quede libre y después de la campaña y la matriz de la fase 3c: 31 procesos, 6 ajustes a la vez (`irace/launch.sh`) |

## 3. Particiones

Las de la fase 3: LOGO (32 grupos), LOFO (5 familias) y aleatoria 80/20 por problema (100
repeticiones, semilla 20261021). Para cada destino, el generalista es `gen_lofo` de **su familia**:
- **En LOFO** se entrena exactamente con el mismo conjunto que los métodos. Es la comparación limpia.
- **En LOGO y en la aleatoria** se entrena con un subconjunto del entrenamiento del pliegue, sin la
  familia del destino. No hay fuga, pero el generalista sale perjudicado: si aun así gana, la
  conclusión es más fuerte.

## 4. Métodos añadidos (`analyze_3g.recommend_3g`)

| Método | Definición |
|---|---|
| `generalist` (línea base 1) | `gen_lofo` de la familia del destino |
| `consensus_generalist` | El generalista, salvo que la configuración con mejor HVn medio en los 3 problemas de entrenamiento más cercanos le supere ahí en al menos 0.05. Es la regla de consenso de la fase 3, con el generalista irace en lugar del SBS |
| `distance_units` | La distancia al problema de entrenamiento más cercano, en unidades de ruido de remuestreo: la distancia mediana entre dos muestras de un mismo problema de entrenamiento, en el mismo espacio de escalado robusto |

Se informan también, como en D11: NSGA-II por defecto (línea base 2), el donante al azar (control
de ablación), el SBS (referencia secundaria), y el oráculo y la configuración propia (techos).

## 5. Puerta G6 (análisis principal)

**G6 (LOFO):** HVn(`knn_selector`) > HVn(`generalist`), con una prueba de Wilcoxon de rangos con
signo unilateral sobre los 32 grupos de formulación. El valor de cada grupo es la media sobre sus
destinos y muestras.

Se supera si la diferencia media es positiva y p < 0.05. Si no se supera, se informa como resultado
negativo. No se cambian el método, la distancia ni la regla para repetir la prueba.

**Expectativa, declarada antes de conocer el resultado:** es probable que no se supere. En LOFO,
`knn_selector` queda 0.047 por debajo del SBS, y se espera que el generalista irace iguale o supere
al SBS.

## 6. Análisis secundarios, descriptivos

Para cada partición (LOFO, LOGO y aleatoria):
- **El HVn medio** por método.
- **La pérdida frente al oráculo:** mediana, fracción mayor que 0.10 y media del peor 10 %.
- **Comparaciones bilaterales sobre los 32 grupos,** sin corregir y presentadas como exploración:
  - `knn_selector` frente al generalista, a NSGA-II por defecto y al donante al azar;
  - `consensus_generalist` frente al generalista;
  - el generalista frente a NSGA-II por defecto y frente al SBS.
- **Con qué frecuencia** la regla de consenso se aparta del generalista.
- **La ganancia de `knn_selector` sobre el generalista según `distance_units`,** en los tramos
  [0, 1.5], (1.5, 3], (3, 6] y más de 6. Es el análisis instancia a instancia de D11 (L13).

## 7. Recursos y desviaciones

- **Ajuste:** 6 ejecuciones de irace de 20 000 experimentos, 120 000 en total. Al ritmo de la fase 3,
  unas 10–15 h en NicoVM.
- **Evaluación:** 6 configuraciones × 37 problemas × 10 semillas, 2 220 ejecuciones, del orden de
  minutos.
- **Recogida:** `scripts/collect_3g.py` recoge las élites en `data/tuned_configs.json`.
- **Cualquier desviación** de este documento se registra en el informe de la fase.
