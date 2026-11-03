"""Pruebas para K4: Logging estructurado en JSON a stdout con trace_id."""

import json
import logging
from django.test import SimpleTestCase
from comercial_kit.logging import JsonFormatter, DynamicLogLevelFilter
from comercial_kit.middleware import trace_id_ctx, span_id_ctx


class TestK4Logging(SimpleTestCase):
    def test_json_formatter_formatea_evento_con_trace_id(self):
        """Verifica que cada línea sea un objeto JSON válido con los campos requeridos."""
        formatter = JsonFormatter()
        logger = logging.getLogger("test.logger")

        # Configurar contexto
        t_token = trace_id_ctx.set("abcdef1234567890abcdef1234567890")
        s_token = span_id_ctx.set("1234567890abcdef")

        try:
            record = logger.makeRecord(
                name="test.logger",
                level=logging.INFO,
                fn="test_file.py",
                lno=42,
                msg="Evento de prueba para log JSON",
                args=(),
                exc_info=None,
                extra={"modulo": "pricing", "sku": "COC-PRE-0012"},
            )
            output = formatter.format(record)

            # Debe ser JSON válido
            data = json.loads(output)
            self.assertIn("ts", data)
            self.assertEqual(data["nivel"], "INFO")
            self.assertEqual(data["trace_id"], "abcdef1234567890abcdef1234567890")
            self.assertEqual(data["span_id"], "1234567890abcdef")
            self.assertEqual(data["evento"], "Evento de prueba para log JSON")
            self.assertIn("extra", data)
            self.assertEqual(data["extra"]["sku"], "COC-PRE-0012")
        finally:
            trace_id_ctx.reset(t_token)
            span_id_ctx.reset(s_token)

    def test_dynamic_log_level_filter(self):
        """Verifica el comportamiento del filtro de nivel dinámico."""
        filtro = DynamicLogLevelFilter()
        logger = logging.getLogger("test.filter")
        record_debug = logger.makeRecord("test.filter", logging.DEBUG, "f.py", 1, "msg", (), None)
        record_info = logger.makeRecord("test.filter", logging.INFO, "f.py", 1, "msg", (), None)

        # Sin configuración en Parametro pasa todo por defecto
        self.assertTrue(filtro.filter(record_debug))
        self.assertTrue(filtro.filter(record_info))
