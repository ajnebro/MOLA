# Pre-registro de la fase 3 — Transferencia de configuraciones (RQ3, puerta G3)

Fecha: 2026-10-20. Se fija **antes de que exista la matriz de rendimiento cruzada**. Cuando se escribe:
- el ajuste con irace de las c*_P está en marcha en NicoVM;
- no hay ningún resultado de transferencia con estas configuraciones.

El código del análisis, `scripts/analyze_transfer.py`, se sube con este documento y solo se ha
probado con datos sintéticos. Cualquier cambio posterior se registra como desviación.

Instrucciones del usuario del 2026-10-20 que se aplican aquí:
- "usa siempre irace";
- presupuesto de 20 000 o más;
- comprobar siempre que NicoVM no está ocupado.

## 1. Alcance

- **Pregunta (RQ3):** ¿la configuración del problema más parecido según el paisaje es mejor que las
  alternativas, en formulaciones y familias no vistas?
- **Datos:** solo los 37 problemas de desarrollo. Los 17 reservados para test (hash `7c97fa68…`) no
  se tocan hasta la fase 5.

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Problemas | Los 37 de `common.pilot_problems()`, todos biobjetivo |
| c*_P | irace 4.5 con `maxExperiments = 20 000` por problema y el resto de opciones por defecto (incluido `nbIterations`). Semilla 8000 + índice del problema. Espacio NSGA-II invariante (`runs.invariant_nsgaii_space()`), con NSGA-II por defecto como candidata inicial. Cada ejecución hace 20 000 evaluaciones con VAMOS 1.0.0 (`0a8bbb0`) y motor numpy |
| Objetivo del ajuste | HV con normalización min-max por el ideal y el nadir del frente de Pareto verdadero (`data/tuning_bounds.json`: analítico en DTLZ, LZ09 y UF6, y el de referencia de VAMOS en el resto) y punto de referencia 1.1 |
| Matriz | Las 37 c*_P más NSGA-II, MOEA/D y SMS-EMOA por defecto (población 100), en los 37 problemas, con 10 semillas de evaluación (5001–5010) y 20 000 evaluaciones |
| HVn | HV de cada frente final, con la misma normalización y referencia que el ajuste, dividido entre el HV de la unión de todos los frentes finales de la matriz en ese problema. HVn(c, Q) es la media de las 10 semillas |
| Caracterización | MOLA 0.3.0 con geometría `bound` y k = D: las 5 muestras LHS de la etapa A de la fase 2 (`phase2/data/pilot_features.csv`). Cada problema de entrenamiento se representa por la media de sus 5 muestras. El problema destino se evalúa con cada una de sus 5 muestras por separado |

## 3. Grupos y familias

- **Grupos de formulación:** los de `phase2/catalogue.csv`, más los parientes estructurales de
  LZ09/UF. Estos se identificaron en la etapa A de la fase 2 por las confusiones de 1-NN entre sus
  muestras, antes de que existieran datos de transferencia:
  - {UF1, LZ09_F2, LZ09_F9};
  - {UF2, LZ09_F5};
  - {LZ09_F7, LZ09_F8}.

  Las confusiones entre funciones ZCAT no se usan para agrupar. Son una limitación de las
  features, no un parentesco de formulación: agruparlas haría la definición circular.
- **Familias:** ZDT, DTLZ, LZ09/UF, ZCAT y RE/RWA.

## 4. Métodos (`analyze_transfer.recommend`)

Para un destino Q y un conjunto de entrenamiento T, los candidatos son las c*_P con P ∈ T.

