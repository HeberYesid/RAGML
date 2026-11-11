# Asistente RAG para tiendas

Prototipo académico local en español para Nexo Demo. Consulta documentos mediante recuperación
semántica y entrega respuestas extractivas con fuentes. El perfil, catálogo y fuentes se mantienen
separados del núcleo para facilitar su sustitución por una tienda real autorizada.

**Actualización del 10 de noviembre de 2026:** el chat HTTP/web integra consultas documentales,
asesoría, comparación y sesiones aisladas. Las respuestas documentales utilizan modelos locales;
las recomendaciones aplican reglas explícitas sobre el catálogo. La disponibilidad efectiva se
comprueba en `/ready` y depende de los modelos, el corpus y los datos configurados.

## Contenido

- [Estado y componentes](#estado-y-componentes)
- [Requisitos](#requisitos)
- [Instalación inicial](#instalación-inicial)
- [Configuración](#configuración)
- [Ejecución habitual](#ejecución-habitual)
- [Consultas al RAG](#consultas-al-rag)
- [Cómo funciona el RAG](#cómo-funciona-el-rag)
- [Interfaz web y API](#interfaz-web-y-api)
- [Evaluación y verificación](#evaluación-y-verificación)
- [Detener los servicios](#detener-los-servicios)
- [Solución de problemas](#solución-de-problemas)
- [Documentación](#documentación)

## Estado y componentes

| Componente | Estado actual |
| --- | --- |
| Catálogo ficticio | 6 categorías, 60 productos y 90 variantes |
| Corpus documental de demostración | 72 fuentes y 204 fragmentos |
| Ingesta e índice | Embeddings de 1024 dimensiones almacenados en SQLite |
| Recuperación y respuesta documental | Disponibles mediante `ragml.rag_cli`; consultas independientes de un turno |
| Asesoría y comparación | Reglas deterministas conectadas al chat y al contexto de la sesión |
| Interfaz web | Chat integrado, catálogo, fuentes, reloj simulado y conversación nueva |
| Evaluación | 60 casos de ajuste medidos por HTTP con modelos reales; conjunto final y utilidad con personas pendientes |

Todos los datos de Nexo Demo son ficticios. Las comprobaciones de software y los ejemplos de
inferencia no constituyen validación con una tienda real ni con participantes.

## Requisitos

Entorno documentado para Windows:

- Python **3.13.7** instalado; el proyecto admite Python `>=3.13,<3.14`.
- **uv 0.9.26** y **PowerShell 7** utilizados en la preparación original.
- Aproximadamente **12 GiB de disco disponibles** para recursos y cachés.
- Internet durante la preparación inicial para descargar dependencias, Ollama portátil y modelos.

No se requieren cuentas ni claves de modelos. Después de descargar los recursos, el flujo de
consulta utiliza servicios locales. No requiere instalar Node ni compilar un frontend.

Comprueba las herramientas antes de instalar:

```powershell
py -3.13 --version
uv --version
$PSVersionTable.PSVersion
```

Todos los comandos siguientes se ejecutan desde la raíz de `RAGML`. Por ejemplo, en este equipo:

```powershell
Set-Location 'C:\Users\HeberYesid\Desktop\Universidad Trabajos\RAGML'
```

En otro equipo, sustituye esa ruta por la ubicación de tu copia. Se usa directamente el Python
de `.venv`, por lo que no es necesario activar el entorno virtual.

## Instalación inicial

### 1. Preparar el entorno Python

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache\uv'
uv sync --locked --group dev --python 3.13.7 --no-python-downloads --no-managed-python --default-index https://pypi.org/simple
```

Este comando prepara `.venv` e instala el proyecto y las herramientas de desarrollo.
`--locked` exige que `uv.lock` coincida con el proyecto; no actualiza silenciosamente el archivo.
Las opciones de Python requieren que la versión indicada ya esté instalada.

### 2. Descargar e iniciar los modelos

```powershell
.\scripts\setup-models.ps1
```

El script descarga el ejecutor portátil fijado en `config/runtime.lock.json`, verifica su hash,
inicia el servidor del proyecto y descarga los modelos de `config/models.lock.json`:

| Modelo | Función |
| --- | --- |
| `qwen3-embedding:0.6b` | Convertir documentos y preguntas en vectores de 1024 dimensiones |
| `qwen3:4b-instruct-2507-q4_K_M` | Seleccionar extractos documentales para responder |

El servidor escucha en `http://127.0.0.1:11435` y conserva sus recursos en `.cache/ollama/`.
Utiliza el ejecutor del proyecto, sin requerir una instalación global de Ollama.

### 3. Comprobar la base local

```powershell
.\.venv\Scripts\ragml.exe doctor
```

Revisa que `models.generation`, `models.embedding` y `foundation_ready` sean `true`.
El campo `rag_available` del diagnóstico de base no comprueba el recorrido HTTP integrado.
Utiliza `/ready` para conocer la disponibilidad del asistente web y sus dependencias.

Continúa con la ingesta de la sección siguiente para preparar el corpus.

## Configuración

Los valores predeterminados permiten ejecutar la demostración sin crear `.env`. Si necesitas
personalizarlos, copia `.env.example` únicamente cuando no exista una configuración previa:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

| Variable | Valor predeterminado / uso |
| --- | --- |
| `RAGML_DATA_MODE` | `demo`; debe coincidir con el modo del catálogo |
| `RAGML_CATALOG_PATH` | `data/sample/catalog.json` |
| `RAGML_COMMERCIAL_PATH` | `data/sample/commercial.json` |
| `RAGML_SOURCE_MANIFEST` | `data/sample/sources.json` |
| `RAGML_OLLAMA_URL` | `http://127.0.0.1:11435` |
| `RAGML_PORT` | `8000`, para la API o la web |
| `RAGML_RETRIEVAL_K` | `5` fragmentos por consulta |
| `RAGML_CONTEXT_TOKENS` | `4096` |
| `RAGML_OUTPUT_TOKENS` | `256` |

Las rutas relativas se resuelven desde el directorio de proyecto. El CLI base acepta
`--project-dir` y `--env-file` antes del subcomando; la web también admite esas opciones.
Los comandos de ingesta, RAG y evaluación aceptan `--project-dir` y cargan el `.env` del proyecto.
Consulta las opciones completas en [.env.example](.env.example).

## Ejecución habitual

### 1. Iniciar los modelos

Con los recursos ya descargados:

```powershell
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\ragml.exe doctor
```

El script reconoce su proceso si ya está en ejecución. Si otro servicio ocupa el puerto 11435,
se detiene con un error en lugar de reutilizarlo.

### 2. Preparar o actualizar el índice

```powershell
.\.venv\Scripts\python.exe -m ragml.ingestion
```

La ingesta valida catálogo, comercio y manifiesto, comprueba los archivos y sus hashes, verifica
que los fragmentos sean extractos exactos y genera embeddings en lotes de hasta 16.
El índice derivado se guarda en `data/runtime/corpus.sqlite3`.

- `status: "published"`: se publicó el corpus.
- `status: "unchanged"`: la publicación coincide y se reutiliza sin recalcular sus vectores.

No necesitas repetir este paso antes de cada pregunta. Repítelo al actualizar el corpus y sigue
la [guía de ingesta](docs/data/ingestion.md) si cambia el modelo o la configuración del índice.
La existencia del archivo SQLite por sí sola no garantiza su compatibilidad.

## Consultas al RAG

### Recuperar fragmentos sin generar una respuesta

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía?' --retrieval-only
```

Este modo utiliza el modelo de embeddings, pero no el generador. Permite inspeccionar `retrieved`,
el texto y ubicación de cada fragmento, su `score` y el tiempo de recuperación.
El `score` expresa similitud coseno; no es un porcentaje de certeza.

### Consultar con respuesta y fuentes

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía de demostración y durante cuánto tiempo?'
```

Para limitar la consulta a un producto y sus fuentes aplicables:

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_cli 'Según la ficha, ¿qué potencia tiene la Lámpara Flexo?' --product-id NEX-ILU-001
```

Para cambiar la cantidad de resultados o guardar evidencia local:

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía?' --retrieval-only --k 3
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía?' --output .cache/verification/consulta-garantia.json
```

Otras opciones son `--variant-id`, `--category-id`, `--no-store-policies`, `--revision` y
`--database`. Los filtros de producto, variante y categoría pueden repetirse; sus relaciones
se intersectan. `--k` admite valores entre 1 y 10. Consulta la ayuda con:

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_cli --help
```

### Interpretar el resultado

| Campo | Contenido |
| --- | --- |
| `response.status` | `answered`, `clarification_required`, `insufficient_evidence` o `temporarily_unavailable` |
| `response.answer` | Respuesta presentada al usuario |
| `response.citations` | Fuente, versión, fragmento, ubicación y extracto utilizado |
| `response.warnings` | Advertencias sobre evidencia, contexto o disponibilidad |
| `retrieved` | Fragmentos encontrados por la búsqueda |
| `context_chunk_ids` | Fragmentos que realmente entraron al contexto del generador |
| `metrics` | Tiempos y contadores de tokens disponibles |

El modo `--retrieval-only` entrega el índice, los fragmentos y métricas de recuperación,
sin el objeto `response`. Cada consulta documental es independiente; todavía no hay historial
ni resolución de referencias como «el segundo» entre ejecuciones.

## Cómo funciona el RAG

RAG significa *generación aumentada por recuperación*. El flujo implementado es:

```text
Documentos + catálogo + manifiesto
    -> Validación de fuentes y fragmentos
    -> Embeddings de los fragmentos
    -> Índice local en SQLite

Pregunta del usuario
    -> Embedding de la pregunta
    -> Filtros y búsqueda por similitud coseno en el índice
    -> Selección de fragmentos que caben en el contexto
    -> Modelo selecciona citas
    -> Validación de extractos y referencias
    -> Respuesta con fuentes o abstención
```

### Fuentes, recuperación y generación

Los documentos están en `data/sample/documents/`. El manifiesto `data/sample/sources.json`
define fuentes, versiones, hashes, fragmentos y ubicaciones. El recuperador usa similitud coseno
exacta sobre vectores normalizados en SQLite; no utiliza LangChain, Chroma ni una base vectorial remota.

El generador recibe la pregunta y evidencia recuperada dentro del presupuesto de contexto.
Devuelve una selección de citas en JSON y el servicio verifica que los extractos existan
literalmente en los fragmentos proporcionados. La respuesta actual es extractiva, sin síntesis
libre completa. Una cita literal demuestra procedencia textual, no garantiza pertinencia o corrección.

Copiar un PDF o Word a la carpeta no lo incorpora automáticamente al RAG. Es necesario preparar
su representación documental, fragmentos y metadatos compatibles, y ejecutar después la ingesta.
Consulta [los datos de demostración](docs/data/README.md) antes de modificar el paquete generado.

### Precios, existencias y recomendaciones

Los datos comerciales se mantienen en `data/sample/commercial.json`, separados de la autoridad
documental. El RAG documental se abstiene ante consultas comerciales reconocidas; no confirma
precios ni existencias actuales a partir de una ficha.

El módulo `ragml.advice` implementa reglas de recomendación y comparación con datos estructurados
y se conecta al chat mediante `ragml.chat`. Los registros comerciales tienen ventanas de vigencia:
una instantánea vencida no debe renovarse silenciosamente ni presentarse como actual.
Consulta [la guía de asesoría](docs/advice/README.md).

## Interfaz web y API

### Abrir la interfaz

En otra terminal, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m ragml.web
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) y mantén la terminal abierta.
La interfaz muestra el catálogo y envía los turnos al asistente integrado. Permite consultar
productos y políticas, pedir recomendaciones, comparar alternativas y cambiar el presupuesto.
El indicador de conexión consulta la salud de la API; `/ready` verifica las dependencias del chat.
En Nexo Demo se declara el reloj comercial simulado; sus precios y existencias son ficticios.

Si el puerto 8000 está ocupado, selecciona otro antes de iniciar:

```powershell
$env:RAGML_PORT = '8006'
.\.venv\Scripts\python.exe -m ragml.web
```

Abre entonces [http://127.0.0.1:8006](http://127.0.0.1:8006). La variable afecta los siguientes
procesos de esa terminal hasta cerrarla o ejecutar `Remove-Item Env:RAGML_PORT`.

### Ejecutar únicamente la API base

Como alternativa a la web:

```powershell
.\.venv\Scripts\ragml.exe serve
```

La web ya incluye la API; no necesitas iniciar ambos procesos. Para usarlos simultáneamente,
asigna puertos diferentes.

| Ruta | Comportamiento actual |
| --- | --- |
| `GET /health` | `200`; informa salud y acceso al corpus, sin comprobar por sí solo toda la inferencia |
| `GET /ready` | `200` si las dependencias están listas; `503` si alguna no está disponible |
| `POST /v1/chat` | Respuesta conversacional y sesión; errores explícitos cuando faltan dependencias |
| `GET /openapi.json` | Contrato HTTP local |
| `GET /` | Interfaz, disponible al iniciar `ragml.web` |
| `GET /v1/web/catalog` | Catálogo validado, disponible al iniciar `ragml.web` |

`/docs` y `/redoc` están desactivados para evitar recursos de documentación desde CDN.
Los servicios escuchan en loopback para uso local. Consulta [la guía web](docs/web/README.md)
para detalles de la interfaz, sesiones del cliente y estados de error.

## Evaluación y verificación

### Explorar el dataset y generar gráficos

El extra `analysis` incorpora Matplotlib; las estadísticas sin gráficos solo necesitan las
dependencias base. Usa un directorio nuevo para conservar las evidencias de cada ejecución:

```powershell
uv sync --locked --extra analysis --cache-dir .cache/uv
.\.venv\Scripts\python.exe -m ragml.analysis --output-dir docs/analysis/nueva-ejecucion
```

El comando genera estadísticas, cinco tablas CSV y cinco gráficos PNG/SVG. Distingue precios
vigentes, desconocidos y vencidos, conserva los valores ausentes y señala posibles atípicos IQR
sin eliminarlos. Los atributos se comparan por categoría y unidad. El reloj comercial simulado y
los hashes de las entradas quedan registrados. Consulta los [resultados del análisis](docs/analysis/2026-11-09/README.md)
y la [guía de reproducción](docs/analysis/README.md). `--no-charts` permite exportar solo tablas.

### Medir el asistente integrado

Con los modelos y la web iniciados:

```powershell
.\.venv\Scripts\python.exe -m ragml.integrated_evaluation --output-dir docs/evaluation/integrated/nueva-ejecucion --base-url http://127.0.0.1:8000 --include-security-fixtures
```

El ejecutor usa los 60 casos de ajuste y conserva los turnos reales, errores, tiempos y huellas
del candidato. Las cuatro pruebas con documentos adversariales usan fuentes e índices clonados
y un servidor temporal aislado. No se modifican las fuentes activas ni se abre el archivo final
reservado. Una coincidencia de estado HTTP o una cita literal válida no equivalen a corrección
semántica ni a utilidad con personas. Véase la [guía de evaluación integrada](docs/evaluation/integrated/README.md).

### Entrega académica del Previo 3

El [informe fuente](docs/reports/previo3-informe.md) desarrolla los once apartados de la guía,
la metodología, los resultados, su interpretación y las limitaciones. La [bibliografía contrastada](docs/reports/bibliografia-verificada.md)
conserva las fuentes y decisiones de citación. El [guion de sustentación](docs/reports/guion-sustentacion.md)
incluye la demostración y preguntas previsibles.

La carpeta `outputs/previo3/` reúne el informe editable, su PDF y la presentación. La realización
de la exposición por el equipo y los estudios con participantes son actividades distintas de la
preparación de estos materiales.

La [medición consolidada](docs/evaluation/integrated/complete-20261110/completion.json)
cubre los 60 casos en dos tramos del mismo candidato, sin errores de ejecución y con 50
coincidencias de estado. Esas coincidencias no son exactitud semántica. El informe explica
las discrepancias y el p95 de unos 184 segundos por turno, superior a la meta de diseño.
También está preparado el [informe de avance](docs/reports/informe-avance.md).

### Medir recuperación sobre ajuste

Con los modelos en ejecución y el índice preparado:

```powershell
.\.venv\Scripts\python.exe -m ragml.rag_evaluation --output .cache/verification/evaluacion-recuperacion.json
```

El ejecutor utiliza los casos documentales y de políticas de
`data/evaluation/adjustment/cases.json`, calcula Recall@k y registra latencias y fallos.
No abre los casos finales reservados. Esta medición evalúa recuperación; no mide por sí sola
corrección de respuestas, fidelidad semántica de citas ni utilidad con participantes.

Los resultados históricos, condiciones y límites están en
[la guía de fase 4](docs/evaluation/phase4/README.md). Los tiempos registrados de dos respuestas
de demostración fueron de aproximadamente 80–129 segundos; no son una garantía de rendimiento.

### Comprobar el software

Desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src
uv build --no-sources --offline --cache-dir .cache/uv --out-dir dist
```

El build offline requiere que sus dependencias ya estén en caché. La batería usa datos sintéticos
y transporte HTTP simulado para el proveedor; la inferencia con modelos reales, el HTTP real y
la revisión visual tienen comprobaciones separadas. Los comandos anteriores no implican que se
hayan ejecutado en cada revisión documental. Véase [la guía de pruebas](tests/README.md).

Las pruebas de software no sustituyen la evaluación académica. El informe de avance se entrega
al finalizar todo el proyecto, en fase 8.

## Detener los servicios

Detén la web o la API con **Ctrl+C** en su terminal. Después, si el servidor de modelos no está
siendo utilizado por otro trabajo:

```powershell
.\scripts\stop-models.ps1
```

## Solución de problemas

| Síntoma | Qué revisar |
| --- | --- |
| No existe `.venv\Scripts\python.exe` | Ejecutar la preparación Python desde la raíz y comprobar la versión instalada |
| Falta Ollama portátil o un modelo | Ejecutar `setup-models.ps1` durante la preparación inicial y revisar su resultado |
| `doctor` no confirma los modelos | Iniciar el servidor del proyecto y comprobar la configuración y los archivos lock |
| Puerto 11435 ocupado | Identificar el servicio que lo utiliza; el script no reutiliza procesos ajenos |
| Puerto 8000 ocupado | Seleccionar otro mediante `RAGML_PORT` antes de iniciar la web o API |
| Chat no disponible | Consultar `/ready`, iniciar modelos y comprobar el índice y los datos activos |
| `rag_available: false` en `doctor` | Es el diagnóstico de base; comprobar `/ready` y un turno real del chat |
| `index_unavailable_or_incompatible` | Comprobar ingesta, rutas, revisión activa y compatibilidad de modelo, digest y dimensiones |
| `provider_unavailable` | Comprobar el servidor local y `doctor`; revisar `.cache/ollama/server.stderr.log` |
| `clarification_required` | Indicar explícitamente el producto o variante y revisar los filtros |
| `insufficient_evidence` | Revisar advertencias, fuentes y contexto; puede ser una abstención esperada |
| No hay recomendaciones comerciales | Revisar vigencia, precio, disponibilidad y restricciones; los datos son ficticios y pueden estar vencidos |

## Documentación

- [Arquitectura y cierre de fase 2](docs/architecture/README.md).
- [Decisiones técnicas y presupuesto](docs/architecture/decisions.md).
- [Contratos y esquemas](docs/architecture/contracts.md).
- [Modelos locales](docs/architecture/local-models.md).
- [Entorno y evidencia de verificación](docs/architecture/local-environment.md).
- [Datos de demostración](docs/data/README.md).
- [Ingesta e índice](docs/data/ingestion.md).
- [RAG documental y resultados de ajuste](docs/evaluation/phase4/README.md).
- [Asesoría y comparación](docs/advice/README.md).
- [Interfaz web](docs/web/README.md).
- [Particiones de evaluación](data/evaluation/README.md).
- [Pruebas](tests/README.md).
- [Plan general](plans/001-plan-del-proyecto.md).
