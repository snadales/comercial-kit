"""Pruebas para K1: Tema Navarino Nocturno y plantillas."""

import os
from django.test import SimpleTestCase
from django.template.loader import render_to_string


class TestK1TemaNavarino(SimpleTestCase):
    def test_css_contiene_tokens_nocturno(self):
        """Verifica que el CSS incluya la paleta y tokens semánticos oficiales."""
        css_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "comercial_kit", "static", "comercial_kit", "css", "navarino_admin.css"
        )
        self.assertTrue(os.path.exists(css_path), "navarino_admin.css debe existir")
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Tokens de color
        self.assertIn("#0A1118", content)  # beagle
        self.assertIn("#1A2531", content)  # basalto
        self.assertIn("#8A9AA8", content)  # acero
        self.assertIn("#E2E8F0", content)  # niebla
        self.assertIn("#E65C00", content)  # senal
        self.assertIn("#B84A00", content)  # senal-profunda
        self.assertIn("#FFFFFF", content)  # blanco

        # Semánticos
        self.assertIn("--nav-surface", content)
        self.assertIn("--nav-surface-raised", content)
        self.assertIn("--nav-ink", content)
        self.assertIn("--nav-ink-muted", content)
        self.assertIn("--nav-accent", content)

        # Regla sin sombras ni degradados
        self.assertIn("box-shadow: none", content)
        self.assertIn("text-shadow: none", content)

    def test_admin_base_site_usa_logo_svg_marca_navarino(self):
        """Verifica que el admin use la ruta /marca-navarino/ y nunca texto."""
        rendered = render_to_string("admin/base_site.html", {"title": "Panel"})
        self.assertIn("/marca-navarino/navarino-logo-negativo.svg", rendered)
        self.assertIn("navarino-logo-img", rendered)

    def test_plantilla_base_renderiza_correctamente(self):
        """Verifica que la plantilla base de comercial-kit renderice con estructura Nocturno."""
        rendered = render_to_string("comercial_kit/base.html", {})
        self.assertIn("nav-header", rendered)
        self.assertIn("nav-container", rendered)
        self.assertIn("/marca-navarino/navarino-logo-negativo.svg", rendered)
