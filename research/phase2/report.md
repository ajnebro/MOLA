# Informe de la fase 2 — Piloto

Fecha: 2026-10-20 · Rama `research/phase2` · MOLA 0.3.0 · VAMOS 1.0.0 (`0a8bbb0`, motor numpy) ·
Pre-registro: `preregistration.md` (commit `b99b9ac`, anterior a cualquier ajuste).

## 1. Resultado

**G2: superada según la regla pre-registrada, aunque por poco.**

| Medida | Valor |
|---|---|
| Grupos con hueco (donante oráculo − SBS) ≥ 0.01 | 12 de 36 (33 %; umbral, 25 %) |
| Bootstrap sobre grupos (10 000 réplicas), intervalo del 90 % de esa fracción | 0.19–0.47; en el 89 % de las réplicas es ≥ 0.25 |
| Sensibilidad al umbral X | 36 % con 0.005, 17 % con 0.02, 14 % con 0.05 |
| Con 5 000 / 10 000 / 20 000 evaluaciones | 28 % / 50 % / 33 % |

**Dónde está el margen.** Los huecos grandes se concentran en cinco problemas multimodales o de
convergencia difícil, donde el generalista falla y algún donante no:

| Problema | HVn del SBS | HVn del mejor donante | HVn de su propia c*_Q |
|---|---|---|---|
| DTLZ6 | 0.000 | 0.995 | 0.986 |
| DTLZ3 | 0.158 | 0.668 | 0.152 |
| UF5 | 0.148 | 0.654 | 0.508 |
| UF3 | 0.502 | 0.752 | 0.698 |
| ZDT4 | 0.803 | 0.982 | 0.980 |

En los demás problemas casi todas las configuraciones rinden igual. ZCAT, RE/RWA, DTLZ2/4 y ZDT2/3
tienen huecos por debajo de 0.005, y seis de los doce grupos que pasan lo hacen por menos de 0.01 de
margen sobre el umbral. **Conclusión operativa:** hay margen para la transferencia, pero está en
pocos problemas. Un recomendador solo puede mostrar valor si acierta precisamente en ellos, y la
evaluación de la fase 3 debe informar por estrato (problemas "fáciles" frente a "difíciles"), no
solo en media.

**Generalista (SBS).** La c*_P de ZDT1 es el SBS para 34 de 37 destinos (HVn medio 0.889). Supera a
NSGA-II por defecto (0.871), a SMS-EMOA por defecto (0.856) y a MOEA/D por defecto (0.715).

## 2. Qué se hizo

| Tarea | Resultado | Commit |
|---|---|---|
| Entorno | VAMOS fijado en `0a8bbb0` (instalado desde `git archive`, sin tocar el repositorio, que tiene trabajo en curso en Studio; el núcleo no cambia desde ese commit) y entorno reproducible en `C:\tmp\mola-phase2` | — |
| Catálogo y reserva | 59 problemas biobjetivo continuos. Duplicados exactos: DTLZ2 ≡ DTLZ5 con M = 2, y los 5 grupos ZCAT del E23, confirmados también en VAMOS. Hay 17 problemas reservados para test (todo WFG y un 25 % de los grupos de ZDT, DTLZ y ZCAT), con hash | `5cdd45a` |
| Micro-benchmark | Con 20 000 evaluaciones: NSGA-II, ~1.1 s; configuraciones muestreadas, mediana 1.4 s (hasta 15 s); MOEA/D, ~14 s; SMS-EMOA, ~17 s; MOLA, ≤ 6 s por caracterización | `b99b9ac` |
| Invariancia de VAMOS (E19) | Confirmada ejecutando, con excepciones (§3.1) | `b99b9ac` |
| Pre-registro de G2 | Antes del ajuste | `b99b9ac` |
| Etapa A: estabilidad | 37 × 5 caracterizaciones (§3.2) | `0809865` |
| Etapa B: ajuste | 37 F-Races, 11 240 ejecuciones, 90 min de reloj | `a332e19` |
| Etapa C: evaluación cruzada | 40 configuraciones × 37 problemas × 5 semillas = 7 400 ejecuciones, 72 min | `4905dcc` |

