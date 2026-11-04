# Plan de trabajo del proyecto RAG

Revisión y planificación realizadas el 4 de noviembre de 2026. El proyecto desarrollará un asistente web en español para consultar y recibir asesoría sobre el catálogo de una tienda.

El [plan del proyecto](001-plan-del-proyecto.md) contiene la revisión de los tres documentos disponibles, las decisiones pendientes, las actividades de cada fase y sus criterios de cierre. Se preparó con la habilidad de planificación improve y se adaptó al estado documental del proyecto.

El usuario seleccionó un catálogo de demostración y autorizó definir sus características, con el requisito de facilitar una futura tienda real. La [definición de fase 1](002-fase-1-definicion.md) establece Nexo Demo, seis categorías, 60 productos y 90 variantes como metas de construcción; incluye requisitos de sustitución mediante configuración y adaptadores. También están preparados el [protocolo e instrumentos](phase-1/evaluation-protocol.md) y las [notas internas de trabajo](phase-1/working-notes.md). El informe de avance se preparará y entregará al finalizar el proyecto, en la fase 8, según la aclaración del usuario.

## Orden y estado de las fases

| Fase | Objetivo | Depende de | Estado |
| --- | --- | --- | --- |
| 1 | Definir tienda, requisitos y protocolo de evaluación | Ninguna | IN PROGRESS: definición documental lista; caracterización y revisión académica pendientes |
| 2 | Diseñar la arquitectura y preparar la base técnica | Definición documental de 1 disponible | DONE: tecnologías y modelos locales fijados, contratos y API de base, 44 comprobaciones e inferencia real verificadas |
| 3 | Preparar el catálogo y la base documental | Definición de 1 y base de 2 disponibles | DONE: catálogo, fuentes, ingesta SQLite, 204 embeddings locales y 60 casos de ajuste más 60 reservados verificados |
| 4 | Implementar y medir el RAG básico | 2 y 3 | IN PROGRESS: recuperación semántica, respuestas extractivas con citas y Recall@5 sobre ajuste; calidad de respuesta, latencia e integración pendientes |
| 5 | Integrar datos comerciales y asesoría conversacional | 4 | TODO |
| 6 | Construir e integrar el prototipo web | 5 | TODO |
| 7 | Evaluar el prototipo y analizar los resultados | 6 y protocolo de 1 | TODO |
| 8 | Cerrar la documentación, entregar el informe de avance y preparar el mantenimiento | 7 | TODO |

Estados: TODO, IN PROGRESS, DONE y BLOCKED con una razón concreta. La revisión inicial está terminada y la definición de la tienda de demostración está documentada. La [fase 2](../docs/architecture/README.md) cerró su base técnica local. La [fase 3](../docs/data/README.md) cerró la preparación e ingesta: 60 productos, 90 variantes, 72 fuentes, 204 vectores locales y particiones de referencias separadas. Recuperación, conversación, web y evaluación tienen sus propios criterios de cierre; la preparación de datos no acredita esas capacidades.

Por indicación expresa del usuario, el prototipo se desarrolla sin TDD y conserva comprobaciones de funcionamiento posteriores. Los comandos y sus límites están en la [guía del entorno](../docs/architecture/local-environment.md).

## Dependencias y seguimiento

La fase 1 determina qué construir y cómo evaluarlo. La fase 2 define los contratos y comandos reales del proyecto antes de implementar. La fase 3 prepara la evidencia que utilizarán las fases 4 y 5. La fase 6 integra el prototipo; la fase 7 comprueba su calidad y utilidad; la fase 8 entrega el trabajo reproducible.

La búsqueda de fuentes y la redacción académica pueden avanzar durante todo el proyecto. La interfaz puede diseñarse antes con datos de prueba, pero su integración depende de los contratos y servicios definidos. Cada fase conserva evidencias y notas internas; el informe de avance se elaborará con los resultados acumulados al finalizar todo el proyecto.

No se fijaron fechas ni duraciones: faltan disponibilidad del equipo, fecha de entrega y recursos; el tamaño objetivo del catálogo ya está definido. La definición permite preparar la fase 2 manteniendo visibles los pendientes de fase 1. La planificación no autoriza publicación, transferencias de datos, servicios remotos, commits ni despliegues.
