# Informe de la fase 1 — Núcleo verificable

Fecha: 2026-10-19 · Rama `research/phase1` (en origin) · Base: `research/phase0` (`4114626`) ·
Versión resultante: MOLA 0.3.0.

Alcance: el de `research/phase0/protocol.md` §7, con las decisiones D1–D3 y T1–T4 de
`research/decisions/decisions.md`. No se han regenerado los CSV históricos.

## 1. Estado de la puerta G1

| Criterio (protocol.md §7) | Resultado |
|---|---|
| Tests verdes, incluidos los casos A, B y C | **Cumplido.** 216 tests de Python (152 en 0.2.0) y 32 de Java. A, B y C, además de la meseta, los duplicados, M = 1 y el conjunto vacío, están en `tests/test_hull.py` |
| Concordancia con el verificador exacto en DTLZ2 y RE33 | **Cumplido.** 0 discrepancias en `supp_n` global y 0 grupos locales discrepantes en `lnd` y `lsupp`, también en RE21, RE41, RE61 y Ahmad2017 (§3.1) |
| Las 49 features invariantes ante la transformación afín de §6.4 con el perfil `bound` | **Cumplido.** 0 features cambian en RE25, RE33 y RE42; la diferencia relativa máxima es de 1e-15. Con `raw` cambian 39 (§3.2) |
| CI en verde | **Cumplido.** Ruff y pytest en Python 3.11 y 3.12, y `mvn clean test` en Temurin 21 (§3.3) |

**G1: superada.**

## 2. Cambios

Veintidós commits atómicos, cada uno con los tests en verde:

| Punto de §7 | Commits | Qué cambia |
|---|---|---|
| 1. Soporte exacto (E1–E3) | `07afce3` fix, `f3b67f8` test | Soportado = minimizador de una suma ponderada con pesos estrictamente positivos, admitiendo empates (T1). Tres métodos exactos según M: cadena convexa (M = 2), facetas de conv(P) + R^M_≥ (M = 3, 4) y un programa lineal por punto (M ≥ 5 o si Qhull falla). Desaparecen el atajo `|P| ≤ M` y la aproximación ante `QhullError` |
| 2. Validación y estados (E9) | `544e13e` fix, `edc2307` test; `f680409` feat | `Sample` rechaza NaN e infinitos en X o F y las cotas invertidas. Cada feature indefinida lleva una causa en `characterize_report()` |
| 3. Geometría y `k` (E4, E6) | `44ee2d8` feat, `24aef59` test | `mola.geometry`: `bound` por defecto (D1) y `raw`. Se pueden fijar `neighbours=` y `-k`; ambos quedan registrados en el informe |
| 4. Normalización (E5) y documentación (E24) | `4cb42f3` fix, `e26afa7` test, `30cc8c4` docs | `dist_x_avg_neig` y `dist_f_avg_neig` se normalizan con el rango global de la muestra, y los cocientes usan los valores normalizados (T2). Se corrige la regla de NaN de `fdc` (\|ND\| ≤ 2) y la cita a una decisión "lnd/lsupp" inexistente. El docstring de las 30 caminatas se corrigió en `44ee2d8` |
| Informe y procedencia (T3) | `f680409` feat, `0100c5b` feat, `4a571d0` test | `characterize_report()` y `--report`: valor, estado y causa de cada feature, más la versión, el perfil `paper49-v1`, la geometría, `k` y las caminatas |
| 5. CI y `pom` (E7, E8) | `962cbdf` chore, `c8e939a` chore, `eb60516` chore | jMetal 7.8 de Maven Central, sin el repositorio de snapshots. `.github/workflows/ci.yml` |
| 6. Rendimiento (E10, E22) | `fd0d27b` refactor, `ab797dc` test, `79e7b14` refactor | Ranking con `moocore.pareto_rank` (con un test que lo compara con jMetalPy) y frentes locales con `moocore.is_nondominated` |
| 7. Documentación y versión | `cb0505b`, `a835515`, `041e8e7` docs; `5614319` chore | `decisions.md` (T1–T4), CLAUDE.md, README, llms.txt y la versión 0.3.0 |

`characterize()` y `--output` conservan el formato plano de 52 campos de 0.2.0. Los valores sí
cambian (§4).

