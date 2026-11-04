# Contratos de la fase 2

Versión de diseño: `0.1`. Fecha: 4 de noviembre de 2026.
Estado: modelos de catálogo, comercio, fuentes, fragmentos, conversación, citas y errores implementados.
Los contratos de servicios están tipados; la API de base está disponible y el orquestador RAG sigue pendiente.
Los nombres de tipos y campos se mantendrán en inglés. Las respuestas al usuario serán en español.

## Convenciones

- Los identificadores serán cadenas opacas, no vacías y estables. Todo acceso incluirá `store_id`.
  Dos tiendas podrán compartir un `product_id` local sin referirse al mismo producto.
- `schema_version` versionará el formato; `revision` identificará una publicación de datos.
  No son equivalentes. Un cambio incompatible requerirá una nueva versión del contrato.
- Un campo obligatorio ausente será un error de entrada; `null` solo se permitirá donde represente
  un desconocido expresamente admitido. Se rechazarán claves inesperadas para detectar errores.
- Las fechas tendrán zona horaria explícita, se normalizarán a UTC y se intercambiarán en ISO 8601.
  No se aceptarán fechas sin zona, intervalos invertidos ni observaciones futuras como actuales.
- El dinero se transmitirá como una cadena decimal finita no negativa y una moneda de tres letras.
  No se usarán flotantes binarios para comparar presupuestos. La precisión permitida se definirá
  por moneda en el perfil; no se asumirá que todas tienen dos decimales ni se convertirán monedas.
- Los datos sintéticos llevarán `data_mode: demo`. El modo `real` no demostrará por sí mismo permiso,
  exactitud o validación; requerirá sus comprobaciones y documentación de procedencia.

## Catálogo

| Tipo | Campos obligatorios | Regla principal |
| --- | --- | --- |
| `StoreProfile` | `schema_version`, `store_id`, `display_name`, `data_mode`, `locale`, `currency`, `currency_decimal_places`, `categories`, `revision` | La identidad y las categorías se cargan como datos; no se codifican en el núcleo |
| `Category` | `category_id`, `name`, `attribute_definitions` | La definición de atributos declara tipo, unidad y si es obligatorio para comparar |
| `AttributeDefinition` | `key`, `label`, `value_type`, `required_for_comparison` | Tipos admitidos: `text`, `number`, `boolean`, `choice`; unidades y valores permitidos explícitos cuando corresponda |
| `Product` | `store_id`, `product_id`, `category_id`, `name`, `attributes`, `revision` | Pertenece a una categoría existente; no incluye precio ni existencias vigentes |
| `Variant` | `store_id`, `variant_id`, `product_id`, `name`, `attributes`, `revision` | Pertenece a un producto de la misma tienda; una presentación vendible sin opciones también tiene variante |
| `AttributeValue` | `key`, `value`, `unit`, `evidence_refs` | `value: null` significa desconocido; una afirmación técnica exige procedencia |

`human_contact` será opcional en el perfil y no se inventará para una tienda ficticia.
Un SKU externo será opcional; no sustituirá al identificador estable de variante.
Las claves de atributos serán únicas por entidad y coincidirán con la definición de categoría.
Los atributos de producto se heredarán; un valor específico de variante los reemplazará conservando
su evidencia. Unidades incompatibles o valores contradictorios impedirán una comparación concluyente.
Una categoría nueva se incorporará mediante datos y definiciones; no requerirá un bloque condicional
con el nombre de categoría en el servicio de conversación.

## Fuentes y fragmentos

`Source` contendrá `store_id`, `source_id`, `title`, `version`, `content_hash`, `data_mode`,
`scope`, `locator` y el registro local de permiso o de creación sintética. `locator` será una
referencia controlada por el servidor; una ruta local privada no se devolverá al navegador.

`scope` será una unión explícita:

| Alcance | Referencia | Restricción |
| --- | --- | --- |
| `store` | Ninguna referencia a producto | Políticas generales de la tienda |
| `category` | `category_id` | Solo una categoría existente de esa tienda |
| `product` | `product_id` | Fuente común a las variantes de ese producto, salvo excepciones documentadas |
| `variant` | `variant_id` | Información de esa variante exacta |

`Chunk` contendrá `store_id`, `chunk_id`, `source_id`, `source_version`, `content_hash`,
`text` y `location`. La ubicación incluirá al menos una referencia comprensible: página,
sección, tabla o párrafo. Páginas y números de párrafo serán positivos. Si se guardan offsets,
se referirán al texto de la versión de extracción declarada, no al documento original sin mapear.

Un fragmento retirado no podrá presentarse como fuente activa. Las citas resolverán la misma
versión que se recuperó. Referencias de otra tienda o huérfanas se rechazarán al importar o
componer evidencia. No se asignarán productos ficticios a políticas de alcance general.

