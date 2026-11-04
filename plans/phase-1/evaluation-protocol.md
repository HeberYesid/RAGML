# Protocolo de evaluación e instrumentos para Nexo Demo

Versión 1 del 4 de noviembre de 2026. Estado: diseño previo a la implementación; no se han ejecutado evaluaciones ni reclutado participantes.

Este protocolo comprobará el asistente sobre fuentes sintéticas versionadas. Separa la comparación técnica de configuraciones de la evaluación de utilidad con personas. Sus cifras son decisiones de diseño adoptadas para el prototipo y no resultados de estudios previos ni afirmaciones de representatividad estadística.

## Preguntas de evaluación

1. ¿Recupera evidencia del producto y variante correctos y responde con afirmaciones respaldadas?
2. ¿Respeta presupuesto y requisitos y consulta los datos comerciales correctos?
3. ¿Aclarar, abstenerse o derivar resuelve adecuadamente los casos sin información suficiente?
4. ¿Permite completar las tareas de consulta y selección frente al catálogo y los documentos convencionales?
5. ¿Puede cambiarse el entorno de tienda manteniendo los mismos comportamientos y contratos?

## Conjuntos técnicos y separación

Se construirán 120 escenarios: 60 de ajuste y 60 reservados para evaluación final. Un escenario puede incluir varios turnos. Los casos concretos se crearán en la fase 3 contra las fuentes existentes; hoy se fijan cuotas y criterios, no respuestas de referencia imaginarias.

| Tipo principal de escenario | Ajuste | Evaluación final |
| --- | --- | --- |
| Consulta documental directa | 12 | 12 |
| Precio, existencias y vigencia | 8 | 8 |
| Búsqueda por necesidad y recomendación | 10 | 10 |
| Comparación | 8 | 8 |
| Políticas generales | 6 | 6 |
| Conversación con cambio de requisitos | 6 | 6 |
| Información ausente, contradictoria o sin alternativas | 6 | 6 |
| Instrucciones maliciosas y límites de acceso | 4 | 4 |
| Total | 60 | 60 |

Cada partición tendrá nueve casos con categoría principal por cada una de las seis categorías y seis casos de políticas de ámbito general. Los dos criterios de reparto describen los mismos 60 casos, no conjuntos que deban sumarse. Las consultas entre categorías conservarán una categoría principal y etiquetas adicionales.

Las paráfrasis, diálogos derivados y variaciones de una misma familia de escenario permanecerán en una sola partición. Se podrán compartir productos entre particiones porque se evalúa consulta del mismo catálogo; no se compartirán casos de referencia ni sus derivaciones. El conjunto final no se usará para elegir instrucciones, modelos, fragmentación ni parámetros.

La fase 3 registrará el manifiesto, versiones y huellas de los conjuntos. Cada consulta de ajuste tendrá evidencia comprobada; los casos finales se prepararán y reservarán sin exponer sus respuestas al ejecutor de ajustes. Si el mismo responsable debe acceder a ambos conjuntos, se declarará esa limitación y se conservará un registro de cambios. Una prueba final reutilizada después de corregir el sistema se reportará como exploratoria o se reemplazará por nuevos casos reservados.

Los casos de carga, contrato, interfaz y migración no forman parte de los 120 escenarios de calidad; se reportarán como pruebas de software separadas.

## Registro de cada escenario

La plantilla se completará con: `case_id`, partición, familia, categoría principal, etiquetas, tipo de tarea, consulta y turnos, producto y variante esperados cuando apliquen, versión de catálogo y documentos, reloj de referencia, registros comerciales, restricciones obligatorias, preferencias, evidencias esperadas, conducta esperada y rúbrica.

Se registrarán respuestas aceptables o criterios verificables. Una recomendación no tendrá necesariamente un único producto válido. Se distinguirán los requisitos obligatorios de las preferencias. Los casos sin evidencia no tendrán un fragmento de referencia ficticio.

Cada ejecución conservará configuración, versiones de modelos, parámetros, resultados recuperados, respuesta, citas, tiempos, uso disponible y valoraciones. Se distinguirán fallos del sistema, fuentes incompletas y errores de la referencia.

## Comparaciones técnicas

- **RAG básico:** recuperación documental y generación, sin consultar registros comerciales. Puede abstenerse justificadamente ante un precio que no puede confirmar.
- **Sistema integrado:** el RAG más consulta comercial, restricciones y conversación. Su mejora global no se atribuirá exclusivamente a la recuperación porque dispone de capacidades adicionales.
- **Recuperación mejorada, si se adopta:** se comparará con la recuperación básica sobre el mismo subconjunto documental y con modelo y fuentes constantes cuando sea posible.

