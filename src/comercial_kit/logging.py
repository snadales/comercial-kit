"""Logging estructurado en JSON a stdout con trace_id (K4) y nivel dinámico (K5)."""

import json
import logging
from datetime import datetime, timezone
from django.conf import settings
from comercial_kit.middleware import get_current_trace_id, get_current_span_id


class JsonFormatter(logging.Formatter):
    """Formateador JSON a stdout con una línea por evento."""

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", None) or get_current_trace_id()
        span_id = getattr(record, "span_id", None) or get_current_span_id()
        servicio = getattr(settings, "SERVICE_NAME", "comercial")

        log_data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "nivel": record.levelname,
            "servicio": servicio,
            "trace_id": trace_id or "00000000000000000000000000000000",
            "span_id": span_id or "0000000000000000",
            "logger": record.name,
            "evento": record.getMessage(),
        }

        # Extraer campos adicionales si se pasaron en extra={}
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "trace_id", "span_id"
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extras:
            log_data["extra"] = extras

        if record.exc_info:
            log_data["excepcion"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class DynamicLogLevelFilter(logging.Filter):
    """Filtro que permite ajustar el nivel de log en caliente vía Parametro('log.nivel') (K5)."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from comercial_kit.models import Parametro
            nivel_config = Parametro.get("log.nivel", "").upper()
            if nivel_config:
                target_level = getattr(logging, nivel_config, None)
                if isinstance(target_level, int):
                    return record.levelno >= target_level
        except Exception:
            pass
        return True
