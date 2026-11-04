# Comprobaciones locales

El ejecutor es pytest. La batería de fase 2 tiene 44 casos:

- `test_local_contracts.py`: 22 casos de catálogo y consulta comercial mediante archivos locales.
- `test_foundation.py`: 22 casos de configuración, fuentes, citas, proveedor simulado y API de base.

Se trabaja sin TDD por indicación expresa del usuario. Las comprobaciones se escribieron después
de implementar; no se afirma evidencia RED/GREEN. Las pruebas no descargan pesos ni llaman a modelos.

Las inferencias reales y el HTTP desde el paquete instalado se verificaron por separado y tienen
[evidencia técnica](../docs/architecture/local-environment.md). Los casos y datos sintéticos de
software no sustituyen los escenarios de ajuste y evaluación final ni la prueba con participantes.
