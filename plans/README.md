# Plan de trabajo del proyecto RAG

Actualizado el 10 de noviembre de 2026 a partir del plan inicial del 4 de noviembre.
El proyecto ya incluye un asistente web en español para consultar y recibir
asesoría sobre el catálogo sintético de Nexo Demo. Este índice distingue la
implementación actual de las evidencias históricas y los estudios todavía no ejecutados.

El [plan del proyecto](001-plan-del-proyecto.md) conserva la revisión inicial,
las actividades de las ocho fases y sus criterios de cierre. Sus afirmaciones
sobre la carpeta y sus estados corresponden a aquella instantánea. El estado
actual se resume aquí y se contrasta con código y registros fechados.

La [definición de fase 1](002-fase-1-definicion.md) fija el entorno ficticio,
los requisitos y la futura sustitución de fuentes. El catálogo ya contiene las
seis categorías, 60 productos y 90 variantes previstos. El [protocolo e
instrumentos](phase-1/evaluation-protocol.md) y las [notas internas](phase-1/working-notes.md)
conservan las decisiones originales. La entrega del Previo 3 se está consolidando
con el informe, la exploración y la sustentación en `docs/reports/` y
`outputs/previo3/`, sin equipararla a estudios aún no realizados del protocolo amplio.

## Orden y estado de las fases

| Fase | Objetivo | Depende de | Estado |
| --- | --- | --- | --- |
| 1 | Definir tienda, requisitos y protocolo de evaluación | Ninguna | Definición contextualizada disponible; informe y bibliografía se actualizan. La caracterización con participantes sigue sin ejecutarse y no se atribuye a una empresa real. |
| 2 | Diseñar la arquitectura y preparar la base técnica | Definición documental de 1 disponible | DONE: tecnologías y modelos locales fijados, contratos y API de base, 44 comprobaciones e inferencia real verificadas |
| 3 | Preparar el catálogo y la base documental | Definición de 1 y base de 2 disponibles | DONE: catálogo, fuentes, ingesta SQLite, 204 embeddings locales y 60 casos de ajuste más 60 reservados verificados |
| 4 | Implementar y medir el RAG básico | 2 y 3 | Implementado: recuperación y selección extractiva conectadas al chat. Recall@5 histórico sobre 18 consultas de ajuste; revisar calidad y latencia del candidato actual por separado. |
| 5 | Integrar datos comerciales y asesoría conversacional | 4 | Implementado: recomendaciones por reglas, comparación, restricciones, aclaraciones y contexto de sesión. Validación integrada en curso; no constituye estudio de utilidad. |
| 6 | Construir e integrar el prototipo web | 5 | Implementado: API y web conectan ChatService. Sesiones por propietario en memoria, TTL y eliminación; evidencia nueva de modelos/navegador debe conservarse fechada. |
| 7 | Evaluar el prototipo y analizar los resultados | 6 y protocolo de 1 | En curso: análisis exploratorio y ejecutor de recorridos integrados. Revisar registros observados antes de declarar metas cumplidas; evaluación final reservada y participantes son estudios separados. |
| 8 | Cerrar la documentación, entregar el informe de avance y preparar el mantenimiento | 7 | Materiales del Previo 3 preparados: informe Word/PDF de 20 páginas, presentación de 14 diapositivas, guion e informe de avance. El equipo debe ensayar y realizar la sustentación. El protocolo amplio y la migración real conservan sus pendientes. |

Estados: TODO, IN PROGRESS, DONE y BLOCKED con una razón concreta. La revisión inicial está terminada y la definición de la tienda de demostración está documentada. La [fase 2](../docs/architecture/README.md) cerró su base técnica local. La [fase 3](../docs/data/README.md) cerró la preparación e ingesta: 60 productos, 90 variantes, 72 fuentes, 204 vectores locales y particiones de referencias separadas. Recuperación, conversación, web y evaluación tienen sus propios criterios de cierre; la preparación de datos no acredita esas capacidades.

Las notas de fase 2 describen un desarrollo histórico sin TDD. Las instrucciones
actuales exigen observar una prueba relevante fallida antes de implementar cambios
de comportamiento y verificar después el resultado. No se atribuye retroactivamente
ese proceso a implementaciones anteriores. La [guía de pruebas](../tests/README.md)
identifica los comandos y el alcance actual de la batería.

## Dependencias y seguimiento

La fase 1 determina qué construir y cómo evaluarlo. La fase 2 define los contratos y comandos reales del proyecto antes de implementar. La fase 3 prepara la evidencia que utilizarán las fases 4 y 5. La fase 6 integra el prototipo; la fase 7 comprueba su calidad y utilidad; la fase 8 entrega el trabajo reproducible.

La búsqueda de fuentes y la redacción académica pueden avanzar durante todo el proyecto. La interfaz puede diseñarse antes con datos de prueba, pero su integración depende de los contratos y servicios definidos. Cada fase conserva evidencias y notas internas; el informe de avance se elaborará con los resultados acumulados al finalizar todo el proyecto.

El reloj comercial del demo es una reproducción explícita fijada en sus metadatos,
distinta de la fecha de ejecución. Las sesiones utilizan una cookie firmada de
propietario y contexto en memoria del servidor con TTL; el historial visible
permanece en la pestaña y no se guarda como conversación en disco.

Git existe actualmente: `424485a` es la revisión de partida para esta entrega,
con cambios de trabajo posteriores. Las referencias antiguas a ausencia de Git
no describen el estado actual. La identidad del candidato evaluado debe incluir
las huellas de los archivos realmente ejecutados.

Las salidas analíticas se organizan en `docs/analysis/2026-11-09/` y las nuevas
ejecuciones de ajuste integrado en `docs/evaluation/integrated/`. Una carpeta,
un protocolo o un ejecutor no prueban por sí solos que una medición pasó. No se
consideran ejecutadas las entrevistas, la evaluación con voluntarios o una
sustitución completa de tienda por haber preparado sus instrumentos. La guía
académica permite una problemática contextualizada y no fija una muestra de
participantes. La planificación no autoriza publicación, transferencias remotas,
servicios externos, commits ni despliegues.
