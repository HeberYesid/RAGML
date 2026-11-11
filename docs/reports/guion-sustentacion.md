# Guion de sustentación de Nexo Demo

Duración prevista: de 10 a 12 minutos. Este documento prepara la presentación y la demostración; no acredita que la sustentación ya se haya realizado. El equipo debe distribuir las intervenciones según sus integrantes y ensayar los pasos en el mismo computador que utilizará.

## Preparación previa

Desde la raíz del proyecto, iniciar los modelos con `scripts/start-models.ps1 -Background`, comprobar `ragml doctor` mediante el ejecutable del entorno y verificar que el índice corresponde al catálogo actual. Si el índice falta o es incompatible, ejecutar el proceso de ingesta antes de la exposición. Iniciar la interfaz mediante `.\.venv\Scripts\python.exe -m ragml.web` y abrir `http://127.0.0.1:8000`.

Comprobar que se ven el nombre de Nexo Demo, el aviso de datos ficticios y el reloj comercial simulado. Abrir el informe y la presentación. Dejar preparados los gráficos del análisis exploratorio y los registros reales de evaluación. No abrir archivos finales reservados para improvisar ejemplos.

La carga de modelos puede añadir espera. Hacer una consulta de preparación y declarar si la demostración se realiza con modelos ya cargados. La grabación o las capturas de una ejecución anterior pueden acompañar la explicación, con su fecha y versión, pero no deben describirse como una ejecución en vivo.

## Distribución del tiempo

| Tiempo aproximado | Contenido | Evidencia para mostrar |
| --- | --- | --- |
| 0:00 a 1:15 | Problema y alcance. | Situación de consulta y objetivo general. |
| 1:15 a 2:15 | Antecedentes y decisión de usar RAG. | Referencias de Lewis, recuperación densa y evaluación. |
| 2:15 a 3:45 | Dataset y preparación. | Cantidades, faltantes y gráficos exploratorios. |
| 3:45 a 5:00 | Algoritmos y arquitectura. | Flujo de recuperación y separación comercial. |
| 5:00 a 8:30 | Demostración de la aplicación. | Consultas, cambio de presupuesto y citas. |
| 8:30 a 10:00 | Resultados y errores. | Registro de evaluación y límites de cada métrica. |
| 10:00 a 11:30 | Conclusiones y preguntas. | Conclusiones limitadas a lo observado. |

## Apertura

“Nuestro proyecto permite consultar y comparar productos de una tienda de demostración. El problema que estudiamos es reunir información de fichas y políticas sin confundir productos, variantes o condiciones comerciales. Construimos Nexo Demo para repetir las pruebas con datos controlados. No estamos presentando un diagnóstico medido en una empresa ni resultados de ventas.”

Explicar el objetivo general y seleccionar dos o tres objetivos específicos que puedan relacionarse con lo que se mostrará. No leer todos los párrafos del informe.

## Antecedentes

“Los trabajos sobre RAG proponen recuperar información externa para apoyar la respuesta. La investigación en recuperación densa muestra cómo representar preguntas y textos mediante vectores. La evaluación de RAG distingue encontrar evidencia, usarla fielmente y responder a la consulta. Nosotros conservamos esa separación para analizar el sistema.”

Mencionar que los casos comerciales se usan como contexto y que sus resultados no constituyen evidencia del desempeño de Nexo Demo. Si se muestra una cifra de un antecedente, indicar su autor, año y tarea.

## Dataset y procesamiento

Presentar las seis categorías, 60 productos, 90 variantes y 72 fuentes. Explicar que un producto tiene una ficha y que sus variantes pueden tener precio y existencias diferentes. Mostrar un gráfico por categoría y otro sobre desconocidos o estados comerciales.

“Estos datos son sintéticos. Conservamos los valores desconocidos y no los convertimos en cero. Las estadísticas comparan atributos con la misma unidad y dentro de categorías pertinentes. Los valores señalados por IQR se revisan, sin eliminarlos automáticamente.”

Mostrar el reloj de reproducción del 4 de noviembre de 2026 y explicar que los tiempos de ejecución se miden en la fecha real de la prueba. El precio simulado no debe presentarse como una oferta actual de una empresa.

## Algoritmos

“El componente de aprendizaje automático proviene de dos modelos preentrenados. Uno convierte los textos en vectores y el otro selecciona evidencia documental. Calculamos la similitud coseno para recuperar los fragmentos más cercanos a la consulta. Después comprobamos que las citas existan en esos fragmentos. No entrenamos los pesos de los modelos con los 60 productos.”

“El presupuesto, la vigencia y las existencias se verifican mediante datos estructurados y reglas. Esta parte no se presenta como un modelo de recomendación aprendido. Separarla permite comprobar condiciones que una respuesta textual no debería suponer.”

## Secuencia de demostración

Las frases siguientes corresponden a recorridos cubiertos por las pruebas de integración. Antes de la sustentación debe comprobarse su ejecución con los modelos reales y consultar el registro de evaluación de esta entrega. Una prueba con un proveedor simulado no garantiza la calidad de una respuesta real.

