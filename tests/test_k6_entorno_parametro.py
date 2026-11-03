"""Pruebas para K6: Entorno mínimo, modelo Parametro, Connect y kit_check_env."""

import io
import os
from django.test import TestCase
from django.core.management import call_command
from comercial_kit.models import Parametro, Aviso
from comercial_kit.op_connect import set_mock_secret, clear_cache, resolve_op_reference


class TestK6EntornoParametro(TestCase):
    def tearDown(self):
        clear_cache()

    def test_parametro_casteo_tipos(self):
        """Verifica casteo de string, integer, float, boolean y json."""
        p_str = Parametro.objects.create(clave="p.str", valor="hola", tipo=Parametro.TIPO_STRING)
        self.assertEqual(p_str.valor_casteado(), "hola")

        p_int = Parametro.objects.create(clave="p.int", valor="42", tipo=Parametro.TIPO_INTEGER)
        self.assertEqual(p_int.valor_casteado(), 42)

        p_float = Parametro.objects.create(clave="p.flt", valor="3.1416", tipo=Parametro.TIPO_FLOAT)
        self.assertAlmostEqual(p_float.valor_casteado(), 3.1416)

        p_bool1 = Parametro.objects.create(clave="p.b1", valor="true", tipo=Parametro.TIPO_BOOLEAN)
        p_bool2 = Parametro.objects.create(clave="p.b2", valor="0", tipo=Parametro.TIPO_BOOLEAN)
        self.assertTrue(p_bool1.valor_casteado())
        self.assertFalse(p_bool2.valor_casteado())

        p_json = Parametro.objects.create(clave="p.json", valor='{"canales": ["ML", "FAL"]}', tipo=Parametro.TIPO_JSON)
        self.assertEqual(p_json.valor_casteado(), {"canales": ["ML", "FAL"]})

    def test_parametro_metodos_get_y_set(self):
        """Verifica métodos de clase Parametro.get y Parametro.set."""
        Parametro.set("umbral.acantilado", 19990, tipo=Parametro.TIPO_INTEGER, descripcion="Umbral ML")
        self.assertEqual(Parametro.get("umbral.acantilado"), 19990)
        self.assertIsNone(Parametro.get("no_existe"))
        self.assertEqual(Parametro.get("no_existe", default=55), 55)

    def test_resolucion_op_connect_con_cache_en_memoria(self):
        """Verifica que las referencias op:// se resuelvan y queden en caché."""
        ref = "op://IA/zbook_odoo20_svc_precios/credential"
        set_mock_secret(ref, "secreto-super-confidencial")

        p = Parametro.objects.create(clave="fuente.odoo.clave", valor=ref, tipo=Parametro.TIPO_STRING)
        # La lectura resuelve mediante caché
        self.assertEqual(p.valor_casteado(), "secreto-super-confidencial")

        # Modificar caché para verificar que toma de memoria
        set_mock_secret(ref, "secreto-en-cache-actualizado")
        self.assertEqual(resolve_op_reference(ref), "secreto-en-cache-actualizado")

    def test_kit_check_env_detecta_variables_desconocidas(self):
        """Verifica que kit_check_env emita un aviso ante variables no estándar."""
        out = io.StringIO()
        # Agregar variable de negocio indebida en os.environ
        os.environ["MARGEN_OBJETIVO_EN_ENV"] = "25"
        try:
            call_command("kit_check_env", stdout=out)
            output = out.getvalue()
            self.assertIn("MARGEN_OBJETIVO_EN_ENV", output)
            self.assertIn("Variables no estándar detectadas", output)

            # Debe haber registrado un Aviso en BD
            aviso = Aviso.objects.filter(codigo="K6_ENV").first()
            self.assertIsNotNone(aviso)
            self.assertEqual(aviso.nivel, Aviso.NIVEL_AVISO)
        finally:
            del os.environ["MARGEN_OBJETIVO_EN_ENV"]
