"""Pruebas para la interfaz admin de comercial-kit."""

from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from comercial_kit.models import Parametro, ConsumidorToken, Aviso
from comercial_kit.admin import ParametroAdmin, ConsumidorTokenAdmin, AvisoAdmin


class DummyRequest:
    pass


class TestAdmin(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.param_admin = ParametroAdmin(Parametro, self.site)
        self.token_admin = ConsumidorTokenAdmin(ConsumidorToken, self.site)
        self.aviso_admin = AvisoAdmin(Aviso, self.site)

    def test_parametro_admin_valor_resumido(self):
        p = Parametro.objects.create(clave="p.largo", valor="x" * 80)
        res = self.param_admin.valor_resumido(p)
        self.assertTrue(res.endswith("..."))
        self.assertEqual(len(res), 60)

    def test_consumidor_token_admin_acciones(self):
        tok, _ = ConsumidorToken.crear_token("app-test")
        qs = ConsumidorToken.objects.filter(pk=tok.pk)

        self.token_admin.desactivar_tokens(DummyRequest(), qs)
        tok.refresh_from_db()
        self.assertFalse(tok.activo)

        self.token_admin.activar_tokens(DummyRequest(), qs)
        tok.refresh_from_db()
        self.assertTrue(tok.activo)

    def test_aviso_admin_acciones_y_badges(self):
        a = Aviso.objects.create(
            origen="precios",
            codigo="P1",
            objeto="SKU-1",
            mensaje="M" * 100,
            nivel=Aviso.NIVEL_CRITICO,
        )
        qs = Aviso.objects.filter(pk=a.pk)

        badge = self.aviso_admin.nivel_badge(a)
        self.assertIn("#FF3333", badge)
        self.assertIn("CRITICO", badge)

        corto = self.aviso_admin.mensaje_corto(a)
        self.assertTrue(corto.endswith("..."))

        self.aviso_admin.marcar_como_visto(DummyRequest(), qs)
        a.refresh_from_db()
        self.assertEqual(a.estado, Aviso.ESTADO_VISTO)

        self.aviso_admin.marcar_como_cerrado(DummyRequest(), qs)
        a.refresh_from_db()
        self.assertEqual(a.estado, Aviso.ESTADO_CERRADO)
