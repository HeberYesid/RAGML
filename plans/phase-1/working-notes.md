# Notas internas de definición de la fase 1

Fecha: 4 de noviembre de 2026. Proyecto: asistente conversacional para consulta y asesoría de productos mediante RAG.

Estas notas conservan el trabajo de definición de la fase 1 y sustituyen el borrador prematuro del informe de avance. Son un registro interno, sin entrega académica por fase. El informe de avance se preparará y entregará al finalizar todo el proyecto, en la fase 8, según la aclaración del usuario.

## Propósito del registro

Registrar la definición del entorno de demostración, los requisitos y el diseño de evaluación, incorporando la decisión del usuario de facilitar una futura migración a una tienda real.

## Trabajo documentado

Se seleccionó Nexo Demo como negocio ficticio para el hogar y el espacio de trabajo. Se definieron seis categorías y una meta de 60 productos con 90 variantes, así como un primer lote de 12 productos con 18 variantes. Estas cantidades especifican la construcción posterior y no representan registros ya creados.

Se prepararon requisitos de consulta, comparación, recomendación, datos comerciales, citas y manejo de incertidumbre. Se añadieron requisitos para sustituir perfil, catálogo, fuentes y políticas mediante configuración y adaptadores, conservando la lógica del asistente.

Se diseñó una evaluación técnica con 60 escenarios de ajuste y 60 reservados, junto con metas de aceptación e instrumentos de caracterización y utilidad. La participación prevista es de ocho adultos voluntarios, todavía sin reclutar.

## Evidencias disponibles

| Evidencia documental | Resultado comprobable | Límite |
| --- | --- | --- |
| [Definición de la fase 1](../002-fase-1-definicion.md) | Perfil, alcance, inventario previsto, 14 requisitos funcionales y ocho de sustitución | Este entregable no genera el catálogo ni implementa funciones |
| [Protocolo e instrumentos](evaluation-protocol.md) | Cuotas, métricas, criterios, separación de conjuntos e instrumentos | No hay resultados de evaluación ni participantes confirmados |
| [Plan y seguimiento](../README.md) | Decisiones y estado de la fase actualizados | La fase 1 sigue en curso por sus pendientes empíricos y académicos |

Los documentos permiten preparar la arquitectura. No prueban exactitud de respuestas, facilidad de migración implementada, utilidad con usuarios ni resultados comerciales. La comprobación de esta entrega es documental: lectura de coherencia, enlaces, cantidades y correspondencia con el alcance.

Se observó además una base técnica en preparación con configuración Python y un paquete inicial. Se conservaron esos archivos y no se ejecutaron sus comprobaciones como parte de este avance de fase 1; su estado corresponde al trabajo técnico de fase 2.

## Limitaciones actuales

La elección de un catálogo ficticio permite controlar los datos, pero no aporta un diagnóstico de una empresa. Las hipótesis de consulta deberán contrastarse con personas y sus resultados se reportarán en ese entorno de demostración.

Todavía no se conocen fecha de entrega, disponibilidad del equipo ni hardware. Por ello no se presentan fechas de ejecución ni capacidades de modelos como confirmadas. La bibliografía y la entrega académica anterior requieren una revisión específica antes de cerrar ese componente.

## Trabajo pendiente

1. Aplicar la caracterización con participantes y registrar qué requisitos se confirman o cambian.
2. Actualizar y revisar el primer informe académico, incluidos el entorno de demostración y el contraste de referencias.
3. Confirmar responsables, disponibilidad, fecha académica y recursos locales.
4. En la fase 2, elegir tecnologías y formalizar contratos, comandos de verificación y presupuesto de rendimiento.
5. En la fase 3, crear el catálogo y las 72 fuentes documentales previstas, verificar referencias y reservar escenarios.
6. Implementar y evaluar las funciones y la sustitución de tienda en sus fases correspondientes.

## Estado de la definición

El entorno de prueba y las obligaciones de adaptación están definidos documentalmente. La futura incorporación de una tienda real requerirá sus datos autorizados, configuración, mapeos y posibles adaptadores, además de nuevas pruebas. La caracterización, el desarrollo y la evaluación aún no se han ejecutado; sus resultados no se anticipan en estas notas.
