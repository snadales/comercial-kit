"""Pruebas del proyecto de ejemplo con exactamente las 4 variables de entorno base."""

import os
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient


class TestExampleProject(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_arranque_con_solo_4_variables(self):
        """Verifica que el sistema funcione con exactamente las 4 variables requeridas."""
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["DJANGO_SECRET_KEY"] = "clave-secreta-de-prueba-exactamente-32-chars"
        os.environ["OP_CONNECT_TOKEN"] = "token-connect-test"
        os.environ["PUBLIC_HOST"] = "pricing.yarken.cl"

        # 1. Comprobar salud
        resp_salud = self.client.get("/v1/salud")
        self.assertEqual(resp_salud.status_code, 200)
        self.assertEqual(resp_salud.json()["status"], "ok")

        # 2. Comprobar diagnóstico
        resp_diag = self.client.get("/v1/diagnostico")
        self.assertEqual(resp_diag.status_code, 200)
        self.assertEqual(resp_diag.json()["public_host"], "pricing.yarken.cl")

        # 3. Comprobar comando kit_check_env
        call_command("kit_check_env")