Las tablas distinguirán tareas documentales comunes y tareas que requieren consulta comercial. Se informarán cobertura de capacidad, abstenciones y exactitud; no se penalizará como alucinación una abstención correcta del RAG básico. El contraste de recuperación no mezclará la incorporación de una fuente comercial con una mejora del índice.

## Métricas y metas de aceptación

| Dimensión | Definición operativa | Meta de diseño para el sistema integrado |
| --- | --- | --- |
| Recuperación | Promedio por caso de evidencias relevantes recuperadas entre evidencias de referencia, usando k igual a 5 | Recall@5 al menos 0,85 |
| Corrección factual | Afirmaciones verificables correctas entre afirmaciones verificables emitidas | Al menos 0,95 |
| Respaldo | Afirmaciones verificables respaldadas por evidencia identificada entre afirmaciones verificables emitidas | Al menos 0,95 |
| Citas | Citas cuyo contenido respalda la afirmación asociada entre citas emitidas | Al menos 0,95 |
| Identidad comercial | Confirmaciones de precio y existencias con producto, variante, moneda y versión correctos | 1,00 en los casos aplicables |
| Restricciones obligatorias | Recomendaciones presentadas como aptas que cumplen todos los requisitos confirmados | 1,00 |
| Manejo de insuficiencia | Casos con aclaración, abstención o derivación conforme a la conducta de referencia | Al menos 0,90 |
| Resolución de tareas | Escenarios resolubles completados sin error crítico entre escenarios resolubles | Al menos 0,85 |
| Sesiones y seguridad | Cruces de sesión, exposición de secretos o seguimiento de instrucciones maliciosas de una fuente | Cero eventos observados en la batería definida |
| Sustitución de tienda | Contratos y recorridos aplicables pasan con el segundo proveedor y perfil sin editar el núcleo | Todos los casos de la batería de migración |

Las metas no son garantías. Se reportarán numeradores y denominadores junto con los porcentajes. Un denominador vacío se marcará como no aplicable; no se convertirá en 100 %. Recall se calculará solo para casos con evidencia documental positiva de referencia. La cantidad de fragmentos relevantes y las equivalencias aceptadas quedarán anotadas antes de ejecutar.

Se desglosarán los resultados por tipo de tarea y categoría, mostrando el número de casos. Con pocos casos se informarán las observaciones y conteos sin atribuir precisión estadística al porcentaje. El promedio global no reemplazará el análisis de una categoría con errores.

Las abstenciones no generan afirmaciones falsas, pero tampoco cuentan como resolver un caso que sí era resoluble. Esa distinción impide aprobar un sistema que responde «no sé» a todas las preguntas. Los casos de falta de información se puntuarán por la conducta correcta, no por ofrecer un producto.

Un error crítico será confirmar precio o existencias sin respaldo vigente, recomendar como apta una alternativa que viola una restricción obligatoria, mezclar una variante en una confirmación comercial o cruzar información entre tiendas o sesiones. Se reportará por separado aunque el promedio supere una meta.

Se registrarán latencia mediana y percentil 95 por turno, diferenciando arranque y ejecución posterior, hardware y concurrencia. También se registrarán costo o recursos consumidos, sin presentar ejecución local como ausencia de costo computacional. La fase 2 fijará un presupuesto numérico de rendimiento antes de medirlo con el conjunto final; no se inventa una capacidad del hardware todavía desconocido.

## Rúbrica humana de cada tarea

El revisor marcará corrección del producto, exactitud de los datos, suficiencia de fuentes, cumplimiento de restricciones y adecuación de la respuesta como cumple, parcial, incumple o no aplicable, con una explicación y evidencia. Los porcentajes de afirmaciones y tareas se calcularán con las definiciones anteriores; la etiqueta parcial no sustituirá esos cálculos.

Se requiere una revisión humana de las respuestas finales. Una segunda revisión es deseable para resolver desacuerdos; si no existe otro revisor se declarará esa limitación. Las métricas automáticas que se incorporen serán complementarias y registrarán la configuración del evaluador.

## Caracterización antes de las pruebas de utilidad

Instrumento breve para adultos voluntarios, con duración prevista de 10 a 15 minutos. No se recopilarán nombres ni contactos. Cada sesión tendrá un código y fecha. Esta etapa identifica necesidades y permite ajustar los escenarios de desarrollo antes de cerrar los casos finales.

1. Describe una ocasión reciente en la que comparaste productos y qué información necesitabas.
2. Explica cómo buscarías una alternativa para un espacio pequeño y un presupuesto limitado.
3. Indica qué atributos necesitarías confirmar antes de elegir y cuáles serían solo preferencias.
4. Describe cómo resolverías nombres parecidos, variantes o dudas sobre compatibilidad.
5. Explica qué harías si falta un dato, dos fuentes se contradicen o el producto está agotado.
6. Indica qué te permitiría confiar en una respuesta sobre precio, disponibilidad o garantía.
7. Realiza una tarea exploratoria con el material de demostración y describe los obstáculos observados.
8. Indica en qué situaciones preferirías consultar a una persona.

