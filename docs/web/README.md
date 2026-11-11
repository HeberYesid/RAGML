# Prototipo web integrado

Actualizado el 9 de noviembre de 2026. Estado: chat integrado en código; la
verificación de la entrega actual se registra por separado. La evidencia del
4 de noviembre se conserva más abajo como una instantánea histórica.

La interfaz local en español utiliza el servicio conversacional de `api.py` y
`chat.py` para consultas documentales, asesoría, comparación y continuidad de
restricciones. No requiere un proyecto Node, compilación de
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
- Reloj comercial simulado explícito cuando los metadatos del paquete demo
  corresponden al catálogo activo. La fecha de reproducción no representa
  precios o existencias de una empresa en la fecha real de ejecución.
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
  variante y atributos disponibles. La asesoría calcula alternativas mediante
  reglas de elegibilidad y preferencias; la ficha visible representa el producto
  devuelto por ese recorrido, no un recomendador entrenado en el navegador.
- Diseño de escritorio y móvil, etiquetas de controles, foco visible, enlace para
  saltar al contenido y avisos accesibles. El contenido recibido se inserta como
  texto, sin interpretar HTML o Markdown.

El historial visible y el borrador permanecen en memoria de la pestaña y se pierden
al recargar; no se guardan en almacenamiento web. El servidor utiliza una cookie
opaca firmada `ragml_owner`, con `HttpOnly` y `SameSite=Strict`, para vincular la
sesión con su propietario. Los requisitos y referencias de sesión se conservan en
memoria del proceso, con TTL de inactividad configurable de 1800 segundos por
defecto; no se almacenan conversaciones en disco. Reiniciar el servidor pierde
ese estado e invalida las firmas anteriores.

«Conversación nueva» descarta el contexto del cliente y solicita eliminar su sesión
mediante `DELETE /v1/chat/sessions/{session_id}`. Si la solicitud no llega, se aplica
la expiración del servidor. «Cancelar espera» aborta la solicitud del navegador;
no garantiza detener una inferencia que el servidor ya haya iniciado. La espera
del cliente se limita a 240 segundos. Una sesión vencida o ajena devuelve
`session_not_found`, y el cliente libera su identificador antes de reintentar.

## Integración y archivos

`src/ragml/web.py` reutiliza la API integrada de `create_app` y añade:

| Ruta | Uso |
| --- | --- |
| `GET /` | Documento HTML |
| `/assets/*` | Recursos empaquetados de la interfaz |
| `GET /v1/web/catalog` | Catálogo validado, sin caché; 503 si falta, es inválido o su modo difiere de la configuración |
| `GET /v1/web/runtime` | Tienda, revisión, reloj comercial y política de sesiones del servicio integrado |

La interfaz consulta `/ready` para mostrar disponibilidad del asistente. Ese
endpoint comprueba catálogo, manifiesto, corpus, fuente comercial y modelos;
devuelve 200 o 503 según el resultado. `/health` comprueba salud y existencia de
una publicación coherente, sin sustituir todas las comprobaciones de `/ready`.
`POST /v1/chat` ejecuta `ChatService`; `rag_not_ready` indica una preparación fallida,
no que la integración sea una función pendiente en toda instalación.

Los recursos están en `src/ragml/web_assets/`; `chat-client.mjs` concentra el
transporte y la sesión. El paquete wheel incluye los cuatro recursos del frontend.

## Evidencia histórica del 4 de noviembre

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

En aquella versión, una consulta al endpoint real devolvió `503 rag_not_ready`; se
observó el aviso correspondiente con el texto conservado y la opción de reintentar.
Se inspeccionaron capturas de escritorio y móvil; no hubo errores de JavaScript en
la pantalla inicial. Las capturas locales están en `.cache/phase6/`.

El empaquetado local offline pasó y se comprobó con `TestClient` que la copia
extraída del wheel sirve HTML, JavaScript, CSS y catálogo. Comando de construcción:

```powershell
uv build --no-sources --offline --cache-dir .cache/phase6/uv --out-dir .cache/phase6/dist
```

La batería global de aquella instantánea terminó con **140 pruebas correctas**. Un fallo de fase 4
observado en una ejecución anterior ya no se reprodujo tras los avances paralelos;
no se modificó ese código en este avance de interfaz. El resultado es una
instantánea, no un cierre de las otras fases.

## Verificación de la entrega del 9 de noviembre

- La integración se encuentra en `api.py`, `chat.py`, `interpretation.py` y
  `sessions.py`. `tests/test_chat_integration.py` comprueba recorridos HTTP con
  inferencia sustituida; esas pruebas no estiman la calidad del modelo real.
- Los registros nuevos de inferencia y recorridos de ajuste se organizan en
  `docs/evaluation/integrated/`; utilizar solo las ejecuciones que ya existan y
  tengan resultados observados. La disponibilidad de un ejecutor no demuestra
  que una evaluación haya pasado.
- Comprobar versiones de catálogo frente a las referencias de cada respuesta al
  actualizar los datos; las fichas actuales corresponden al catálogo cargado en la
  pestaña. Recargar tras una actualización.
- Conservar el resultado de los recorridos completos del candidato actual. El
  comercio de esta entrega es simulado, incluso cuando la inferencia es real.
  La comprobación móvil histórica fue emulada en Chromium; no se probaron
  dispositivos físicos, otros motores ni un lector de pantalla.

Las pruebas con participantes pertenecen al protocolo amplio de evaluación y
siguen requiriendo un estudio real. La sustentación y sus resultados técnicos se
preparan en `docs/reports/` sin inventar satisfacción ni observaciones de clientes.

Las respuestas controladas y las pruebas de software no son evaluación académica
del RAG, validación comercial ni evidencia de utilidad con usuarios.
