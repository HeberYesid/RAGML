# Desarrollo por fases del asistente RAG para una tienda

Fecha de revisión: 4 de noviembre de 2026.

El proyecto se organizará en ocho fases para construir y evaluar un asistente web en español que responda consultas, compare productos y oriente compras con evidencia de una tienda. La ruta comienza con la selección de la tienda y la definición de las pruebas, continúa con los datos y el sistema, y termina con la evaluación y la entrega académica.

Este documento registra la ruta del proyecto. La revisión inicial se realizó y la fase 1 cuenta con una [definición documental de Nexo Demo](002-fase-1-definicion.md), adoptada tras la elección del usuario de trabajar con un catálogo ficticio fácilmente sustituible por una tienda real. La fase 2 completó la [base técnica local](../docs/architecture/README.md): contratos ejecutables, API de base, modelos locales fijados y verificación. La preparación paralela de fase 3 ya contiene el catálogo y corpus; todavía no hay chatbot integrado ni piloto ejecutado.

## Estado comprobado y documentos revisados

Carpeta revisada: `C:\Users\HeberYesid\Desktop\Universidad Trabajos\RAGML`.

Al iniciar la revisión contenía exclusivamente los tres archivos siguientes. No había código, configuración de dependencias, pruebas, catálogo, corpus documental de productos ni repositorio Git en esta carpeta. Esto describe la evidencia local disponible y no permite descartar trabajo guardado en otra ubicación.

| Fuente | Contenido comprobado | Uso en este plan |
| --- | --- | --- |
| [Fundamentos del asistente](../Fundamentos_Asistente_Conversacional_Tienda_RAG.docx) | Título, problema, objetivos, justificación, estado del arte, propuesta de evaluación y ocho referencias | Define el producto, sus límites y las obligaciones de evaluación |
| [Guía del primer informe](../Primer%20Informe%20del%20Proyecto%20(1).pdf) | Una página que solicita título, problema, objetivos, justificación, estado del arte y referencias | Define la estructura de la primera entrega académica |
| [Guía del informe de avance](../Informe%20de%20avance.pdf) | Una página que solicita objetivo, avances, resultados con evidencias, dificultades, pendientes y conclusiones | Define la estructura del informe que, por aclaración del usuario, se entregará al finalizar el proyecto |

Los PDF son instrucciones de elaboración; no son informes diligenciados ni prueban resultados. El Word ya desarrolla las seis secciones solicitadas por la primera guía, pero esa correspondencia estructural no demuestra aprobación académica ni validación del contenido.

Se revisó el texto completo del Word, incluidas sus dos tablas y sus referencias; también se comprobaron las partes adicionales de notas y pie de página. No se encontraron comentarios ni inserciones o eliminaciones con control de cambios. Los dos PDF se leyeron y se inspeccionaron visualmente. Esta revisión se centró en contenido, alcance y planificación; no incluye una auditoría de maquetación del Word ni una nueva verificación externa de su bibliografía.

### Evidencia que determina el alcance

- Secciones 2 1 y 2 4 del Word: una tienda, distintas categorías y un prototipo web en español. Posteriormente el usuario eligió un catálogo de demostración; se definió Nexo Demo.
- Secciones 2 2 y 2 4: fichas, manuales y políticas como evidencia documental; precios y existencias desde registros actualizados; asociación entre producto, variante y fuente.
- Sección 2 4: el prototipo permite consulta y orientación. Excluye pagos, ejecución de compras, gestión de devoluciones y seguimiento individual de pedidos. Sí incluye explicar políticas documentadas.
- Secciones 2 5 y 5 7: caracterización con usuarios, respuestas de referencia, separación entre ajuste y evaluación final y definición anticipada de participantes y aceptación.
- Secciones 4 2, 5 6 y 5 7: RAG básico como referencia, sistema integrado como alternativa y comparación con la consulta convencional del catálogo y sus documentos.
- Secciones 4 4 y 5 7: actualización, costos, cobertura por categoría, participación informada y límites frente a instrucciones contenidas en los documentos.

### Decisiones y pendientes actualizados