El registro separará observaciones, citas autorizadas anonimizadas e interpretación del investigador. No se atribuirán respuestas a personal de Nexo Demo, porque no existe una tienda con empleados participantes. El reclutamiento y la aplicación están pendientes.

## Prueba de utilidad con personas

La meta inicial será ocho personas adultas voluntarias, mediante muestra por conveniencia. Es una meta de reclutamiento, no una muestra conseguida ni una base para generalizar a todos los compradores. Las personas que intervengan en la caracterización inicial no participarán en la evaluación final para evitar familiaridad con las tareas, y ningún participante habrá desarrollado el prototipo ni preparado sus referencias.

Se prepararán seis pares de tareas equivalentes, uno por categoría. Cada persona realizará seis tareas diferentes: tres mediante catálogo y documentos convencionales y tres mediante el asistente. No repetirá la misma selección de producto con otra herramienta. La asignación de versiones y herramientas se contrabalanceará entre participantes; cuatro comenzarán con cada condición y cada categoría se distribuirá entre ambas herramientas.

Con ocho participantes se prevén 48 observaciones de tarea, 24 por condición. Las observaciones de una misma persona no se tratarán como participantes independientes. El análisis será descriptivo: éxito, cumplimiento, tiempo, problemas y utilidad percibida. Se reportará el tamaño real conseguido, incluyendo abandonos y tareas incompletas.

El catálogo convencional mostrará los mismos registros comerciales y documentos disponibles al asistente integrado. Se mantendrán constantes las versiones, instrucciones y límites de tiempo previamente fijados en el protocolo de sesión. La fase de preparación comprobará que los pares tengan dificultad comparable.

### Información y aceptación de participación

Texto previsto: «Participarás voluntariamente en una prueba académica de una tienda ficticia. Realizarás tareas de consulta; no comprarás productos ni ingresarás datos de pago. Registraremos resultados, tiempos y observaciones con un código. Puedes omitir una pregunta o retirarte. La grabación no forma parte de esta prueba y requeriría autorización adicional. Confirma si deseas participar».

Se registrará aceptación o rechazo antes de iniciar. Los resultados anonimizados se usarán para el proyecto; se ofrecerá un código para solicitar retiro de los registros mientras siga abierta la recolección. Los datos de sesión se conservarán hasta 90 días después de cerrar la evaluación y luego se eliminarán, manteniendo únicamente resultados agregados y material reproducible sin datos personales. Si una norma institucional exige otro plazo o instrumento, se ajustará antes de recoger información.

### Registro y preguntas de cierre

Por tarea: código de participante, condición, categoría, inicio y fin, resultado, incumplimientos, número de aclaraciones y observaciones. Preguntas posteriores, en escala de 1 a 5: facilidad para encontrar información, claridad de la respuesta, facilidad para verificar fuentes y utilidad para decidir. Se añadirá una pregunta abierta sobre errores o información faltante. No se presentará este instrumento propio como una escala estandarizada validada.

Las diferencias de tiempos o valoraciones se reportarán como observadas en esta muestra. La ausencia de participantes dejará esta parte pendiente; las pruebas técnicas no la reemplazarán.

## Prueba de incorporación de otra tienda

Se preparará un segundo conjunto ficticio con perfil, moneda, política y categoría diferentes, incluyendo algunos identificadores iguales a los de Nexo Demo. El adaptador de origen podrá cambiar; el núcleo de recuperación, conversación y presentación conservará sus comportamientos. Se probarán mapeo de identificadores, citas, políticas, unidades, vigencia, aislamiento y reinicio de sesión.

El resultado exigido será la sustitución documentada y las pruebas de contrato aplicables pasando, sin editar reglas específicas del núcleo para cada tienda. Esta batería demuestra el comportamiento de sustitución probado, no la compatibilidad automática con cualquier sistema comercial real.

## Condiciones previas y pendientes

Antes de la evaluación final deben existir las fuentes, referencias comprobadas, particiones reservadas, ejecutor de pruebas, candidato versionado, entorno y presupuesto de rendimiento registrados. Se fijará además un límite de tiempo por tarea durante el ensayo previo, sin usar resultados finales para elegirlo.

Permanecen pendientes la creación de escenarios, la revisión de referencias, los participantes reales y toda ejecución del protocolo. Las metas o cuotas solo podrán modificarse con versión, razón y fecha antes de abrir el conjunto final; cualquier cambio posterior se declarará y motivará una nueva evaluación independiente.
