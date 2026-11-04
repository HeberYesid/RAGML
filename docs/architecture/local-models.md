# Modelos locales: preparación y operación

Selección comprobada el 4 de noviembre de 2026, con Windows y PowerShell 7.
No se necesitan cuenta, API key ni servicios de pago. La descarga inicial requiere internet.

## Versiones fijadas

| Uso | Modelo | Cuantización | Tamaño descargado |
| --- | --- | --- | --- |
| Respuestas | `qwen3:4b-instruct-2507-q4_K_M` | Q4_K_M | 2.497.293.803 bytes |
| Representaciones | `qwen3-embedding:0.6b` | Q8_0 | 639.150.858 bytes |

Los digests completos y las dimensiones están en [models.lock.json](../../config/models.lock.json).
El ejecutor portátil es Ollama 0.40.14; URL, versión y SHA256 publicados están registrados en
[runtime.lock.json](../../config/runtime.lock.json). El ZIP se verificó antes de extraer y el
script de arranque comprueba también el SHA256 de `ollama.exe`.

## Primera preparación

Después de instalar dependencias con `uv sync --locked --group dev` según la guía del entorno:

```powershell
.\scripts\setup-models.ps1
.\.venv\Scripts\ragml.exe doctor
```

El procedimiento descarga el ZIP oficial si falta, comprueba el hash, extrae en `.cache/ollama`,
inicia el proceso del proyecto en una ventana oculta y descarga los dos tags. Finalmente verifica
que los digests locales coincidan con el lock. Si un tag cambia en el registro, no se acepta en
silencio: hay que revisar el modelo y actualizar la selección de forma explícita.

El script se comprobó sobre esta instalación con los pesos ya descargados; la descarga, checksum,
extracción y ejecución inicial se observaron en pasos separados. No se repitió toda la descarga
en otra máquina. Una interrupción puede dejar un archivo parcial: el checksum lo detectará y el
script se detendrá sin ejecutarlo ni borrar datos automáticamente.

## Uso posterior y cierre

```powershell
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\ragml.exe doctor
.\.venv\Scripts\ragml.exe probe-models
.\scripts\stop-models.ps1
```

Sin `-Background`, `start-models.ps1` conserva el servidor en la terminal y se detiene con Ctrl+C.
El cierre automático por script solo actúa sobre el PID registrado y su ruta de ejecutable
comprobada. No detiene otro Ollama ni otro servicio. El puerto 11435 se reserva para este proyecto;
un servicio ajeno en ese puerto provoca un error, sin reutilizarlo.

Las variables del proceso son `OLLAMA_HOST=127.0.0.1:11435`, `OLLAMA_NO_CLOUD=1`,
`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, contexto 4096 y permanencia de dos minutos.
No se instala servicio de Windows, no se modifica el PATH ni se abre un puerto a la red.
Ollama puede crear su configuración de usuario habitual; los pesos y ejecutables utilizados aquí
permanecen en la caché del proyecto. No se guardan claves en el código ni en el cliente.

## Límites y actualización

El cliente solo acepta HTTP en `127.0.0.1` con puerto explícito, ignora proxies del entorno y no
sigue redirecciones. Antes de cada operación comprueba el digest. No descarga automáticamente
modelos durante una consulta ni recurre a un proveedor remoto cuando el local falla.

Las respuestas incompletas se rechazan. Las representaciones se comprueban por cantidad,
dimensión, finitud y norma; los errores de contexto no se resuelven truncando embeddings en silencio.
La consulta lleva la instrucción de recuperación recomendada por Qwen; el documento no.

Cambiar modelo o ejecutor requiere revisar licencia, compatibilidad, lock y pruebas. Cambiar
embeddings obliga a reconstruir el índice. La conexión a una tienda real requerirá sus fuentes
permitidas y un adaptador; no requiere contratar un proveedor de generación.
