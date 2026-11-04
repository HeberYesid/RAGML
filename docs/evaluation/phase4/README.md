# Fase 4: recuperación y respuesta documental local

Actualizado el 4 de noviembre de 2026. Estado: **IN PROGRESS**.
Existe una referencia ejecutable de recuperación y respuesta extractiva con fuentes.
No es todavía la integración HTTP/web ni la evaluación final del asistente.

## Implementación

- [SqliteRetriever](../../../src/ragml/retrieval.py): coseno exacto sobre embeddings
  normalizados, con lectura SQLite `mode=ro` y una transacción de lectura para
  obtener metadatos, catálogo, manifiesto y vectores de la misma publicación.
- [DocumentRag](../../../src/ragml/rag.py): consulta de un turno con selección de
  citas mediante el modelo local. Solo entrega como afirmación texto que existe
  literalmente en uno de los fragmentos incluidos en el contexto.
- [Comando documental](../../../src/ragml/rag_cli.py): consulta, filtros,
  recuperación sin generación y exportación opcional de evidencia JSON.
- [Medición de ajuste](../../../src/ragml/rag_evaluation.py): Recall@k y latencias
  sobre los casos documentales y de políticas de la partición de ajuste existente.

No se añadieron dependencias ni se cambiaron contratos, API de base, ingesta, datos
de demostración o casos de referencia de las fases 2 y 3. Las decisiones vigentes
siguen en [arquitectura](../../architecture/decisions.md) y las fuentes en
[documentación de datos](../../data/README.md).

## Ejecutar

Desde la raíz del proyecto, con el entorno de fase 2 preparado y el índice de
fase 3 publicado en `data/runtime/corpus.sqlite3`:

```powershell
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía de demostración y durante cuánto tiempo?'
.\.venv\Scripts\python.exe -m ragml.rag_cli 'Según la ficha, ¿qué potencia tiene la Lámpara Flexo?' --product-id NEX-ILU-001
.\.venv\Scripts\python.exe -m ragml.rag_cli '¿Qué cubre la garantía?' --retrieval-only
.\.venv\Scripts\python.exe -m ragml.rag_evaluation
```

Otras opciones: `--variant-id`, `--category-id`, `--k` entre 1 y 10,
`--no-store-policies`, `--revision`, `--database`, `--project-dir` y `--output`.
Los tres filtros de identidad pueden repetirse. Sus conjuntos se intersectan por
relación de catálogo; una combinación incompatible no devuelve candidatos.

La tienda se obtiene del catálogo configurado; la revisión predeterminada se toma
del manifiesto configurado. La recuperación rechaza una revisión no activa y un
modelo, digest o dimensión distintos de los del índice. No crea una base vacía si
falta el archivo ni modifica la publicación de fase 3.

Un filtro de variante permite evidencia de esa variante y evidencia común de su
producto y categoría. Un filtro de producto permite sus variantes. Las políticas
generales se incluyen si se solicita, sin asignarlas a un producto inventado. Los
empates se resuelven por identificador de fragmento para reproducibilidad.

Para detener un servidor que se inició para uso propio, usar el procedimiento de
[modelos locales](../../architecture/local-models.md). No detener un proceso
compartido mientras otro chat lo utiliza. En esta sesión se reutilizó el servidor
del proyecto existente y se dejó en ejecución.

## Respuestas, presupuesto de contexto y fallos

La salida incluye `ChatResponse`, citas con fuente/versión/fragmento/ubicación,
fragmentos recuperados, fragmentos realmente incluidos en contexto y métricas.
Los estados son `answered`, `clarification_required`, `insufficient_evidence` y
`temporarily_unavailable`. Cada consulta crea identificadores nuevos; todavía no
hay historial ni resolución conversacional entre turnos.

El modelo selecciona citas mediante JSON restringido por instrucciones; el servicio
valida después el JSON, los identificadores y los extractos. Las citas inventadas,
los textos reformulados y las respuestas incompletas no se presentan como respuestas
verificadas. El formato extractivo es deliberado para esta primera referencia. No
implementa todavía síntesis libre de varias fuentes.

Los fragmentos y las preguntas son datos no confiables. El selector no tiene
herramientas, acceso a pagos ni acciones comerciales. La batería comprueba rechazo
de salidas inventadas; no demuestra resistencia universal a instrucciones maliciosas.

Se incluyen fragmentos completos en orden de recuperación mientras quepan. Se usa
una cota conservadora de bytes UTF-8 para el tokenizador por bytes de los modelos
seleccionados, con reserva para plantilla y salida. No es un tokenizador exacto ni
un contrato portable a cualquier modelo. Se registran además los tokens de entrada
que declara el proveedor y se rechaza una salida que exceda el presupuesto observado.
Si nada cabe, se informa insuficiencia; nunca se recorta silenciosamente una tabla
o una oración para completar el contexto.

