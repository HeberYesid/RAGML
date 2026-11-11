# Entrega del proyecto Nexo Demo

La entrega corresponde al Previo 3 de Machine Learning. El catálogo y las
condiciones comerciales son sintéticos. El informe distingue modelos
preentrenados, reglas, pruebas de software y mediciones de la aplicación.

## Archivos de la entrega

- `Informe_Proyecto_RAGML.docx`: informe editable.
- `Informe_Proyecto_RAGML.pdf`: versión para lectura y entrega.
- `Sustentacion_RAGML.pptx`: presentación con notas para exponer.
- `Guion_Sustentacion.md`: tiempos, demostración y preguntas previsibles.
- `Informe_Avance.md`: avance consolidado según la guía previa.
- `Codigo_RAGML.zip`: código, configuración de ejemplo, pruebas y datos públicos
  de demostración; no incluye modelos, entorno Python, configuración privada ni
  el archivo de evaluación final reservado.

El documento original de fundamentos se conserva en la raíz del proyecto. Las
fuentes editables del informe, la bibliografía y la matriz de requisitos se
encuentran en `docs/reports/`. Los resultados y gráficos del análisis están en
`docs/analysis/2026-11-09/`.

## Demostración desde este proyecto

En PowerShell, desde la raíz de RAGML:

```powershell
.\scripts\start-models.ps1 -Background
.\.venv\Scripts\ragml.exe doctor
.\.venv\Scripts\python.exe -m ragml.ingestion
.\.venv\Scripts\python.exe -m ragml.web
```

Abrir `http://127.0.0.1:8000` y comprobar el aviso de datos ficticios y reloj
simulado. Consultar `/ready` para conocer el estado del asistente. Mantener la
terminal del servidor abierta durante la demostración.

Para repetir el análisis, usar un directorio nuevo:

```powershell
uv sync --locked --extra analysis --cache-dir .cache/uv
.\.venv\Scripts\python.exe -m ragml.analysis --output-dir docs/analysis/otra-ejecucion
```

Los modelos se descargan durante la preparación inicial siguiendo la guía de
`docs/architecture/local-models.md`; no están incorporados al archivo de código.
Este equipo ya dispone de ellos. No se declara probada una instalación limpia
en otro computador.

## Antes de sustentar

Completar los datos de los integrantes según el formato exigido por el docente.
Distribuir las intervenciones, ensayar las consultas del guion y mantener visible
qué resultados corresponden a ejecuciones previas. Los tiempos documentales
pueden ser largos; las capturas previas deben identificarse como evidencia
registrada y no como demostración en vivo.

La sustentación del grupo y cualquier estudio con participantes son actividades
humanas distintas de preparar y verificar estos materiales. No se presentan como
ya realizadas.
