# Historial de Cambios (changeLog) — comercial-kit

## [Sin publicar] - 2026-11-03 — Brandbook web y tokens (Navarino#303)

### 1. Intención
Llevar el brandbook Navarino a la web: tema Día por defecto (decisión D1), Nocturno opcional, logos oficiales y una biblioteca de componentes que solo consume `--nv-*`.

### 2. Cambios
- Logos oficiales en `static/comercial_kit/marca/` (7 archivos + `SHA256SUMS`); el antiguo `svg/navarino-logo-negativo.svg` pasa a `_archive/`. SVG de la wiki sin metadatos C2PA, verificados por render contra los PNG oficiales.
- `navarino-tokens.json` generado desde el CSS con `scripts/generar_tokens_json.py` (`--check` en los tests).
- `navarino-componentes.css`: botones, campos, tabla, tarjetas/KPI, estados, alertas, navegación, pestañas, vacío/cargando/error y gráficos.
- `comercial_kit/base.html` y el admin cargan tokens y componentes, sin `:root` duplicado, con favicon e interruptor de tema accesible; el admin deja de forzar oscuro y reemplaza el modo oscuro propio de Django.
- Alias `--nav-*` → `--nv-*` para no romper plantillas existentes de los servicios.
- Muestra estática `docs/muestra-brandbook.html` y capturas en `docs/capturas/`.

### 3. Estilo D5 «Patagonia viva» (decisión de Seba, 2026-11-03)
Motivo: el estilo anterior era «muy cuadrado, con colores poco atractivos». Logo sin cambios; D1 vigente (Día por defecto, Nocturno opcional, sin cobalto #1D5BD8).
- Fondo de página glaciar (`--nv-surface-sunken` #EEF5F6), tarjetas blancas sin borde duro con `--nv-shadow-card` (`0 2px 10px rgba(11,92,99,.10)`); filete `--nv-line` #D3E3E6.
- Radios nuevos: `--nv-radius-sm` 5 px, `--nv-radius-control` 10 px (botones y campos), `--nv-radius-card` 12 px (tarjetas, tablas, alertas, menús); insignias, chips y pestañas en píldora. `--nv-radius-0` y `--nv-radius-3` se conservan por compatibilidad, sin uso en los componentes.
- Acento separado: `--nv-accent-fill` #E65C00 con texto tinta `--nv-on-accent-fill` #0A1118 (5,3:1) para el botón principal; `--nv-accent-text` / `--nv-accent` #B84A00 para naranja como texto (5,2:1 sobre blanco; 4,7:1 sobre glaciar). `--nv-accent` mantiene su valor por compatibilidad con el admin.
- Botón secundario blanco con texto `--nv-glaciar-ink` #0B5C63 y borde `--nv-glaciar-line` #BFDDE0 (decorativo: el texto identifica el control).
- Colores de apoyo: glaciar #0E7C86 / #0B5C63 / #DDF0F1 y lenga #5B8C3A / #3E6624 / #E6F0DC; equivalentes Nocturno #4FB3BC y #9CC26A. Insignias de estado en píldora con fondo teñido, más `--glaciar`, `--lenga` e `--info`.
- Paleta de datos Día ajustada por claridad (ΔL* ≥ 5 entre todas las series y ≥ 3:1 contra tarjeta y fondo): data-2 #0E7C86→#0E7882, data-3 #5B8C3A→#588738, data-4 #3F7CAC→#326289, data-5 #8C6A3C→#624A2A (tenía la misma claridad que glaciar). Nocturno: #55B6BE, #A0C570, #679CC7, #DDCAAE. Nunca #7FB2E0 en Día.
- `--nv-line-strong` Día #4D5B68→#647A80 (4,5:1 sobre blanco y 4,1:1 sobre glaciar; sigue ≥ 3).
- Contraste WCAG AA recalculado: 98/98 pares OK (49 por tema + separación por claridad).
- Componentes, muestra y capturas (`brandbook-{dia,nocturno,movil}.png`) actualizados; móvil 375 px sin scroll horizontal.

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
