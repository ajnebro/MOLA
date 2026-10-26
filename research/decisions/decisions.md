# Registro de decisiones

Cada decisión indica quién la tomó, cuándo, qué alternativas se descartaron y qué implica. Las
alternativas completas para D1–D3 están en [`question1.md`](question1.md).

## D1 — Geometría por defecto: `bound` (opción 1B)

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** MOLA caracteriza por defecto con X llevado a [0,1]^D mediante las cotas declaradas,
  tanto para construir el grafo de vecinos como para medir distancias. La geometría en bruto se
  conserva como opción explícita (`raw`).
- **Motivo:** es la única geometría verificada como invariante ante cambios afines por variable (E6:
  ninguna de las 49 features cambia). Coincide con la referencia en la que trabajan los operadores de
  VAMOS (E19) y con MO-ELA (E18).
- **Implicaciones:**
  - Los valores dejan de coincidir con los CSV de `examples/benchmarks/` y con FEATURE_ANALYSIS.md,
    que siguen correspondiendo a MOLA 0.2.0 (`58bc0ca`). Para reproducirlos exactamente hay que usar
    ese commit. La geometría `raw` de la nueva versión reproduce la elección geométrica, pero con las
    definiciones ya corregidas.
  - Las variables fijas (cota inferior igual a la superior) necesitan un tratamiento explícito.
  - Cada salida registra la geometría y `k`.
- **`k`:** se mantiene `k = D` por defecto, por comparabilidad con el artículo; k ∈ {1, D, 10} queda
  como factor de la RQ1.

## D2 — Portafolio: una configuración ajustada por problema de entrenamiento (opción 2.5)

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** el artículo se plantea como **transferencia de configuraciones**, que es la línea de
  la tesis (recommoonder). Para cada problema de entrenamiento P se ajusta una configuración c*_P. Para
  un problema nuevo Q se recomienda la configuración de su donante más similar. El portafolio es la
  unión de las c*_P de entrenamiento.
- **Descartadas, salvo como comparadores o controles:** algoritmos por defecto (opción 1), variantes a
  mano (2), Evolver (3), un portafolio genérico ajustado (4) y la construcción por complementariedad
  (6). La configuración por defecto y la generalista (SBS) siguen siendo comparadores obligatorios de
  la RQ3.
- **Implicaciones:**
  - **Coste cuadrático:** cada c*_P se evalúa en todos los problemas de evaluación, con
    |entrenamiento| × |evaluación| × semillas ejecuciones, además de una ejecución de ajuste por
    problema de entrenamiento. El tamaño del estudio (número de problemas, presupuesto de ajuste,
    semillas) se fija con el micro-benchmark de tiempos de VAMOS, que es la primera tarea de la fase 2.
  - **Fuga:** c*_P solo puede ajustarse con P. Si un problema pasa de entrenamiento a evaluación en otra
    partición, su configuración no se usa como donante de su propio grupo de formulación. Los alias y
    variantes (E11, E23) comparten grupo.
  - **La puerta G2 sigue vigente:** hay que medir el hueco entre la mejor c*_P única y el VBS sobre las
    c*_P. Si las configuraciones ajustadas apenas se distinguen entre sí, no queda margen para la
    transferencia.
  - **Para los métodos 6 y 7 de la RQ3** se necesita la matriz cruzada completa del rendimiento de c*_P
    sobre Q.

## D3 — Ejecutor: VAMOS

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** todas las ejecuciones de optimización y el ajuste por problema de D2 se hacen en
  VAMOS (1.0.0, fork local en `0a8bbb0`), con la versión y el backend fijados. Por la regla de generar
  y evaluar en el mismo framework, el ajuste de D2 usa el tuner de VAMOS (racing por defecto; el
  backend concreto se decide en la fase 2).
- **Implicaciones:**
  - Evolver y jMetal quedan fuera de la campaña. El adaptador Java de MOLA se mantiene solo como
    productor del formato de intercambio.
  - La invariancia de los operadores de VAMOS ante cambios de unidades (E19, por lectura estática) se
    confirma ejecutando antes de la RQ1.
  - VAMOS se usa como dependencia externa de los experimentos y no se modifica desde este proyecto.

