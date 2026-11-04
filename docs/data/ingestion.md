# Ingesta y publicación del corpus local

La fase 3 incorpora un repositorio SQLite con una revisión activa por tienda. `src/ragml/ingestion.py` valida las fuentes y publica sus vectores; no implementa respuestas del asistente ni modifica la API de chat de fase 2.

## Ejecución local

Los modelos y el ejecutor ya están instalados por la fase 2. Iniciar únicamente el servidor del proyecto:

```powershell
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\python.exe -m ragml.ingestion --output docs/data/ingestion-results.json
```

La primera ejecución valida catálogo, comercio y manifiesto, verifica que los archivos coincidan con sus hashes y que los fragmentos sean extractos exactos, y genera embeddings en lotes de hasta 16. El modo de datos configurado debe coincidir con el del catálogo. No se descargan nuevos modelos ni se habilitan servicios remotos.

Los datos comerciales se validan, pero su contenido no se integra como autoridad de precios en el índice documental. El adaptador comercial conserva su propio procedimiento y sus ventanas de vigencia.

La base derivada se guarda en `data/runtime/corpus.sqlite3`, excluida del control de versiones por la configuración existente. La publicación observada contiene 72 fuentes activas y 204 vectores de 1024 dimensiones, identificados con el modelo y digest de `config/models.lock.json`.

## Resultado observado

La [primera ingesta](ingestion-results.json) procesó los 204 fragmentos con el modelo local en 128,665 segundos. La base ocupó 1 310 720 bytes, aproximadamente 1,25 MiB; estos valores están por debajo de las metas iniciales de diez minutos y 100 MiB fijadas para el corpus. Es una medición de esta ejecución, no una garantía para otros datos o equipos.

La [repetición sin cambios](reingestion-results.json) conservó la publicación y no pidió nuevos embeddings. Las comprobaciones con dobles de prueba cubren sustitución, retirada, fallos, colisiones de identificadores entre tiendas y cambios comerciales independientes. La ejecución real anterior comprueba el uso del modelo para indexar; las pruebas con dobles comprueban el control de publicación.

## Interfaz para las fases siguientes

`CorpusStore(database)` ofrece:

- `info(store_id)`: identidad de la revisión activa, huella, modelo, digest, dimensión y cantidades.
- `load(store_id, revision)`: manifiesto validado de esa revisión; satisface el puerto de repositorio de fuentes existente.
- `catalog(store_id, revision)`: catálogo asociado a esa revisión.
- `vectors(store_id, revision)`: pares de fragmento validado y vector float32, ordenados por identificador.
- `publish(...)`: publicación mediante el puerto de embeddings, sin depender de nombres de tienda o de categorías.

Una revisión que ya no esté activa produce un error explícito. La recuperación de fase 4 deberá comprobar modelo, digest y dimensión contra su configuración, aplicar los filtros de ámbito y calcular similitud sin mezclar tiendas o revisiones. Una puntuación vectorial no prueba que una afirmación sea correcta.

## Actualizar documentos

1. Preparar los documentos y el catálogo que corresponda. Mantener identificadores estables y cambiar las versiones de las fuentes cuyo contenido cambie.
2. Actualizar hashes, extractos y una revisión nueva del manifiesto. Conservar solo fragmentos de fuentes activas y referencias de atributos aplicables.
3. Ejecutar la ingesta. Una modificación que pretenda reutilizar la misma revisión se rechazará.
4. Comprobar la publicación nueva. La sustitución de la revisión y sus vectores ocurre en una transacción: no quedan filas de fragmentos obsoletos de esa tienda.

Los embeddings se preparan antes de reemplazar la publicación. Si falla el proveedor o la validación, se conserva la anterior. Un fallo de SQLite revierte la transacción completa. Si otra ingesta publicó durante el cálculo de vectores, el trabajo anterior no sobrescribe esa publicación concurrente.

## Retirar una fuente

Publicar un manifiesto nuevo con la fuente inactiva y sin sus fragmentos, o sin la fuente y sus fragmentos. Ajustar las referencias de atributos afectadas antes de importar. Una fuente inactiva no necesita conservar el archivo original disponible para volver a generar embeddings. La publicación sustituye los fragmentos de la tienda, por lo que los retirados dejan de ser consultables. Se conserva un registro técnico de revisión y huella, sin mantener contenido obsoleto como evidencia activa.

## Cambiar precios o existencias

Actualizar únicamente el archivo comercial con una revisión comercial coherente y sus fechas. No modificar fichas ni usar la fecha de consulta como actualización del origen. Si catálogo y manifiesto no cambiaron, una nueva ejecución de ingesta detecta el mismo corpus y no recalcula vectores. Ese comportamiento se comprobó con dos revisiones comerciales sintéticas.

## Alcance y comprobaciones

El importador actual admite fuentes locales UTF-8 cuyos fragmentos ya estén declarados. Las fuentes de Nexo Demo son Markdown. La importación de PDF, imágenes u otros formatos requerirá extracción y revisión antes de formar un manifiesto; no se afirma que este módulo realice OCR o interprete tablas de cualquier archivo.

Las comprobaciones de software incluyen persistencia tras reabrir SQLite, integridad de archivos, normalización y dimensión de vectores, ingesta idempotente, cambio de revisión, retirada, aislamiento entre tiendas con identificadores repetidos, fallo de proveedor, rollback de SQLite y protección frente a publicaciones concurrentes. No equivalen a calidad de recuperación, fidelidad generativa, seguridad general ni migración del recorrido completo de una tienda real.

Se consultaron la [documentación de transacciones SQLite de Python](https://docs.python.org/3.13/library/sqlite3.html#how-to-use-the-connection-context-manager) y la [validación JSON de Pydantic](https://docs.pydantic.dev/latest/concepts/models/#validating-data) mediante Context7. La comprobación ejecutada usa las versiones fijadas por el proyecto.
