# Informe de avance del proyecto Nexo Demo

Fecha de cierre de esta entrega: 10 de noviembre de 2026.

## 1 Objetivo del informe

Presentar el estado del prototipo académico, las actividades realizadas, sus
evidencias, las dificultades observadas y el trabajo que requiere intervención
del equipo o una evaluación posterior.

## 2 Avances del proyecto

Se consolidó el informe del Previo 3 con los once apartados de la guía y sus
referencias bibliográficas contrastadas. Se prepararon la presentación, el guion
de demostración y una matriz que relaciona los requisitos con su evidencia.

Se implementó el análisis reproducible del dataset: estadísticas descriptivas,
faltantes, estados comerciales, longitudes de textos y posibles atípicos IQR.
Las salidas incluyen tablas CSV, JSON y cinco gráficos PNG y SVG. El catálogo
conserva seis categorías, 60 productos, 90 variantes y 72 fuentes sintéticas.

Se implementó un ejecutor HTTP para registrar el recorrido integrado y se
corrigieron dos defectos del intérprete: preguntas sobre unidades restantes y
presupuestos expresados con conectores adicionales. Las recomendaciones
conservan presupuesto, disponibilidad y restricciones obligatorias.

## 3 Resultados obtenidos

Las comprobaciones del candidato corregido registraron 186 pruebas Python y
ocho pruebas del cliente web correctas. El análisis estático, formato, tipos y
construcción offline del paquete pasaron. Estas comprobaciones de software no
se presentan como evaluación de satisfacción de usuarios.

La medición con modelos reales cubrió los 60 casos de ajuste en dos tramos con
la misma huella de código, datos y parámetros. Los 60 se completaron sin errores
de ejecución. Se observaron 50 coincidencias entre el estado devuelto y el
esperado; ese indicador no equivale a exactitud semántica. Las 38 respuestas con
citas documentales valorables pasaron la comprobación de procedencia literal,
sin que esto pruebe la pertinencia de cada cita.

Los registros contienen 66 turnos HTTP. Su p95 fue aproximadamente 184 segundos,
superior a la meta de diseño de 60 segundos por turno. La mediana de las
consultas documentales fue aproximadamente 177 segundos, frente a 0,073 segundos
en consultas comerciales. La diferencia hace necesario ensayar la sustentación
y distinguir las operaciones por reglas de las que requieren inferencia.

Los resultados completos, sus límites y los ejemplos se encuentran en el informe
principal y en `docs/evaluation/integrated/complete-20261110/`. Las figuras y las
tablas del dataset están en `docs/analysis/2026-11-09/`. La interfaz dispone de
capturas de ejecuciones reales identificadas por su fecha.

## 4 Dificultades presentadas

La inferencia local es lenta en el equipo utilizado. Reducir la ventana a 2048
tokens no fue una solución aceptada: en el ensayo se omitió evidencia necesaria
y la respuesta no contestó el atributo solicitado. Se conservó la configuración
de 4096 tokens para la medición principal.

Una interrupción detuvo la corrida después de 36 casos. Sus observaciones se
preservaron; los 24 restantes se ejecutaron en otro directorio y se verificaron
las huellas y la cobertura antes de consolidar. No se declaró un ensayo continuo
ni un estado de carga controlado. También se documentaron discrepancias de
estado y respuestas genéricas ante un presupuesto que deja de ser suficiente.

## 5 Actividades pendientes

El equipo debe completar sus datos de identificación, distribuir las
intervenciones, ensayar y realizar la sustentación. La adaptación a una tienda
real, la instalación limpia en otro equipo, el estudio con participantes y la
evaluación del conjunto final reservado corresponden a trabajos posteriores;
no se presentan como realizados ni son requisitos adicionales inventados para
esta entrega contextualizada.

## 6 Conclusiones del avance

El proyecto dispone de código, datos de demostración, una aplicación integrada
y materiales académicos sustentados en observaciones registradas. La revisión
permitió corregir defectos verificables y explicar las diferencias entre
funcionamiento técnico, resolución de una consulta y utilidad con personas.
Las limitaciones de latencia y calidad semántica permanecen visibles en las
conclusiones del prototipo.