| Decisión | Momento de resolución | Consecuencia |
| --- | --- | --- |
| Catálogo de demostración Nexo Demo y fuentes sintéticas propias | Resuelto en fase 1 por autorización del usuario | Permite controlar datos; no equivale a validación de una empresa real |
| Seis categorías, 60 productos y 90 variantes como meta | Definido en fase 1; se construirá y comprobará en 3 | El inventario está especificado, todavía no generado |
| Instrumentos preparados y meta de ocho participantes | Definido documentalmente; reclutamiento y aplicación pendientes | No se inventan participantes ni diagnóstico observado |
| Protocolo, métricas, metas y reparto de 60 casos de ajuste y 60 finales | Diseño fijado en fase 1; casos concretos y referencias en 3 | Evita elegir metas después de conocer resultados |
| Tecnologías, modelos locales y presupuesto de diseño sin servicios de pago | Cerrado en fase 2; rendimiento del RAG se medirá al integrar | Versiones, hashes, límites y comandos en arquitectura |
| Instantáneas comerciales sintéticas; 15 minutos como vigencia inicial configurable para una futura fuente real | Definido en fase 1; contratos en 2 e implementación en 5 | La fecha de lectura no sustituye la de actualización de la fuente |
| Disponibilidad del equipo y fecha de entrega | Fase 1 | Permite convertir las fases en un cronograma realista |
| Destino de una eventual publicación | Después de definir la entrega | Requiere autorización específica; no es condición del prototipo local |

No se atribuyen al proyecto mejoras de ventas, ahorro, satisfacción o exactitud antes de medirlas. Los resultados numéricos citados en el estado del arte pertenecen a otros trabajos y no se utilizan como resultados ni metas automáticas de este prototipo.

## Alcance que se debe conservar

El resultado final deberá consultar el catálogo incorporado de una tienda y cubrir sus categorías, con atributos comunes y específicos. La incorporación puede empezar con un lote controlado, pero el lote inicial no reemplaza el alcance final. Las carencias documentales se registrarán y se reflejarán en las respuestas.

Para Nexo Demo se construirán seis categorías con 60 productos y 90 variantes. El usuario requiere que una tienda real pueda incorporarse sustituyendo configuración, fuentes y adaptadores, conservando el núcleo del asistente. La [definición de fase 1](002-fase-1-definicion.md) detalla ocho requisitos de sustitución y la prueba prevista con un segundo conjunto ficticio.

El asistente deberá responder preguntas de productos y políticas, buscar por necesidades y presupuesto, comparar alternativas pertinentes, justificar recomendaciones y gestionar aclaraciones durante la conversación. Cuando falte evidencia, deberá aclarar, abstenerse o indicar el canal humano disponible. No se presupone una integración automática con personal de atención.

Los precios y las existencias se consultarán en registros estructurados con fecha y procedencia. No se tomarán cifras de un fragmento documental como confirmación de vigencia. Las compatibilidades, garantías y demás atributos solo se afirmarán si existe respaldo.

La evaluación cubrirá una muestra justificada de categorías y consultas. Se distinguirá la cobertura del catálogo de la cobertura evaluada; incorporar un producto no prueba que su asesoría esté validada.

## Arquitectura funcional propuesta

La consulta del usuario llegará a una capa de conversación que identificará la intención, resolverá referencias a productos y conservará los requisitos de la sesión. Esta capa coordinará dos fuentes: recuperación de documentación y consulta del catálogo estructurado. La respuesta utilizará la evidencia obtenida y presentará referencias y límites comprensibles para el usuario.

La ingesta documental conservará identificadores y ubicaciones de las fuentes; la actualización comercial tendrá su propio procedimiento. Los documentos recuperados se tratarán como datos y no podrán cambiar las reglas del asistente. Se registrarán las versiones y mediciones necesarias para evaluar sin almacenar identificadores personales innecesarios.

La fase 2 seleccionó Python, FastAPI/Uvicorn, Pydantic, SQLite, interfaz HTML/CSS/JavaScript nativo y modelos Qwen locales mediante Ollama. La base de servicio, contratos y adaptadores de modelos están implementados; recuperación, conversación e interfaz se integrarán en sus fases. Las decisiones y límites están en la [documentación de arquitectura](../docs/architecture/decisions.md), contrastados con documentación vigente e inferencia local.

## Fase 1 Definir la tienda los requisitos y la evaluación

