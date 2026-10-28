# Estado del arte: notas por trabajo (revisión del 2026-10-27)

Se leyó el texto completo de cada trabajo, no solo el resumen. Las inferencias propias se marcan como
"(inferencia)" y lo no encontrado en el texto, como "no encontrado". El resumen y las acciones están
en `plan.md`, §10.

## Selección de algoritmos multiobjetivo con features

### Liefooghe et al., GECCO 2021 — las 49 features que implementa MOLA
- **Tarea:** clasificar el mejor algoritmo y predecir el HV de cada uno.
  - **Portafolio:** NSGA-II, GDE3, MOEA/D-DE-DRA y DECMO2++, con los ajustes recomendados en la
    literatura (sin ajustar).
  - **Ejecución:** población de 200 (300 en MOEA/D), 50 000 evaluaciones y 100 ejecuciones.
- **Benchmark:** 1 200 problemas MO-ICOP generados en X = [−5, 5]^d: 50 por celda, con d ∈ {5, 10,
  20, 30} y k ∈ {1, …, 6}.
- **Features:** las 49, sobre un LHS de 200·d puntos; 500 puntos bastan.
- **Modelo:** random forest de R con los parámetros por defecto.
- **Protocolo:** 50 repeticiones de submuestreo aleatorio 80/20. Hay 50 problemas por celda (d, k),
  así que en entrenamiento y test hay problemas del mismo generador con los mismos parámetros
  (inferencia). No hay test agrupado ni fuera de distribución.
- **Resultados:**
  - Acierta el mejor de media en más del 75 % y uno de los estadísticamente mejores en más del 85 %.
  - Queda a menos del 0.5 % del VBS.
  - No hay diferencia significativa con usar los parámetros ocultos del generador.
  - Mucho mejor que usar solo d: error ≈ 0.2 frente a 0.35–0.43.
- **Hueco SBS–VBS:** pequeño, ≈ 3 % (leído de la figura).
- **Limitaciones que declaran:** solo biobjetivo y un solo generador. `dist_f_*` está muy
  correlacionada con k.

### Liefooghe et al., EMO 2023 — DBMOPP
- **Tarea:** regresión del rendimiento y clasificación del mejor por presupuesto, entre NSGA-II, IBEA,
  MOEA/D y búsqueda aleatoria, todos por defecto.
- **Benchmark:** 945 configuraciones del generador × 30 instancias = 28 350.
- **Features:** **no usa features de paisaje**, solo los 7 parámetros del generador.
- **Protocolo:** 30 × 10-fold CV sobre las configuraciones, siempre dentro del mismo generador.
- **Resultados:** R² mediano > 0.85 y acierto mediano > 0.75; regret 0.0016–0.0044.
  - Según la figura, la ventaja sobre IBEA es de ~5× con 5 000 evaluaciones y de ~2× después; el
    texto dice "un orden de magnitud".
- **Lo que dejan abierto:** "sensitivity of algorithm parameters, and their joint impact with problem
  features", que es exactamente nuestra pregunta.

### Cosson et al., EvoCOP 2021 — features por descomposición
- **Tarea:** regresión de la desviación de HV de tres variantes de MOEA/D.
- **Benchmark:** 1 000 instancias ρmnk combinatorias.
- **Protocolo:** 90/10 aleatorio, repetido 50 veces.
- **Resultados:** mérito (RS − VBS)/(SBS − VBS), con el SBS elegido en entrenamiento. Un 0 es el
  VBS y un 1, el SBS.
  - Con features de caja negra el mérito es 0.29–0.37: cierran un 63–71 % del hueco.
  - Con el modelo de caja blanca sobre (ρ, k) es 0.41, así que las features igualan o mejoran a los
    parámetros del generador.
  - El error frente al mejor de media es ≈ 36 %, pero el error estadístico solo ≈ 3 %, porque casi
    todo son empates.

### MO-ELA (Preuß, Rook, Bossek y Trautmann, arXiv 2602.00098, 2026)
- **Tarea:** clasificar el mejor de NSGA-II, SMS-EMOA y MOEA/D, por defecto y sin ajustar.
- **Benchmark:** 1 165 problemas:
  - bi-objetivo: bbob-biobj (92 funciones, instancia 1), ZDT, DTLZ y MPM2;
  - tri-objetivo: MPM2 y DTLZ;
  - con d ∈ {2, 5, 10, 20}.
