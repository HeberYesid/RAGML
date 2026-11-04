# Guía de modelos locales para un portátil con 6 GB de VRAM

Fecha de revisión: 4 de noviembre de 2026. Proyecto: RAGML.

Esta guía documenta la configuración existente y opciones de prueba. No instala modelos,
no cambia la selección activa ni acredita resultados en el portátil de destino.
Los comandos están preparados para Windows con PowerShell 7, desde la raíz del proyecto.

## 1. ¿El modelo actual es bueno y cumple su función?

**Es una elección razonable para el prototipo documental, con funcionamiento demostrado
en ejemplos concretos. Todavía no hay evidencia suficiente para afirmar que el asistente
completo cumple todos sus objetivos de calidad y rendimiento.**

Actualmente hay dos modelos con funciones distintas:

| Función | Modelo fijado | Tamaño de descarga registrado |
| --- | --- | --- |
| Seleccionar extractos para responder | `qwen3:4b-instruct-2507-q4_K_M` | 2,50 GB aproximadamente |
| Buscar documentos mediante vectores | `qwen3-embedding:0.6b`, Q8_0, 1024 dimensiones | 0,64 GB aproximadamente |

La identidad exacta está en [config/models.lock.json](../../config/models.lock.json).
El ejecutor fijado es Ollama 0.40.14, según
[config/runtime.lock.json](../../config/runtime.lock.json).

Evidencia registrada en el proyecto, consultada para esta guía; no son mediciones nuevas:

| Evidencia | Resultado observado | Qué permite concluir |
| --- | --- | --- |
| [Recuperación sobre ajuste](../evaluation/phase4/adjustment-retrieval.json) | Recall@5 medio 1,00 en 18 casos aplicables, sin consultas fallidas | La búsqueda incluyó la referencia esperada entre sus cinco resultados en esos casos |
| [Consulta sobre garantía](../evaluation/phase4/probe-warranty.json) | Respuesta con cita literal; 129,37 s en total | Ese ejemplo completó el recorrido documental |
| [Consulta filtrada sobre lámpara](../evaluation/phase4/probe-lamp.json) | Respuesta sobre 8 W con cita literal; 80,62 s en total | Ese ejemplo identificó el dato solicitado |
| [Prueba breve de infraestructura](evidence/local-model-probe-20261104.json) | 4,464 s inicialmente y 0,592 s al repetir | El modelo puede completar una consulta muy corta; esos tiempos no representan el RAG completo |

Recall@5 no es exactitud de respuesta: encontrar el fragmento correcto no garantiza que el
generador lo elija o que su respuesta resuelva la pregunta. Los 18 casos pertenecen al ajuste,
con una referencia positiva por caso; no constituyen evaluación final independiente.
Dos respuestas revisadas tampoco permiten estimar una tasa general de acierto.

El RAG actual responde con extractos literales validados. Puede abstenerse si no hay evidencia.
Eso ayuda a controlar la procedencia, pero una cita literal también puede ser irrelevante.
El modelo no aporta por sí mismo precios ni inventario actuales: esos datos tienen otra fuente.

La [documentación de fase 4](../evaluation/phase4/README.md) registra calidad pendiente de evaluar
y latencia por reducir. Los dos tiempos completos son elevados para una interacción fluida;
no permiten calcular un p95, ni demostrar la meta de p95 de 60 s del recorrido integrado.

Además, el código actual de [la API](../../src/ragml/api.py) devuelve `rag_not_ready` en el chat.
El recorrido documental disponible es [ragml.rag_cli](../../src/ragml/rag_cli.py), de un turno.
Cambiar el modelo no implementa integración web, memoria conversacional ni recomendaciones.

## 2. Qué puede mejorar el portátil

Una GPU compatible con más VRAM puede reducir la carga en CPU y acelerar el recorrido.
**Ejecutar el mismo modelo en una GPU mejor no aumenta por sí solo su capacidad de respuesta.**
La mejora de calidad requiere otro modelo, mejores fuentes, recuperación o ajustes comprobados.