## Datos comerciales

La consulta comercial devolverá un `CommercialLookup` por variante, con `store_id`, `variant_id`,
`lookup_status`, `checked_at` y, cuando exista registro, `snapshot_id`, `source_id` y `revision`.
`lookup_status` distinguirá `found`, `not_found` y `unavailable`.

Un registro encontrado contendrá observaciones independientes `price` y `stock`. Cada una tendrá
`value`, `source_updated_at`, `expires_at` y `source_ref`. Un valor desconocido será `null`; no llevará
una afirmación de vigencia. La validación comprobará zona horaria e intervalo, pero la vigencia
se evaluará con el reloj de la consulta; no se almacenará un booleano `is_fresh` permanente.

| Situación | Representación | Consecuencia para la respuesta |
| --- | --- | --- |
| Precio conocido y vigente | `price.value = Money`, ventana válida | Puede mostrarse como precio confirmado de demostración o real según el origen |
| Precio desconocido | `price.value = null` | No confirmar importe ni afirmar que cumple un presupuesto |
| Existencias positivas confirmadas | `stock.value.availability = in_stock` | Puede indicarse disponibilidad durante la ventana vigente |
| Agotado confirmado | `stock.value.availability = out_of_stock` | No recomendarlo como disponible |
| Cantidad desconocida | `stock.value.quantity = null` | No inventar unidades; puede existir un estado de disponibilidad explícito sin cantidad |
| Disponibilidad desconocida | `stock.value = null` | No transformar desconocido en agotado |
| Registro ausente | `lookup_status = not_found` | El catálogo puede contener la variante; falta información comercial |
| Fuente caída | `lookup_status = unavailable` | Error recuperable; no confirmar el último dato como actual |
| Dato vencido | `evaluated_at >= expires_at` | No poblar el campo comercial confirmado; advertir falta de vigencia |

Cuando exista cantidad será un entero no negativo. Cantidad cero solo será compatible con
`out_of_stock`; una cantidad positiva solo con `in_stock`. `unknown` se representará mediante
valor nulo, no mediante una cantidad cero. Un precio cero será un importe explícito válido,
distinto de desconocido, y requerirá la misma procedencia que cualquier otro precio.
La disponibilidad no implicará reserva, pago ni garantía de existencias futuras.

## Conversación, respuestas y citas

