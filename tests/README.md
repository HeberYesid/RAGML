# Comprobaciones locales

Actualizado el 9 de noviembre de 2026. El ejecutor principal es pytest. El número
total de casos cambia durante el desarrollo; utilizar el resumen de la ejecución
observada para el candidato actual, sin trasladar conteos históricos.

| Área | Archivos de referencia | Qué comprueba |
| --- | --- | --- |
| Contratos y proveedor | `test_local_contracts.py`, `test_foundation.py` | Datos, procedencia, configuración, transporte del proveedor y contrato HTTP. |
| Ingesta y recuperación | `test_ingestion.py`, `test_retrieval.py` | Publicaciones coherentes, filtros, referencias y comportamiento con vectores controlados. |
| Respuesta documental | `test_rag.py`, `test_rag_cli.py`, `test_rag_evaluation.py` | Extractos, estados, comando documental y cálculo de recuperación. |
| Asesoría y conversación | `test_advice.py`, `test_chat_integration.py` | Restricciones, comparación, datos comerciales, cambios de presupuesto y sesiones por propietario. |
| Web | `test_web.py`, `web/chat-client.test.mjs` | Recursos, catálogo, transporte, errores, cancelación, reinicio y expiración del cliente. |
| Evaluación | `test_evaluation.py`, `test_integrated_evaluation.py` | Métricas y registros, cobertura, errores y ejecución integrada mediante límites controlados. |
| Exploración de datos | `test_analysis.py` | Estadísticas, faltantes, reloj comercial, exportación y tratamiento de valores atípicos sobre ejemplos comprobables. |

## Ejecutar

Desde la raíz y con el entorno preparado:

```powershell
$testDir = Join-Path '.cache' ('pytest-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $testDir
.\.venv\Scripts\python.exe -m ruff check src tests --no-cache
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src
node --test --test-isolation=none tests/web/chat-client.test.mjs
```

El nombre temporal único evita reutilizar o eliminar una carpeta de otra prueba.
En este equipo se observaron errores de permisos de pytest dentro del aislamiento
de archivos de Windows; la ejecución aprobada fuera de ese aislamiento permite
comprobar la batería sin modificar permisos ni desactivar aserciones. Node se usa
para probar el transporte; no es necesario para servir la interfaz web.

## Alcance de la evidencia

Las pruebas automatizadas no descargan modelos ni representan un estudio con
usuarios. Los recorridos HTTP de `test_chat_integration.py` utilizan un doble en
el límite externo de inferencia, con orquestación y datos locales reales del
proyecto. Acreditan coordinación de software, no relevancia semántica o calidad
del modelo de lenguaje. Las pruebas del cliente simulan el transporte.

La inferencia con los modelos instalados y los recorridos de navegador deben
conservar sus propias evidencias fechadas. Los registros de la nueva evaluación
integrada se organizan en `docs/evaluation/integrated/`; las comprobaciones
históricas de entorno están en [la guía técnica](../docs/architecture/local-environment.md).
Inspeccionar cada registro para saber qué se ejecutó y qué falló.

El chat actual usa una cookie firmada para aislar propietarios y un repositorio
en memoria con TTL de inactividad. El historial visible no persiste al recargar.
La reproducción comercial del demo usa un reloj explícito y no equivale a precios
actuales de una tienda. Estas condiciones deben mantenerse en las pruebas.

Las instrucciones actuales exigen TDD para cambios de comportamiento. Las notas
de fase 2 que indican comprobaciones posteriores describen una etapa histórica;
no se inventa evidencia RED/GREEN para ella. La cantidad de pruebas de software
no se suma a los casos académicos ni sustituye la evaluación final reservada o
la utilidad con participantes.