## Decisiones técnicas de la fase 1 (tomadas al implementar; reversibles)

- **T1 — Definición de punto soportado (revisada al implementar):** un punto no dominado es
  soportado si minimiza alguna suma ponderada con pesos **estrictamente positivos**, admitiendo
  empates (los puntos soportados de Ehrgott). Equivale a que ninguna combinación convexa del conjunto
  lo domine. Incluye los puntos soportados no extremos (caso B), que es la intención de CLAUDE.md
  ("findable by minimizing some linear scalarization", "lies on a facet"). La versión 0.2.0
  implementaba en la práctica la variante extrema, y además con los fallos E1 y E3.
  - **Por qué no pesos no negativos, como decía la primera redacción de T1:** con un peso nulo, una
    meseta en un objetivo hace soportados a todos los puntos empatados en ella. En RE33 hay 17 puntos
    no dominados con f3 = 0 (la violación de restricciones). Con pesos no negativos, `supp_n` sale
    0.258, solo por el peso (0, 0, 1); con pesos estrictamente positivos sale 0.185, igual que el
    extremo. El caso de la meseta (0,6,6), (0,0,10), (0,10,0) es un test.
  - **Por qué admitir empates:** en RE41, con 213 puntos no dominados empatados en el mínimo de f2,
    `supp_n` vale 0.882 con empates y 0.008 con soportado extremo. La versión 0.2.0 daba 0.027.
  - **Implementación:** tres métodos exactos, elegidos por M solo por velocidad: cadena convexa para
    M = 2; normales de las facetas de conv(P) + R^M_≥ para M = 3 y 4; un programa lineal por punto
    para M ≥ 5 o si Qhull falla. Los tests comprueban que coinciden en conjuntos aleatorios con
    empates, mesetas y duplicados. Los objetivos se escalan a [0, 1] en el conjunto y la tolerancia
    es 1e-9 en esas unidades.
- **T2 — Contrato de normalización (E5):** `dist_x_avg_neig` y `dist_f_avg_neig` se normalizan con
  el rango global de distancias de su espacio, como establece la decisión "Normalization reference" de
  CLAUDE.md y como hacían la tesis y moorphology. Se corrige el código, no la documentación.
  - Los dos cocientes son el cociente de las features tal como se reportan:
    `dist_f_dist_x_avg_neig` divide las dos normalizadas, y `diff_f_dist_x_avg_neig` divide
    `diff_f_avg_neig` (en bruto) por `dist_x_avg_neig` normalizada. Si el denominador es 0, el
    resultado es NaN, con causa, en lugar de una excepción.
  - Las medidas por solución de las correlaciones de rugosidad siguen en bruto, porque la
    normalización min-max no es monótona sobre un cociente por solución.
- **T3 — Perfil de features y procedencia:** las definiciones de 0.3.0 se identifican como
  `paper49-v1` (`mola.report.FEATURE_PROFILE`). `characterize_report()` y `mola ... --report`
  registran la versión, el perfil, la geometría, el `k` y el número de caminatas usados. Las features
  indefinidas llevan `value: null`, `status: "undefined"` y una causa, según el contrato del
  recomendador. `characterize()` y `--output` mantienen el formato plano de 52 campos de 0.2.0.
- **T4 — Backend de ranking:** `moocore.pareto_rank` sustituye al `FastNonDominatedRanking` de
  jMetalPy (E10), con un test que compara ambos con empates y duplicados. Una caracterización de ZDT1
  con D = 30 (n = 6000) pasa de 26 s a 3.9 s. El test de dominancia por pares entre vecinos sigue
  usando el comparador de jMetalPy, que no es un cuello de botella.

## Decisiones técnicas de la fase 2 (tomadas al implementar; reversibles)

