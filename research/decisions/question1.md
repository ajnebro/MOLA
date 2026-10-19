# Question 1 — Default geometry and origin of the configuration portfolio

Options laid out on 2026-10-19, after phase 0. The decision taken is recorded in
[`decisions.md`](decisions.md) (D1–D3). The text below is the analysis exactly as it was presented
(in Spanish).

---

Son dos decisiones de naturaleza distinta. La geometría es barata de cambiar: es un perfil y se recalcula en segundos. El portafolio es caro: fija qué ejecuciones haces y qué pregunta responde el artículo.

## 1. Geometría por defecto

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| **A. `raw`** (lo actual) | Grafo y distancias sobre las variables tal cual | Mantiene la continuidad con los CSV y con FEATURE_ANALYSIS. Si todas las variables tienen las mismas cotas, como en el artículo ([−5,5]^d), solo cambian 7 features y por un factor constante | Depende de las unidades: con cotas heterogéneas, el grafo solo comparte el 6–12 % de los vecinos con el normalizado, y la recomendación puede cambiar aunque el optimizador se comporte igual |
| **B. `bound`** | X se lleva a [0,1]^D con las cotas declaradas | Es la única opción **verificada como invariante**: ante cambios afines por variable no cambia ninguna de las 49 features. Además es como "ve" el problema VAMOS, cuyos operadores trabajan relativos a las cotas, y lo que hace MO-ELA, lo que facilita compararse con su trabajo | Depende de que las cotas declaradas sean razonables: unas cotas artificialmente anchas comprimen la región útil. Las variables fijas (cota inferior igual a la superior) hay que excluirlas. Rompe la continuidad numérica con lo ya publicado |
| **C. Híbrida** | Grafo normalizado, distancias en bruto | El grafo es invariante y los máximos quedan en unidades del problema | Las 15 features que miden distancias en X siguen dependiendo de las unidades, y la mezcla es difícil de interpretar |
| **D. Normalización por la muestra** | Min-max o z-score de la X muestreada, o una transformación por rangos | No depende de las cotas declaradas. Con rangos es invariante ante cualquier transformación monótona | Con LHS, el min-max de la muestra coincide casi exactamente con B. Los rangos deforman las distancias y hacen que la geometría dependa de cada muestra |

**Recomendación:** B por defecto para el recomendador y el artículo, conservando A como perfil `paper-raw` para reproducir los resultados ya publicados y la tesis. C y D entran como variantes de la RQ1, no como alternativas por defecto. El tamaño de vecindad `k = D` lo mantendría por comparabilidad, y probaría k ∈ {1, D, 10} dentro de la RQ1.

## 2. Origen del portafolio

| Opción | A favor | En contra |
|---|---|---|
| **1. Algoritmos por defecto en VAMOS** (NSGA-II, SMS-EMOA, MOEA/D y, para tres objetivos, NSGA-III o RVEA) | Sin ajuste y sin fuga; barato; es el mismo portafolio que MO-ELA, así que la comparación es directa | Se convierte en selección de algoritmos más que en transferencia de configuraciones, lo que se aleja de la línea de la tesis. Hay riesgo de poca complementariedad (que la puerta G2 falle) |
| **2. Variantes diseñadas a mano** (archivo externo, versión estacionaria, distintos índices de SBX y PM, tamaños de población) | Barato e interpretable; la diversidad se introduce a lo largo de ejes conocidos | Elección arbitraria; la complementariedad no está garantizada |
| **3. Ajustadas con Evolver** (jMetal) sobre un conjunto disjunto | Es la línea de Aldana-Martín y Nebro, y produce el tipo de configuraciones que usaba recommoonder | Está en Java. Una configuración de Evolver no se traslada tal cual a VAMOS, así que toda la matriz de rendimiento tendría que ejecutarse en jMetal. Es caro, y el conjunto disjunto quita problemas a la evaluación |
| **4. Ajustadas con el tuner de VAMOS** (racing y random incluidos; optuna, SMAC3 y BOHB como extras) | Se generan y evalúan en el mismo framework, sin traslados; VAMOS es rápido | Pierde el vínculo con Evolver. También exige un conjunto disjunto |
| **5. Una configuración ajustada por problema de entrenamiento** (lo que hacía la tesis) | Es la prueba más pura de "transferir la configuración del problema más parecido" | El coste crece de forma cuadrática: cada configuración ajustada hay que evaluarla en todos los problemas. Además, hay que reajustar si un problema pasa a test |
| **6. Portafolio construido por complementariedad**, eligiendo de forma voraz, de un conjunto grande de candidatas, las que más acercan al VBS (o usando el archivo de meta-qdo, sección 5.9 de la tesis) | Maximiza el margen SBS–VBS, que es justo lo que G2 exige. meta-qdo es también trabajo de la tesis | Requiere más ingeniería; meta-qdo es código de investigación temprano |

Hay dos reglas que valen para cualquier opción:
- **Generar y evaluar en el mismo framework.** Un "NSGA-II con SBX" de jMetal y otro de VAMOS no son la misma configuración.
- **Elegir cómo evitar la fuga:** construir el portafolio con problemas que no se evalúan nunca (barato, pero pierdes problemas) o reconstruirlo dentro de cada partición de entrenamiento (lo más limpio, pero caro).

**Recomendación por etapas:**
1. Piloto con 1 + 2 en VAMOS: barato, sin fuga, y sirve para medir el hueco SBS–VBS (puerta G2).
2. Si el hueco es pequeño, pasar a la opción 6: candidatas generadas con el tuner de VAMOS sobre un conjunto disjunto y selección por complementariedad.
3. Un experimento lateral pequeño con la opción 5, en 10–20 problemas, para enlazar con el capítulo 7 de la tesis.
4. Evolver (opción 3) solo si Nebro y Aldana-Martín prefieren mantener jMetal como línea. En ese caso, toda la campaña se ejecuta en jMetal.

## Qué preguntar a Nebro

1. ¿Acepta que MOLA cambie a `bound` por defecto, sacando una nueva versión y conservando `paper-raw` para reproducir lo publicado?
2. ¿Los experimentos se ejecutan en VAMOS o en jMetal? De eso depende si Evolver forma parte del portafolio.
3. ¿El artículo se plantea como transferencia de configuraciones ajustadas por problema (opción 5, la línea de la tesis) o como selección sobre un portafolio fijo (opciones 1, 2 y 6, más barata y comparable con MO-ELA)?

La tercera es la que más condiciona el artículo.