- **Features:** 279/292 (las de Liefooghe más nuevas). Escalan X por las cotas y F con min-max sobre
  la muestra, como nuestros perfiles `bound` y `sample`. Selección forward-backward. Las features se
  calculan con 4 tamaños de muestra × 20 semillas.
- **Modelos:** SVM, XGBoost (el mejor) y RF.
- **Protocolo:**
  - **80/20 aleatorio** sobre filas (función × d × tamaño × semilla) con la etiqueta por función.
    Así, la misma función queda en entrenamiento y test con features casi idénticas (inferencia).
  - **El modelo final se elige en el conjunto de test.**
  - No hay análisis agrupado.
- **Resultados (RI = hueco cerrado):**

  | Conjunto | RI |
  |---|---|
  | Biobjetivo, global | 0.963 |
  | BBOB | 0.446 |
  | DTLZ | 0.94 |
  | ZDT | 0.98 |
  | Triobjetivo, global | 0.272 |
  | MPM2 triobjetivo | −0.11 (peor que el SBS) |
  | d = 2 | puede ser negativo |

- **Hueco SBS–VBS absoluto:** no se da.
- **Lectura:** el RI global, al ser un cociente de sumas, lo dominan las instancias con huecos
  grandes (inferencia).

### van der Blom y Vermetten, arXiv 2605.04954 (v3, 2026)
- **Tarea:** selección por instancia en optimización de un objetivo, con portafolios de 22 algoritmos
  de Nevergrad y de 4 elegidos por complementariedad.
- **Benchmarks:** BBOB, MA-BBOB y RandOptGen.
- **Protocolo:** "leave-instance-out". Evitan expresamente "leave-problem-out" porque eso mide la
  generalización fuera de la distribución.
- **Resultados:**
  - El 11–28 % de la pérdida total se debe al presupuesto gastado en features.
  - En MA-BBOB, con un SBS fuerte, el selector pierde frente al SBS; los portafolios pequeños y
    complementarios lo recuperan.
  - "BBOB is too easy to meaningfully differentiate between AS techniques". Advierten del riesgo de
    sobrestimar con protocolos inadecuados.

## Configuración por instancia

### Belkhir et al., GECCO 2017 (y PPSN 2016, con DE)
- **Cómo configuran:** un modelo de rendimiento (random forest) sobre (features, θ) → rendimiento. Para
  un problema nuevo, se busca en rejilla el mejor θ según el modelo.
- **Datos:** entrenan en BBOB y prueban en 21 funciones independientes, con dimensiones hasta 100.
- **Features:** con 50·d muestras.
- **Resultados:** ~20 % de mejora sobre CMA-ES por defecto con d > 8.
  - En PPSN 2016, con *leave-one-function-out*, el modelo supera a la configuración "robusta", que es
    un SBS ajustado con SMAC en todas las funciones, en casi todas las funciones con d = 5.
