"""Pruebas para K5: Endpoints /v1/salud, /v1/diagnostico y contrato /v1/simular."""

from django.test import TestCase
from rest_framework.test import APIClient
from comercial_kit.models import Parametro, Aviso
from comercial_kit import __version__ as KIT_VERSION


class TestK5SaludDiagnostico(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_salud_endpoint_responde_ok(self):
        """GET /v1/salud retorna estado general y latencia de base de datos."""
        resp = self.client.get("/v1/salud")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("db", data)
        self.assertEqual(data["db"]["status"], "ok")
        self.assertIsInstance(data["db"]["latency_ms"], (int, float))

    def test_diagnostico_endpoint_reporta_metadata_y_parametros(self):
        """GET /v1/diagnostico devuelve versión del kit, host y parámetros."""
        Parametro.objects.create(clave="margen.objetivo", valor="0.25", tipo=Parametro.TIPO_FLOAT)
        Parametro.objects.create(clave="fuente.odoo.token_secreto", valor="op://IA/test/cred", tipo=Parametro.TIPO_STRING)
        Aviso.objects.create(
            origen="test",
            codigo="P1",
            objeto="SKU-TEST",
            mensaje="Margen bajo piso",
            nivel=Aviso.NIVEL_CRITICO,
        )

        resp = self.client.get("/v1/diagnostico")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["kit_version"], KIT_VERSION)
        self.assertIn("public_host", data)

        # Parámetro visible casteado
        self.assertIn("margen.objetivo", data["parametros_vigentes"])
        self.assertEqual(data["parametros_vigentes"]["margen.objetivo"], 0.25)

        # Parámetro sensible u op:// enmascarado
        self.assertIn("fuente.odoo.token_secreto", data["parametros_vigentes"])
        self.assertEqual(data["parametros_vigentes"]["fuente.odoo.token_secreto"], "op://***[OCULTO]***")

        # Aviso crítico visible
        self.assertEqual(len(data["ultimos_avisos_criticos"]), 1)
        self.assertEqual(data["ultimos_avisos_criticos"][0]["codigo"], "P1")
