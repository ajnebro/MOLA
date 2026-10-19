# Informe de la fase 0

Fecha: 2026-10-19 · Rama local `research/phase0` (sin commit ni push) · Referencia de MOLA `58bc0ca`
(coincide con `origin/main`).

El detalle de cada afirmación está en `claims.csv` (E1–E25), la correspondencia de features en
`feature_contract.csv` (51 filas), la afectación por fuente en `affectation_matrix.csv`, el contrato
de salida en `recommender_contract.md`, el protocolo y la fase 1 en `protocol.md`, y versiones y
hashes en `manifest.json`.

## 1. Hallazgos prioritarios

1. **`supported_mask` tiene tres defectos (E1–E3), y el más grave no estaba identificado.** La prueba
   de facetas no detecta vértices soportados: en el caso C marca como no soportado el único minimizador
   de f₃.
   - En DTLZ2 (n=2400), `lsupp_avg_neig` da 0.370 frente a 0.405 con el cálculo exacto, con 1 074
     falsos negativos locales.
   - En RE33, la definición de soportado importa: `supp_n` es 0.185 con soportado extremo y 0.258 con
     soportado. Los empates no son despreciables en ese problema.
2. **Geometría.** Con cotas heterogéneas (RE25, RE33, RE42), el grafo bruto comparte solo el 6–12 % de
   los vecinos con el normalizado por cotas, y cambian 39 de las 49 features. Con cotas homogéneas
   (RE36, COCO) el grafo es idéntico y cambian exactamente las 7 features de escala previstas en E6.
   - Cambiar solo el grafo altera exactamente las 34 features dependientes de la vecindad; `fdc` no
     está entre ellas, lo que confirma la corrección que se hizo a una afirmación anterior.
   - Con la geometría normalizada por cotas, una transformación afín por variable **no cambia ninguna**
     de las 49 features.
3. **Fallos de moorphology demostrados ejecutándolo** (`master` 9d57172, jMetal 6.1):
   - El ranking local sobrescribe el global (E13). En una misma ejecución, el rango máximo global vale
     34 (35 frentes) y el publicado 1 con D=2; con D=4, 40 frente a 3. La demostración aislada en
     jMetal 6.1 muestra `[0 1 2 3] → [0 1 0 1]`.
   - `sup + inf + inc` = (d−1)/d (E12).
   - Las correlaciones vecinales son otra estadística distinta de la del artículo (E21).
   - La normalización global difiere de la de MOLA (E25).
4. **La inestabilidad de las distancias vecinales de la tesis se debe al acumulador `=` (E14).** Sobre
   las mismas matrices X, el CV es del 16–68 % con `=` y del 0–3 % con `+=`. El alcance es de 5
   problemas.
5. **Datos con duplicados.** Los 72 problemas de MOLA contienen alias exactos: RE34 ≡ Liao2008 y
   RE37 ≡ Goel2007 (E11), y a M=2 cinco grupos de ZCAT idénticos (E23). Los 20 ZCAT de 2 objetivos son
   14 funciones distintas, que es exactamente el "14 valores distintos" que FEATURE_ANALYSIS
   interpretaba como capacidad de discriminación.
6. **VAMOS, por lectura estática (E19):** sus operadores por defecto (SBX, PM, DE, recorte e
   inicialización) son relativos a las cotas y, por tanto, invariantes ante cambios de unidades, salvo
   un épsilon absoluto de 1e-14 en SBX. Es la premisa de la RQ1; falta confirmarla ejecutándolo.

## 2. Clasificación de la evidencia

| Estado | Afirmaciones |
|---|---|
| REPRODUCIDO | E1, E2, E3, E4, E6, E7, E9, E10, E11, E12, E13 (mecanismo y salida de moorphology), E14, E15, E16, E17, E20, E22, E23, E25 |
| CONFIRMADO_EN_CODIGO | E5, E8, E19 (VAMOS, estático), E21, E24 |
| DOCUMENTAL | E18 (MO-ELA) |
| Pendiente o HIPOTESIS | Enlace entre moorphology 9d57172 y los números de la tesis y de moody (E13); causa de los duplicados ZCAT (E23); invariancia de VAMOS en ejecución (E19); generalidad de E14 |

## 3. Diferencias de definición (no son fallos de una implementación por sí mismas)

- **Soportado frente a soportado extremo.** MOLA coincide con el extremo en el caso B. CLAUDE.md
  describe la idea de "estar en una faceta minimizante", que incluye los puntos interiores.