- **T5 — Espacio de configuraciones invariante:** se ajusta sobre el espacio de NSGA-II de VAMOS sin
  PCX, UNDX, las mutaciones gaussiana y de Cauchy, la reparación `round` y el inicializador Halton.
  Son los operadores que, ejecutando, rompen la identidad bit a bit ante cambios de unidades por
  variable (`research/phase2/data/invariance.csv`). Así se mantiene la premisa de la RQ1 para todo el
  portafolio. El resto del espacio y los algoritmos por defecto sí son invariantes.
- **T6 — F-Race clásico:** se usa racing sin reinicios elitistas porque `use_elitist_restarts=True`
  falla en VAMOS 1.0.0 (`racing/refill.py:25`, `KeyError` con parámetros condicionales). Son 60
  configuraciones iniciales, la por defecto incluida, y 20 bloques de semillas, con un máximo de 400
  ejecuciones por problema.
- **Resultado de G2 (fase 2):** superada según la regla pre-registrada, con 12 de 36 grupos (33 %)
  frente al umbral del 25 %. El margen se concentra en problemas multimodales. Ver
  `research/phase2/report.md`.

## D4 — Escalado de objetivos `sample` para el recomendador

- **Fecha y autor:** 2026-10-20, decisión del usuario (opción 1 de la consulta sobre cómo medir el
  parecido entre problemas).
- **Decisión:** el recomendador caracteriza los problemas con MOLA 0.4.0 y
  `objective_scaling = "sample"`, que escala cada objetivo a [0, 1] según su mínimo y su máximo en la
  muestra. MOLA mantiene `raw` por defecto, que son las definiciones del artículo.
- **Motivo:**
  - 17 features dependen de las unidades de los objetivos. Las de hipervolumen variaban hasta 7
    órdenes de magnitud entre problemas y decidían por sí solas el vecino más cercano: en DTLZ3 la
    distancia al más cercano era de 98 536.
  - NSGA-II, en todo su espacio de ajuste, y MOEA/D son invariantes bit a bit ante el escalado de
    los objetivos (`research/phase3/data/objective_invariance.csv`). Como lo que se transfiere no
    ve las unidades de los objetivos, la representación tampoco debe verlas.
  - Es la misma lógica que D1 aplica a las variables, y es lo que hace MO-ELA.
- **Implicaciones:**
  - Se aplicó como enmienda 1 al pre-registro de la fase 3, antes de que existiera la matriz.
  - SMS-EMOA por defecto no es invariante: su punto de referencia se desplaza 1.0 en unidades
    absolutas. Si alguna vez entra en el portafolio, hay que tenerlo en cuenta.

## D5 — Ajuste siempre con irace; NicoVM como máquina de cálculo

- **Fecha y autor:** 2026-10-20, instrucción del usuario: "Usa siempre irace. Usa budget de 20000, o
  más si lo consideras necesario. Siempre comprueba que NicoVM no está ocupado."
- **Decisión:**
  - Todo ajuste de configuraciones usa irace (≥ 4.4.4) con `maxExperiments` ≥ 20 000 por tarea.
    Cada ejecución sigue haciendo 20 000 evaluaciones.
  - Sustituye a T6 (F-Race), en línea con la fase 2b, donde irace superó a F-Race en 32 de 37
    problemas con el mismo presupuesto.
  - Antes de cada lanzamiento en NicoVM se comprueba que está libre, y nunca se detienen procesos
    ajenos.

## Decisiones técnicas de la fase 3 (tomadas al implementar; reversibles)

- **T7 — Normalización del objetivo de ajuste por el frente verdadero.** Se usan el ideal y el nadir
  del frente de Pareto verdadero: analítico en DTLZ, LZ09 y UF6, y el frente de referencia de VAMOS
  en el resto, contrastado con todos los frentes evaluados.
  - No se usa la unión de frentes evaluados porque contiene puntos extremos que estiran el nadir: en
    UF5, el nadir de f2 sería 2.52 en lugar de 1.
  - Al contrastarlo, el fichero de UF6 de VAMOS resultó incompleto: le falta el punto aislado (0, 1).
