# Plan 003: avanzar las fases 4 a 8 sin interferir con las fases 2 y 3

Fecha: 4 de noviembre de 2026. Estado: **fase 4 en implementación; fases 5 a 8 previstas**.
Prioridad: P1 para fase 4, P2 para preparación de fases 5 a 8. Esfuerzo total: L.
Riesgo principal: integrar contra contratos o fuentes que todavía están cambiando.

La [base ejecutable de fase 4](../docs/evaluation/phase4/README.md) ya cuenta con
recuperación local, respuestas extractivas con citas y mediciones de ajuste.
Esa guía contiene el estado y los límites actuales; el resto de este archivo
conserva el plan y la instantánea anteriores a la implementación.

Este archivo concreta qué puede prepararse en paralelo y qué requiere una entrega
estable. No declara fases completadas ni contiene resultados de evaluación. No es
el informe de avance: ese informe se elabora al finalizar el proyecto, en fase 8.

## Contexto y límites

El proyecto es un asistente académico local en español para Nexo Demo. La meta de
catálogo es seis categorías, 60 productos y 90 variantes, con datos ficticios en COP.
El núcleo debe permitir cambiar de tienda mediante configuración y adaptadores.
No se incluyen pagos, compras ni seguimiento individual de pedidos.

Los chats de fase 2 y fase 3 comparten esta carpeta y estaban activos durante la
revisión. Fase 2 prepara contratos, API y modelos locales. Fase 3 prepara catálogo,
fuentes y referencias. Sus archivos no deben editarse concurrentemente.

No existe repositorio Git en esta carpeta: `git rev-parse --short HEAD` falló por
esa razón. No hay commit ni diff de referencia. Antes de implementar se deben
volver a leer los contratos y registrar una instantánea de los archivos afectados.
No se autoriza aquí inicializar Git, hacer commits, publicar ni desplegar.

## Estado observado y comprobación de cambios

| Archivo | Estado observado | SHA256 de la lectura |
| --- | --- | --- |
| `src/ragml/ports.py` | Puertos de catálogo, fuentes, recuperación, generación, embeddings y sesiones | `24f2deba18075c15647815a44b9abfb1117783a212ab0065597a89f594837754` |
| `src/ragml/conversation.py` | Contratos de respuesta, citas y estado de sesión; validación de enlaces de evidencia | `ed694d805f156dfb8ae5c02330138856d0650e6d58d53ec5ff627e821e01ac99` |
| `src/ragml/evidence.py` | Manifiesto versionado, ámbitos, ubicaciones y hashes | `c3cbe82b4739ae90076db456b4cd1bef66cd5ac40470617596dffb81b2218976` |
| `plans/phase-1/evaluation-protocol.md` | Cuotas, métricas, instrumentos y separación de ajuste/evaluación | `0aae64a97ee9526f8e087e45e582916c22ae814c777ba93cbf0c9f566949d243` |

Comprobar con `Get-FileHash` antes de ejecutar. Si hay diferencias, comparar el
contenido nuevo; estos hashes no congelan el trabajo de los otros chats.

En `ports.py`, `RetrievalQuery` exige tienda, revisión y texto; admite k entre 1 y
10, filtros y políticas generales. `RetrievalPort.search` devuelve fragmentos con
puntuación entre -1 y 1. No sustituir esos contratos por un formato propio.

En `conversation.py`, `ChatResponse` distingue `answered`, `clarification_required`,
`insufficient_evidence` y `temporarily_unavailable`. `validate_evidence` comprueba
identidad, versión, ubicación, extracto y observaciones comerciales vigentes. Esta
validación estructural no demuestra por sí sola fidelidad semántica.

La ruta `POST /v1/chat` de `api.py` devolvía 503 con `rag_not_ready`. Había archivos
de catálogo, comercio y fuentes apareciendo en `data/sample/`; no se verificó aquí
su integridad ni se considera terminada la fase 3 por su mera existencia.

## Qué puede avanzar y qué debe esperar

| Fase | Preparación independiente | Condición para integrar o cerrar |
| --- | --- | --- |
| 4. RAG básico | Casos sintéticos pequeños; filtros; resolución de citas; diseño del registro de recuperación | Contratos estables de fase 2, corpus validado de fase 3 y modelos comprobados para inferencia real |
| 5. Asesoría | Reglas de presupuesto, requisitos, comparación, ambigüedad y cambios de contexto | Recuperación básica funcional y catálogo/comercio estables |
| 6. Web | Especificación de pantallas y estados; prototipo visual con respuestas de prueba identificadas | Contrato HTTP estable y servicio conversacional para recorrido real |
| 7. Evaluación | Registro de ejecuciones, cálculo de métricas y rúbricas con ejemplos artificiales | Candidato congelado, referencias verificadas y conjunto reservado; participantes para utilidad |
| 8. Entrega | Inventario de manuales y evidencias; estructura de actualización y reproducción | Comandos y procedimientos ejecutados; resultados de fase 7 para informes y conclusiones |

