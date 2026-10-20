# Informe de la fase 2b — irace frente a F-Race

Fecha: 2026-10-20 · Rama `research/phase2` · Protocolo: `protocol.md` (commit `33977a3`). Todo se
ajustó y evaluó en NicoVM con el mismo entorno (Python 3.10, numpy 2.2.6, VAMOS 1.0.0 `0a8bbb0`).

## 1. Resultado

**irace da configuraciones claramente mejores que F-Race con el mismo presupuesto. La corrección
de la normalización, por sí sola, apenas cambia nada.** G2 sigue superándose con los tres brazos.

Calidad de cada c*_P en su propio problema, con normalización común (unión de los frentes de los tres
brazos):

| Comparación | Mejora / empeora | Diferencia media (mediana) | Wilcoxon |
|---|---|---|---|
| B (irace) − A (F-Race), efecto del tuner | 32 / 5 | +0.026 (+0.003) | p = 6.5·10⁻⁷ |
| A − C, efecto de la normalización | 4 / 4 | +0.002 (0.000) | p = 1.0 |
| B − C | 32 / 5 | +0.028 (+0.003) | p = 3.1·10⁻⁷ |

**Dónde gana irace.** La mediana es pequeña porque la mayoría de los problemas están casi saturados
(HVn ≥ 0.99 con cualquier configuración razonable). Las mejoras grandes están en los difíciles:
- DTLZ3: de 0.24 a 0.54 de HVn;
- UF3: de 0.62 a 0.74;
- UF5: de 0.69 a 0.79;
- UF6: de 0.59 a 0.70;
- LZ09_F7 y LZ09_F9: de 0.06 a 0.09 más.

Empeora ligeramente en ZDT4, LZ09_F3, LZ09_F5 y ZCAT6, siempre en menos de 0.015.

**El ajuste puede quedar por debajo de NSGA-II por defecto.** Ocurre en UF6, donde la configuración
por defecto obtiene 0.756 y la mejor ajustada 0.704, y por poco en ZDT4. Es ruido de selección: con
400 ejecuciones, las configuraciones se eligen sobre pocas semillas.

## 2. G2 por brazo

Es la regla pre-registrada de la fase 2, aplicada al portafolio de cada brazo.

| Brazo | Grupos con hueco ≥ 0.01 | Fracción | Con 0.02 | SBS (HVn medio) |
|---|---|---|---|---|
| C (F-Race original, reevaluado en NicoVM) | 11/36 | 31 % | 17 % | c*_ZDT1 (0.890) |
| A (F-Race, normalización corregida) | 11/36 | 31 % | 19 % | c*_ZDT1 (0.886) |
| B (irace) | 14/36 | 39 % | 28 % | c*_ZCAT8 (0.907) |

- **El veredicto no cambia:** G2 se supera en los tres brazos.
- **Robustez al entorno:** el brazo C da 11 grupos en NicoVM y 12 en local. Las diferencias de
  redondeo entre entornos solo mueven un grupo que estaba en el límite.
- **Con irace cambia la forma del margen.** Su generalista es más fuerte (HVn medio 0.907 frente a
  0.89), así que los huecos enormes se reducen:
  - DTLZ6: de 0.99 a 0.74;
  - ZDT4: de 0.16 a 0.01;
  - DTLZ3: de 0.34 a 0.15.

  A la vez aparecen huecos moderados (0.016–0.038) en más problemas de LZ09/UF. El margen deja de
  depender de unos pocos fallos del generalista y se reparte más. Eso es mejor para el estudio de
  transferencia, aunque cada hueco sea más pequeño.
- **Ruido de semillas:** en DTLZ1 el hueco de B es −0.087. El donante elegido con 3 semillas rinde
  mucho peor en las otras 2, lo que confirma que la varianza entre semillas es alta en los
  multimodales.

## 3. Coste

| Brazo | Ejecuciones de ajuste | Reloj en NicoVM |
|---|---|---|
| A (F-Race) | 10 942 (se detiene al quedar un superviviente) | 50 min con 14 procesos |
| B (irace) | 14 385 (360–400 por problema; mediana de 60 configuraciones en 6 iteraciones) | 80 min con 4 × 4 procesos |
| Evaluación de C, A y B | 21 090 | 47 min con 31 procesos |

## 4. Desviaciones

1. **`nbIterations = 5`.** Con 26 parámetros, irace exige al menos 504 experimentos con su valor por
   defecto (6). Se fijó 5 para mantener las 400 ejecuciones de F-Race, y quedó registrado en el
   protocolo antes de la ejecución completa. irace informa de 6 iteraciones porque usó el
   presupuesto sobrante.
2. **NicoVM no reproduce bit a bit los frentes locales:** las diferencias son de ~10⁻¹⁶ (numpy 2.2 y
   Linux frente a numpy 2.5 y Windows). Por eso C se volvió a evaluar allí, como fijaba el protocolo.
3. **Fallo en el script de recogida de elites.** `collect_irace.py` daba por hecho un campo del log
   que irace 4.5 no tiene. Se corrigió antes de usar ningún resultado.

## 5. Recomendación para la fase 3

- **Usar irace** (4.5 o posterior, con la normalización por frentes de referencia) para ajustar las
  c*_P. Con el mismo presupuesto da mejores configuraciones y un portafolio menos dependiente de unos
  pocos fallos del generalista. Es una decisión del usuario; aquí solo se recomienda.
- **Dar más presupuesto o más semillas de evaluación al ajuste** en los problemas multimodales. En
  UF6, ZDT4 y DTLZ1, 400 ejecuciones no bastan para separar señal de ruido.
- **Seguir informando por estrato:** la mayoría de los problemas están saturados con cualquier
  configuración.