| Método | Elige |
|---|---|
| `sbs` | La candidata con mejor HVn medio sobre T |
| `metadata_1nn` | c*_P del P más cercano por metadatos: log D y media y desviación típica del log del rango de las cotas, estandarizados sobre T |
| `random` | Valor esperado de un donante uniforme |
| `thesis_1nn` | c*_P del P más cercano con la distancia de la tesis (ec. 4.1) sobre sus 19 features, omitiendo los términos indefinidos |
| `landscape_1nn` | c*_P del P más cercano con distancia euclídea sobre las 49 features, con escalado robusto (mediana y rango intercuartílico de las muestras de T). Se descartan las features indefinidas en alguna muestra de T o en Q. **Es el método de paisaje principal** |
| `loss_predictor` | El donante con menor pérdida predicha. La pérdida L(A→B) se predice con una regresión ridge (λ = 1) sobre \|z(A) − z(B)\|, ajustada con los pares ordenados de T |
| `knn_selector` | La candidata con mejor HVn medio sobre los 3 problemas de T más cercanos según la misma distancia. Es un selector directo con las mismas features |
| Referencias | `oracle` (la mejor candidata en Q), `self` (c*_Q) y `default` (NSGA-II por defecto) |

## 5. Particiones

- **LOGO:** se deja fuera un grupo de formulación cada vez.
- **LOFO:** se deja fuera una familia cada vez.
- **Aleatoria:** 100 particiones 80/20 por problema, ignorando los grupos (semilla 20261021), para
  medir la fuga que introduce el protocolo de MO-ELA.

## 6. Puerta G3 (análisis principal)

**G3 se supera si, en LOGO, la media por grupo de HVn(`landscape_1nn`) − HVn(`metadata_1nn`) es
positiva y una prueba de Wilcoxon de rangos con signo unilateral sobre los grupos da p < 0.05.**

Si no se supera, se informa como resultado negativo (`plan.md` §6) y se analiza por qué con los
análisis secundarios. No se cambia la representación ni la distancia para repetir la prueba.

## 7. Análisis secundarios, descriptivos

- **Todos los métodos y particiones:** HVn medio en LOGO, LOFO y aleatoria, y regret frente al
  oráculo.
- **Estrato discriminativo:** los grupos en los que el oráculo supera al SBS en LOGO por al menos
  0.01.
- **Estimación de la fuga:** la ganancia de `landscape_1nn` sobre el SBS en la partición aleatoria
  frente a LOGO y LOFO.
- **Estabilidad (RQ2 parcial):** la fracción de destinos cuyo donante de `landscape_1nn` es el mismo
  en las 5 muestras.
- **Comparaciones adicionales** de `knn_selector`, `loss_predictor` y `thesis_1nn` frente a
  `metadata_1nn` y al SBS, sin corrección por multiplicidad y presentadas como exploratorias.

## 8. Recursos

- **Ajuste:** unas 740 000 ejecuciones en NicoVM, con 31 procesos persistentes (`run_server.py`) y
  `nice 19`. Estimación: ~20 h.
- **Matriz:** unas 14 800 ejecuciones, alrededor de 30 min.
- **Uso de NicoVM:** antes de cada lanzamiento se comprueba que está libre.

## 9. Enmienda 1 (2026-10-20, antes de que exista la matriz)

**Motivo.** El usuario preguntó cómo se decide si un problema se parece a otro. Al calcular los
vecinos más cercanos con el método principal, aparecieron distancias desproporcionadas: 98 536 para
DTLZ3, 116 para RE21, frente a 0.5–3 entre problemas comparables. La causa es que 4 features de
hipervolumen (`hv`, `hv_avg_neig`, `hvd_avg_neig`, `nhv_avg_neig`), además de `dist_f_max` y las
`diff_f_*`, están en las unidades de los objetivos y varían hasta 7 órdenes de magnitud entre
problemas. Con ellas, el vecino lo decide la escala de los objetivos, no el paisaje. Esta inspección
solo usó features, sin ningún dato de rendimiento ni de transferencia.

**Comprobación previa.** Con un escalado exacto de cada objetivo por potencias de dos, NSGA-II
(todos los operadores del espacio de ajuste) y MOEA/D por defecto producen poblaciones idénticas bit
a bit (`data/objective_invariance.csv`). SMS-EMOA por defecto no es invariante, porque desplaza su
punto de referencia 1.0 en unidades absolutas, pero solo es un comparador y no forma parte del
portafolio. Como las configuraciones que se transfieren no ven las unidades de los objetivos, la
representación tampoco debe verlas.