**Objetivo:** convertir los fundamentos académicos en requisitos verificables y un piloto delimitado. **Dependencias:** ninguna. **Estado:** IN PROGRESS; definición de demostración, requisitos, protocolo e instrumentos preparados. Aplicación con participantes y revisión académica pendientes.

### Actividades

1. Seleccionar la tienda y confirmar qué documentos y registros se pueden usar. Si se trabaja con demostración, identificarla expresamente y registrar los límites de esa decisión.
2. Inventariar categorías, productos, variantes y fuentes disponibles. Identificar cómo se mantienen precios y existencias.
3. Preparar y aplicar la caracterización mediante entrevistas y tareas de consulta con participación informada. Si aún no hay participantes, mantener el diagnóstico como pendiente y distinguir los requisitos provisionales.
4. Registrar requisitos funcionales, límites, casos de aclaración y criterios de respuesta, con trazabilidad a los objetivos del Word.
5. Diseñar la evaluación: tipos de consultas, respuestas o criterios de referencia, categorías, muestra, participantes, métricas, umbrales y reparto entre ajuste y evaluación final. Las recomendaciones podrán tener varias respuestas válidas.
6. Definir tareas equivalentes para comparar el catálogo y sus documentos con el asistente. Separar esa comparación con usuarios de la comparación técnica entre RAG básico y sistema integrado.
7. Completar decisiones de recursos, calendario y responsables. Contrastar las referencias bibliográficas antes de presentar afirmaciones basadas en ellas y preparar la primera entrega según la guía institucional.

**Entregables previstos:** diagnóstico, inventario inicial, matriz de requisitos y fuentes, protocolo de evaluación, instrumentos, registro de decisiones y primer informe académico revisado. Ubicación propuesta: `docs/requirements/`, `docs/evaluation/` y `docs/reports/`.

**Criterio de cierre:** cada requisito tiene una forma de comprobarse; la procedencia y permisos de los datos están definidos; el protocolo fija muestras y criterios antes de evaluar. El equipo conoce qué está respaldado por diagnóstico y qué sigue siendo provisional. Los casos concretos de referencia se completarán y se comprobarán con las fuentes de la fase 3.

La decisión posterior de usar datos de demostración se desarrolla en la [definición de Nexo Demo](002-fase-1-definicion.md), el [protocolo e instrumentos](phase-1/evaluation-protocol.md) y las [notas internas de trabajo](phase-1/working-notes.md). La caracterización descrita en esos archivos es un instrumento preparado y no una entrevista realizada. La arquitectura puede prepararse con estos requisitos, conservando los pendientes de cierre. El informe de avance corresponde al cierre del proyecto en la fase 8.

## Fase 2 Diseñar la arquitectura y preparar la base técnica

**Objetivo:** establecer contratos y un entorno verificable antes de implementar funciones. **Dependencias:** definición documental de fase 1 disponible; sus pendientes empíricos continúan abiertos. **Estado:** DONE para la base técnica local.

### Actividades

1. Elegir lenguaje, componentes de servidor e interfaz, almacenamiento del catálogo e índice de recuperación, modelo generativo y modelo de representaciones. Justificar cada elección por volumen, español, calidad, costo, restricciones y facilidad de ejecución.
2. Definir contratos para productos, variantes, atributos por categoría, fuentes, fragmentos, consultas, respuestas, citas y errores. Distinguir valores desconocidos, falta de existencias y registros ausentes.
3. Diseñar el flujo de consulta documental y comercial, la gestión de sesiones y los límites de acceso. Separar las fuentes recuperadas de las instrucciones del sistema.
4. Acordar vigencia, actualización y respuesta ante fallos de las fuentes comerciales. Estimar el presupuesto de ingesta, almacenamiento, evaluación y uso.
5. Preparar estructura local, configuración de ejemplo sin secretos, dependencias fijadas y ejecutor de pruebas. Registrar los comandos reales de instalación, pruebas, análisis estático y compilación que correspondan al proyecto.
6. Comprobar los comportamientos implementados con casos relevantes. El usuario indicó expresamente desarrollar sin TDD por tratarse de un prototipo de clase; no se exige ni se afirma evidencia RED/GREEN. Se conservan las verificaciones de funcionamiento, análisis estático y tipos aplicables.

