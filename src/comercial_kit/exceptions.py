"""Manejador de excepciones RFC 9457 (Problem Details) para DRF (K2)."""

import json
from typing import Any
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from comercial_kit.middleware import get_current_trace_id
from comercial_kit.renderers import ProblemJsonRenderer



def rfc9457_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Transforma errores DRF al formato estándar RFC 9457 con trace_id."""
    response = exception_handler(exc, context)
    request = context.get("request")
    trace_id = getattr(request, "trace_id", None) or get_current_trace_id()
    path = getattr(request, "path", "")

    if response is None:
        # Error no manejado por DRF (e.g. 500)
        import logging
        logging.getLogger("comercial_kit.exceptions").exception("Excepción no manejada en DRF: %s", exc)
        problem_data = {
            "type": "https://wiki.yarken.cl/problemas/error-interno",
            "title": "Error Interno del Servidor",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "Ha ocurrido un error inesperado al procesar la solicitud.",
            "instance": path,
            "trace_id": trace_id,
        }
        resp = Response(
            problem_data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/problem+json",
        )
        resp.accepted_renderer = ProblemJsonRenderer()
        resp.accepted_media_type = "application/problem+json"
        resp["Content-Type"] = "application/problem+json"
        resp.renderer_context = context
        return resp


    status_code = response.status_code
    detail = ""
    invalid_params = None

    if isinstance(response.data, dict):
        if "detail" in response.data:
            detail = str(response.data["detail"])
        else:
            detail = "Error de validación en los parámetros enviados."
            invalid_params = response.data
    elif isinstance(response.data, list):
        detail = " ; ".join(str(d) for d in response.data)
    else:
        detail = str(response.data)

    problem_type = f"https://wiki.yarken.cl/problemas/http-{status_code}"
    title = response.status_text or "Error en la solicitud"
    if status_code == 400:
        title = "Solicitud Incorrecta"
    elif status_code == 401:
        title = "No Autenticado"
    elif status_code == 403:
        title = "Acceso Denegado"
    elif status_code == 404:
        title = "Recurso No Encontrado"

    if request:
        request.accepted_renderer = ProblemJsonRenderer()
        request.accepted_media_type = "application/problem+json"

    problem_data = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": path,
        "trace_id": trace_id,
    }
    if invalid_params:
        problem_data["invalid_params"] = invalid_params

    response.data = problem_data
    response.accepted_renderer = ProblemJsonRenderer()
    response.accepted_media_type = "application/problem+json"
    response["Content-Type"] = "application/problem+json"
    return response