1. Iniciar una conversación nueva y escribir **Busco iluminación hasta 200 mil COP**. Mostrar las variantes propuestas, el presupuesto y las fuentes comerciales. Seleccionar una alternativa y explicar por qué cumple las condiciones conocidas.
2. Escribir **¿Cuánto cuesta el segundo?**. Mostrar cómo se resuelve la referencia a una alternativa presentada, conservando su identidad de variante.
3. Escribir **Compara el primero y el segundo**. Revisar los atributos usados y explicar cualquier valor desconocido. Si la consulta anterior altera la lista de referencia, repetir este paso inmediatamente después de una nueva búsqueda de alternativas; no atribuir al sistema una selección que no esté en pantalla.
4. En una nueva búsqueda escribir **Busco iluminación hasta 100 mil COP** y después **Ahora mi presupuesto es de 50 mil COP**. Mostrar si se reduce el conjunto y explicar que un cambio de presupuesto sustituye la condición anterior.
5. Abrir una conversación nueva y escribir **Según la ficha de Lámpara Flexo ¿qué potencia tiene?**. Esperar la respuesta real, abrir la fuente y localizar el extracto. Aclarar que la respuesta es extractiva y que una cita necesita ser pertinente, además de existir literalmente.
6. Mostrar un caso de información insuficiente o de dato vencido que figure en los registros efectivamente ejecutados. Explicar por qué la abstención puede ser el comportamiento esperado. No inventar una respuesta favorable si el caso falla.

Si la aplicación devuelve un error, mostrar el estado y describir su alcance. Si el modelo tarda demasiado, informar la espera y usar una evidencia previa claramente identificada para continuar la explicación. Conservar el error como parte del análisis; reiniciar una demostración no convierte el intento anterior en éxito.

## Interpretación de resultados

“La medición histórica de recuperación obtuvo Recall@5 de 1,00 en 18 casos de ajuste. Esto indica que la evidencia de referencia apareció entre los primeros cinco fragmentos en esos casos. No significa que todas las respuestas sean correctas ni demuestra utilidad con personas. Para el recorrido integrado mostramos por separado los casos ejecutados, sus errores y sus tiempos.”

La medición del 10 de noviembre completó 60 casos de ajuste en dos tramos con la misma huella de candidato: cero errores de ejecución y 50 coincidencias de estado. Hubo 66 turnos HTTP, con p95 de 183,779 segundos; no se alcanzó la meta de 60 segundos. Estos indicadores no equivalen a exactitud semántica. Leer también del registro las versiones y las condiciones. Mencionar un acierto y un fallo o limitación documentados. Si una métrica no fue calculada, decirlo directamente. No usar la cantidad de pruebas de software como tamaño de muestra de clientes.

## Cierre

“El proyecto permite estudiar consulta documental y comparación sobre un catálogo controlado. La trazabilidad muestra de dónde procede una afirmación; la separación comercial evita usar fichas antiguas para confirmar precios. Los límites principales son el dataset sintético, el vocabulario del parser y el costo de inferencia. Las conclusiones corresponden a nuestras ejecuciones y no se generalizan a una tienda real.”

## Preguntas previsibles

**¿Qué modelo entrenaron ustedes?**

Se utilizaron modelos preentrenados. El trabajo del proyecto consiste en preparar las fuentes, calcular su representación, implementar recuperación e integración y evaluar el sistema. No se afirma entrenamiento propio ni fine tuning.

**¿Por qué no usaron regresión o K Means?**

La tarea definida es recuperar evidencia y orientar consultas, no predecir una variable numérica ni descubrir grupos en observaciones. Añadir esos algoritmos requeriría otra pregunta y su evaluación. El informe justifica el enfoque seleccionado y lo relaciona con representación, búsqueda, preparación de datos y ciclo de vida de ML.

**¿RAG es el modelo?**

RAG es la arquitectura que conecta recuperación y uso de evidencia. En esta implementación intervienen un codificador de embeddings y un modelo de lenguaje, junto con algoritmos y reglas deterministas.

**¿Un score de 0,8 significa un 80 % de certeza?**

No. Es una similitud coseno entre representaciones. No está calibrada como probabilidad de que una afirmación sea verdadera.

**¿Por qué conservar faltantes?**

Porque imputar precio, compatibilidad o existencias sin una fuente puede crear una confirmación falsa. El sistema debe señalar qué no puede comprobar.

**¿Por qué no eliminar automáticamente los outliers?**

Un artículo más caro o de mayor tamaño puede ser válido. La señal estadística orienta revisión dentro de una categoría; no demuestra un error del dato.

**¿Qué demuestra una cita literal?**

Demuestra que el extracto aparece en la evidencia suministrada. Su pertinencia y suficiencia para responder necesitan revisión adicional.

**¿Los precios se actualizan hoy?**

Son datos de demostración reproducidos con un reloj simulado visible. No son precios ni existencias actuales de una empresa. Una integración real requiere su fuente y política de actualización.

**¿Evaluaron satisfacción de clientes?**

No se presentan resultados con clientes o participantes porque no se ha realizado ese estudio. La evidencia disponible corresponde a datos sintéticos y comprobaciones técnicas.

**¿Qué pasa al incorporar otra tienda?**

Se necesitan fuentes autorizadas, configuración, mapeos y posiblemente un adaptador. Los contratos reducen el acoplamiento, pero no garantizan una migración sin trabajo ni sin nuevas pruebas.
