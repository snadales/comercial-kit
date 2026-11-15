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
- **K1 Tema Navarino (Día por defecto, Nocturno opcional):** tokens `--nv-*` en `static/comercial_kit/css/navarino-tokens.css` (y su espejo `navarino-tokens.json`, generado con `scripts/generar_tokens_json.py`), componentes `nv-` en `navarino-componentes.css`, logos oficiales en `static/comercial_kit/marca/` verificados con `SHA256SUMS`. `data-theme="nocturno"` fuerza Nocturno y `data-theme="auto"` sigue al sistema; el interruptor guarda la preferencia en `localStorage` (`nv-theme`). Sin sombras salvo menús, diálogos y avisos flotantes; sin degradados. Muestra en `docs/muestra-brandbook.html` y capturas en `docs/capturas/`.
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
