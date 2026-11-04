# Definición de la fase 1 para Nexo Demo

Fecha: 4 de noviembre de 2026. Estado: definición documental preparada; caracterización con participantes y revisión académica pendientes.

El proyecto utilizará una tienda ficticia llamada Nexo Demo. La elección responde a la autorización del usuario para decidir el entorno de demostración y a su requisito de poder incorporar una tienda real en el futuro. Este documento fija el alcance funcional, el inventario previsto, los requisitos de sustitución de fuentes y las condiciones de evaluación. No constituye un catálogo generado, una integración implementada ni un diagnóstico observado en una empresa.

## Decisiones adoptadas

| Aspecto | Decisión |
| --- | --- |
| Tienda | Nexo Demo, negocio ficticio de productos para el hogar y el espacio de trabajo |
| Identificador | `nexo-demo`, independiente del nombre visible |
| Idioma y moneda | Español de Colombia y COP; los importes del catálogo serán simulados |
| Cobertura final | Seis categorías, 60 productos base y 90 variantes comercializables |
| Primer lote de incorporación | 12 productos y 18 variantes, distribuidos entre las seis categorías |
| Usuarios previstos | Personas adultas que consultan características, comparan alternativas o buscan productos según necesidad y presupuesto |
| Fuentes | Fichas, guías, políticas y registros comerciales creados expresamente para la demostración |
| Canal | Prototipo web; ejecución local como entrega inicial |
| Venta | Consulta y orientación; sin ejecutar compras, pagos, devoluciones ni seguimiento individual de pedidos |
| Recursos externos | Sin contratación ni gasto en servicios de pago por defecto; la fase 2 comprobará la viabilidad con los recursos disponibles |
| Identificación de la simulación | Aviso visible de tienda ficticia, productos de prueba y precios y existencias simulados |

La cifra de productos expresa una meta de construcción para la fase 3. Hoy no hay 60 productos cargados ni una base de conocimiento de productos disponible. Los perfiles y problemas descritos aquí son hipótesis de diseño; no provienen de entrevistas.

## Catálogo e inventario previstos

| Categoría | Productos base | Variantes finales | Productos y variantes del primer lote | Atributos específicos de ejemplo |
| --- | --- | --- | --- | --- |
| Periféricos | 10 | 15 | 2 y 3 | Conexión, distribución de teclado, dimensiones y compatibilidad documentada |
| Conectividad | 10 | 15 | 2 y 3 | Conectores, protocolo, puertos y límites de uso documentados |
| Iluminación | 10 | 15 | 2 y 3 | Alimentación, potencia, temperatura de color y dimensiones |
| Organización | 10 | 15 | 2 y 3 | Material, capacidad, medidas y forma de instalación |
| Mobiliario | 10 | 15 | 2 y 3 | Medidas, material, ajuste y carga máxima documentada |
| Accesorios cotidianos | 10 | 15 | 2 y 3 | Capacidad, medidas, material y cuidados |
| Total | 60 | 90 | 12 y 18 | Atributos comunes más atributos de cada categoría |

Cada categoría tendrá cinco productos con dos variantes y cinco con una variante. El primer lote tomará un producto de cada tipo por categoría. La variante será la unidad de precio y existencias; un producto con una sola variante también tendrá identificador de variante.

Se usarán nombres y marcas de prueba, sin copiar catálogos comerciales. El rango de diseño del catálogo será de 15 000 a 1 800 000 COP. Se incluirán de manera intencional artículos agotados, variantes con precios distintos, nombres similares y atributos desconocidos para comprobar el manejo de esos casos. Son condiciones de prueba, no características inferidas de una tienda real.

### Inventario de fuentes que se construirá en la fase 3

| Fuente | Cantidad prevista | Contenido y autoridad |
| --- | --- | --- |
| Catálogo estructurado | 60 productos y 90 variantes | Identificadores, categorías, atributos y relaciones |
| Registros comerciales | 90 registros por instantánea | Precio, moneda, existencias, fecha y versión de la fuente por variante |
| Fichas de producto | 60 | Descripción, atributos, diferencias de variantes, cuidados y respaldo de compatibilidades |
| Guías de categoría | 6 | Criterios de comparación, vocabulario y preguntas frecuentes |
| Políticas de demostración | 6 | Condiciones generales ficticias de precios, disponibilidad, entrega, cambios, garantía y ayuda |

Las 72 fuentes documentales previstas son 60 fichas, seis guías y seis políticas. El catálogo y los registros comerciales se contabilizan por separado. Cada afirmación de referencia deberá apuntar al identificador y versión de una fuente o al registro comercial correspondiente.

### Políticas ficticias iniciales