## 3. Evidencia

Scripts en `scripts/` y datos en `data/`. Los resultados se reproducen con
`python research/phase1/scripts/g1_checks.py` y `python research/phase1/scripts/compare_versions.py`
desde la raíz del repositorio.

### 3.1 Concordancia con un verificador exacto independiente

El verificador (`g1_checks.py`) resuelve el programa lineal **primal** (maximizar el peso mínimo
t con Σw = 1 y w·(p_i − p_j) ≤ 0) y no importa `mola.hull`, que usa la formulación dual o la
geometría. Los frentes locales se calculan por fuerza bruta, sin moocore. Geometría `bound`, k = D
y semilla 42.

| Problema | M | Método de MOLA | \|ND\| | `supp_n` MOLA = verificador | Discrepancias globales | `lsupp_avg_neig` MOLA = verificador | Grupos discrepantes (`lnd` / `lsupp`) |
|---|---|---|---|---|---|---|---|
| RE21 | 2 | cadena convexa | 29 | 0.2069 | 0 | 0.5822 | 0 / 0 |
| DTLZ2 | 3 | facetas | 105 | 0.2095 | 0 | 0.4048 | 0 / 0 |
| RE33 | 3 | facetas | 124 | 0.1855 | 0 | 0.6375 | 0 / 0 |
| RE41 | 4 | facetas | 263 | 0.8821 | 0 | 0.9042 | 0 / 0 |
| RE61 | 6 | programas lineales | 600 | 1.0000 | 0 | 1.0000 | 0 / 0 |
| Ahmad2017 | 7 | programas lineales | 243 | 0.1358 | 0 | 0.9294 | 0 / 0 |

DTLZ2 reproduce el valor exacto de la fase 0 (0.405 frente al 0.370 de 0.2.0); como sus cotas son
[0,1], el grafo es el mismo. Los tests unitarios comparan además los tres métodos entre sí en
conjuntos aleatorios con empates, mesetas y duplicados.

### 3.2 Invariancia afín (transformación de la fase 0, §6.4)

Por variable, a ~ U(0.1, 50) y b ~ U(−10, 10), con el generador de semilla 3, aplicado a X y a las
cotas. Muestra con semilla 7.

| Problema | D | Features que cambian con `bound` | Diferencia relativa máxima | Features que cambian con `raw` |
|---|---|---|---|---|
| RE25 | 3 | 0 | 1.0e-15 | 39 |
| RE33 | 4 | 0 | 7.4e-16 | 39 |
| RE42 | 6 | 0 | 9.5e-16 | 39 |

### 3.3 CI

`.github/workflows/ci.yml` se ejecuta en cada push a `main` o `research/**` y en cada pull request.
La primera ejecución, sobre `c8e939a`, terminó en verde (run 39297812077), y también las del último commit de
código, `5614319` (run 39299509804), y de `eb60516` (run 39299700334), que pasa las acciones a
sus versiones con Node 24 para quitar el aviso de obsolescencia de Node 20.

## 4. Cuánto cambian los valores respecto a 0.2.0

Mismas muestras (semilla 42, n = 200·D) caracterizadas con 0.2.0 (`58bc0ca`) y con 0.3.0
(`compare_versions.py`; detalle por feature en `data/version_comparison.csv`).

| Problema | M | D | Cotas | Features distintas, 0.3.0 `raw` | Features distintas, 0.3.0 `bound` |
|---|---|---|---|---|---|
| ZDT1 | 2 | 5 | [0,1] | 4 | 4 |
| DTLZ2 | 3 | 12 | [0,1] | 6 | 6 |
| RE25 | 2 | 3 | heterogéneas | 4 | 39 |
| RE33 | 3 | 4 | heterogéneas | 6 | 39 |
| RE41 | 4 | 7 | heterogéneas | 7 | 39 |
| RE61 | 6 | 3 | heterogéneas | 5 | 26 |

- Con `raw` solo cambian las 4 features de distancia vecinal (por la normalización) y, donde el
  test antiguo fallaba, `supp_n`, `lsupp_avg_neig` y `lsupp_cor_neig`.