Orden recomendado: preparar 4 y el registro de 7; integrar 4; desarrollar 5;
integrar 6; ejecutar 7; consolidar 8. El diseño web puede avanzar en paralelo.
No abrir ni redactar las respuestas del conjunto final para ajustar el sistema.

## Alcance de la siguiente implementación

Rutas propuestas, sujetas a comprobar que ningún otro chat las haya creado:

- `src/ragml/retrieval.py`, `src/ragml/rag.py` y pruebas homónimas: fase 4.
- `src/ragml/advice.py` y `tests/test_advice.py`: reglas independientes de fase 5.
- `src/ragml/evaluation.py` y `tests/test_evaluation.py`: cálculo de métricas.
- `docs/evaluation/`: registros de ajuste y, después, resultados finales separados.

Mantener las convenciones de Python tipado, contratos existentes y errores sin
datos sensibles de `commercial.py` y `providers.py`. Usar `tests/test_local_contracts.py`
como ejemplo de archivos temporales y reloj controlado. Los identificadores de
tienda, categorías y atributos vienen de los datos; no fijar nombres de Nexo Demo
en el núcleo. Las pruebas de software no forman parte de los 120 casos de calidad.

Fuera del alcance de este plan durante la ejecución paralela: editar `ports.py`,
`contracts.py`, `conversation.py`, `evidence.py`, `providers.py`, `settings.py`,
`api.py`, `cli.py`, dependencias, configuración de modelos o `data/sample/`.
La integración en esos archivos se hará cuando el trabajo de su fase esté estable.
Tampoco actualizar `plans/README.md` simultáneamente con el chat de planificación;
incorporar allí este plan cuando termine su edición en curso.

## Pasos y comprobaciones

### 1. Preparar la recuperación aislada de fase 4

Crear una batería pequeña de software con dos tiendas que reutilicen identificadores,
fuentes de producto/variante/categoría y una política general. Incluir revisiones
distintas y fuentes retiradas. Son fixtures artificiales, no casos reservados.
Implementar tras comprobar las interfaces estables y la política de pruebas vigente.

La búsqueda debe filtrar tienda, revisión y ámbitos antes de seleccionar los k
resultados. Una política general no se asocia ficticiamente a un producto. Registrar
modelo, dimensiones y versión del índice; rechazar incompatibilidades. Ordenar
empates de forma reproducible. La puntuación de similitud no equivale a probabilidad
de verdad. No transformar puntuaciones de otro recuperador arbitrariamente para
hacerlas caber en el contrato; acordar su significado antes de cambiar el método.

**Verificación prevista:** `python -m pytest tests/test_retrieval.py`, usando el
Python de `.venv`; todos los casos pasan, incluyendo ausencia de resultados,
filtros combinados, política general, revisión obsoleta y aislamiento de tiendas.
La recuperación semántica real se ejecutará después con el proveedor local de fase 2.

### 2. Preparar respuesta con fuentes y manejo de incertidumbre

Conectar `rag.py` a `RetrievalPort` y `GenerationPort` por inyección. La salida debe
resolver citas contra el manifiesto exacto. Rechazar citas inventadas, extractos
inexistentes y fuentes ajenas. Si no hay evidencia o el proveedor falla, devolver
el estado explícito correspondiente. Precios documentales antiguos no confirman
precio o existencias actuales. Las fuentes se tratan como datos, incluso cuando
contengan instrucciones. Revisar manualmente la fidelidad de las respuestas reales.

**Verificación prevista:** `python -m pytest tests/test_rag.py`; incluir evidencia
positiva, ausencia, contradicción, variante ambigua, cita inválida, instrucciones
maliciosas y proveedor no disponible. Los dobles de prueba verifican el flujo;
no permiten declarar calidad generativa ni resistencia general a ataques.

### 3. Preparar reglas de asesoría de fase 5

Operar inicialmente sobre candidatos y datos comerciales suministrados, sin
duplicar el adaptador existente. Aplicar importe decimal y moneda; aceptar un precio
igual al presupuesto. Excluir de recomendaciones aptas lo agotado, lo que supera
presupuesto o lo que incumple un requisito obligatorio. Un atributo obligatorio
desconocido no cuenta como cumplido. No convertir una preferencia en obligación.

Comparar atributos homogéneos con unidades y procedencia. Si no existen alternativas,
explicarlo sin relajar requisitos silenciosamente. Resolver «el segundo» solo contra
las variantes presentadas en esa sesión; ante ambigüedad, aclarar. Al cambiar de
categoría, conservar solo las restricciones aplicables y preguntar por las dudosas.

