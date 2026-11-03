"""URLs de prueba para comercial-kit."""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from comercial_kit.authentication import RequiereEscritura, RequiereLectura


class VistaProtegidaLectura(APIView):
    permission_classes = [RequiereLectura]

    def get(self, request):
        return Response({"mensaje": "acceso_lectura_ok"})


class VistaProtegidaEscritura(APIView):
    permission_classes = [RequiereEscritura]

    def post(self, request):
        return Response({"mensaje": "acceso_escritura_ok"})


class VistaErrorValidacion(APIView):
    def get(self, request):
        raise ValidationError({"sku": ["Este campo es obligatorio."], "precio": ["Debe ser mayor a 0"]})


class VistaError500(APIView):
    def get(self, request):
        raise RuntimeError("Error forzado no controlado para prueba 500")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("v1/", include("comercial_kit.urls")),
    path("v1/schema", SpectacularAPIView.as_view(), name="schema"),
    path("v1/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Endpoints de prueba
    path("test/lectura", VistaProtegidaLectura.as_view()),
    path("test/escritura", VistaProtegidaEscritura.as_view()),
    path("test/error-val", VistaErrorValidacion.as_view()),
    path("test/error-500", VistaError500.as_view()),
]
