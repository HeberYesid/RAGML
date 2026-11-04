# Entorno local y comprobaciones

Verificación: 4 de noviembre de 2026. Windows, Python 3.13.7, uv 0.9.26 y PowerShell 7.
La fase 2 tiene base ejecutable y contratos. Su verificación se separa del RAG y de la evaluación.

## Instalación y configuración

Desde la raíz:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache\uv'
uv sync --locked --group dev --python 3.13.7 --no-python-downloads --no-managed-python --default-index https://pypi.org/simple
.\scripts\setup-models.ps1
.\.venv\Scripts\ragml.exe doctor
```

`pyproject.toml` declara un paquete con backend `uv_build==0.9.26`, layout `src` y comando `ragml`.
Las dependencias se fijan con `uv.lock`. No se modifica el Python global. El grupo dev contiene
HTTPX2 para el TestClient actual; el adaptador de Ollama usa HTTPX. No se desactivan advertencias.

`load_settings` carga solo el `.env` del directorio de proyecto explícito o el archivo indicado.
Las rutas relativas se resuelven desde ese directorio. Los valores predeterminados ya son locales;
`.env.example` es una configuración válida y no es obligatorio copiarla para ejecutar.

```powershell
.\.venv\Scripts\ragml.exe --project-dir 'C:\ruta\RAGML' --env-file 'C:\ruta\RAGML\.env' doctor
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\ragml.exe serve
```

La API escucha en 127.0.0.1:8000; el modelo en 127.0.0.1:11435. Si el puerto de API está ocupado,
seleccionar otro en `RAGML_PORT` antes de iniciar; no reutilizar el servicio ajeno. El modo inicial
es una instancia local de una sola tienda, sin publicación ni autenticación para exposición externa.

## Matriz de comandos y resultados observados

| Comprobación | Comando | Evidencia |
| --- | --- | --- |
| Dependencias | `uv sync --locked --group dev --python 3.13.7 --no-python-downloads --no-managed-python --cache-dir .cache/uv` | Instalación local realizada; lock fijado |
| Pruebas | `.\.venv\Scripts\python.exe -m pytest` | 44 pasan; sin omitidas ni fallidas en la ejecución final |
| Análisis estático | `.\.venv\Scripts\python.exe -m ruff check src tests` | Sin errores |
| Formato | `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Sin cambios necesarios |
| Tipos | `.\.venv\Scripts\python.exe -m mypy src` | Sin errores en 11 archivos fuente |
| Empaquetado | `uv build --no-sources --offline --cache-dir .cache/uv --out-dir dist` | Wheel y sdist construidos |
| Diagnóstico real | `.\.venv\Scripts\ragml.exe doctor` | SQLite 3.50.4, modelos con digest correcto, base preparada y RAG no disponible |
| Modelos reales | `.\.venv\Scripts\ragml.exe probe-models` | Generación completa en español y vectores de 1024 dimensiones |
| Contratos exportados | `.\.venv\Scripts\ragml.exe export-contracts` | JSON Schema y OpenAPI en `schemas/` |
| Scripts de modelos | `scripts/setup-models.ps1`, `start-models.ps1`, `stop-models.ps1` | Preparación y controles del proceso comprobados; parseo sin errores |

Los comandos offline necesitan artefactos ya descargados. La primera preparación necesita acceso
al registro público de paquetes y de modelos. No se probó instalación en otro sistema operativo.

Se preparó un entorno separado `.cache/wheelcheck` con dependencias fijadas y se instaló el wheel
sin editable. Se verificó que `ragml` se importaba desde `site-packages`, se ejecutó `doctor`
desde otro directorio y se inició la API real con ese paquete. No se sustituyó esta comprobación
por una mera inspección estructural del wheel.

La primera ejecución de pytest en el aislamiento falló al aplicar `chmod` a su caché. Las pruebas
se ejecutaron con la ejecución normal de Windows autorizada por el entorno, sin cambiar permisos
ni ignorar advertencias. También se corrigió el cargador de valores numéricos y booleanos de `.env`.

## Alcance de las 44 comprobaciones

La batería conserva 22 casos de catálogo y comercio y añade 22 de configuración, evidencia,
citas, API y proveedor local simulado. Comprueba importes y desconocidos, relaciones por tienda,
versiones y hashes, ubicación de evidencia, citas huérfanas, vigencia, lectura de revisiones,
identidad de modelo, fallos, redirecciones y respuestas incompletas. Se escribió después de la
implementación: no hay evidencia TDD RED/GREEN.

Las pruebas del proveedor usan MockTransport, no pesos reales. Las inferencias y el HTTP real
se comprobaron aparte con textos sintéticos:

- [Prueba real de modelos](evidence/local-model-probe-20261104.json).
- [Prueba real de API desde el wheel](evidence/local-api-probe-20261104.json).

La API devolvió salud 200, estado RAG 503, error de entrada 422 y contrato OpenAPI 200. Los archivos
de datos se detectan por separado; su presencia no hace disponible una recuperación aún no
implementada. El proceso HTTP de prueba se cerró al terminar. `/docs` y `/redoc` están desactivados
para evitar cargar recursos de documentación externos; OpenAPI permanece local.

Los datos de fase 3 se validaron en lectura con `CatalogDataset`, `CommercialDataset` y
`SourceManifest`, incluidas sus relaciones: 60 productos, 90 variantes, 72 fuentes y 204 fragmentos.
No se generaron embeddings de ese corpus ni se creó su índice para cerrar fase 2.

No hay revisión visual de interfaz, conversación completa, ensayo de concurrencia sostenida,
p95 del RAG o evaluación con participantes. Son verificaciones de sus fases, no fallos omitidos.
El repositorio Git sigue sin inicializar; se revisan archivos y diferencias con la instantánea local
anterior, y se conservan los documentos académicos originales. No hubo commits ni despliegues.
