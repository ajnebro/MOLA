# Protocolo del estudio (v0, resultado de la fase 0) y propuesta de fase 1

Desarrolla las RQ1–RQ4 de `plan.md` §4 con lo aprendido en la fase 0. Los identificadores E* remiten a
`claims.csv`.

## 1. Catálogo de equivalencias y grupos de formulación

Todos los elementos de un grupo van **al mismo lado** de cualquier partición.

| Grupo | Miembros | Evidencia |
|---|---|---|
| rocket-injector | RE37 ≡ Goel2007 (idénticos); Vaidyanathan2004 (variante de 4 objetivos) | E11 |
| vehicle-crashworthiness | RE34 ≡ Liao2008 (idénticos) | E11 |
| ZCAT a M=2, funciones idénticas | {ZCAT3, ZCAT4}, {ZCAT5, ZCAT17}, {ZCAT7, ZCAT18, ZCAT20}, {ZCAT8, ZCAT9}, {ZCAT12, ZCAT15} | E23. Causa HIPOTESIS: `complicated_pareto_set=False` |
| LZ09 / UF | Las funciones de LZ09 reutilizadas en UF (CEC 2009) | Tesis §4.4.2. **HIPOTESIS**: la correspondencia exacta está por establecer |
| DTLZ2 / DTLZ4 | DTLZ4 es DTLZ2 con sesgo `x^100` | Por construcción; se trata como variante |
| bbob-biobj | Todas las instancias de una función (fNN) en un grupo; además, las funciones que comparten componente de un objetivo se marcan como "parientes" | Las instancias pueden diferir mucho entre sí (E17), así que **no son verdad de referencia** de similitud |
| Dimensiones y número de objetivos | La misma formulación con distinta D o M es el mismo grupo | Evita la fuga por escalado de un mismo problema |
| Transformaciones de unidades (RQ1) | Cada transformación afín pertenece al grupo de su problema original | Plan §5 |

Antes de cerrar el catálogo hay que repetir la detección de duplicados del E23 sobre cada suite nueva:
comparar las features de todos los pares, con la misma semilla y tolerancia relativa 1e-9.

## 2. Particiones y semillas

- **Escenarios de evaluación:**
  1. Otro muestreo del mismo problema (reconocimiento).
  2. Otra instancia de la misma formulación.
  3. Formulación excluida.
  4. Suite excluida.
- **Comparación obligatoria:** el mismo pipeline con una partición aleatoria 80/20, para cuantificar la
  fuga frente al protocolo de MO-ELA (E18).
- **Grupos de prueba final:** se fijan y se guardan con su hash **antes** de ajustar ningún método.
  RE/RWA, ya inspeccionados en la fase 0, solo sirven para desarrollo.
- **Semillas:** tres flujos independientes y registrados: muestreo (LHS), optimización (VAMOS) y
  partición o aprendizaje.
- **Tamaños de muestra (RQ2):** 100, 200, 500, 1000 y 200·D, cada uno con un LHS **independiente**,
  nunca prefijos de un LHS mayor. Se usan 10 semillas por tamaño.

## 3. Portafolio candidato (para decidir con Nebro)

- **Tamaño y algoritmos:** 8–12 pares (algoritmo, configuración) en VAMOS 1.0.0, con la versión y el
  backend fijados. Base: NSGA-II, SMS-EMOA y MOEA/D (DE), con la configuración por defecto, más 2–3
  variantes por algoritmo (índices de distribución, archivo externo, tamaño de población).
- **Invariancia de unidades (premisa de RQ1):** la cumplen los operadores por defecto según la lectura
  estática de E19. Antes de basarse en ella hay que confirmarla con una ejecución emparejada barata,
  con a = 2^k y b = 0.
- **Sin fuga:** si se ajustan configuraciones (Evolver, el tuner de VAMOS o meta-qdo), se hace sobre
  problemas que no aparezcan en ningún grupo de evaluación.
- **Puerta G2:** el VBS debe mejorar al SBS en al menos X puntos de HV normalizado en al menos Y % de
  los grupos. **X e Y se fijan antes de ejecutar** el piloto de la fase 2.

## 4. Comparadores (RQ3)

1. La configuración generalista (SBS de entrenamiento).
2. El vecino por metadatos: D, M y estadísticas de las cotas.
3. Un donante aleatorio.
4. La distancia de la tesis (ec. 4.1) sobre las 19 features compartidas, documentando sus casos
   indefinidos (E16).
