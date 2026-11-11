# Correspondencia con la guía del Previo 3

Esta matriz identifica dónde comprobar cada requisito. La preparación de los
materiales se distingue de la sustentación que realizará el equipo. Los datos son
sintéticos y las mediciones de ajuste no constituyen una evaluación con clientes.

| Requisito de la guía | Material y comprobación |
| --- | --- |
| 4.1 Título | Informe, sección 1: identifica el aprendizaje preentrenado y la recuperación documental. |
| 4.2 Planteamiento | Informe, sección 2: contexto, problema, causas y consecuencias de la situación contextualizada. |
| 4.3 Formulación | Informe, sección 3: pregunta coherente con el alcance de la aplicación. |
| 4.4 Objetivo general | Informe, sección 4. |
| 4.5 Objetivos específicos | Informe, sección 5: cinco objetivos que pueden relacionarse con datos, implementación y evaluación. |
| 4.6 Justificación | Informe, sección 6: beneficios, población prevista, pertinencia de ML y viabilidad. |
| 4.7 Estado del arte | Informe, sección 7 y referencias de la sección 16; registro de bibliografía contrastada. |
| 4.8 Dataset | Informe, sección 8; JSON y manifiestos en `data/sample/`; análisis reproducible. |
| 4.9 Algoritmos | Informe, sección 9: modelos preentrenados, similitud coseno, selección extractiva y reglas separadas. |
| 4.10 Herramientas | Informe, sección 10: función de cada tecnología; versiones fijadas en los archivos lock. |
| 4.11 Resultados esperados | Informe, sección 11, separado de los resultados observados de la sección 13. |
| 6.1 Carga y exploración | `ragml.analysis` valida y carga datos, calcula estadísticos y exporta cinco figuras y tablas CSV. |
| 6.2 Preparación | Informe, secciones 8, 9 y 12; contratos, procedencia, faltantes, unidades, IQR y embeddings; justificación de procedimientos que no corresponden. |
| 6.3 Visualización | Figuras en el informe y `docs/analysis/2026-11-09/`; respuestas, productos y fuentes en la interfaz web. |
| 6.4 Funcionamiento | Ingesta y web locales; entradas nuevas y sesiones; CLI con parámetros; evaluación HTTP y ensayo de contexto con evidencia de su límite. |
| 7 Sustentación | Presentación y guion con problema, antecedentes, dataset, algoritmos, demostración, resultados, conclusiones y limitaciones. La exposición la realiza el equipo. |
| 8 Entregables | Informe editable y PDF, código Python con datos de demostración, presentación y guion de ejecución. |

## Localización

- [Informe fuente](previo3-informe.md).
- [Bibliografía contrastada](bibliografia-verificada.md).
- [Guion de sustentación](guion-sustentacion.md).
- [Análisis de datos](../analysis/README.md).
- [Evaluación integrada](../evaluation/integrated/README.md).
- Entregables finales: `outputs/previo3/` desde la raíz del proyecto.

No se atribuyen al prototipo entrenamiento propio, ejecución de RAGAs, una tienda
real, validación con participantes ni resultados del conjunto final reservado.
Los desaciertos y las latencias observadas forman parte del análisis del informe.
