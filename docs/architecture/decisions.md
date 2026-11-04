# Decisiones técnicas y presupuesto

Fecha: 4 de noviembre de 2026. Selección cerrada para el prototipo local. Las versiones Python
están fijadas en `uv.lock`; ejecutor y modelos, en `config/runtime.lock.json` y `config/models.lock.json`.

## Selección y justificación

| Decisión | Motivo y límites |
| --- | --- |
| Python 3.13.7 y uv 0.9.26 | Reutilizar el entorno disponible y un solo lenguaje para contratos, servicio e ingesta; instalación aislada y reproducible |
| FastAPI 0.162.0 y Uvicorn 0.54.0 | API pequeña con modelos tipados y OpenAPI; sin servidor de desarrollo frontend separado |
| Pydantic 2.14.2 y pydantic-settings 2.16.2 | Validación de datos, relaciones y configuración sin crear validadores genéricos propios |
| HTML/CSS/JavaScript nativo | Interfaz sencilla del mismo origen, con recursos locales y sin compilación o CDN; implementación en fase 6 |
| JSON y SQLite 3.50.4 | JSON como intercambio canónico; SQLite local para persistencia e índice derivado, sin administrar un servidor |
| Embeddings normalizados y coseno exacto | Corpus previsto pequeño; evita depender de extensiones vectoriales o servicios remotos. FTS5 está disponible para comparar una búsqueda léxica si el ajuste lo justifica |
| Ollama portátil 0.40.14 | Un ejecutor para generación y embeddings, API solo en loopback, nube deshabilitada y almacén de pesos en el proyecto |
| Qwen3 4B Instruct 2507 Q4_K_M | Tamaño moderado, instrucciones y soporte multilingüe. Variante específica sin razonamiento extendido; su adecuación final se medirá con los casos de ajuste |
| Qwen3 Embedding 0.6B Q8_0 | Modelo multilingüe pequeño, 1024 dimensiones; consulta con prefijo de tarea y documentos sin ese prefijo |
| pytest, Ruff y mypy | Comprobaciones posteriores al desarrollo, sin TDD por indicación del usuario |

Se eligió la variante Instruct explícita tras comprobar que el tag genérico `qwen3:4b` emitía
razonamiento y agotaba una respuesta de 96 tokens con el ejecutor seleccionado. No se relajó la
comprobación de respuestas incompletas: el adaptador rechaza `done_reason: length`.
La variante genérica de prueba se retiró del almacén exclusivo del proyecto.

Los dos modelos elegidos publican licencia Apache 2.0. No hay garantía de exactitud por su licencia,
por su tamaño ni por los resultados de sus autores. No se adopta una afirmación de mejor modelo
universal: esta es la selección comprobada para iniciar el prototipo y ajustarlo sobre sus fuentes.

## Equipo y ejecución observada

Equipo: 16 GiB RAM, Ryzen 5 3600 de seis núcleos y 12 hilos, GTX 1650 con 4 GiB VRAM. El controlador
NVIDIA consultado es 621.01. Ollama administra la carga que quepa en GPU y su eventual reparto con
CPU; no se promete que todo el modelo permanezca en VRAM. No se cerraron aplicaciones del usuario.

El ejecutor y los dos modelos ocupan aproximadamente 5,02 GiB en `.cache/ollama`; el archivo ZIP
original añade alrededor de 1,49 GiB. Es una medición de esta instalación, no del consumo de RAM.

La prueba sintética guardada en [evidencia local](evidence/local-model-probe-20261104.json) produjo:

| Comprobación | Resultado observado | Límite |
| --- | --- | --- |
| Generación breve, carga inicial | 4,464 s; respuesta completa sobre una potencia ficticia de 8 W | Prompt de 63 tokens y salida de 10 tokens |
| Repetición del mismo caso | 0,592 s; respuesta completa de 11 tokens | No estima p95 ni conversaciones largas |
| Dos documentos y una consulta de embeddings | 2,713 s; 1024 dimensiones | Solo tres textos sintéticos |
| Similitud con documento pertinente frente a distractor | 0,704 frente a 0,233 | No es Recall@5 ni validación de recuperación del catálogo |