**Entregables previstos:** arquitectura, contratos de datos e interfaz de servicios, decisiones técnicas, entorno local y matriz de comandos. Ubicación propuesta: `docs/architecture/` y archivos de configuración que determine la tecnología elegida.

**Criterio de cierre:** el entorno se puede preparar siguiendo instrucciones; el ejecutor de pruebas funciona y sus resultados se han observado; los contratos cubren producto y variante, citas, vigencia y errores. Las herramientas y comandos se conocen antes de implementar la ingesta y el RAG. Si el ejecutor no funciona, se pausa la implementación afectada.

**Cierre comprobado:** selección de tecnologías y modelos, configuración local validada, contratos de catálogo/comercio/fuentes/fragmentos/citas/chat/sesiones/errores, puertos de servicios, adaptador comercial y de Ollama, API de base y paquete instalable. Pasan 44 comprobaciones, análisis estático, formato y tipos. Hubo generación y embeddings reales con modelos fijados y prueba HTTP real desde un wheel instalado en un entorno separado. El presupuesto y las metas están definidos; su cumplimiento sobre el RAG completo se medirá en las fases siguientes. Véanse [cierre de arquitectura](../docs/architecture/README.md), [contratos](../docs/architecture/contracts.md) y [comandos y evidencia](../docs/architecture/local-environment.md).

## Fase 3 Preparar el catálogo y la base documental

**Objetivo:** disponer de datos autorizados, consistentes y trazables. **Dependencias:** definición documental de fase 1 y base técnica de fase 2. **Estado:** DONE; catálogo y corpus sintéticos, ingesta SQLite, índice de vectores y particiones de referencia comprobados. No incluye ejecutar la evaluación final ni completar el asistente.

### Actividades

1. Organizar el catálogo con identificadores estables de producto y variante, categoría, atributos, unidad, moneda, precio, existencias, fecha y procedencia cuando corresponda.
2. Recopilar fichas, manuales, preguntas frecuentes y políticas autorizadas. Registrar documento, versión, producto o alcance general, y ubicación de la evidencia.
3. Extraer y limpiar texto preservando el sentido de tablas, unidades, condiciones y variantes. Si una fuente requiere reconocimiento de texto, comprobar la calidad de la extracción antes de usarla.
4. Dividir e indexar documentos conservando el vínculo de cada fragmento con su fuente. Las políticas generales de tienda no deben recibir una asociación ficticia a un producto.
5. Detectar duplicados, identificadores huérfanos, atributos ausentes, datos contradictorios y fechas inválidas. Mantener un informe de cobertura por producto y categoría.
6. Incorporar por lotes hasta alcanzar el catálogo acordado. Construir respuestas y fragmentos de referencia; separar los casos de ajuste de los de evaluación y restringir el uso de estos últimos.
7. Probar actualización, sustitución y retirada de información sin duplicar contenido ni conservar fragmentos obsoletos como vigentes.

**Entregables previstos:** catálogo normalizado, manifiesto de fuentes, proceso de ingesta, informe de calidad y cobertura, y conjuntos separados de ajuste y evaluación. Rutas propuestas para muestras autorizadas: `data/sample/` y `tests/fixtures/`; los datos reales se almacenarán según sus permisos y no se incorporarán automáticamente al control de versiones.

**Criterio de cierre:** cada registro y fragmento tiene procedencia verificable; los identificadores son consistentes; los datos ausentes se conservan como desconocidos; los errores y la cobertura están inventariados. La ingesta y la retirada superan sus pruebas, y los casos de referencia se verifican contra la versión documentada de las fuentes.

**Cierre comprobado:** 60 productos, 90 variantes, 90 registros comerciales y 72 documentos con 204 fragmentos y embeddings locales. Los contratos, hashes y asociaciones se comprobaron; la ingesta sustituye y retira revisiones mediante una transacción y conserva la anterior ante fallos. Pasan 59 comprobaciones de base e ingesta, incluidas 15 nuevas. Se prepararon 60 escenarios de ajuste y 60 finales reservados con referencias comprobadas y limitaciones de autoría compartida declaradas. Se conserva un reloj sintético para datos comerciales. Véanse [datos y límites](../docs/data/README.md), [ingesta](../docs/data/ingestion.md) y [particiones](../data/evaluation/README.md). Este cierre no acredita calidad de recuperación, generación, utilidad con personas ni evaluación final.

