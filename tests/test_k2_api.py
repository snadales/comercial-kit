"""Pruebas para K2: DRF, errores RFC 9457 y tokens de consumidor."""

from django.test import TestCase
from rest_framework.test import APIClient
from comercial_kit.models import ConsumidorToken


class TestK2API(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token_lectura_obj, self.raw_token_lectura = ConsumidorToken.crear_token(
            nombre="consumidor-lectura", alcance=ConsumidorToken.ALCANCE_LECTURA
        )
        self.token_escritura_obj, self.raw_token_escritura = ConsumidorToken.crear_token(
            nombre="consumidor-escritura", alcance=ConsumidorToken.ALCANCE_ESCRITURA
        )

    def test_error_rfc9457_validacion(self):
        """Verifica que errores de validación devuelvan problem+json con trace_id."""
        resp = self.client.get("/test/error-val")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp["Content-Type"], "application/problem+json")
        data = resp.json()
        self.assertEqual(data["status"], 400)
        self.assertIn("trace_id", data)
        self.assertTrue(len(data["trace_id"]) > 0)
        self.assertIn("invalid_params", data)
        self.assertIn("sku", data["invalid_params"])

    def test_error_rfc9457_servidor_500(self):
        """Verifica que error 500 no controlado retorne problem+json."""
        # En test runner DRF propaga excepciones si no se atrapan en vista
        # Para simular respuesta del handler:
        from comercial_kit.exceptions import rfc9457_exception_handler
        class DummyRequest:
            trace_id = "test-trace-id-12345"
            path = "/test/error-500"
        
        resp = rfc9457_exception_handler(RuntimeError("Fallo"), {"request": DummyRequest()})
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp["Content-Type"], "application/problem+json")
        self.assertEqual(resp.data["trace_id"], "test-trace-id-12345")
        self.assertEqual(resp.data["title"], "Error Interno del Servidor")

    def test_autenticacion_token_lectura_exitosa(self):
        """Consumidor con token de lectura puede acceder a vistas de lectura."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw_token_lectura}")
        resp = self.client.get("/test/lectura")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["mensaje"], "acceso_lectura_ok")

    def test_autenticacion_token_lectura_deniega_escritura(self):
        """Consumidor con solo lectura no puede escribir."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw_token_lectura}")
        resp = self.client.post("/test/escritura", {})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp["Content-Type"], "application/problem+json")

    def test_autenticacion_token_escritura_permite_escritura_y_lectura(self):
        """Consumidor con token de escritura puede leer y escribir."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw_token_escritura}")
        resp_get = self.client.get("/test/lectura")
        self.assertEqual(resp_get.status_code, 200)
        resp_post = self.client.post("/test/escritura", {})
        self.assertEqual(resp_post.status_code, 200)

    def test_token_inactivo_rechaza_acceso(self):
        """Token marcado inactivo devuelve 401."""
        self.token_lectura_obj.activo = False
        self.token_lectura_obj.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw_token_lectura}")
        resp = self.client.get("/test/lectura")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp["Content-Type"], "application/problem+json")

    def test_token_invalido_o_malformado(self):
        """Token falso devuelve 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_falso_invalido")
        resp = self.client.get("/test/lectura")
        self.assertEqual(resp.status_code, 401)

    def test_openapi_schema_disponible(self):
        """Verifica que el schema OpenAPI esté generado en /v1/schema."""
        resp = self.client.get("/v1/schema", {"format": "json"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("openapi", resp.json())