## 3. Hallazgos

### 3.1 Invariancia de VAMOS ante cambios de unidades (E19)

Con un escalado por variable a_i = 2^k_i, la misma semilla da resultados **idénticos bit a bit** en:
- NSGA-II, MOEA/D y SMS-EMOA con sus valores por defecto;
- 8 de los 10 cruces y 7 de las 9 mutaciones;
- 5 de las 6 reparaciones y 5 de los 6 inicializadores;
- todas las selecciones y proporciones de descendencia.

**No son invariantes:**
- los cruces PCX y UNDX, que usan direcciones que mezclan variables;
- las mutaciones gaussiana y de Cauchy, con escala absoluta;
- la reparación `round`;
- el inicializador Halton, que difiere en ZDT1 y no en UF1.

Se excluyeron del espacio de ajuste para mantener la premisa de la RQ1 (T5). La RQ1 queda así
respaldada para el portafolio del estudio, pero no para el espacio completo de VAMOS.

### 3.2 Estabilidad de la caracterización (etapa A)

- **Variación entre problemas y dentro de cada problema:**
  - La mayoría de las features varían mucho más entre problemas que entre muestras de uno mismo: la
    mediana de la proporción de varianza entre problemas es 0.99.
  - Las más ruidosas son `fdc` (0.60), `supp_n` (0.71) y `nd_per_plo` (0.73).
  - 46 de las 49 están definidas en las 185 muestras.
- **Reconocimiento:** solo el 63 % de las muestras tiene como vecina más cercana otra muestra del
  mismo problema. Los fallos se concentran en dos familias:
  - **LZ09/UF:** UF1 con LZ09_F2 y LZ09_F9, UF2 con LZ09_F5, y LZ09_F7 con LZ09_F8;
  - **ZCAT:** sus funciones se confunden entre sí.
- **Estabilidad del donante:** el problema de otro grupo más cercano es el mismo en las 5 muestras
  para 21 de 37 problemas (moda media del 81 %).

**Implicación:** el parentesco LZ09/UF, hasta ahora una hipótesis, tiene apoyo empírico. En 8 de los
15 destinos LZ09/UF el mejor donante es de esa misma familia. En la fase 3 hay que agrupar esos
pares para que no se cuenten como transferencia lejana.

### 3.3 Ajuste por problema (D2)

- **Configuraciones ganadoras:**
  - NSGA-II por defecto gana en 5 problemas (DTLZ1, UF4, ZCAT11, ZCAT13 y ZCAT19).
  - En los otros 32 ganan configuraciones diversas: SBX en 20, BLX en 9, aritméticos en 5; mutación
    Lévy en 10 y polinómica en 8; población de 22 a 197; 8 de ellas casi estacionarias
    (`offspring_ratio = 0`).
- **El ajuste no siempre encuentra lo mejor para su propio problema.** En DTLZ3, c*_Q obtiene 0.15
  mientras la configuración ajustada para UF5 obtiene 0.67; en UF5, c*_Q obtiene 0.51 frente a 0.65.
- **Causa probable:** la normalización del ajuste se calibró con NSGA-II por defecto. En problemas
  donde no converge, el nadir calibrado queda muy lejos del frente; en DTLZ3 es (8.4, 6.4) frente a
  un frente real hacia (1, 1). Eso comprime la señal del HV.

### 3.4 Comparadores sin ajustar

- **Medias:** MOEA/D por defecto queda 0.14 de media por debajo del SBS y SMS-EMOA por defecto
  0.002.
- **Problemas difíciles:** ambos superan al SBS en ≥ 0.01 en 5–6 de ellos, por ejemplo MOEA/D en
  DTLZ6 por 0.99 y SMS-EMOA en ZDT4 por 0.13.
- **Implicación:** diversificar el algoritmo añadiría margen justo donde ya lo hay.

## 4. Desviaciones respecto al plan y al pre-registro