- **T8 — Servidor de ejecución persistente para irace.** El target runner es un cliente mínimo que
  envía cada experimento a 31 procesos con VAMOS ya cargado. Así se evita ~0.9 s de arranque de
  Python por experimento, unas 185 h de CPU en la campaña. Los resultados no cambian: misma función
  y mismas semillas.

## D6 — Réplica de la fase 3 en Evolver (jMetal)

- **Fecha y autor:** 2026-10-20, decisión del usuario: opción 2 ("las dos") y "todo [el] espacio del
  nsga-ii".
- **Decisión:**
  - La fase 3 se completa primero en VAMOS, tal como está pre-registrada.
  - Después se repite entera en Evolver/jMetal: caracterización con el adaptador Java de MOLA, ajuste
    con irace (≥ 20 000 experimentos, D5), matriz y el mismo análisis de G3. Así se generan y evalúan
    las configuraciones en el mismo framework en cada réplica.
  - El espacio de configuraciones es el de NSGA-II completo de Evolver, `NSGAIIDouble.yaml` (unos 32
    parámetros, el del artículo de Evolver).
- **Motivo:**
  - Es la línea de la tesis y del grupo de Nebro.
  - Evolver ya trae runners de irace y un servidor de evaluación.
  - Si la transferencia por paisaje se sostiene en dos frameworks, el resultado es más sólido.
- **Implicaciones:**
  - Hay que rehacer el catálogo, los duplicados, los frentes verdaderos y la comprobación de
    invariancia con las implementaciones de jMetal, que no son idénticas a las de VAMOS.
  - **Punto abierto, resuelto el 2026-10-21 por el usuario ("quita esos 4 parámetros").** La
    invariancia medida en jMetal 7.8 (`research/phase3e/data/jmetal_invariance.csv`) es esta:
    - **Objetivos:** todas las opciones de `NSGAIIDouble.yaml` son invariantes.
    - **Variables:** no lo son el cruce PCX, el cruce UNDC, el cruce de Laplace (escala absoluta) y
      la mutación uniforme (perturbación absoluta).
    - **Se excluyen esos cuatro operadores y sus parámetros:** `pcxCrossoverZeta`,
      `pcxCrossoverEta`, `undcCrossoverZeta`, `undcCrossoverEta`, `laplaceCrossoverScale` y
      `uniformMutationPerturbation`. El resto del espacio se mantiene completo.
    - **Lo que sí es invariante:** SDX, la reparación `round` (que en Evolver lleva el valor a la cota
      opuesta) y la inicialización Cauchy.
    - **La selección Boltzmann** discrepó en 1 de 4 casos, probablemente por el épsilon absoluto
      (1e-14) del SBX de jMetal con padres casi idénticos. Se mantiene.
    - **Diferencia con VAMOS:** en Evolver el tamaño de la población está fijo en 100, que es la
      convención de Evolver y de su artículo; en VAMOS se ajustaba en [20, 200].

## D7 — Orden de las preguntas de investigación

- **Fecha y autor:** 2026-10-26, decisión del usuario ("aplica el nuevo orden").
- **Decisión:** la transferencia pasa a ser la primera RQ. Orden nuevo:
  1. transferencia (antes RQ3);
  2. invariancia y geometría (antes RQ1);
  3. incertidumbre del muestreo (antes RQ2);
  4. cuándo recomendar (sin cambios).
- **Motivo:**
  - Es la pregunta del título y del resultado principal, y la única con una puerta pre-registrada
    (G3).
  - Las otras tres se miden con la pérdida de transferencia que ella define.
  - La invariancia está asegurada casi toda por diseño (D1, D4, T5, D6). Queda como análisis de
    sensibilidad.
  - El muestreo alimenta la última: la estabilidad entre muestras es una señal de confianza.
- **Alcance:**
  - Se renumera `plan.md` §4, que incluye la tabla de correspondencia.
  - Los documentos anteriores conservan la numeración antigua, porque están congelados: los
    pre-registros, los informes de las fases 0 a 3e, D1–D6 y T1–T8, y el prompt de la §9 del plan.
  - La regla de G3 no cambia, solo su etiqueta.