**Verificación prevista:** `python -m pytest tests/test_advice.py`; incluir límite
exacto del presupuesto, moneda distinta, precio desconocido o vencido, agotado,
atributo ausente, ausencia de alternativas, cambio de requisitos y sesiones aisladas.

### 4. Preparar el registro y las métricas de fase 7

Registrar por ejecución: identificador, partición, familia del caso, versiones y
hashes de fuentes/modelos, k, parámetros, reloj, fragmentos recuperados, respuesta,
citas, estado, tiempos por etapa, consumo disponible y revisión humana. Los prompts
y conversaciones de participantes no se registran por defecto.

Probar Recall@5 con ejemplos calculados a mano: dos evidencias de referencia y una
recuperada producen 0,5; duplicar un fragmento no aumenta el numerador; un caso sin
referencias positivas es no aplicable. Un denominador vacío no es 100 %. Separar
errores de ejecución de ausencia de evidencia y reportar cobertura. El cálculo de
respaldo y fidelidad necesita etiquetas humanas verificadas; enlazar una cita no
basta para marcar una afirmación como correcta.

Conservar las cuotas existentes: 60 escenarios de ajuste y 60 finales, separados
por familias. Los prepara fase 3 contra fuentes concretas. No producir otro conjunto
que compita con aquel. Comparar capacidades documentales comunes y consulta comercial
por separado; la abstención correcta del RAG básico no se etiqueta como alucinación.

**Verificación prevista:** `python -m pytest tests/test_evaluation.py`; casos manuales
de métricas, duplicados, denominadores vacíos y errores. Ejecutar primero solo ajuste.
Antes de evaluar el conjunto final, fijar candidato y presupuesto de latencia.
No declarar utilidad sin participantes; el protocolo ya contiene los instrumentos.

### 5. Preparar interfaz y documentación sin anticipar resultados

Fase 6: especificar conversación, nueva sesión, fuentes con ubicación, comparación,
indicador de datos ficticios y estados de espera, aclaración, insuficiencia y fallo.
Prever escritorio, móvil, teclado y conservación del texto ante errores. La futura
implementación consultará documentación vigente y usará el contrato HTTP estable.
Una maqueta no cuenta como integración ni revisión visual del producto real.

Fase 8: mantener un inventario de evidencias para instalación, configuración,
operación local, cambio de tienda, actualización de precios, reingesta/retirada,
fallos conocidos y reproducción de evaluación. Completar cada procedimiento después
de ejecutarlo. No escribir conclusiones, manuales definitivos ni informe de avance
con comandos o resultados supuestos.

**Verificación prevista:** revisión documental de enlaces, correspondencia con
contratos y estados cubiertos. Después de implementar: navegador real y recorridos
completos; después de documentar instalación: reproducción observada. No inventar
un comando de frontend cuando todavía no existe ese proyecto.

## Comandos del proyecto y criterio de cierre

En PowerShell desde la raíz, usar `.\.venv\Scripts\python.exe` en lugar de `python`
en los comandos anteriores. Los comandos de comprobación configurados son:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src
```

Son puertas de verificación para la implementación futura; no se ejecutaron en esta
revisión documental. Los comandos por archivo solo serán aplicables tras crearlo.
No instalar ni ejecutar nuevos modelos mientras fase 2 está usando el equipo.

Para cerrar fase 4: casos de software pasando, recuperación y generación locales
observadas, citas revisadas, métricas de ajuste reproducibles y fallos documentados.
Para cerrar 5 y 6: reglas y recorrido web integrado verificados. Para cerrar 7 y 8:
resultados trazables, limitaciones explícitas y procedimientos reproducidos. Ninguna
fase se marca terminada por haber completado esta planificación.

## Condiciones para detener la parte afectada

- Otro chat está editando el mismo archivo o cambió un contrato necesario: volver
  a leer y coordinar la integración antes de tocarlo.
- Falta el ejecutor de pruebas o no funciona: informar; no inventar evidencia.
- Faltan fuentes estables: continuar con fixtures de software, sin medir calidad real.
- Hacen falta cambios fuera de alcance, servicios remotos, pagos o transferencias:
  explicar la dependencia y obtener la autorización que corresponda.
- Se requiere consultar el conjunto final para ajustar: mantenerlo reservado y
  continuar con ajuste; si ya se abrió, declarar la limitación.

El mayor riesgo de mantenimiento es mezclar versiones de catálogo, fuentes, índice
y modelos. Toda actualización debe invalidar lo incompatible, conservar trazabilidad
y retirar contenido obsoleto. El procedimiento se comprobará con una segunda tienda
ficticia antes de atribuir al prototipo facilidad de sustitución demostrada.