1. **Racing clásico en lugar de iterado (antes del pre-registro):**
   - `RacingTuner` con `use_elitist_restarts=True` falla en VAMOS 1.0.0. Lanza `KeyError` en
     `vamos/engine/tuning/racing/refill.py:25` (`make_neighbor_config`) en cuanto un parámetro
     condicional, como `mutation_eta`, no está en la configuración base.
   - Se usó F-Race con 60 configuraciones iniciales.
   - Es un fallo de VAMOS que conviene corregir allí.
2. **El espacio de ajuste excluye los operadores no invariantes** (T5, antes del pre-registro).
3. **El hueco puede ser negativo en problemas concretos.** Con validación cruzada, el donante
   oráculo elegido con 3 semillas puede rendir peor que el SBS en las otras 2. Es lo esperado y no
   se recortó.
4. **Análisis no pre-registrados:** `secondary_g2.py` (identidades, bootstrap y comparadores) es
   descriptivo y se añadió después de ver G2. No cambia la regla ni el veredicto.
5. **Frentes en bruto:** 33 MB en 1 480 ficheros. Se quedan en `C:\tmp\mola-phase2\raw\fronts` con
   sus hashes en `data/raw_fronts_SHA256SUMS`. El repositorio guarda los frentes de referencia por
   problema (`data/reference_fronts.npz`), que fijan la normalización.

## 5. Coste

| Etapa | Evaluaciones | Reloj (8 procesos) |
|---|---|---|
| Catálogo y duplicados | ~0.3 M | ~5 min |
| Micro-benchmark | 8.3 M | 4.5 min |
| Invariancia | 1.5 M | ~10 min |
| Etapa A | 0.85 M | 1.6 min |
| Calibración y ajuste | 3.7 M + 224.8 M | 90 min |
| Etapa C | 148 M | 72 min |
| **Total** | **≈ 387 M** (funciones analíticas) | **≈ 3.3 h**, ~20 h de CPU |

La máquina se comprobó antes de cada etapa pesada (`check_load.ps1`: CPU < 35 %, ≥ 8 GB libres y
memoria comprometida ≤ 85 %).

**Estimación para la fase 3 con los tiempos medidos:**
- Una configuración ajustada tarda de media 3.8 s por ejecución (con 8 procesos en paralelo) y un
  ajuste unos 1 000 s de CPU por problema.
- Con los 59 problemas del catálogo, la matriz completa (59 × 59 × 5) más el ajuste cuesta unas 34 h
  de CPU, unas 4–5 h de reloj con 8 procesos.
- Añadir MOEA/D y SMS-EMOA multiplica el coste por ejecución por 4–8.

## 6. Recomendaciones para la fase 3

1. **Recalibrar la normalización del ajuste** con frentes mejores que los de NSGA-II por defecto: por
   ejemplo, las uniones de esta fase (`reference_fronts.npz`) o los frentes de referencia de VAMOS.
   Volver a ajustar DTLZ3 y UF5 como mínimo.
2. **Agrupar LZ09/UF por parentesco**, con la correspondencia que sugiere la etapa A, antes de usar
   esa familia para medir transferencia.
3. **Informar de los resultados por estrato** (problemas con hueco grande frente a pequeño) y no solo
   en media, porque el margen se concentra en pocos problemas.
4. **Valorar un portafolio con MOEA/D y SMS-EMOA ajustados.** G2 se supera sin ellos, pero añadirían
   margen precisamente en los problemas difíciles.
5. **Comunicar a VAMOS** el fallo de `refill.py` y la no invariancia de PCX, UNDX, gaussiana, Cauchy
   y Halton.

## 7. Qué no se debe afirmar

- Que el paisaje permita recomendar: G2 solo mide si hay margen, no si MOLA lo aprovecha (RQ3).
- Que el 33 % sea robusto: depende del umbral (17 % con 0.02) y de cinco problemas difíciles.
- Que las c*_P sean óptimas: en DTLZ3 y UF5 el ajuste falló.
- Que los resultados valgan para tres objetivos: el piloto es solo biobjetivo.

**PHASE2_COMPLETE.**