La primera política descargaba embeddings en cada llamada y la comprobación tardó 31,363 s.
Mantenerlos hasta dos minutos permite reutilizarlos durante la ingesta y consultas consecutivas;
`OLLAMA_MAX_LOADED_MODELS=1` evita mantener simultáneamente ambos modelos. Esto no demuestra aún
la latencia del recorrido que alternará recuperación y generación.

## Presupuesto de diseño para las siguientes fases

Se fijan metas antes de la evaluación final. No son resultados ya conseguidos sobre el corpus:

| Recurso | Límite o meta de diseño |
| --- | --- |
| Servicios externos de inferencia | 0; no hay proveedor remoto ni credenciales configuradas |
| Concurrencia | Una operación de modelo por cliente; servidor Ollama con una petición paralela y un modelo cargado |
| Contexto y salida | Contexto 4.096 tokens, salida hasta 256; plan de composición: hasta 3.584 de entrada y 256 de reserva |
| Generación | Meta de 30 s por respuesta con modelo cargado; 90 s con carga inicial |
| Recorrido integrado | Meta p95 de 60 s por turno con el candidato de fase 6; medir antes de evaluar utilidad |
| Timeout del proveedor | 180 s; conexión 3 s; fallos explícitos y sin confirmar datos |
| RAM del ejecutor | Presupuesto inicial de 8 GiB; medir pico sostenido durante integración |
| Disco de preparación | Reservar 12 GiB para ejecutor, pesos, archivo de instalación y cachés |
| Corpus e índice por tienda | Presupuesto inicial de 100 MiB; contabilizar texto, metadatos e índice real en fase 3 |
| Ingesta de este corpus | Meta inicial de 10 minutos; lotes de embeddings de hasta 16 textos |
| Evidencia por consulta | k=5 inicialmente; se ajusta solo con casos de desarrollo |

El límite de 12.000 caracteres de entrada del adaptador es una guardia de ingeniería y no un
contador de tokens. La fase 4 debe componer y comprobar el presupuesto real de contexto; no se
puede afirmar ausencia de truncamiento solo por contar caracteres. Para embeddings se solicita
`truncate=false` y se comprueban cantidad, dimensiones, finitud y normalización.

Con los 204 fragmentos disponibles, 204 × 1024 × 4 son 835.584 bytes de vectores float32 sin
sobrecarga. Se propone guardarlos como BLOB en SQLite con dimensión, modelo y digest. Ese cálculo
no mide el tamaño del índice futuro ni la sobrecarga de las tablas.

Para T turnos de evaluación, planificar hasta T × 3.584 tokens de entrada y T × 256 de salida,
sin convertirlo en consumo medido. Los 120 escenarios comparados en dos configuraciones implican
al menos 240 turnos si todos tuvieran uno; los diálogos aumentan T. No hay una tarifa externa que
facturar, pero sí uso de equipo, electricidad, almacenamiento y conectividad de descarga.

Si una meta no se cumple, se documentará y ajustará la implementación con los casos de desarrollo.
No se cambiarán metas después de abrir los casos finales para presentar un resultado favorable.

## Fuentes de las decisiones

Se consultaron documentación oficial mediante Context7 y fichas primarias de los modelos:
[FastAPI](https://fastapi.tiangolo.com/tutorial/), [recursos locales de documentación](https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/),
[uv](https://docs.astral.sh/uv/), [Pydantic](https://docs.pydantic.dev/latest/),
[SQLite](https://www.sqlite.org/fts5.html), [Ollama en Windows](https://docs.ollama.com/windows),
[Qwen3 4B Instruct](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507),
[distribución Q4_K_M](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M) y
[Qwen3 Embedding 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
La compatibilidad actual de TestClient requiere HTTPX2 como dependencia de desarrollo;
[su documentación permite coexistir con HTTPX](https://github.com/pydantic/httpx2/blob/main/docs/migration.md).
