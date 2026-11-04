# Datos de demostración de Nexo Demo

Fase 3, 4 de noviembre de 2026. Estado: preparación técnica completada; catálogo, corpus, ingesta, índice local y particiones de referencia comprobados. La recuperación, el chat y su evaluación pertenecen a las fases siguientes.

Este paquete utiliza la base local completada en la fase 2. Contiene especificaciones originales inventadas, sin datos de una tienda, fabricantes o participantes reales. Se conserva `data_mode: demo` y no se presenta como evidencia de condiciones comerciales reales.

## Inventario construido

| Componente | Cantidad | Ubicación |
| --- | --- | --- |
| Categorías | 6 | Perfil incluido en [catálogo](../../data/sample/catalog.json) |
| Productos base | 60 | [Catálogo](../../data/sample/catalog.json) |
| Variantes vendibles | 90 | [Catálogo](../../data/sample/catalog.json) |
| Registros comerciales | 90 | [Instantánea comercial](../../data/sample/commercial.json) |
| Fichas de producto | 60 | `data/sample/documents/products/` |
| Guías de categoría | 6 | `data/sample/documents/guides/` |
| Políticas ficticias | 6 | `data/sample/documents/policies/` |
| Fuentes documentales | 72 | [Manifiesto](../../data/sample/sources.json) |
| Fragmentos por sección | 204 | Incluidos en el manifiesto, con ubicación y hash |
| Vectores locales de 1024 dimensiones | 204 | Índice derivado en `data/runtime/corpus.sqlite3` |
| Escenarios de ajuste | 60 | [Particiones de evaluación](../../data/evaluation/README.md) |
| Escenarios finales reservados | 60 | Archivo separado; no utilizado para ajustar ni evaluar el asistente |

Cada categoría tiene diez productos y 15 variantes: cinco productos con dos presentaciones y cinco con una presentación única. Las opciones A y B cambian el empaque ficticio y su registro comercial; no cambian los atributos técnicos comunes. La variante es la unidad de precio y existencias.

La revisión activa es `demo-20261104-v2`. Los identificadores de producto, variante y fuente no dependen de la posición de una fila. El [registro del paquete](../../data/sample/package-metadata.json) contiene revisión, procedencia, cantidades, cobertura y huellas de los 75 archivos de datos y fuentes; el archivo de metadatos es el archivo número 76 y no se incluye en su propio hash.

## Asociación de datos y evidencia

Los atributos conocidos apuntan a la ficha de su producto. Los atributos desconocidos conservan `null`; no se transforman en cero. Las guías tienen alcance de categoría y las políticas alcance de tienda, sin asociaciones inventadas a un producto.

Cada fuente conserva identificador, versión, ruta relativa controlada, procedencia sintética y SHA256 de sus bytes. Cada fragmento es una sección exacta de su documento, con hash propio y encabezado localizable. Se generaron embeddings reales mediante el modelo local y se publicaron en SQLite. Esto no demuestra relevancia de recuperación ni calidad de respuestas; esas capacidades se medirán después.

Los registros comerciales permanecen separados de las fichas. Los precios se representan como cadenas decimales y COP tiene precisión de cero decimales en este perfil. Las referencias comerciales identifican variante y campo. La documentación de producto no confirma precios ni existencias.

## Tiempo simulado y condiciones de prueba

La instantánea se creó con tiempo sintético de referencia `2026-11-04T12:00:00Z`. El reloj recomendado de comprobación es `2026-11-04T12:05:00Z`, registrado en los metadatos. No es la hora de actualización de una empresa real ni una afirmación de vigencia al abrir el prototipo otro día.

Cada observación tiene ventana explícita de 15 minutos. El producto número diez de cada categoría tiene intencionalmente un precio anterior y vencido al tiempo de comprobación. Las existencias de ese producto sí pertenecen a la ventana de referencia, para verificar vigencia independiente.

| Condición al tiempo de referencia | Cantidad comprobada |
| --- | --- |
| Precios vigentes simulados | 78 |
| Precios desconocidos | 6 |
| Precios vencidos | 6 |
| Estados de existencias vigentes simulados | 84 |
| Disponibilidad desconocida | 6 |
| Agotados con cantidad cero, incluidos entre los estados vigentes | 6 |
| Disponibles con cantidad exacta desconocida, incluidos entre los estados vigentes | 6 |

Una consulta con el reloj real posterior a la caducidad deberá informar datos vencidos; no se debe extender automáticamente su ventana ni sustituir la fecha de origen por la fecha de lectura. Para una nueva sesión interactiva se puede publicar explícitamente otra revisión sintética con un tiempo nuevo. Su exposición en el asistente se resolverá durante la integración conversacional; esta preparación no añade una renovación silenciosa ni cambia el reloj del servidor.

## Generación y comprobación reproducibles

El [generador](../../scripts/build_demo_data.py) usa la biblioteca estándar, no un modelo generativo. Las especificaciones inventadas están declaradas en su conjunto de datos; el formato de salida utiliza los contratos del proyecto. La sustitución futura por una tienda real se realizará mediante su configuración y adaptadores, sin utilizar este generador ficticio como conector real.

Desde la raíz, verificar que los 76 archivos coinciden con la generación determinista, sin escribir:

```powershell
.\.venv\Scripts\python.exe scripts\build_demo_data.py --as-of '2026-11-04T12:00:00Z' --revision 'demo-20261104-v2' --check
```

