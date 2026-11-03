"""Middleware OpenTelemetry W3C traceparent y trazabilidad (K3)."""

import re
import secrets
from contextvars import ContextVar
from typing import Callable
from django.http import HttpRequest, HttpResponse

# ContextVars para logging y propagación en el hilo de ejecución
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
span_id_ctx: ContextVar[str] = ContextVar("span_id", default="")

_TRACEPARENT_REGEX = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def get_current_trace_id() -> str:
    """Retorna el trace_id actual del contexto."""
    return trace_id_ctx.get()


def get_current_span_id() -> str:
    """Retorna el span_id actual del contexto."""
    return span_id_ctx.get()


class OpenTelemetryTraceMiddleware:
    """Middleware que asegura propagación W3C traceparent entrante y saliente."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        raw_tp = request.META.get("HTTP_TRACEPARENT", "").strip().lower()
        match = _TRACEPARENT_REGEX.match(raw_tp)

        if match:
            trace_id = match.group(1)
            # Generar nuevo span_id para esta ejecución
            span_id = secrets.token_hex(8)
            flags = match.group(3)
        else:
            trace_id = secrets.token_hex(16)
            span_id = secrets.token_hex(8)
            flags = "01"

        out_traceparent = f"00-{trace_id}-{span_id}-{flags}"

        # Asignar a request
        request.trace_id = trace_id
        request.span_id = span_id
        request.traceparent = out_traceparent

        # Guardar en contexto para el logger estructurado
        token_t = trace_id_ctx.set(trace_id)
        token_s = span_id_ctx.set(span_id)

        try:
            response = self.get_response(request)
            response["traceparent"] = out_traceparent
            response["X-Trace-ID"] = trace_id
            return response
        finally:
            trace_id_ctx.reset(token_t)
            span_id_ctx.reset(token_s)