- **Dónde falla:**
  - funciones sin nada parecido en el entrenamiento ("the training set should cover all the
    foreseeable difficulties");
  - d = 100, fuera del rango de entrenamiento;
  - 10·d muestras, que no bastan.
- **Relevancia:** es el único de los revisados que prueba con funciones no vistas, y es justo donde
  aparecen los fallos.

### Prager et al., IEEE SSCI 2020 (CMA-ES modular)
- **Cómo configuran:** se ejecutan las 4 608 configuraciones de módulos; una cadena de 11 random
  forests predice cada módulo a partir de features ELA (50·D muestras, mediana de 10 cálculos).
- **Protocolo:** *leave-one-instance-out* en BBOB, así que la función siempre está en el
  entrenamiento.
- **Resultados (relERT):**

  | Método | relERT |
  |---|---|
  | SBS | 28.26 |
  | Cadena de random forests | 16.02 |
  | HCMA | 9.19 |

  Antes de ajustar sus hiperparámetros, la mayoría de las cadenas pierden frente al SBS. En F15–F19
  gana el SBS.

### ISAC (Kadioglu et al., ECAI 2010)
- **Cómo configuran:** agrupan las instancias por features (g-means) y ajustan una configuración por
  grupo (GGA), más una R sobre todo el entrenamiento.
- **Cómo eligen:** el grupo más cercano si la instancia está dentro de la media + 2 desviaciones de
  las distancias del grupo; si no, R (≈ 9 % de los casos).
- **Resultados:** supera a GGA sobre todo en SAT, set covering y MIP, pero siempre dentro de la misma
  distribución.
- **Su argumento contra la sobreespecialización:** "tuning on a collection of instances helps prevent
  over-tuning".

### Hydra (Xu, Hoos y Leyton-Brown, AAAI 2010)
- **Cómo construyen el portafolio:** de forma voraz. La primera configuración es el SBS. Cada nueva se
  ajusta sobre todo el conjunto, pero puntúa max(la suya, la del portafolio): solo cuenta donde
  mejora al portafolio.
- **Cómo eligen:** con SATzilla (regresión por solver).
- **Resultados:** reduce mucho el PAR-10 frente a una sola configuración ajustada (por ejemplo,
  RAND 631 frente a 1 167), dentro de las mismas distribuciones.

## Antecedente directo: tesis de Aldana-Martín (2024), recommoonder

- **Cómo recomienda:** devuelve la configuración del problema más parecido (1-NN). La distancia es la
  ec. 4.1, sin pesos, sobre 21 features. La base de conocimiento son 66 problemas, con M = 2 a 9,
  ajustados con irace o Evolver.
- **Evaluación:** 4 casos, sin partición ni línea base salvo NSGA-II por defecto, y solo con
  comparación visual de frentes.
  - Los dos éxitos son casi duplicados que ya estaban en la base: Liao2008 = RE34 y Goel2007 ≈ RE37.
  - Xu2020, sin un parecido claro, muestra una diferencia "poco apreciable".
- **Ideas que propone:**
  - un umbral de confianza con una alternativa por defecto;
  - filtrar por (n_obj, n_var) antes de buscar similitud;
  - pesos aprendidos para las features.
- **Advertencias:** reconoce que las features de distancia vecinal son inestables, pero las mantiene.

## Comprobación de publicación y trabajos afines (2026-10-27)

### Estado de MO-ELA
- **Sigue siendo un preprint:** arXiv 2602.00098, solo la v1, del 24 de enero de 2026. No tiene
  referencia de revista ni comentario de envío en arXiv. Un buscador atribuye el comentario
  "submitted to Computational Optimization and Applications", pero no aparece ni en la ficha ni en el
  listado de arXiv, así que queda **sin confirmar**.
- **Código:** el texto no incluye ningún enlace a repositorio ni declaración de disponibilidad. Solo
  cita las herramientas que usa (ecr, moeadr, mlxtend, scikit-learn y XGBoost).
- **Consecuencia:** no podemos usar sus features como representación alternativa (L4 y la vía 3)
  mientras no publiquen el código. En el artículo hay que citarlo como preprint.

### Trabajos afines que faltaban

| Trabajo | Qué aporta | Relevancia para nosotros |
|---|---|---|
| Cenikj, Petelin, Seiler, Cenikj y Eftimov, "Landscape features in single-objective continuous optimization: have we hit a wall in algorithm selection generalization?", *Swarm and Evolutionary Computation* 94, 101894 (2025), doi:10.1016/j.swevo.2025.101894 | Con datos fuera de la distribución, "none of the feature-based AS models outperform a simple baseline model, i.e., a Single Best Solver". Lo prueban con ELA, TLA y representaciones profundas (DeepELA, TransOptAS y Doe2Vec) | **El resultado más cercano al nuestro**, en un objetivo y con selección de algoritmos. Nuestro negativo con particiones agrupadas no es una anomalía |
| Nikolikj, Kostovska, Cenikj, Doerr y Eftimov, "Generalization ability of feature-based performance prediction models: a statistical analysis across benchmarks", IEEE CEC 2024 (arXiv 2405.12259) | La generalización de un modelo depende de lo parecidas que sean las distribuciones de features de entrenamiento y test | Sostiene la puerta de confianza por distancia (L7 y L8): se puede medir antes si el destino está "dentro de la distribución" |
| Gjorgjieva, Tuba, Koroušić Seljak, Doerr y Eftimov, "On the structural (dis)agreement of landscape representations in black-box optimization", IEEE CEC 2026 (arXiv 2605.28121) | ELA, DeepELA, TransOptAS y DoE2Vec organizan los mismos problemas de forma distinta, y ninguna captura del todo el rendimiento | La similitud depende de la representación. Apoya la RQ7 y el cribado de features (L9) |
| Feurer et al., "Auto-sklearn 2.0: hands-free AutoML via meta-learning", JMLR (2022), arXiv 2007.04074 | En AutoML, sustituyen el arranque por los k conjuntos de datos más parecidos según meta-features por una cartera fija y diversa, construida de forma voraz, y la cartera gana | **El análogo en AutoML de nuestra hipótesis y de nuestro resultado.** Justifica el portafolio complementario (L6) frente a la recuperación por similitud |
| Lindauer y Hutter, "Warmstarting of model-based algorithm configuration", AAAI 2018 | Reutilizan el rendimiento en conjuntos de instancias anteriores para arrancar la configuración en uno nuevo (SAT; hasta 165 veces más rápido) | Una alternativa a transferir la configuración: transferir conocimiento para **arrancar** irace en el problema nuevo |
| Long, Frenzel, Krause, Gitterle, Bäck y van Stein, "Landscape-aware automated algorithm configuration using multi-output mixed regression and classification", PPSN 2024 (arXiv 2409.01446) | Una red predice la configuración a partir de features, entrenada con funciones generadas al azar y MA-BBOB, y probada en BBOB. Suele superar a la configuración por defecto y a veces compite con el SBS | Configuración por instancia con features, un objetivo. Igual que nosotros: supera al default, no claramente al SBS |
| Rook, Benjamins, Bossek, Trautmann, Hoos y Lindauer, "MO-SMAC: multi-objective sequential model-based algorithm configuration", *Evolutionary Computation* (2025), doi:10.1162/evco_a_00371 | Configuración con varios criterios a la vez | Es configuración, no transferencia. Sus autores sugieren usar features de paisaje dentro del modelo sustituto |
| Seiler, Kerschke y Trautmann, "Deep-ELA", *Evolutionary Computation* (2025), doi:10.1162/evco_a_00367 | Features aprendidas por un transformer, para uno y varios objetivos | Una representación alternativa con código publicado (a comprobar) |
| Seiler, Preuß y Trautmann, "RandOptGen", GECCO 2025, doi:10.1145/3712256.3726478 | Generador aleatorio de problemas de uno y varios objetivos | Una vía para generar muchas instancias si se quiere ampliar S1 o probar el régimen de la literatura |

**No se encontró** ningún trabajo que transfiera configuraciones ajustadas entre problemas
multiobjetivo según la similitud de su paisaje. El hueco que ocupa nuestro artículo sigue abierto.
La búsqueda no es sistemática; antes de enviar conviene revisar las actas de GECCO 2026, EMO 2025 y
CEC 2026.

### Detalle de Cenikj et al. 2025 (leído el 2026-10-28, texto completo de arXiv 2501.17663v1)
- **Tarea:** selección entre variantes configuradas de DE y PSO (portafolios 5DE, 5PSO, 5DE+5PSO y
  2DE+2PSO), con presupuesto fijo de 100 iteraciones. Un objetivo.
- **Problemas:** 8 280 combinaciones afines de pares de funciones de BBOB (5 instancias de las 24
  clases, α ∈ {0.25, 0.5, 0.75}).
- **Features:** ELA (62, flacco), TinyTLA, Doe2Vec, TransOptAS y DeepELA, sobre un LHS de 50·d.
- **Modelo:** random forest de regresión multisalida (scikit-learn, 100 árboles, sin ajustar).
- **Línea base:** un modelo "dummy" que predice el rendimiento medio de cada algoritmo en
  entrenamiento, es decir, el SBS. No informan del VBS.
- **Cuatro particiones, de fácil a difícil:** instancia fuera, aleatoria, combinación con una clase
  fuera y clases fuera (ninguna de las dos clases del test aparece en entrenamiento).
- **Mejora mediana de ELA sobre el SBS** (métrica en [0, 1], mayor es mejor):

  | Partición | 5DE+5PSO | 2DE+2PSO | 5DE | 5PSO |
  |---|---|---|---|---|
  | Instancia fuera | +0.041 | +0.067 | +0.032 | +0.011 |
  | Aleatoria | +0.039 | +0.064 | +0.033 | +0.007 |
  | Combinación con una clase fuera | +0.032 | +0.030 | +0.013 | +0.001 |
  | Clases fuera | −0.011 | −0.009 | +0.006 | −0.004 |

- **Matiz:** la frase "ninguno supera al SBS" se refiere a la partición más difícil, y es
  aproximada: en 5DE, ELA queda +0.006 por encima, una diferencia despreciable. Las demás
  representaciones quedan por debajo de ELA, y combinarlas no mejora.
- **Su explicación:** la similitud de features solo coincide con la similitud de rendimiento cuando
  es muy alta, así que los modelos funcionan casi solo con casi duplicados del entrenamiento.
- **Relevancia:** su escalera de particiones coincide con la nuestra (instancia fuera ≈ S1, función
  fuera ≈ S3, grupo fuera ≈ S2), y su tarea (variantes configuradas de una misma familia) está más
  cerca de la nuestra que la de MO-ELA.
