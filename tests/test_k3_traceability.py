"""Pruebas para K3: Trazabilidad OpenTelemetry W3C traceparent y simple-history."""

from django.test import TestCase
from rest_framework.test import APIClient
from comercial_kit.models import Parametro


class TestK3Trazabilidad(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_traceparent_entrante_se_propaga_a_saliente(self):
        """Verifica que el trace_id entrante se mantenga y se devuelva en la cabecera traceparent."""
        in_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        in_span_id = "00f067aa0ba902b7"
        traceparent_in = f"00-{in_trace_id}-{in_span_id}-01"

        resp = self.client.get("/v1/salud", HTTP_TRACEPARENT=traceparent_in)
        self.assertEqual(resp.status_code, 200)

        # Cabeceras salientes
        self.assertIn("traceparent", resp)
        self.assertIn("X-Trace-ID", resp)
        self.assertEqual(resp["X-Trace-ID"], in_trace_id)

        # Formato W3C
        tp_out = resp["traceparent"]
        parts = tp_out.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "00")
        self.assertEqual(parts[1], in_trace_id)
        self.assertEqual(len(parts[2]), 16)  # nuevo span_id
        self.assertEqual(parts[3], "01")

    def test_traceparent_ausente_se_genera_automaticamente(self):
        """Si la petición no trae traceparent, se genera uno válido W3C."""
        resp = self.client.get("/v1/salud")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("traceparent", resp)
        tp_out = resp["traceparent"]
        parts = tp_out.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "00")
        self.assertEqual(len(parts[1]), 32)
        self.assertEqual(len(parts[2]), 16)
        self.assertEqual(parts[3], "01")
        self.assertEqual(resp["X-Trace-ID"], parts[1])

    def test_simple_history_registra_cambios(self):
        """Verifica que los cambios en modelos guarden historial simple-history."""
        p = Parametro.objects.create(clave="margen.objetivo", valor="0.25", tipo=Parametro.TIPO_FLOAT)
        self.assertEqual(p.history.count(), 1)

        p.valor = "0.30"
        p.save()
        self.assertEqual(p.history.count(), 2)

        primer_registro = p.history.earliest("history_date")
        self.assertEqual(primer_registro.valor, "0.25")
        ultimo_registro = p.history.latest("history_date")
        self.assertEqual(ultimo_registro.valor, "0.30")