5. Una distancia adaptada a cada tipo de feature: proporciones, correlaciones con signo y distancias
   con escala robusta.
6. Pesos aprendidos o un predictor de la pérdida de transferencia L(P→Q; b).
7. Un selector directo de configuraciones con las mismas features.

Cada método se ejecuta con los perfiles `raw` y `bound` y con las representaciones de 19 y de 49
features. Si hay código disponible, se añade MO-ELA como representación externa.

## 5. Presupuesto, controles y medidas

- **Presupuesto:** `B_total = B_caracterización + B_optimización + B_configuración_en_objetivo`. Las
  soluciones del muestreo se conservan en el archivo final.
- **Controles:**
  - La configuración generalista con todo el presupuesto.
  - El mismo muestreo inicial y la configuración generalista con el presupuesto restante.
  - Si el muestreo inicializa la población, la misma regla se aplica a todos los métodos.
- **Medidas:**
  - HV normalizado con referencia fija por problema, a partir de la unión de los frentes finales.
    Solo se usa para evaluar.
  - IGD+ donde haya un frente defendible.
  - Regret frente al VBS, mejora frente al SBS y frecuencia y tamaño de las pérdidas frente al SBS.
  - Curvas de cobertura frente a riesgo (RQ4).
  - Estabilidad de vecinos y recomendación (RQ2).
  - Evaluaciones y CPU de caracterización.
- **Estadística:** agregación por grupo de formulación y comparaciones emparejadas. Las semillas y los
  pares donante–destino no cuentan como observaciones independientes.

## 6. Estimación de coste (con tiempos medidos)

| Elemento | Medido en la fase 0 | Estimación |
|---|---|---|
| Caracterización con D ≤ 6 y n ≤ 1200 | 0.3–1.9 s por muestra (`pilot_meta.csv`) | — |
| Caracterización con D=30 y n=6000 | ~15 s, de los que el ranking de jMetalPy supone ~7 s y `local_nondominance` ~4.7 s (`evidence/profile_mola.py`) | ~3–5 s con `moocore.pareto_rank` (E10) y una `local_nondominance` vectorizada. **Estimación sin medir** |
| Malla de la RQ2 | — | ~150 problemas × 5 tamaños × 10 semillas = 7 500 caracterizaciones, del orden de 2–6 h de CPU en un núcleo |
| Ejecuciones de VAMOS | **No medido**: la fase 0 no permitía ejecutarlo | La primera tarea de la fase 2 es un micro-benchmark de tiempos; las estimaciones del piloto salen de ahí |

## 7. Propuesta de fase 1 (prioridad: corregir antes que añadir)

**Bloqueantes para generar la matriz de rendimiento:**
1. Sustituir `supported_mask` por un test exacto basado en programación lineal y fijar si se usa
   soportado o soportado extremo (E1–E3). Incluir los casos A, B y C como tests.
2. Añadir a `Sample` la validación de entradas no finitas y de cotas degeneradas (E9), y un estado con
   causa para cada feature indefinida.
3. Un perfil de geometría versionado (`raw` o `bound`) y un `k` explícito, ambos registrados en cada
   salida (E4, E6). Decidir el valor por defecto con Nebro.
4. Resolver el contrato de normalización de `dist_x_avg_neig` y `dist_f_avg_neig` (E5), y corregir las
   inconsistencias de documentación de E24.

**Infraestructura:**
5. CI con pytest, ruff y `mvn test` con jMetal 7.8 desde Maven Central (E7, E8).

**Rendimiento:**
6. Usar `moocore.pareto_rank` como backend de ranking (E10) y vectorizar `local_nondominance` (E22).

**Fuera de la fase 1:** regenerar los CSV históricos (se harán en una carpeta versionada cuando se
congelen las definiciones), RDF, selectores, adaptadores nuevos más allá de COCO y la integración con
VAMOS.

**Criterio de cierre (G1):** tests verdes, incluidos los nuevos A, B y C; concordancia con el
verificador exacto en DTLZ2 y RE33; los 49 valores para el perfil `bound` invariantes ante la
transformación afín de §6.4; y CI en verde.

## 8. Lo que no se debe afirmar con la evidencia actual

- Que los números concretos de la tesis o del grafo de moody salgan de moorphology `master` 9d57172:
  falta enlazar la versión (E13).
- Que las distancias vecinales sean, en general, las features más estables: E14 cubre 5 problemas.
- Que el reconocimiento entre remuestreos implique transferencia (E15).
- Que los operadores de VAMOS sean invariantes en la práctica: E19 es una lectura estática.