- Los importes estarán expresados en COP como precio final simulado. No se aplicarán descuentos que no estén registrados.
- Una existencia igual a cero significa agotado. Una existencia desconocida no significa que haya unidades. Consultar no reserva inventario.
- La entrega simulada tendrá un plazo orientativo de tres a cinco días hábiles dentro de la zona ficticia de cobertura. El costo simulado será de 15 000 COP y será cero para pedidos desde 300 000 COP. No se recogerán direcciones ni se ejecutarán pedidos.
- El escenario de cambios contemplará solicitudes dentro de los 15 días siguientes a la entrega ficticia, con producto sin uso y comprobante simulado. El asistente solo explicará la política.
- La garantía ficticia cubrirá defectos de fabricación durante 12 meses y excluirá daños por uso indebido. Cualquier particularidad deberá aparecer en la ficha correspondiente.
- La derivación será una indicación de acudir al canal de ayuda de demostración. No se enviarán mensajes ni se presumirá una conexión con personal real.

Estas condiciones son material de prueba inventado; no describen derechos legales ni políticas de una empresa real. Al incorporar una tienda se reemplazarán por sus documentos autorizados.

## Datos mínimos y procedencia

Los nombres de campo siguientes son un vocabulario conceptual para la arquitectura, no un esquema de base de datos ya implementado:

- Perfil: `store_id`, nombre visible, idioma, moneda, modo de datos y referencias de políticas.
- Producto: `product_id`, `store_id`, nombre, categoría, atributos y estado de incorporación.
- Variante: `variant_id`, `product_id`, atributos que la distinguen y código comercial cuando exista.
- Registro comercial: `variant_id`, precio o valor desconocido, moneda, existencias o valor desconocido, `source_updated_at`, versión e identificador de fuente.
- Documento: `source_id`, `store_id`, título, versión, ubicación, ámbito y relaciones con productos o categorías cuando correspondan.
- Evidencia: identificador de fragmento, fuente y ubicación original; el fragmento no puede perder el vínculo con producto o variante.

La fecha de lectura no reemplazará la fecha de actualización de la fuente. En demostración se consultarán instantáneas identificadas y se mostrará su naturaleza simulada. Las pruebas controlarán el tiempo de referencia. Para datos reales, la política inicial de diseño considerará vigente un registro comercial con antigüedad máxima de 15 minutos, configurable según la fuente que se integre; un registro vencido no se presentará como confirmado.

No se convertirá una medida desconocida en cero, una ausencia de precio en producto gratuito ni una compatibilidad no documentada en compatibilidad válida. Las unidades y la moneda se conservarán explícitas.

## Requisitos funcionales

Los comportamientos se comprobarán durante las fases de código y se evaluarán con el protocolo enlazado al final. El usuario indicó posteriormente trabajar sin TDD, por ser un prototipo de clase. Esta matriz especifica criterios de aceptación; la evidencia efectivamente ejecutada se conserva por separado en la documentación de cada fase.

| ID | Requisito | Comprobación de aceptación prevista |
| --- | --- | --- |
| RF01 | Consultar características de productos y variantes | La respuesta identifica el artículo correcto y sus atributos coinciden con la ficha |
| RF02 | Buscar alternativas por necesidad y categoría | Solo devuelve candidatos pertinentes presentes en el catálogo |
| RF03 | Aplicar presupuesto y requisitos obligatorios | No recomienda como apto un candidato que incumpla una restricción obligatoria |
| RF04 | Comparar productos con criterios de su categoría | Compara atributos pertinentes y señala valores desconocidos |
| RF05 | Consultar precios y existencias estructurados | Los valores corresponden a la variante, fuente y fecha consultadas |
| RF06 | Mostrar fuentes verificables | Las citas permiten localizar el respaldo y corresponden a la afirmación |
| RF07 | Aclarar ambigüedades | Pide identificar producto, variante o requisito antes de dar una confirmación ambigua |
| RF08 | Conservar y actualizar el contexto de la sesión | Interpreta referencias y aplica un cambio de presupuesto sin conservar restricciones sustituidas |
| RF09 | Responder políticas generales | Explica la política de la tienda activa sin afirmar que ejecuta una operación |
| RF10 | Manejar ausencia y contradicción de información | Aclara, se abstiene o deriva según la evidencia, sin completar atributos por suposición |
| RF11 | Manejar agotados y falta de alternativas | No presenta un agotado como disponible y explica cuándo no hay opciones que cumplan |
| RF12 | Actualizar y retirar fuentes | Una nueva versión sustituye a la anterior; una fuente retirada deja de sustentar respuestas |
| RF13 | Identificar el modo de demostración | El usuario puede reconocer que el negocio y las condiciones comerciales son ficticios |
| RF14 | Iniciar una conversación nueva | El contexto anterior no influye en la sesión nueva ni en otro usuario |

## Requisitos para incorporar una tienda real

La migración deberá requerir configuración, preparación de fuentes y, cuando cambie el origen de los datos, un adaptador. No se promete que cualquier tienda pueda conectarse sin trabajo de integración. El objetivo verificable es conservar la lógica de consulta, conversación y presentación.