- **`dist_*_avg_neig`:** MOLA devuelve la media en bruto; CLAUDE.md y moorphology la normalizan (E5).
- **`dist_x_avg` y `dist_f_avg`:** moorphology fija el mínimo en 0 e incluye la diagonal (E25), así
  que sus valores y los de MOLA no son comparables directamente.
- **Correlaciones vecinales:** son estadísticas distintas en moorphology y en MOLA (E21).

## 4. Cambios recomendados

Están en `protocol.md` §7. **Bloqueantes:** test de soporte exacto, validación de entradas y estados de
indefinido, perfil de geometría versionado con `k` explícito, y contrato de normalización.
**Infraestructura:** CI y jMetal 7.8. **Rendimiento:** moocore y vectorización. No se regeneran los CSV
históricos hasta congelar las definiciones.

## 5. Límites de estas conclusiones

- El piloto cubre 5 problemas (D ≤ 6) y 3–5 semillas; no permite generalizar sobre estabilidad.
- El reconocimiento entre remuestreos (`pilot_similarity.csv`) no es transferencia. Los cocientes (a),
  dentro frente a media de los demás, y (b), dentro frente al vecino distinto más cercano, se reportan
  por separado.
- El LHS de moorphology no es reproducible con `JMetalRandom.setSeed` (E20): los números históricos no
  se pueden regenerar bit a bit.
- La invariancia de VAMOS (E19) y la causa de los duplicados ZCAT (E23) no se han comprobado
  ejecutando.

## 6. Coste y desviaciones

| Concepto | Evaluaciones | Tiempo |
|---|---|---|
| Comprobaciones (`checks.py`) | 3 800 | 179 s |
| moorphology en Java (original e instrumentado) | 2 400 | ~4 s |
| Piloto (`pilot.py`) | 12 200 | 40 s |
| Scripts de verificación del agente del contrato | 14 000 | no registrado |
| **Total** | **32 400** | todo el cómputo, muy por debajo de los 60 min |

**Desviaciones:**
- **Se superó el límite de 25 000 evaluaciones:** el agente que redactó el contrato hizo sus propias
  comprobaciones y no le transmití el límite. Son funciones analíticas baratas y no alteran ningún
  resultado, pero es un incumplimiento del alcance pactado.
- **JDK:** el PATH lista un JDK 21 que no está instalado; se usó Temurin 24.0.2.
- `plan.md` y `research/` siguen sin commit.

## 7. Reproducción

```bash
# venv con Python 3.12 (C:\Users\nicor\AppData\Local\Programs\Python\Python312\python.exe)
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]" coco-experiment
.venv/Scripts/python -m pytest -q
.venv/Scripts/python research/phase0/scripts/env_inventory.py > research/phase0/data/environment.json
.venv/Scripts/python research/phase0/scripts/checks.py     # 6.1–6.6 -> data/checks_results.json
.venv/Scripts/python research/phase0/scripts/pilot.py      # 7 -> data/pilot_*.csv, pilot_summary.json
.venv/Scripts/python research/phase0/scripts/build_registers.py
.venv/Scripts/python research/phase0/scripts/build_manifest.py
# Java (JDK 24; Maven incluido en IntelliJ):
#   mvn -B -Dmaven.repo.local=<vacío> test                      (en una copia de jmetal-adapter: falla)
#   mvn -B -Dmaven.repo.local=<vacío> -Djmetal.version=7.8 test (pasan los 32 tests)
# Rangos en jMetal 6.1 y moorphology: research/phase0/java/*.java, con las versiones de manifest.json
```

## 8. Alcance de la fase 1

El que propone `protocol.md` §7: seis correcciones priorizadas, con la puerta G1. Las decisiones que
dependen de Nebro (geometría por defecto, fuente del portafolio) quedan señaladas allí.

## 9. Estado

**PHASE0_COMPLETE.**

Criterio: se han producido todos los entregables de §9 y se han ejecutado todas las comprobaciones de
§6 y el piloto de §7.

Queda pendiente, y no puede resolverse en esta fase:
- confirmar con los autores qué versión de moorphology generó los números de la tesis y del grafo de
  moody;
- la causa de los duplicados ZCAT, porque ZCAT no está en el jMetalPy 1.9.0 instalado;
- confirmar ejecutando la invariancia de VAMOS.

La desviación de presupuesto se describe en §6.