- Cambios en `supp_n`: RE41 pasa de 0.027 a 0.882 y RE61 de 0.498 a 1.000.
- Cambios en `lsupp_avg_neig`: DTLZ2 pasa de 0.370 a 0.405, y RE33, con `raw`, de 0.771 a 0.738.
  Este último es el valor "extremo" de la fase 0, porque los puntos que añadía la variante débil
  eran los de la meseta f3 = 0.
- Antes, `dist_f_avg_neig` estaba en las unidades de F: 926 488 en RE25 y 795 247 en RE61.
  Ahora está en [0, 1].
- Con `bound`, los problemas con cotas heterogéneas cambian en 26–39 features, como predecía E4.

## 5. Decisiones y desviaciones durante la implementación

1. **T1 cambia respecto a lo registrado antes de empezar:** pesos estrictamente positivos, no
   negativos. Con un peso nulo, una meseta en un objetivo hace soportados a todos sus puntos
   empatados (RE33: 0.258 frente a 0.185). Está razonado en `decisions.md` y lo cubre un test. Es
   una decisión técnica reversible, pero cambia una definición, así que conviene que la revise
   Nebro.
2. **No se ha vectorizado todo `local_nondominance`.** Con el ranking de moocore, lo que queda de
   su coste es el test exacto de soporte (unos 0.8 ms por grupo con M = 3). Una caracterización
   completa tarda 2.3 s en DTLZ2 (antes 5.9 s) y 3.9 s en ZDT1 con D = 30 (antes 26 s). La
   dominancia por pares entre vecinos sigue usando el comparador de jMetalPy, porque no es un cuello
   de botella.
3. **El test de soporte añade una vía de cálculo por número de objetivos.** Las facetas de
   conv(P) + R^M_≥ no son prácticas con M ≥ 5: el envolvente no terminó en 150 s con RE61 ni con
   Ahmad2017, mientras que los programas lineales tardan 2.2 s y 0.5 s.
4. **Con `raw` no se reproduce 0.2.0 exactamente**, porque las definiciones ya están corregidas.
   Los CSV de `examples/benchmarks/`, `FEATURE_ANALYSIS.md` y las salidas de `notebooks/` siguen
   siendo de 0.2.0. Así consta en CLAUDE.md y en el README, y no se han regenerado.
5. **Los mensajes de los dos primeros commits se rehicieron antes del push**, para quitar el ámbito
   (`fix(hull):` pasó a `fix:`), como pide `GIT_GUIDELINES.md`. El contenido no cambió.
6. **Comportamiento nuevo en la CLI:** con `bound`, una muestra con cotas infinitas da un error
   claro y hay que pasar `--geometry raw`. Entre los problemas de RE y RWA de jMetalPy, solo RE91
   tiene cotas infinitas, y el script de benchmarks ya lo omitía.

## 6. Coste

| Concepto | Evaluaciones | Tiempo |
|---|---|---|
| `g1_checks.py` | 9 200 | ~2 min (el verificador local domina) |
| `compare_versions.py` | 6 800 | ~2 min |
| Prototipos y perfiles durante el desarrollo, sin contador | ≈ 40 000 (estimación) | — |

Son funciones analíticas baratas. La fase 1 no tenía límite de evaluaciones; los prototipos se
estiman por las muestras que se generaron, una o dos por problema.

## 7. Qué no se debe afirmar

- Que MOLA 0.3.0 sea correcto en todo: G1 verifica el test de soporte, la invariancia y la
  normalización, no las 49 definiciones frente al código original de Liefooghe et al.
- Que `bound` sea la mejor geometría para la recomendación: es la única invariante ante cambios
  afines por variable, pero depende de que las cotas declaradas sean razonables. Lo evalúa la RQ1.
- Que los operadores de VAMOS sean invariantes en la práctica: E19 sigue siendo una lectura
  estática (fase 2).

## 8. Siguiente fase

La fase 2 (piloto) empieza con el micro-benchmark de tiempos de VAMOS, que fija el tamaño del
estudio según D2, y con la comprobación ejecutando la invariancia de VAMOS (E19). La puerta es G2:
el hueco entre la mejor configuración ajustada única y el VBS sobre las c*_P.

**PHASE1_COMPLETE.**