## Fase 4 Implementar y medir el RAG básico

**Objetivo:** construir una referencia funcional de recuperación y respuesta antes de añadir asesoría compleja. **Dependencias:** fases 2 y 3. **Estado:** TODO.

### Actividades

1. Implementar la recuperación de fragmentos con filtros pertinentes de producto, variante y categoría. Incluir las políticas generales cuando corresponda.
2. Generar respuestas en español respaldadas por esos fragmentos y ofrecer citas que permitan revisar la evidencia.
3. Implementar el manejo de consultas ambiguas, evidencia insuficiente y documentos contradictorios. Las preguntas de precios y existencias no se confirmarán con datos documentales antiguos.
4. Medir Recall@k, correspondencia de citas, corrección y latencia sobre el conjunto de ajuste. Registrar k, configuración, fuentes y costos disponibles.
5. Guardar una configuración y resultados reproducibles del RAG básico para su comparación posterior. Las mejoras de recuperación contextual, búsqueda híbrida o reordenamiento se incorporarán solo si las pruebas de ajuste justifican su costo y latencia.

**Entregables previstos:** servicio de RAG básico, pruebas, referencias verificables y mediciones de ajuste. Ubicación propuesta: módulos que determine la fase 2, `tests/` y `docs/evaluation/`.

**Criterio de cierre:** las pruebas de recuperación, citas y manejo de ausencia de evidencia pasan; se cumplen los criterios preliminares fijados en el protocolo o se documenta el incumplimiento. Existe una configuración básica conservada para comparar. Estos resultados son desarrollo y ajuste, no evaluación final ni validación con usuarios.

## Fase 5 Integrar datos comerciales y asesoría conversacional

**Objetivo:** responder con datos comerciales comprobables y recomendar según requisitos explícitos. **Dependencias:** fase 4. **Estado:** TODO.

### Actividades

1. Consultar precios y existencias en la fuente estructurada, vinculando producto y variante exactos. Conservar fecha y procedencia y aplicar la política de vigencia definida.
2. Gestionar necesidad, presupuesto, preferencias y requisitos obligatorios durante la sesión. Pedir aclaraciones útiles y resolver referencias como «el segundo» o «uno más económico».
3. Buscar y comparar alternativas con atributos adecuados para cada categoría. Aplicar restricciones explícitas y explicar los motivos de selección.
4. Mantener el contexto cuando cambien presupuesto, requisitos o categoría, sin mezclar productos o sesiones. La falta de alternativas deberá producir una explicación y una aclaración pertinente.
5. Gestionar productos agotados, precios desconocidos, fuentes no disponibles, atributos incompletos y evidencia contradictoria. No inventar descuentos, compatibilidades ni condiciones.
6. Registrar evidencia documental y consulta comercial por separado para analizar sus efectos. Mantener disponible la configuración básica de la fase 4.

**Entregables previstos:** consulta comercial, gestión de conversación y comparación, reglas de recomendación y pruebas con datos controlados.

**Criterio de cierre:** las pruebas demuestran correspondencia de precios y existencias con su fuente, cumplimiento de requisitos y manejo de incertidumbre. Un cambio controlado del registro comercial se refleja en la siguiente consulta conforme a la política acordada, sin depender de reindexar manuales. Los fallos no producen confirmaciones comerciales sin respaldo.

## Fase 6 Construir e integrar el prototipo web

**Objetivo:** ofrecer un recorrido completo de consulta en español para uso y evaluación. **Dependencias:** fase 5. **Estado:** TODO.

### Actividades

1. Implementar conversación, presentación de productos, comparación y acceso a fuentes. Mostrar la vigencia comercial y la condición de datos de prueba cuando aplique.
2. Representar espera, errores, consultas sin respuesta y aclaraciones de forma comprensible. Permitir iniciar una conversación nueva y revisar las referencias.
3. Integrar los servicios y probar consultas informativas, políticas, recomendaciones y cambios de requisitos en pantallas de escritorio y móviles, con navegación por teclado.
4. Verificar aislamiento de sesiones, límites de entrada, tratamiento de errores y ausencia de secretos en el cliente. Probar instrucciones maliciosas contenidas en fuentes y su incapacidad para cambiar las reglas del asistente.
5. Medir tiempos y consumos del recorrido completo, y corregir defectos con los casos de ajuste. Registrar versiones y configuración del candidato a evaluación.

