# Historial de Cambios (changeLog) — comercial-kit

## [1.0.0] - 2026-11-03

### 1. Intención
Implementar la versión inicial `v1.0.0` de `comercial-kit` que establece el estándar común K1–K7 para los servicios comerciales de Navarino (Precios y Promociones), cumpliendo con la épica #279.

### 2. Estado Actual
Paquete Django reusable implementado, probado y validado con 36 pruebas automatizadas en verde y cobertura del 94% sobre todo el código.

### 3. Estado Deseado
Disponer del tag `v1.0.0` instalable desde git por el servicio Precios (`PK2 / G1`) y Promociones (`PK1`), permitiendo arrancar servicios con solo 4 variables de entorno.

### 4. Problemas Encontrados y Soluciones
- Contención en content-negotiation de DRF para errores RFC 9457: resuelta con `ProblemJsonRenderer` desacoplado y configuración correcta de `EXCEPTION_HANDLER`.
- Template override de Django Admin: resuelto priorizando `comercial_kit` antes de `django.contrib.admin` en `INSTALLED_APPS`.
- Aislamiento no bloqueante de avisos críticos: implementado en `Aviso.save()` con captura de excepciones para garantizar que ningún fallo de red en el hub bloquee operaciones.

### 5. Iteraciones Realizadas
- Creación de estructura inicial de repo con `repo-orden`.
- Módulos K1 a K7 desarrollados con tipado y documentación.
- Suite de pruebas completa (`tests/test_k*.py`, `test_op_connect.py`, `test_admin.py`, `test_example_project.py`).
- Verificación con `coverage run -m pytest`.

### 6. Evidencia de Verificación
- 36 tests unitarios pasando al 100%.
- Cobertura global de 94%.
- `kit_check_env` validado con entorno de 4 variables.
