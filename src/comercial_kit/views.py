"""Vistas estándar K5 (/v1/salud, /v1/diagnostico, contrato /v1/simular)."""

import os
import time
import subprocess
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from comercial_kit import __version__ as KIT_VERSION
from comercial_kit.models import Parametro, Aviso


class SaludView(APIView):
    """GET /v1/salud: chequeo de vitalidad, conexión a BD y latencias (K5)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verificación de salud del servicio",
        description="Evalúa estado del proceso, base de datos y fuentes externas.",
        responses={200: OpenApiResponse(description="Servicio saludable"), 503: OpenApiResponse(description="Servicio degradado")},
    )
    def get(self, request):
        db_status = "ok"
        db_latency = 0.0
        is_healthy = True

        t0 = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_latency = round((time.perf_counter() - t0) * 1000, 2)
        except Exception as e:
            db_status = f"error: {str(e)}"
            is_healthy = False

        sources_status = {}
        # Evaluar fuentes si están registradas en el servicio
        evaluador_fuentes = getattr(settings, "HEALTH_CHECK_SOURCES_FN", None)
        if callable(evaluador_fuentes):
            try:
                sources_status = evaluador_fuentes()
            except Exception as e:
                sources_status = {"error": str(e)}

        payload = {
            "status": "ok" if is_healthy else "degraded",
            "servicio": getattr(settings, "SERVICE_NAME", "comercial"),
            "timestamp": time.time(),
            "db": {
                "status": db_status,
                "latency_ms": db_latency,
            },
            "fuentes": sources_status,
        }

        http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)


class DiagnosticoView(APIView):
    """GET /v1/diagnostico: metadata de versiones, parámetros vigentes y avisos (K5)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Diagnóstico técnico del servicio",
        description="Retorna versiones de kit y servicio, commit git, parámetros activos y avisos críticos recientes.",
    )
    def get(self, request):
        commit = os.environ.get("GIT_COMMIT", "")
        if not commit:
            try:
                commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
            except Exception:
                commit = "desconocido"

        # Parámetros vigentes (filtrando referencias sensibles)
        params = {}
        for p in Parametro.objects.all():
            val = p.valor
            if "secreto" in p.clave.lower() or "token" in p.clave.lower() or "password" in p.clave.lower() or val.startswith("op://"):
                params[p.clave] = "op://***[OCULTO]***"
            else:
                params[p.clave] = p.valor_casteado()

        # Últimos avisos críticos
        criticos = list(
            Aviso.objects.filter(nivel=Aviso.NIVEL_CRITICO)
            .order_by("-creado_en")[:5]
            .values("codigo", "objeto", "mensaje", "creado_en", "estado")
        )

        return Response({
            "servicio": getattr(settings, "SERVICE_NAME", "comercial"),
            "version": getattr(settings, "SERVICE_VERSION", "1.0.0"),
            "commit": commit,
            "kit_version": KIT_VERSION,
            "public_host": os.environ.get("PUBLIC_HOST", "localhost"),
            "parametros_vigentes": params,
            "ultimos_avisos_criticos": criticos,
        })


class ContratoSimularView(APIView):
    """Contrato base para el endpoint /v1/simular (K5).
    
    Los microservicios deben heredar de esta vista o implementar esta signatura.
    """

    @extend_schema(
        summary="Simular y explicar cálculo comercial paso a paso",
        parameters=[
            OpenApiParameter("sku", str, description="Código SKU del producto", required=True),
            OpenApiParameter("canal", str, description="Código del canal/marketplace", required=True),
            OpenApiParameter("pvp", int, description="PVP objetivo para cálculo directo (opcional)", required=False),
        ],
        responses={200: OpenApiResponse(description="Desglose matemático completo paso a paso")},
    )
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("Cada microservicio debe implementar el cálculo de /v1/simular")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