`ChatRequest` incluirá `schema_version`, `message` y `session_id` opcional para la primera consulta.
El servidor resolverá la tienda activa y generará la sesión; no aceptará instrucciones del cliente
para cambiar de proveedor, ruta de archivos o tienda. Los límites de entrada propuestos están en
la [arquitectura](README.md#sesiones-y-límites-propuestos).

`SessionState` contendrá `session_id`, `store_id`, `profile_revision`, `created_at`, `last_seen_at`,
restricciones explícitas y una lista ordenada de variantes presentadas. Los requisitos obligatorios,
preferencias y atributos desconocidos se conservarán separados. Una sesión vencida o de otra tienda
no heredará silenciosamente el contexto. No se incluirán nombres o correos para usar el prototipo.

`ChatResponse` incluirá:

| Campo | Contenido |
| --- | --- |
| `schema_version`, `request_id`, `session_id`, `store_id` | Identidad y trazabilidad |
| `data_mode` | `demo` o `real`, coherente con las fuentes utilizadas |
| `status` | `answered`, `clarification_required`, `insufficient_evidence` o `temporarily_unavailable` |
| `answer` | Texto en español, sin afirmar que las pruebas sintéticas validan una tienda real |
| `citations` | Citas documentales o comerciales diferenciadas |
| `products` | Referencias exactas de productos y variantes; las confirmaciones comerciales se respaldan con citas |
| `warnings` | Ausencia de atributos, fuentes contradictorias o datos comerciales no vigentes |
| `versions` | Revisiones de perfil, catálogo, corpus, índice y configuración de modelos empleadas |

Cada `Citation` tendrá `citation_id`, `kind`, `store_id`, `source_id` y `source_version`.
Las citas documentales incluirán `chunk_id`, ubicación y un extracto verificable. Las comerciales
incluirán `snapshot_id`, variante, campo respaldado, revisión y ventana de vigencia. Una cita
comercial no se fabricará a partir de un manual. La respuesta tendrá referencias explícitas a los
identificadores de cita para localizar qué afirmación respaldan.

No se producirá `answered` con afirmaciones técnicas sin evidencia. Una pregunta ambigua podrá
devolver una aclaración sin citas. Un error de generación no impedirá declarar que el servicio
está temporalmente indisponible. La validez de los identificadores de cita y la fidelidad semántica
de las frases se comprobarán por medios distintos; los contratos solo cubren la primera parte.

## Servicios y errores

Los puertos están definidos en `src/ragml/ports.py` y `commercial.py`. Los adaptadores de comercio,
generación y embeddings están implementados; los repositorios y la recuperación se implementan en
las fases siguientes conservando estas interfaces.

| Puerto | Operación canónica | Resultado |
| --- | --- | --- |
| `CatalogPort` | `get_product`, `get_variant`, `search(store_id, CatalogQuery)` | Producto/variante o ausencia explícita; candidatos sin confirmar importes por documentos |
| `CommercialPort` | `lookup(store_id, variant_ids, evaluated_at)` | Un resultado por variante; observaciones independientes con vigencia |
| `SourceRepository` | `load(store_id, revision)` | Manifiesto de la tienda y revisión exactas |
| `RetrievalPort` | `search(RetrievalQuery)` | `RetrievedChunk`: fragmento y puntuación de coseno entre -1 y 1 |
| `GenerationPort` | `generate(system, user, output_tokens=...)` | Respuesta de proveedor completa o fallo explícito |
| `EmbeddingPort` | `embed(texts, query=False)` | Vectores y métricas del proveedor; 1024 dimensiones comprobadas |
| `SessionRepository` | `load`, `save`, `delete` con propietario | Estado de sesión aislado por tienda y propietario |

`RetrievalQuery` fija tienda, revisión, texto, k de 1 a 10, filtros de categoría/producto/variante
y la inclusión de políticas generales. `CatalogQuery` separa texto, categorías y requisitos.
El estado de sesión conserva presupuesto, requisitos, preferencias y orden de variantes, pero
su TTL y aislamiento efectivo se comprobarán al implementar el repositorio y la conversación.

`ErrorResponse` contiene `code`, `message`, `request_id` y `retryable`, sin entrada ni trazas.
La API de base usa `invalid_input`, `not_found`, `rag_not_ready`, `provider_unavailable` e
`internal_error`. Los puertos distinguen ausencia y fallos antes de mapearlos a respuestas HTTP;
un registro comercial ausente no significa variante inexistente ni agotada.

## API de base

| Ruta | Respuesta actual | Alcance |
| --- | --- | --- |
| `GET /health` | 200, versión y `rag_available: false` | Proceso de base disponible |
| `GET /ready` | 503, dependencias por separado | No anuncia un RAG aún no implementado |
| `POST /v1/chat` | 503 `rag_not_ready`, o 422 si la entrada no cumple el contrato | Valida el formato; no simula una respuesta generada |
| `GET /openapi.json` | 200 | Contrato local; sin interfaces que descarguen recursos de CDN |

Las solicitudes reciben un identificador UUID generado por el servidor y su cabecera correlativa.
No hay endpoint para seleccionar URLs de proveedores, leer rutas arbitrarias o descargar modelos.
La futura respuesta `ChatResponse` ya está tipada, pero todavía no es una respuesta exitosa de chat.

## Contratos exportados y validación

Los [JSON Schema y OpenAPI exportados](schemas/) corresponden a las clases de Python. Regenerar con:

```powershell
.\.venv\Scripts\ragml.exe export-contracts
```

Los esquemas expresan forma y restricciones de campos; las validaciones cruzadas se ejecutan en
Python. `SourceManifest.validate_for_catalog` comprueba tienda, modo, alcance y referencias de
atributos a fuentes activas aplicables. `ChatResponse.validate_evidence` comprueba la versión,
ubicación y extracto exactos y exige una observación comercial vigente para citar precio o stock.
La integridad estructural no demuestra que una frase esté semánticamente respaldada; esa parte
pertenece a la evaluación. El permiso registrado tampoco prueba por sí solo una autorización real.

## Interfaces para pruebas

La batería tiene 44 casos posteriores a la implementación, sin TDD por indicación del usuario:

1. Catálogo y consulta comercial: importes, desconocidos, agotados, ausentes, fallos, vigencia,
   nuevas revisiones y separación entre tiendas sintéticas.
2. Evidencia y citas: hashes, ubicaciones, versiones, relaciones, extractos y vigencia comercial.
3. Configuración: rutas explícitas, `.env` válido y rechazo de proveedores remotos.
4. Proveedor: API local, digests, dimensiones, redirecciones, timeout y respuestas incompletas,
   utilizando transporte simulado.
5. API: salud, indisponibilidad RAG explícita, errores sin eco de la entrada y contrato OpenAPI.

Los modelos reales y el HTTP real se comprobaron aparte. Los resultados y límites están en la
[guía del entorno](local-environment.md). No sustituyen los escenarios académicos reservados,
una prueba de migración del asistente completo ni la evaluación con participantes.
