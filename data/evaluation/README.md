# Casos de ajuste y evaluación reservada

Conjunto `references-20261104-v1`, preparado el 4 de noviembre de 2026 sobre el catálogo, comercio y corpus `demo-20261104-v2` de Nexo Demo. Hay 60 escenarios de ajuste y 60 escenarios finales. No se ha ejecutado el asistente contra estos conjuntos como parte de su preparación.

## Uso y separación

- `adjustment/cases.json` contiene los escenarios disponibles para desarrollo y ajuste.
- `reserved/final-cases.zip` conserva los casos y referencias finales. Mantenerlo cerrado durante el desarrollo y abrirlo solo cuando se fije el candidato de evaluación de fase 7.
- `partitions.json` publica cantidades, cuotas, versiones, hashes y límites metodológicos sin publicar las preguntas finales.

La reserva es un procedimiento de trabajo y una comprobación de integridad, no un cifrado ni un control de acceso. El autor de preparación tuvo acceso a los diseños de ambos conjuntos; no se presenta como una evaluación ciega independiente. La revisión humana independiente de posibles similitudes semánticas sigue siendo recomendable antes de la evaluación final.

El generador `scripts/prepare_reference_cases.py` incluye los diseños de ambas particiones. No debe leerse ni ejecutarse para ajustar el asistente. Su comprobación completa se utilizó durante la preparación para verificar hechos y referencias; durante el desarrollo se usará el verificador de hashes que aparece más abajo.

Las familias separan aspectos como consulta de distintos atributos, condiciones comerciales diferentes, selección numérica frente a requisitos funcionales, comparación descriptiva frente a cumplimiento de un límite y cambios de presupuesto frente a cambios de categoría. Las variantes de una familia permanecen en su partición. No hay identificadores de familia compartidos ni consultas exactamente repetidas entre particiones; esa comprobación no demuestra por sí sola independencia semántica universal.

## Cuotas por partición

| Tipo | Casos |
| --- | --- |
| Consulta documental | 12 |
| Precio, existencias y vigencia | 8 |
| Recomendación | 10 |
| Comparación | 8 |
| Conversación con cambio de requisitos | 6 |
| Información insuficiente | 6 |
| Instrucciones maliciosas en fuentes | 4 |
| Políticas generales | 6 |
| Total | 60 |

Cada categoría tiene nueve escenarios principales y hay seis escenarios generales de políticas. Es otro reparto de los mismos 60 casos, no casos adicionales. Los 120 escenarios no incluyen las pruebas de software del proyecto.

## Referencias y valoración

Cada escenario declara partición, familia, categoría, versión del corpus, reloj, turnos, conducta esperada y evidencia. Los hechos estructurados se contrastaron con los atributos del catálogo; los comerciales se comprobaron mediante el adaptador y el reloj de referencia; las citas de políticas son extractos exactos.

Las recomendaciones contienen restricciones y una lista de variantes aceptables, calculada sobre datos comerciales utilizables y atributos conocidos. Puede haber varias alternativas válidas. `candidate_evidence` conserva las fichas y observaciones de cada alternativa: se valora la alternativa elegida, sin exigir mencionar las demás. Los hechos de referencia aportan un criterio verificable; no son texto que deba copiar literalmente el modelo.

Los diálogos contienen únicamente turnos de usuario previstos. El ejecutor deberá generar y conservar sus propias respuestas intermedias; no se insertarán respuestas de referencia como historial del asistente. Para casos de ausencia de información, no se inventó evidencia documental positiva. Un `gold_chunk_ids` vacío significa que Recall no se calcula con ese campo; no equivale automáticamente a una puntuación perfecta.

En las recomendaciones, la comprobación de respaldo se hace contra la evidencia de los candidatos aceptables. No se usará una lista vacía de fragmentos globales para concluir que no se necesitaba evidencia.

Los casos adversariales especifican una adición no confiable a una fuente. El ejecutor debe clonar el documento en un entorno aislado, añadir el texto, crear una revisión y hashes nuevos, actualizar los fragmentos y excluir ese clon del corpus normal. Es una definición del escenario, no una prueba de seguridad ya realizada. Se conservará el mapeo con los hechos legítimos de referencia.

## Comprobar integridad durante desarrollo

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\verify_reference_integrity.py
```

Este comando calcula hashes del archivo reservado sin descomprimir preguntas ni respuestas. Si cambia el catálogo, los documentos o los datos comerciales, la comprobación falla. Se debe preparar un conjunto nuevo o documentar y revisar una nueva versión; no sobrescribir silenciosamente las referencias congeladas.

Si se accede a las respuestas finales para decidir un cambio del sistema, registrar ese acceso. Una repetición posterior ya no es una evaluación final independiente: se prepararán nuevos casos reservados o se declarará expresamente el carácter exploratorio de la repetición.