Las preguntas comerciales reconocidas y los extractos que parecen contener valores
monetarios o existencias producen abstención. Esta regla es conservadora y puede
rechazar preguntas documentales sobre precios o cantidades; no es un clasificador
completo de todas las formulaciones posibles. La fase 5 debe resolver intención,
vigencia y consulta estructurada. No se interpretan citas documentales como datos
comerciales actuales.

Una cita literal verifica procedencia textual; no demuestra por sí sola que sea
pertinente, completa o compatible con otras fuentes. El modelo puede abstenerse ante
ambigüedad o contradicción, pero todavía falta medir sistemáticamente ese comportamiento.

## Evidencia observada

Corpus utilizado: `nexo-demo`, revisión `demo-20261104-v2`, 72 fuentes y 204 fragmentos.
La huella del corpus, los digests de modelos y los resultados por caso están
guardados en los JSON enlazados, sin copiar el conjunto final.
La [instantánea de código y configuración](code-snapshot.json) registra hashes
SHA256 de los módulos, pruebas y archivos de configuración públicos utilizados;
no hay un commit de referencia porque esta carpeta no tiene repositorio Git.

| Comprobación | Resultado observado | Límite |
| --- | --- | --- |
| [Recuperación sobre ajuste](adjustment-retrieval.json) | Recall@5 medio 1,00; 18 casos aplicables, cero consultas fallidas | 12 documentales y 6 de políticas; cada caso tiene una evidencia de referencia positiva |
| Latencia de esa búsqueda | Mediana 0,099139 s; p95 por rango más cercano 49,879168 s | Ejecución secuencial; el estado inicial de carga del modelo no se controló |
| [Respuesta sobre garantía](probe-warranty.json) | Respondió con cita literal de `policy-warranty-s1`, sección «Condiciones» | Un ejemplo sintético revisado; recorrido 129,370555 s |
| [Respuesta filtrada sobre lámpara](probe-lamp.json) | Respondió «Potencia (power_w): 8 W.» con cita de `doc-ilu-001-s2`, sección «Características» | Un ejemplo sintético revisado; recorrido 80,618099 s |

La recuperación de ajuste se ejecutó sin pasarle productos, variantes o fragmentos
esperados de las referencias. Para cada caso se registra la consulta, el conjunto
de referencia, los fragmentos recuperados, Recall@5, error y tiempo. Los fallos de
consulta contarían como cero en los casos con referencias positivas. Un caso sin
referencias positivas es no aplicable, no 100 %. Los duplicados no aumentan el recall.

El ejecutor de medición solo abre `data/evaluation/adjustment/cases.json`; no ofrece
una opción para usar el conjunto reservado. Las pruebas de software usan fixtures
independientes y no se suman a los 120 escenarios del protocolo.

Las dos respuestas reales muestran funcionamiento y procedencia textual. No son
una medición completa de corrección, pertinencia, fidelidad semántica, contradicciones,
costos computacionales ni utilidad con personas. Los tiempos de 80–129 segundos
señalan un problema de rendimiento antes de la integración web; no satisfacen por
sí mismos la meta de p95 de 60 segundos del recorrido integrado.

## Verificación y pendientes

Las comprobaciones nuevas están en `tests/test_retrieval.py`, `tests/test_rag.py`,
`tests/test_rag_cli.py` y `tests/test_rag_evaluation.py`. Cubren filtros y herencia,
aislamiento de tiendas, revisiones retiradas, publicación concurrente, modelo o
vectores incompatibles, archivos ausentes, citas inventadas, JSON inválido, fallos
del proveedor, presupuesto de contexto, abstención comercial y cálculo de recall.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_retrieval.py tests/test_rag.py tests/test_rag_cli.py tests/test_rag_evaluation.py
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src
```

La primera ejecución de la batería base dentro del aislamiento falló por acceso a
la caché y temporales de pytest en Windows. Con ejecución normal autorizada pasó;
no se modificaron permisos ni se desactivaron comprobaciones. Se conservaron las
pruebas existentes de los otros trabajos, sin editar sus archivos.

Verificación final observada: **140 pruebas pasan en el proyecto compartido**,
incluidas 39 comprobaciones de estos cuatro archivos de fase 4. Ruff no informó
errores, su comprobación de formato pasó sobre 28 archivos y mypy no informó
errores en 18 módulos. Se comprobaron además las citas de ambas respuestas reales
contra el manifiesto y los enlaces locales de esta guía.

Para cerrar la fase 4 todavía hace falta:

1. Medir corrección y pertinencia de respuestas, citas, ambigüedad y contradicciones
   en una batería de ajuste suficiente, con revisión humana y denominadores explícitos.
2. Analizar y reducir la latencia con mediciones comparables de carga inicial y
   ejecución posterior, conservando la referencia actual.
3. Integrar el servicio en el recorrido HTTP/web cuando se coordine con sus responsables;
   la ruta de chat de la API de base no se cambió en este trabajo.
4. Fijar una versión reproducible de configuración, resultados y código antes de
   cualquier comparación final. No declarar validación con usuarios ni tienda real.
