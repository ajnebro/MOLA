# Fase 5, preparación: verificación de los 17 problemas reservados (2026-11-02)

Corresponde a la decisión D12 (C8): Claude verifica las cotas y los frentes de referencia de los
reservados antes de abrirlos.

**Lo que no se ha hecho:** no se ha ejecutado ningún algoritmo sobre ellos. Solo se comparan
definiciones, así que no se ha visto el rendimiento de ningún método en el conjunto reservado.

**Lo que se ha hecho:**
- **Script y salida:** `scripts/verify_reserved.py`, con salida en `data/reserved_verification.json`.
- **Propuesta de cotas:** `data/reserved_bounds_proposed.json`. Se usará solo cuando lo fije el
  pre-registro de la fase 5.

## 1. Definiciones de los problemas (VAMOS frente a jMetal 7.8)

| Problemas | Dimensión y cotas | Objetivos en 1 000 puntos al azar |
|---|---|---|
| ZDT6, DTLZ7 y ZCAT2, 7, 14, 16, 18, 20 | Iguales | **Idénticos.** jMetalPy coincide también en ZDT6 y DTLZ7; su versión instalada no tiene WFG ni ZCAT |
| WFG1–8 | Iguales (24 variables, x_i ∈ [0, 2i]) | Coinciden con jMetal WFG(k = 4, l = 20) hasta 3·10⁻⁵ en relativo, que es ruido numérico. Con k = 2 no coinciden |
| WFG9 | Iguales | **Diferencia pequeña:** 1.4·10⁻³ en relativo frente a jMetal. Se marca; no se corrige |

## 2. Frentes de referencia y cotas de normalización

| Problema | Frente de VAMOS | Decisión propuesta |
|---|---|---|
| **WFG1** | **Desplazado:** ideal (0.069, 0.069) y nadir (2.069, 4.069), frente al analítico (0, 0)–(2, 4). El de Evolver coincide con el analítico | Cotas analíticas |
| WFG2 | 32 puntos; ideal y nadir correctos | Cotas analíticas |
| WFG3–9 | Coincide con el analítico. Los de Evolver son más escasos y en WFG4, 5 y 9 no llegan a los extremos | Cotas analíticas |
| **ZDT6** | **Ligeramente fuera:** f2 llega a 0.9233 frente al 0.9212 analítico, y no llega a 0. El de Evolver coincide con el analítico | Cotas analíticas |
| **DTLZ7** | **El fichero es de tres objetivos.** No hay frente biobjetivo | El de Evolver: ideal (0, 2.307), nadir (0.859, 4.0), coherente con f2 = 4 − f1 (1 + sin 3πf1) |
| ZCAT 2, 7, 14, 16, 18 y 20 | Idéntico al de Evolver y a menos de 0.1 % del analítico (0, 0)–(1, 4) | El frente de VAMOS, como en los ZCAT de desarrollo |

## 3. Consecuencias

- **Si se hubieran usado sin revisar,** los frentes de referencia de VAMOS habrían normalizado mal
  el HVn de WFG1 y ZDT6. DTLZ7 no tenía frente biobjetivo.
- **Las cotas propuestas** se fijarán en el pre-registro de la fase 5, después de G6 y G7.
- **Fallos nuevos de VAMOS 1.0.0, a comunicar al proyecto** (pregunta pendiente 7):
  - el frente de WFG1 está desplazado;
  - el de ZDT6 está ligeramente fuera;
  - no hay frente biobjetivo de DTLZ7;
  - WFG9 difiere de jMetal en 1.4·10⁻³.
