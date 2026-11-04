# Prototipo web: avance de fase 6

Fecha de verificación: 4 de noviembre de 2026. Estado: **en progreso**.

Se implementó una interfaz local en español, conectada al contrato HTTP existente.
El servidor web es un punto de entrada independiente para conservar los archivos
que desarrollan las otras fases. No requiere un proyecto Node, compilación de
frontend, CDN, fuentes remotas ni dependencias Python adicionales.

## Ejecutar

Desde la raíz del proyecto, con el entorno Python ya preparado:

```powershell
.\.venv\Scripts\python.exe -m ragml.web
```

Abrir `http://127.0.0.1:8000`. El servidor utiliza `Settings` y admite los argumentos
`--project-dir` y `--env-file`. Solo escucha en `127.0.0.1`.

Para convivir con una API que ya ocupe el puerto 8000:

```powershell
$env:RAGML_PORT = '8006'
.\.venv\Scripts\python.exe -m ragml.web
```

Abrir `http://127.0.0.1:8006`. Detener con Ctrl+C; el valor de la variable afecta
los siguientes procesos de esa terminal hasta quitarlo con
`Remove-Item Env:RAGML_PORT` o cerrar la terminal.

## Comportamiento implementado

- Nombre de tienda, modo de datos, categorías, cantidades y fichas procedentes del
  catálogo configurado. No se fijan identificadores de Nexo Demo en el cliente.
- Aviso visible de datos ficticios cuando el perfil declara `demo`.
- Consultas JSON a `POST /v1/chat`, con el `session_id` devuelto por el servicio.
- Conversación nueva, atajos Enter y Mayús + Enter, protección de composición IME,
  límite de entrada, bloqueo de envíos duplicados y conservación del borrador
  ante fallos. Los botones de categorías y ejemplos preparan un borrador editable.
- Estados `answered`, `clarification_required`, `insufficient_evidence` y
  `temporarily_unavailable`, además de errores HTTP, conexión y respuesta inválida.
- Fuentes por respuesta con versión, extracto, página, sección, párrafo y tabla;
  enlaces desde las afirmaciones hacia la fuente correspondiente.
- Citas comerciales con fecha de actualización, vencimiento y advertencia cuando
  ya están vencidas al mostrarlas. Las fichas no presentan precios ni existencias
  como actuales a partir de atributos documentales.
- Referencias de productos resueltas contra el catálogo cargado, con nombre de
  variante y atributos disponibles. Esas fichas no son recomendaciones calculadas.
- Diseño de escritorio y móvil, etiquetas de controles, foco visible, enlace para
  saltar al contenido y avisos accesibles. El contenido recibido se inserta como
  texto, sin interpretar HTML o Markdown.

La conversación y el borrador permanecen en memoria de la pestaña; no se usan
cookies, almacenamiento web ni analítica. Recargar los pierde. Iniciar otra
conversación descarta la sesión del cliente; no solicita borrar registros del
servidor. «Cancelar espera» aborta la solicitud del navegador; no garantiza detener
una inferencia que el servidor ya haya iniciado. La espera se limita a 240 segundos.

## Integración y archivos

`src/ragml/web.py` reutiliza `create_app` y añade únicamente:

| Ruta | Uso |
| --- | --- |
| `GET /` | Documento HTML |
| `/assets/*` | Recursos empaquetados de la interfaz |
| `GET /v1/web/catalog` | Catálogo validado, sin caché; 503 si falta, es inválido o su modo difiere de la configuración |

La interfaz consulta `/health` para indicar **conexión a la API**, no disponibilidad
del RAG. Las rutas y respuestas de la API base se conservan. No se modificaron
`api.py`, `conversation.py`, `settings.py`, `pyproject.toml`, los datos ni los modelos.

Los recursos están en `src/ragml/web_assets/`; `chat-client.mjs` concentra el
transporte y la sesión. El paquete wheel incluye los cuatro recursos del frontend.

## Verificación observada

Las pruebas nuevas se ejecutaron primero con fallo y después con la implementación.
Los comandos siguientes se ejecutan desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web.py -q
node --test --test-isolation=none tests/web/chat-client.test.mjs
.\.venv\Scripts\python.exe -m ruff check src/ragml/web.py tests/test_web.py
.\.venv\Scripts\python.exe -m ruff format --check src/ragml/web.py tests/test_web.py
.\.venv\Scripts\python.exe -m mypy src/ragml/web.py
```

Resultado: 2 pruebas HTTP y 6 pruebas del cliente correctas; estilo, formato y tipos
correctos. Node se usa para comprobar el transporte, no para ejecutar la aplicación.
`--test-isolation=none` evita el error `spawn EPERM` del sandbox de Windows sin
desactivar las aserciones. Pytest requirió ejecución fuera del sandbox por permisos
de su caché y archivos temporales.

Con `agent-browser` instalado y el servidor web iniciado, ejecutar:

```powershell
.\tests\web\browser-smoke.ps1 -BaseUrl http://127.0.0.1:8006
```

Este recorrido pasó en Chromium: cuatro estados de respuesta, fuentes y enlaces,
producto referenciado, dato comercial vencido, texto con HTML sin ejecución,
reinicio, composición IME, fallo de red, recuperación del borrador, ejemplos y foco
por teclado. También comprobó ausencia de desbordamiento horizontal de la página
a 1440, 390 y 320 píxeles. Las categorías tienen desplazamiento horizontal propio
en móvil. El script crea y cierra una sesión de navegador aislada e intercepta
solo las respuestas de chat de esa sesión con fixtures identificados como pruebas.
No cambia el servidor ni guarda esos fixtures en el catálogo.

Por separado, una consulta al endpoint real devolvió `503 rag_not_ready`; se
observó el aviso correspondiente con el texto conservado y la opción de reintentar.
Se inspeccionaron capturas de escritorio y móvil; no hubo errores de JavaScript en
la pantalla inicial. Las capturas locales están en `.cache/phase6/`.

El empaquetado local offline pasó y se comprobó con `TestClient` que la copia
extraída del wheel sirve HTML, JavaScript, CSS y catálogo. Comando de construcción:

```powershell
uv build --no-sources --offline --cache-dir .cache/phase6/uv --out-dir .cache/phase6/dist
```

La última batería global terminó con **140 pruebas correctas**. Un fallo de fase 4
observado en una ejecución anterior ya no se reprodujo tras los avances paralelos;
no se modificó ese código en este avance de interfaz. El resultado es una
instantánea, no un cierre de las otras fases.

## Pendiente para cerrar la fase

- Conectar y verificar el servicio conversacional real cuando las fases 4 y 5
  estabilicen su integración HTTP. En esta instantánea `/v1/chat` sigue respondiendo
  `rag_not_ready`; no se presenta el prototipo como un RAG web completo.
- Integrar recomendaciones, comparación comercial y continuidad de restricciones
  de fase 5. El botón «Compara opciones» solo prepara una consulta al asistente.
- Comprobar versiones de catálogo frente a las referencias de cada respuesta al
  actualizar los datos; las fichas actuales corresponden al catálogo cargado en la
  pestaña. Recargar tras una actualización.
- Hacer recorridos completos con inferencia y comercio reales, y pruebas con
  participantes. La comprobación móvil fue emulada en Chromium; no se probaron
  dispositivos físicos, otros motores ni un lector de pantalla.

Las respuestas controladas y las pruebas de software no son evaluación académica
del RAG, validación comercial ni evidencia de utilidad con usuarios.