Solo se conoce la VRAM del portátil. La ruta siguiente supone una NVIDIA compatible;
el modelo exacto de GPU, RAM, potencia y refrigeración siguen sin comprobarse.
En AMD hay que revisar el soporte específico de Ollama para Windows antes de asumir aceleración.
Consulta [hardware compatible](https://docs.ollama.com/gpu) y
[requisitos de Windows](https://docs.ollama.com/windows).

Recomendación práctica de recursos, no requisito oficial medido del proyecto:

- 16 GB de RAM como punto de partida; 32 GB si se probarán varios modelos o cargas mixtas CPU/GPU.
- SSD con unos 25 GB libres para preparar el entorno y conservar varios candidatos pequeños.
- Portátil conectado a corriente y sin otras cargas intensivas de GPU durante la comparación.

El tamaño descargado no equivale al consumo de VRAM. También consumen memoria el contexto,
la caché, los buffers del ejecutor y otras aplicaciones. GB de descarga y GiB reportados por
el sistema tampoco son unidades idénticas. La comprobación decisiva es la carga real en el portátil.

## 3. Opciones y orden recomendado

Tamaños aproximados publicados para los tags concretos consultados. La adecuación a 6 GB
es una estimación de ingeniería, pendiente de medición; no es una tabla de VRAM garantizada.

| Opción | Tag exacto | Descarga aprox. | Decisión para 6 GB |
| --- | --- | --- | --- |
| Referencia actual | `qwen3:4b-instruct-2507-q4_K_M` | 2,50 GB | Medirlo primero en el portátil; permite saber cuánto mejora solo el equipo |
| Primera alternativa | `qwen3.5:4b-q4_K_M` | 3,3 GB | Primer candidato por su margen de memoria relativo; comparar calidad, compatibilidad y velocidad |
| Alternativa con más parámetros | `qwen3:8b-q4_K_M` | 5,2 GB | Ajustada: puede repartir trabajo entre CPU y GPU al añadir contexto y buffers |
| Alternativa adicional | `qwen2.5:7b-instruct-q4_K_M` | 4,7 GB | Útil como comparación de seguimiento de instrucciones; ser mayor o más antiguo no demuestra mejora |
| Experimento fuera del objetivo de carga íntegra en GPU | `qwen3.5:9b-q4_K_M` | 6,6 GB | No planificar que quepa completo en 6 GB; podría funcionar con RAM/CPU, con latencia por medir |

Fuentes de los tags y tamaños: [Qwen3.5 4B](https://ollama.com/library/qwen3.5:4b-q4_K_M),
[Qwen3 8B](https://ollama.com/library/qwen3:8b-q4_K_M),
[Qwen2.5 7B](https://ollama.com/library/qwen2.5:7b-instruct-q4_K_M) y
[Qwen3.5 9B](https://ollama.com/library/qwen3.5:9b-q4_K_M).

**Recomendación: medir el actual y después Qwen3.5 4B Q4_K_M, conservando el embedding actual.**
Qwen3.5 es un candidato a mejorar resultados, no una mejora ya demostrada en este corpus.
Su [ficha del autor](https://huggingface.co/Qwen/Qwen3.5-4B) describe otra arquitectura y capacidades;
eso no sustituye una comparación local. No atribuir al 4B las tablas del modelo insignia de su familia.

Después probaría Qwen3 8B si interesa comprobar más capacidad y se acepta un posible aumento
de latencia. No asumir que un 8B anterior supera al 4B Instruct 2507 actual en esta tarea.
Los modelos de 14B o más quedan fuera de la recomendación práctica para esta VRAM.

No cambiar inicialmente el embedding: su referencia de recuperación actual es favorable en ajuste.
Cambiar generación permite conservar el índice si corpus, embedding, digest y dimensiones coinciden.
Cambiar embeddings obliga a regenerar vectores; la implementación fija además 1024 dimensiones.

## 4. Preparar el proyecto en el otro portátil

Trabajar sobre una copia local del proyecto. No reutilizar la carpeta `.venv` de otro equipo.
Preparar Python 3.13.7, uv y PowerShell 7 siguiendo el [README](../../README.md).
No hace falta entrenar ni afinar los pesos para estas pruebas: se utiliza inferencia local.

```powershell
Set-Location 'C:\ruta\a\RAGML'
$ErrorActionPreference = 'Stop'
py -3.13 --version
uv --version
$PSVersionTable.PSVersion
nvidia-smi
```

La ruta anterior es un ejemplo: sustituirla por la ubicación real. `nvidia-smi` solo corresponde
a NVIDIA; revisar allí nombre, memoria y controlador. Si no hay aceleración compatible,
resolver eso antes de atribuir la lentitud al modelo. Revisar los requisitos oficiales enlazados.

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache\uv'
uv sync --locked --group dev --python 3.13.7 --no-python-downloads --no-managed-python --default-index https://pypi.org/simple
if ($LASTEXITCODE -ne 0) { throw 'Environment setup failed' }
.\scripts\setup-models.ps1
.\.venv\Scripts\ragml.exe doctor
if ($LASTEXITCODE -ne 0) { throw 'Baseline model check failed' }
.\.venv\Scripts\python.exe -m ragml.ingestion
if ($LASTEXITCODE -ne 0) { throw 'Corpus ingestion failed' }
```

La preparación descarga el ejecutor y los modelos oficiales fijados; requiere internet.
Las preguntas posteriores se procesan localmente, con la nube deshabilitada y puerto 11435.
`doctor` debe confirmar ambos modelos y `foundation_ready`. Su `rag_available: false`
describe la integración HTTP pendiente, no el estado de una consulta documental por CLI.
La ingesta puede devolver `published` o `unchanged`.

## 5. Medir primero el modelo actual en el portátil

Usar una terminal dedicada a esta comparación, sin activar todavía un candidato.
Los valores efectivos de `.env` deben coincidir con la referencia que se quiere comparar.

```powershell
$runtimeLock = Get-Content -Raw -LiteralPath 'config\runtime.lock.json' | ConvertFrom-Json
$ollamaExe = Join-Path (Get-Location) ".cache\ollama\runtime-v$($runtimeLock.version)\ollama.exe"
$env:OLLAMA_HOST = '127.0.0.1:11435'
$runStamp = Get-Date -Format 'yyyyMMdd-HHmmssfff'
$comparisonDir = Join-Path (Get-Location) ".cache\verification\modelos-6gb-$runStamp"
New-Item -ItemType Directory -Path $comparisonDir -ErrorAction Stop | Out-Null

.\.venv\Scripts\ragml.exe probe-models --output (Join-Path $comparisonDir 'baseline-infrastructure.json')
if ($LASTEXITCODE -ne 0) { throw 'Baseline infrastructure probe failed' }
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía de demostración y durante cuánto tiempo?' --output (Join-Path $comparisonDir 'baseline-warranty.json')
if ($LASTEXITCODE -ne 0) { throw 'Baseline RAG probe failed' }
& $ollamaExe ps
.\.venv\Scripts\python.exe -m ragml.rag_evaluation --output (Join-Path $comparisonDir 'baseline-retrieval.json')
if ($LASTEXITCODE -ne 0) { throw 'Baseline retrieval measurement failed' }
```

La prueba de infraestructura es breve y no mide calidad general. `rag_evaluation` mide recuperación,
no calidad del generador. Un código de salida cero del RAG tampoco demuestra pertinencia:
revisar `response.status`, respuesta y citas. La evaluación utiliza ajuste; no abrir el conjunto
final reservado para elegir modelos.

## 6. Descargar un candidato y probarlo sin cambiar el lock original

Continuar en la misma terminal. Conservar `$comparisonDir`, `$runtimeLock` y `$ollamaExe`.
Para cada candidato, elegir un solo tag; no ejecutar las alternativas simultáneamente.

```powershell
$candidateTag = 'qwen3.5:4b-q4_K_M'
# Alternatives for a separate run:
# $candidateTag = 'qwen3:8b-q4_K_M'
# $candidateTag = 'qwen2.5:7b-instruct-q4_K_M'

& $ollamaExe pull $candidateTag
if ($LASTEXITCODE -ne 0) { throw 'Candidate download failed' }
& $ollamaExe show $candidateTag
if ($LASTEXITCODE -ne 0) { throw 'Candidate inspection failed' }
```

Estos comandos usan el servidor portátil del proyecto. No se necesita instalar otro Ollama
global ni usar su puerto habitual 11434. Mantener el ejecutor fijado para la primera comparación.
La disponibilidad de un tag en el registro no acredita su funcionamiento con este ejecutor:
la compatibilidad se comprueba con las pruebas siguientes.

El proyecto comprueba tag y digest completo. Cambiar solo `RAGML_GENERATION_MODEL` provoca
una incompatibilidad con el lock; no desactivar esa comprobación. Crear uno alternativo con
los metadatos del modelo descargado, manteniendo el embedding original:

```powershell
$candidateKey = $candidateTag -replace '[^A-Za-z0-9._-]', '_'
$candidateDir = Join-Path $comparisonDir "$candidateKey-$(Get-Date -Format 'HHmmssfff')"
New-Item -ItemType Directory -Path $candidateDir -ErrorAction Stop | Out-Null
$candidateLockPath = Join-Path $candidateDir 'models.lock.json'

$localTags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -NoProxy -TimeoutSec 10
$selectedModels = @($localTags.models | Where-Object { $_.name -eq $candidateTag })
if ($selectedModels.Count -ne 1) { throw 'Candidate tag was not uniquely found locally' }
$selectedModel = $selectedModels[0]
$candidateDigest = ([string]$selectedModel.digest) -replace '^sha256:', ''
if ($candidateDigest -notmatch '^[0-9a-f]{64}$') { throw 'Invalid full model digest' }

$showBody = @{ model = $candidateTag } | ConvertTo-Json
$modelInfo = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/show' -Method Post -ContentType 'application/json' -Body $showBody -NoProxy -TimeoutSec 30
if ($modelInfo.details.quantization_level -ne 'Q4_K_M') { throw 'Unexpected quantization' }
if ([long]$selectedModel.size -le 0) { throw 'Invalid model size' }

$candidateLock = Get-Content -Raw -LiteralPath 'config\models.lock.json' | ConvertFrom-Json
$candidateLock.generation.tag = $candidateTag
$candidateLock.generation.digest = $candidateDigest
$candidateLock.generation.size_bytes = [long]$selectedModel.size
$candidateLock.generation.quantization = [string]$modelInfo.details.quantization_level
$candidateLock | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $candidateLockPath -Encoding utf8NoBOM
$modelInfo | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $candidateDir 'model-info.json') -Encoding utf8NoBOM
```

El digest se obtiene completo de `/api/tags`, no del identificador abreviado de `ollama list`.
Este lock registra la descarga elegida para comparaciones futuras; por sí solo no es una
verificación independiente del editor del modelo. Las fuentes de descarga anteriores son oficiales.

Guardar los valores previos de las variables que se van a modificar y activar el candidato
solo para los procesos iniciados desde esta terminal:

```powershell
$profileKeys = @(
    'RAGML_GENERATION_MODEL', 'RAGML_MODEL_LOCK_PATH',
    'RAGML_CONTEXT_TOKENS', 'RAGML_OUTPUT_TOKENS'
)
$previousProfile = @{}
foreach ($profileKey in $profileKeys) {
    $previousProfile[$profileKey] = [Environment]::GetEnvironmentVariable($profileKey, 'Process')
}
$env:RAGML_GENERATION_MODEL = $candidateTag
$env:RAGML_MODEL_LOCK_PATH = $candidateLockPath
$env:RAGML_CONTEXT_TOKENS = '4096'
$env:RAGML_OUTPUT_TOKENS = '256'

.\.venv\Scripts\ragml.exe doctor
if ($LASTEXITCODE -ne 0) { throw 'Candidate identity check failed; restore the previous profile' }
.\.venv\Scripts\ragml.exe probe-models --output (Join-Path $candidateDir 'infrastructure.json')
if ($LASTEXITCODE -ne 0) { throw 'Candidate inference failed; inspect compatibility before continuing' }
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía de demostración y durante cuánto tiempo?' --output (Join-Path $candidateDir 'warranty.json')
if ($LASTEXITCODE -ne 0) { throw 'Candidate RAG probe failed' }
& $ollamaExe ps
.\.venv\Scripts\python.exe -m ragml.rag_cli 'Según la ficha, ¿qué potencia tiene la Lámpara Flexo?' --product-id NEX-ILU-001 --output (Join-Path $candidateDir 'lamp.json')
if ($LASTEXITCODE -ne 0) { throw 'Candidate filtered probe failed' }
```

Si una prueba falla, conservar la evidencia y restaurar las variables con la sección 9 antes
de probar otro candidato. No volver a guardar `$previousProfile` mientras siga activo el anterior.
No hay que reconstruir el índice por cambiar únicamente generación.

## 7. Confirmar GPU y ajustar memoria

Ejecutar `& $ollamaExe ps` justo después de una respuesta, mientras el modelo sigue cargado.
La columna `PROCESSOR` indica `100% GPU`, `100% CPU` o reparto CPU/GPU; no es el porcentaje
instantáneo de utilización del procesador. Ver [FAQ de Ollama](https://docs.ollama.com/faq).
En otra terminal puede observarse `nvidia-smi` durante la consulta, si la GPU es NVIDIA.

El [script de arranque](../../scripts/start-models.ps1) fija un modelo cargado, una petición
paralela, contexto predeterminado 4096 y permanencia de dos minutos. Es una configuración
prudente para la memoria. Alternar embedding y generación puede provocar recargas;
no atribuir toda la latencia al número de parámetros sin medir.

Si el 8B ocupa demasiada memoria o funciona lentamente, volver al candidato 4B. Como
experimento separado, se puede reducir contexto antes de repetir la consulta:

```powershell
$env:RAGML_CONTEXT_TOKENS = '2048'
```

El adaptador pasa `num_ctx` explícitamente a Ollama, por lo que esta variable sí afecta a
las consultas RAG aunque el arranque mantenga un valor predeterminado de 4096. Reducirlo
puede dejar menos fragmentos en contexto y reducir calidad: guardar esa configuración
como experimento diferente. El proyecto admite entre 1024 y 8192 tokens de contexto y
entre 16 y 512 de salida; aumentar el contexto consume más memoria.

El adaptador actual solicita `think: false`. Comprobar que el candidato entregue contenido
final completo; no asumir que otro tag se comporte igual. Una respuesta con
`done_reason: length` se rechaza. Subir el límite de salida hasta 512 solo tendría sentido
tras comprobar que la causa es truncamiento, y se debe medir como otro cambio.
No aumentar timeouts para presentar una respuesta lenta como una mejora.

Qwen3.5 admite imágenes, pero este proyecto le envía texto. Cambiar a ese modelo no incorpora
automáticamente OCR, lectura de imágenes, herramientas ni nuevos formatos documentales.
Si el ejecutor no soporta el candidato, registrar el fallo y usar otra opción compatible.
Actualizar Ollama sería una tarea separada: revisar versión, hashes del ZIP y ejecutable,
lock de runtime, coherencia del lock de modelos y pruebas. No reemplazar el ejecutable
saltándose la comprobación SHA256 del script de arranque.

## 8. Cómo decidir si realmente mejora

Comparar en el mismo portátil, con idénticos corpus, embedding, preguntas, filtros, `k`,
contexto y límite de salida. Usar la referencia de 4096/256 anterior; comprobar que la
configuración efectiva de la medición inicial también tenía esos valores.
Registrar GPU, RAM, controlador, ejecutor, tags, digests y condiciones de carga.

1. Repetir preguntas de ajuste que cubran fichas, políticas, ambigüedad y falta de evidencia.
   Incluir solicitudes de precios o existencias para comprobar la abstención documental.
2. Revisar manualmente si cada respuesta contesta lo pedido y si la cita lo respalda;
   contar aciertos, errores, abstenciones correctas y fallos de formato con denominadores.
3. Medir primera carga y consultas posteriores por separado. Repetir el recorrido completo;
   con un solo modelo residente, una segunda consulta RAG no garantiza que el generador
   siga en memoria después de calcular el embedding de la pregunta.
4. Conservar `metrics.total_seconds`, `retrieval_seconds`, `generation_seconds`, estados,
   citas y `context_chunk_ids` de cada ejecución. Usar nombres de salida distintos para
   conservar las repeticiones. No comparar el microejemplo de 0,592 s con un RAG completo.
5. Elegir con casos de ajuste y mantener intacto el conjunto final hasta fijar la configuración.

No hay actualmente un comando que puntúe automáticamente toda la calidad de respuestas.
`rag_evaluation` solo calcula recuperación; cambiar el generador no debería mejorar Recall@5
si la búsqueda sigue idéntica. Para la revisión de respuestas, consultar el
[protocolo humano](../evaluation/human-review.md) y registrar también los fallos.

Plantilla para completar con resultados observados, sin rellenar estimaciones como mediciones:

| Configuración | Casos revisados | Respuestas correctas/total | Citas pertinentes/total | Fallos de formato | Latencia inicial y posterior | Carga GPU/CPU |
| --- | --- | --- | --- | --- | --- | --- |
| Actual 4B, 4096/256 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| Qwen3.5 4B, 4096/256 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| Qwen3 8B, 4096/256 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| Qwen2.5 7B, 4096/256 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

Adoptar el candidato si mejora las respuestas verificadas y mantiene tiempos aceptables,
sin perder citas, abstención ni controles. La meta de p95 de 60 s corresponde al recorrido
integrado pendiente; medir CLI ayuda a diagnosticarlo, pero no acredita esa integración.

## 9. Volver a la configuración anterior

En la misma terminal, después de cada candidato, incluso si alguna prueba falló:

```powershell
foreach ($profileKey in $profileKeys) {
    [Environment]::SetEnvironmentVariable($profileKey, $previousProfile[$profileKey], 'Process')
}
.\.venv\Scripts\ragml.exe doctor
if ($LASTEXITCODE -ne 0) { throw 'Restored profile check failed' }
```

Los valores ausentes se eliminan del entorno del proceso y vuelve a aplicarse `.env` o el
predeterminado. Los originales `config/models.lock.json` y `.env` permanecen sin editar.
El modelo descargado puede quedarse en disco; el siguiente uso cargará el que corresponda.
Los archivos de comparación se guardan en `.cache`, que puede limpiarse: copiar fuera de esa
carpeta los resultados y locks que se quieran conservar como evidencia duradera.

Para uso habitual tras elegir un ganador, formalizar después su tag y digest en el lock
principal y en la configuración, actualizar la documentación y ejecutar las comprobaciones
del proyecto. Esa adopción no se ha realizado como parte de esta guía.

## 10. Alcance de esta revisión

Se inspeccionaron configuración, scripts, adaptador Ollama, CLI, límites e informes locales.
Se consultó documentación actual mediante Context7 y fuentes primarias enlazadas.
Se comprobaron las opciones de ayuda de los comandos del proyecto y la sintaxis de los
bloques PowerShell de esta guía. Son comprobaciones documentales, no inferencia comparativa.
No se descargaron los candidatos ni se midió el portátil de 6 GB. La calidad y velocidad
de cada alternativa siguen pendientes de la comparación descrita.