**Entregables previstos:** prototipo local integrado, guía de ejecución, pruebas de integración y de recorridos completos, y evidencias de revisión visual.

**Criterio de cierre:** los recorridos acordados funcionan de extremo a extremo, las comprobaciones técnicas pasan y la revisión visual está documentada. La cobertura coincide con el inventario acordado y sus carencias están declaradas. Al terminar esta fase existe un prototipo funcional candidato a evaluación, todavía sin una conclusión de utilidad demostrada.

## Fase 7 Evaluar el prototipo y analizar los resultados

**Objetivo:** determinar la calidad y utilidad del sistema siguiendo el protocolo previamente fijado. **Dependencias:** fase 6 y protocolo de fase 1. **Estado:** TODO.

### Actividades

1. Fijar versiones del catálogo, corpus, índice, modelos, reglas y configuración. Utilizar los casos reservados sin reajustar el sistema a partir de sus respuestas.
2. Comparar técnicamente RAG básico y sistema integrado. Conservar modelo generativo y fuentes cuando sea posible y declarar otras diferencias, especialmente el acceso a datos comerciales.
3. Comparar la consulta convencional del catálogo y documentos con el asistente mediante tareas equivalentes, alternando el orden de uso según el protocolo.
4. Medir recuperación, corrección de producto y variante, vigencia comercial, fidelidad, citas, cumplimiento de requisitos y manejo de información insuficiente. Complementar con éxito de tareas, valoración humana, tiempos, latencia y costo.
5. Analizar errores y resultados por tarea y categoría cuando la muestra lo permita. Documentar tamaños de muestra, cobertura y límites de generalización.
6. Si los resultados requieren cambios, volver al desarrollo con los casos de ajuste. Evaluar otra versión con nuevos casos reservados o declarar expresamente que una repetición es exploratoria.

**Entregables previstos:** ejecución versionada, resultados y rúbricas, análisis comparativo, errores y limitaciones. Ubicación propuesta: `docs/evaluation/` y `docs/reports/`, con registros anonimizados según los permisos establecidos.

**Criterio de cierre:** cada resultado es trazable a una ejecución y fuente; se informa el cumplimiento o incumplimiento de los criterios fijados. Se distingue funcionamiento técnico de utilidad con usuarios. Si no hay participantes, queda pendiente la evaluación de utilidad y no se afirma validación real de tienda a partir de pruebas técnicas o datos de demostración.

## Fase 8 Cerrar la documentación y preparar el mantenimiento

**Objetivo:** entregar el proyecto reproducible, con conclusiones proporcionales a la evidencia. **Dependencias:** fase 7. **Estado:** TODO.

### Actividades

1. Consolidar problema, objetivos, antecedentes, metodología, arquitectura, implementación, evaluación, resultados, discusión, conclusiones y referencias según las instrucciones académicas que estén vigentes para la entrega final. La guía disponible solo fija la estructura del primer informe.
2. Preparar anexos con instrumentos, casos autorizados, rúbricas, cobertura, configuración y evidencias. Evitar incluir datos personales o material sin permiso.
3. Documentar instalación, configuración, uso, actualización comercial, ingesta, retirada documental, incorporación de categorías y respuesta ante fallos.
4. Repetir la preparación y ejecución local con las instrucciones de entrega y registrar las comprobaciones. Preparar la demostración con datos que puedan mostrarse.
5. Revisar citas y referencias, trazabilidad de objetivos y coherencia entre resultados y conclusiones. Registrar limitaciones y trabajo futuro.
6. Preparar y entregar el informe de avance al finalizar todo el proyecto, con los seis apartados de la guía y las evidencias acumuladas. Esta entrega corresponde a la fase 8 por aclaración del usuario.

**Entregables previstos:** informe de avance consolidado para la entrega al finalizar el proyecto, informe final, anexos, manual técnico, guía de uso y paquete local reproducible. La presentación o un despliegue se prepararán cuando formen parte de la entrega autorizada.