| ID | Requisito de sustitución | Evidencia que se exigirá en fases 2 a 6 |
| --- | --- | --- |
| RP01 | Separar el perfil de tienda de la lógica del asistente | Cambiar nombre, moneda, políticas y fuentes sin editar el flujo de conversación |
| RP02 | Acceder al catálogo y a los datos comerciales mediante contratos | Un proveedor de demostración y otro proveedor de prueba pasan las mismas pruebas de contrato |
| RP03 | Mantener la ingesta documental independiente del origen | Importar fuentes distintas conservando identificadores, versión y citas |
| RP04 | Declarar categorías y atributos en datos o configuración | Añadir una categoría y sus atributos sin una rama de código específica para Nexo Demo |
| RP05 | Evitar información comercial incrustada en instrucciones o interfaz | La búsqueda de reglas del negocio muestra que precios, stock y políticas proceden de fuentes |
| RP06 | Aislar los datos de la tienda activa | Cambiar de tienda no recupera documentos, productos ni sesiones del catálogo anterior |
| RP07 | Separar configuración y credenciales | Configuración de ejemplo sin secretos; las credenciales de una futura integración no llegan al cliente ni a los registros |
| RP08 | Probar una sustitución completa antes de declarar portabilidad | Una segunda tienda ficticia usa otro origen de datos y otra categoría sin modificar el núcleo del asistente |

La segunda tienda será un conjunto pequeño de pruebas de contrato y migración, no una ampliación del producto a un servicio para múltiples tiendas simultáneas. La arquitectura de la fase 2 deberá ubicar claramente los límites de catálogo, datos comerciales, fuentes documentales y modelo generativo. La independencia del modelo evita mezclar la identidad de la tienda con un proveedor de generación.

La prueba RP08 deberá incluir identificadores que coincidan entre ambas tiendas para detectar contaminación, una categoría nueva con atributos propios, un cambio de moneda configurado y una política diferente. Se conservará la misma batería de comportamientos aplicables. Las reindexaciones necesarias se documentarán; no se mantendrán índices antiguos disponibles para la nueva tienda.

## Calidad y condiciones de trabajo

- Corrección, respaldo, vigencia y abstención se medirán por separado. Los umbrales elegidos son metas del proyecto, no resultados observados.
- Las fuentes recuperadas no podrán introducir instrucciones que alteren las reglas del asistente ni solicitar secretos.
- Los registros de evaluación usarán códigos de caso y participante. No se requieren nombres, direcciones ni contactos para consultar el catálogo ficticio.
- La interfaz se revisará en escritorio, móvil y navegación por teclado. El idioma visible será español; los identificadores técnicos serán consistentes.
- El desarrollo se realizará por entregables. La fecha académica, la disponibilidad del equipo, sus integrantes y el hardware real siguen sin estar confirmados y no se inventan.
- No se contratarán servicios, publicarán datos ni habilitarán integraciones remotas como consecuencia de esta definición. La fase 2 deberá registrar las limitaciones del equipo disponible antes de escoger modelos.

## Escenarios y caracterización

Los escenarios iniciales cubrirán consulta directa, búsqueda de un regalo, presupuesto sin alternativas, comparación, agotados, cambio de requisitos, políticas y atributos desconocidos. También se incluirán fuentes comerciales antiguas, variantes similares y documentos que intenten dar instrucciones al asistente.

Las hipótesis son que algunas consultas requieren reunir fuentes, distinguir variantes o traducir una necesidad en criterios. No se afirma su frecuencia ni su gravedad en clientes reales. El instrumento preparado permitirá comprobar estas hipótesis con participantes cuando se disponga de ellos. No se representará a un comerciante inexistente ni se inventarán entrevistas al personal.

## Entregables y estado de la fase

| Entregable | Estado comprobable |
| --- | --- |
| Selección de tienda, alcance e inventario previsto | Definido en este documento |
| Requisitos funcionales y de migración | Definidos; pendientes de implementación y pruebas |
| Protocolo, cuotas, metas e instrumentos | Preparados en el documento de evaluación |
| Catálogo, fichas, políticas e instantáneas | Especificados; se construirán en la fase 3 |
| Caracterización con participantes | Instrumento preparado; aplicación pendiente |
| Primer informe académico y contraste de bibliografía | Pendientes de actualización y revisión específica |
| Calendario, equipo y hardware | Pendientes de confirmación; no bloquean la definición de la tienda |

La definición del entorno de demostración permite diseñar la arquitectura en la fase 2. La fase 1 permanece IN PROGRESS porque todavía no se han aplicado los instrumentos ni cerrado la revisión académica prevista en el plan general. No se equipara la documentación de requisitos con una validación empírica.

El informe de avance se preparará y entregará al finalizar todo el proyecto, en la fase 8, según la aclaración del usuario. Durante esta fase solo se conservan notas internas y evidencias de trabajo.

Documentos relacionados: [plan general](001-plan-del-proyecto.md), [protocolo e instrumentos](phase-1/evaluation-protocol.md) y [notas internas](phase-1/working-notes.md).
