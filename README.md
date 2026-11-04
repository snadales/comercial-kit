# comercial-kit

Estándar común K1–K7 para servicios comerciales Navarino (Precios y Promociones).
Paquete Django reusable, instalable por pip desde tag de git (`v1.0.0`).

## Estructura
| Carpeta | Qué contiene |
|---|---|
| `src/comercial_kit/` | Módulos centrales: tema Navarino, DRF RFC 9457, tokens consumidor, middleware OTel, logging JSON, K5 salud/diagnóstico, K6 Parametro y Connect, K7 Avisos |
| `tests/` | Suite completa de pruebas unitarias y de integración (cobertura ≥ 94%) |
| `docs/` | Documentación técnica complementaria del kit |
| `scripts/` | Utilidades locales de verificación y empaquetado |
| `_archive/` | Histórico archivado |

## Estándar K1–K7
- **K1 Tema Navarino Nocturno:** Tokens de color (`beagle`, `basalto`, `acero`, `niebla`, `senal`), proporciones 60/30/10, logo SVG desde `/marca-navarino/`, sin sombras ni degradados.
- **K2 API & DRF:** Prefijo `/v1`, OpenAPI con drf-spectacular en `/v1/docs`, errores RFC 9457 `application/problem+json` con `trace_id`, tokens por consumidor con hash SHA-256.
- **K3 Trazabilidad:** OpenTelemetry con propagación W3C `traceparent` de entrada y salida, e integración con `django-simple-history`.
- **K4 Logging:** JSON estructurado a stdout (un evento por línea) con `trace_id`, `span_id` y `ts` ISO 8601.
- **K5 Diagnóstico:** `/v1/salud` (DB y latencias), `/v1/diagnostico` (versiones y parámetros), contrato `/v1/simular`.
- **K6 Entorno Mínimo:** Lista cerrada de exactamente 4 variables (`DATABASE_URL`, `DJANGO_SECRET_KEY`, `OP_CONNECT_TOKEN`, `PUBLIC_HOST`). Todo lo demás en `Parametro` con resolución `op://` en memoria. Comando `kit_check_env`.
- **K7 Avisos:** Modelo `Aviso` (`info`, `aviso`, `critico`), despacho no bloqueante de críticos al hub central (AgoraOS#1245). Solo avisos, nunca bloqueos.

## Variables de entorno
Solo 4 variables obligatorias:
- `DATABASE_URL`
- `DJANGO_SECRET_KEY`
- `OP_CONNECT_TOKEN`
- `PUBLIC_HOST`

- **K8 Arranque sin .env:** `comercial_kit.arranque.cargar_secretos({"DATABASE_URL": "op://IA/<item>/<campo>", ...})` lee el Docker secret `/run/secrets/op_connect_token` y resuelve en memoria `DATABASE_URL`, `DJANGO_SECRET_KEY` y `CLAVE_MAESTRA_CIFRADO` desde 1Password Connect (`OP_CONNECT_HOST`, por nombre). Reintenta con backoff y lanza `ArranqueError` si Connect no responde. Sin secret, usa variables de entorno (retrocompatible).
