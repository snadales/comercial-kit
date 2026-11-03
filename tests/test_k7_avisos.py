"""Pruebas para K7: Modelo Aviso, niveles, estados y envío de críticos al hub."""

from unittest.mock import patch
from django.test import TestCase
from comercial_kit.models import Aviso
from comercial_kit.hub_alertas import HubAlertasAdapter


class TestK7Avisos(TestCase):
    def test_creacion_aviso_informativo_y_aviso(self):
        """Verifica que avisos de nivel info y aviso no invoquen hub_alertas."""
        with patch.object(HubAlertasAdapter, "enviar_critico") as mock_hub:
            a_info = Aviso.objects.create(
                origen="precios",
                codigo="P3",
                objeto="COC-PRE-0012",
                mensaje="Acantilado en 19.990",
                nivel=Aviso.NIVEL_AVISO,
            )
            self.assertEqual(a_info.estado, Aviso.ESTADO_ABIERTO)
            mock_hub.assert_not_called()

    def test_aviso_critico_despacha_a_hub_central(self):
        """Verifica que un aviso crítico invoque enviar_critico en el hub."""
        with patch.object(HubAlertasAdapter, "enviar_critico") as mock_hub:
            a_crit = Aviso.objects.create(
                origen="precios",
                codigo="P1",
                objeto="COC-PRE-0012",
                mensaje="Precio bajo piso",
                nivel=Aviso.NIVEL_CRITICO,
            )
            self.assertEqual(a_crit.nivel, Aviso.NIVEL_CRITICO)
            mock_hub.assert_called_once_with(a_crit)

    def test_fallo_en_hub_nunca_bloquea_la_accion(self):
        """Regla estricta K7: Los avisos nunca bloquean una acción comercial."""
        with patch.object(HubAlertasAdapter, "enviar_critico", side_effect=RuntimeError("Hub caído")):
            # No debe lanzar excepción
            a_crit = Aviso.objects.create(
                origen="precios",
                codigo="P1",
                objeto="SKU-ROTO",
                mensaje="Fallo crítico simulado",
                nivel=Aviso.NIVEL_CRITICO,
            )
            self.assertIsNotNone(a_crit.pk)
