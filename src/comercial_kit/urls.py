"""Rutas de API estándar de comercial-kit (K2, K5)."""

from django.urls import path
from comercial_kit.views import SaludView, DiagnosticoView

urlpatterns = [
    path("salud", SaludView.as_view(), name="salud"),
    path("diagnostico", DiagnosticoView.as_view(), name="diagnostico"),
]