**Criterio de cierre:** otra persona puede preparar y ejecutar el prototipo con las instrucciones; el informe refleja las pruebas observadas y sus límites; el procedimiento de actualización está comprobado. Los criterios no cumplidos permanecen explícitos y no se ocultan mediante un promedio o una declaración general de éxito.

## Trazabilidad de los objetivos

| Objetivo específico del Word | Fases que lo desarrollan | Evidencia de cierre |
| --- | --- | --- |
| Caracterizar necesidades, categorías y requisitos | 1 | Diagnóstico, requisitos y protocolo |
| Conformar base documental y catálogo | 3 | Fuentes, datos, calidad y cobertura |
| Diseñar arquitectura integrada y contexto conversacional | 2 y 5 | Arquitectura, contratos y pruebas de conversación |
| Implementar prototipo web para consulta y asesoría | 4, 5 y 6 | Servicios, interfaz y recorridos completos |
| Evaluar corrección, respaldo, requisitos y utilidad | Diseño en 1; ejecución en 7 | Resultados comparativos y análisis humano |
| Documentar resultados, límites y actualización | Todas; consolidación en 8 | Informes, manuales y reproducción local |

## Verificación durante el desarrollo

La línea base inicial no incluía herramientas de verificación. En fase 2 se preparó el entorno Python y se observaron 44 comprobaciones pasando, además de análisis estático, formato y tipos sin errores, construcción e instalación del paquete e inferencia local real. La [matriz de comandos](../docs/architecture/local-environment.md) identifica alcance, dependencias y límites; no hay compilación de frontend ni revisión de navegador porque esas partes todavía no existen.

Se trabaja sin TDD por indicación del usuario. Las comprobaciones incluyen casos relevantes, análisis estático, tipos y compilación cuando corresponda, además de revisión del cambio. Una comprobación estructural no reemplaza una ejecución, y una ejecución técnica no reemplaza revisión visual ni evaluación con usuarios.

No se deben introducir frameworks, bases de datos o servicios por suposición. Las decisiones dependientes de bibliotecas o proveedores se verificarán con documentación vigente mediante Context7 y, si corresponde, fuentes oficiales. Un destino remoto y sus credenciales requieren autorización específica.

## Seguimiento académico y control del alcance

Durante cada fase se conservarán evidencias y notas internas de trabajo. El usuario aclaró que el informe de avance se entrega al finalizar todo el proyecto: se preparará en la fase 8 con los seis apartados de la guía, objetivo del informe, avances, resultados con evidencia explicada, dificultades, actividades pendientes y conclusiones. Se distinguirá lo previsto de lo ejecutado y lo probado de lo evaluado con participantes.

El orden recomendado es 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Algunas tareas documentales pueden avanzar en paralelo, pero una fase solo se marca DONE cuando sus criterios están respaldados. El cronograma se fijará al conocer recursos, volumen y fecha de entrega.

Detener y comunicar la actividad afectada si falta permiso sobre una fuente, se supera el presupuesto autorizado, el ejecutor de pruebas no funciona, se requiere ampliar el alcance o aparece un cambio sustancial en los documentos de fundamento. La falta de una tienda real permite avanzar con una demostración identificada como tal, pero no atribuirle validación comercial real.

## Línea base de la revisión

No hay commit de referencia porque la carpeta no estaba inicializada como repositorio Git. Para futuras revisiones, los SHA256 de los documentos fuente al elaborar el plan son los siguientes:

| Archivo | SHA256 |
| --- | --- |
| Fundamentos_Asistente_Conversacional_Tienda_RAG.docx | `d18774107411ea301f3971219eb282f216b97b51664c8f8332db69e105d3d0e9` |
| Informe de avance.pdf | `0bfb96bd205c3c4bfd071e256c303deb772f0214109a4e9643deeab344dc62e1` |
| Primer Informe del Proyecto (1).pdf | `d2391d479e43505ab04e71804bf261313678e8baceb90333a4a5f20fd2c2d7c4` |

Si cambia una fuente, revisar su alcance y los criterios del plan antes de continuar. Esta línea base documenta los archivos revisados; no confirma la vigencia de sus referencias externas.