**Cambio, decidido por el usuario.** MOLA 0.4.0 añade el perfil `objective_scaling = "sample"`, que
escala cada objetivo a [0, 1] según su mínimo y su máximo en la muestra (MO-ELA hace lo mismo). Con
él, las 49 features son invariantes a cambios afines positivos de las unidades de cualquier objetivo.
Las mismas 185 muestras de la etapa A se vuelven a caracterizar con ese perfil
(`data/features_sample_scaled.csv`). Cambian 17 features, todas las que dependen de las unidades de
los objetivos. Las de dominancia, rangos y Spearman no cambian.

- **Todos los métodos de paisaje** (`thesis_1nn`, `landscape_1nn`, `loss_predictor` y
  `knn_selector`) usan las features escaladas.
- **Nuevo secundario: `landscape_1nn_raw_objectives`.** Es `landscape_1nn` con las features sin
  escalar, para mostrar qué cambia la enmienda.
- **La regla de G3 no cambia** (§6): `landscape_1nn` frente a `metadata_1nn` en LOGO, con Wilcoxon
  unilateral sobre los grupos y p < 0.05.

## 10. Enmienda 2 (2026-10-26): IBEA sustituye a SMS-EMOA como comparador sin ajustar

**Cuándo.**
- La decidió el usuario el 2026-10-26 ("sustituye SMS-EMOA por IBEA donde se use").
- La matriz ya tenía 259 pares de configuraciones ajustadas y ningún algoritmo por defecto.
- SMS-EMOA nunca llegó a ejecutarse en esta matriz: se paró y se relanzó sin él.
- Se registra antes de cualquier análisis o inspección de la matriz: no se ha calculado ningún HVn,
  ninguna pérdida de transferencia ni G3.

**Hallazgo y reparación.** El IBEA de VAMOS calculaba su indicador ε por defecto sobre los objetivos
sin escalar, con κ = 1.
- En VAMOS 1.0.0 (`0a8bbb0`) además ponía a 0 las contribuciones que se desbordaban.
- En RE21 la población colapsa en un solo punto: HV 0.110 frente a 0.881 de NSGA-II.
- Tampoco era invariante a las unidades de los objetivos (`data/objective_invariance_ibea_vamos0a8bbb0.csv`).

Se reparó en VAMOS, en la rama `fix/ibea-epsilon-scaling` (PR vamos-optimization/VAMOS#115):
- `3089157e`: el escalado adaptativo de Zitzler y Künzli (2004) para los dos indicadores;
- `c4569f25`: κ = 0.05 por defecto.

El IBEA reparado es invariante bit a bit a las unidades de objetivos y variables
(`data/objective_invariance_ibea.csv` y `phase2/data/invariance_ibea.csv`).

**Cambio.**
- **Matriz:** las 37 c*_P, NSGA-II por defecto y MOEA/D por defecto (VAMOS 1.0.0, `0a8bbb0`), más
  IBEA por defecto (población 100) con el VAMOS de `c4569f25`. Son 40 configuraciones.
  - IBEA se ejecuta aparte, después del resto, con las mismas semillas (5001–5010) y 20 000
    evaluaciones (`scripts`: `evaluate_pilot.py` con `PHASE2_DEFAULT_ALGORITHMS=ibea` y ese VAMOS
    por delante en `PYTHONPATH`).
  - Los 37 problemas de desarrollo son idénticos en los dos VAMOS. Los cambios reales entre ambos
    solo afectan a CF1, welded beam y RE9x, que no están en el piloto.
- **HVn:** la unión de frentes que lo normaliza incluye IBEA en lugar de SMS-EMOA.
- **`analyze_transfer.py`:** usa `default__nsgaii`, `default__moead` y `default__ibea`.

**Lo que no cambia:**
- la regla de G3 (§6);
- los métodos (§4): ninguno usa los algoritmos por defecto, salvo la referencia `default`, que es
  NSGA-II;
- las particiones y los análisis secundarios.