Verificar contratos, integridad de fuentes, cobertura y consulta comercial, y guardar el resultado técnico:

```powershell
.\.venv\Scripts\python.exe scripts\validate_demo_data.py --output docs/data/validation-results.json
```

El [validador](../../scripts/validate_demo_data.py) utiliza los contratos actuales de `src/ragml/contracts.py`, `commercial.py` y `evidence.py`. Se debe repetir cuando la fase 2 cambie sus contratos. El [resultado observado](validation-results.json) corresponde a una comprobación local de datos, no al protocolo final de evaluación ni a un informe académico de avance.

Para volver a publicar datos de demostración se requiere indicar un tiempo con zona, una revisión nueva y `--replace-generated`. Ese indicador solo permite reemplazar un paquete identificado como salida de este generador. Sin él se rechaza sobrescribir datos existentes; también se rechazan destinos fuera de una subcarpeta de `data/` y cambios de contenido que intenten reutilizar la misma revisión.

El generador no elimina archivos ajenos ni importa datos privados. Los cambios manuales de sus salidas deberán incorporarse a una fuente de datos mantenida y versionada antes de regenerar; no se debe usar la opción de reemplazo sobre trabajo que se quiera conservar.

Este generador publica el paquete de demostración completo, por lo que una revisión nueva también cambia las versiones documentales y requiere actualizar el índice cuando exista. No sustituye el mecanismo de actualización comercial independiente: el adaptador comercial de la fase 2 permite publicar sus propios registros sin reconstruir manuales. El validador de este paquete comprueba la publicación inicial conjunta, no impone una revisión única a todas las futuras fuentes de una tienda real.

## Verificación observada

- Los contratos actuales aceptan el catálogo, la instantánea comercial y el manifiesto.
- No se encontraron identificadores huérfanos, atributos de otra categoría, citas de atributo pertenecientes a otro producto ni discrepancias de hash.
- Los 204 fragmentos se localizaron como extractos exactos en sus fuentes; las 72 fuentes tienen fragmentos.
- El adaptador comercial devuelve los estados de precio y existencias indicados y oculta los valores no confirmables.
- La regeneración en modo `--check` coincide con los 76 archivos.
- Se verificó el rechazo de sobrescritura accidental y de uso de `data/` como destino directo.
- El análisis estático y el formato de los dos scripts se comprobaron por separado del trabajo activo en fase 2.

Esta comprobación no es una auditoría semántica independiente de cada especificación inventada. Se revisaron muestras de documentos, asociación de atributos y las reglas explícitas del generador; las respuestas de referencia para evaluar recomendaciones todavía deben comprobarse.

## Cierre técnico de la fase 3

| Criterio | Evidencia |
| --- | --- |
| Compatibilidad con los contratos cerrados de fase 2 | Catálogo, comercio y manifiesto aceptados por el validador actual |
| Ingesta e índice locales | 204 embeddings reales publicados; [medición](ingestion-results.json) |
| Repetición, actualización, retirada y fallos | Pruebas con SQLite real y vectores sintéticos; [procedimiento](ingestion.md) |
| Separación de tiendas | Publicaciones con identificadores repetidos, categorías y monedas diferentes sin contaminación |
| Datos comerciales independientes | Cambiar la revisión comercial no recalcula vectores del mismo corpus |
| Casos y referencias | 60 de ajuste y 60 reservados, cuotas y hechos contrastados con las fuentes |
| Integridad de las particiones y fuentes | [Comprobación por hashes](reference-integrity.json), sin abrir el archivo final |

Las 59 comprobaciones de la base de fase 2 y la ingesta pasan, incluidas 15 nuevas de fase 3. Los vectores reales se generaron en 128,665 segundos y la base ocupó aproximadamente 1,25 MiB. La [guía de ingesta](ingestion.md) describe transacciones, uso y sustitución. Los casos y sus límites están en la [guía de evaluación](../../data/evaluation/README.md).

La [verificación de cierre](phase3-verification.json) registra también una instantánea global del repositorio compartido: 138 pruebas pasan, análisis estático sin errores y tipos correctos en 18 archivos. Los errores observados durante la edición paralela ya no estaban presentes en esa comprobación final. Las pruebas añadidas por otros chats forman parte de ese total global y no se atribuyen a esta entrega de fase 3.

El archivo final está reservado por procedimiento, no cifrado. Las dos particiones comparten autor; esta limitación está registrada. Las referencias se comprobaron con datos, extractos y restricciones, y se inspeccionaron ejemplos de ajuste. Antes de la evaluación final se recomienda una revisión humana independiente de similitud y pertinencia.

## Trabajo de las fases siguientes

La fase 4 consumirá el repositorio e índice y medirá recuperación con ajuste. La fase 5 integrará asesoría y contexto; la fase 6 comprobará el recorrido web; la fase 7 ejecutará la evaluación con candidato fijado y casos reservados. La sustitución del asistente completo por otra tienda y su utilidad con personas no están demostradas por las pruebas de ingesta.

Las comprobaciones globales del repositorio pueden cambiar mientras otros chats implementan esas fases. El cierre aquí corresponde a la preparación e ingesta y no declara terminadas otras funciones ni garantiza que sus archivos en edición pasen todas las verificaciones.

El informe de avance académico se preparará y entregará al finalizar todo el proyecto. Mientras tanto, este documento y los resultados del validador conservan la trazabilidad técnica.
