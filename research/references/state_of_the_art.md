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
