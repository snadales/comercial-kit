"""Pruebas para K1: tema Navarino (Día por defecto, Nocturno opcional) y plantillas."""

import hashlib
import json
import os
import re
import subprocess
import sys

from django.template.loader import render_to_string
from django.test import SimpleTestCase

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(RAIZ, "src", "comercial_kit", "static", "comercial_kit")
CSS_DIR = os.path.join(STATIC, "css")
MARCA = os.path.join(STATIC, "marca")


def leer(*partes):
    with open(os.path.join(*partes), "r", encoding="utf-8") as f:
        return f.read()


class TestK1TokensNavarino(SimpleTestCase):
    def test_tokens_dia_por_defecto_y_nocturno(self):
        css = leer(CSS_DIR, "navarino-tokens.css")
        for hexa in ("#0A1118", "#1A2531", "#8A9AA8", "#E2E8F0", "#E65C00", "#B84A00", "#FFFFFF"):
            self.assertIn(hexa, css)
        self.assertIn('[data-theme="nocturno"]', css)
        self.assertIn('[data-theme="auto"]', css)
        # Día por defecto: el :root base declara superficie blanca y esquema claro
        raiz = re.search(r"(?m)^:root\s*\{(.*?)\n\}", css, re.S).group(1)
        self.assertIn("--nv-surface: #FFFFFF", raiz)
        self.assertIn("color-scheme: light", raiz)

    def test_json_generado_desde_css_y_al_dia(self):
        res = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "scripts", "generar_tokens_json.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        datos = json.loads(leer(CSS_DIR, "navarino-tokens.json"))
        familias = {t["family"] for t in datos["tokens"]}
        self.assertTrue({"color", "spacing", "radius", "type", "z", "breakpoints"} <= familias)
        superficie = next(t for t in datos["tokens"] if t["name"] == "--nv-surface")
        self.assertEqual(superficie["value"], {"dia": "#FFFFFF", "nocturno": "#0A1118"})

    def test_componentes_solo_consumen_nv_y_sin_degradados(self):
        css = leer(CSS_DIR, "navarino-componentes.css")
        self.assertNotIn("gradient", css)
        # Ningún color fijo: todo sale de los tokens
        sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertIsNone(re.search(r"#[0-9A-Fa-f]{3,8}\b", sin_comentarios))
        self.assertIsNone(re.search(r"rgba?\(", sin_comentarios))
        for clase in (".nv-btn--primary", ".nv-btn--secondary", ".nv-btn--ghost", ".nv-btn--danger",
                      ".nv-input", ".nv-select", ".nv-checkbox", ".nv-radio", ".nv-switch",
                      ".nv-table", ".nv-card", ".nv-kpi", ".nv-badge--activo", ".nv-alert--danger",
                      ".nv-tabs", ".nv-skeleton", ".nv-legend", ".nv-bars", ".nv-theme-toggle"):
            self.assertIn(clase, css)
        self.assertIn("prefers-reduced-motion", css)

    def test_admin_css_usa_tokens_nv_y_no_fija_oscuro(self):
        css = leer(CSS_DIR, "navarino_admin.css")
        self.assertIn("var(--nv-surface)", css)
        self.assertIn("var(--nv-ink)", css)
        self.assertIn("var(--nv-accent)", css)
        self.assertNotIn("--nav-", css)
        sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertIsNone(re.search(r"#[0-9A-Fa-f]{3,8}\b", sin_comentarios))
        self.assertIn("text-shadow: none", css)


class TestK1Marca(SimpleTestCase):
    def test_logos_oficiales_coinciden_con_sha256sums(self):
        lineas = leer(MARCA, "SHA256SUMS").strip().splitlines()
        self.assertEqual(len(lineas), 7)
        for linea in lineas:
            esperado, nombre = linea.split(None, 1)
            with open(os.path.join(MARCA, nombre.strip()), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), esperado, nombre)

    def test_admin_base_site_usa_logos_de_marca(self):
        rendered = render_to_string("admin/base_site.html", {"title": "Panel"})
        self.assertIn("comercial_kit/marca/navarino-logo-positivo.svg", rendered)
        self.assertIn("comercial_kit/marca/navarino-logo-negativo.svg", rendered)
        self.assertIn("comercial_kit/css/navarino-tokens.css", rendered)
        self.assertIn("navarino-logo-img", rendered)
        self.assertNotIn("admin/js/theme.js", rendered)

    def test_plantilla_base_dia_por_defecto(self):
        rendered = render_to_string("comercial_kit/base.html", {})
        self.assertIn("comercial_kit/css/navarino-tokens.css", rendered)
        self.assertIn("comercial_kit/css/navarino-componentes.css", rendered)
        self.assertIn("comercial_kit/marca/navarino-logo-positivo.svg", rendered)
        self.assertIn("comercial_kit/marca/navarino-logo-negativo.svg", rendered)
        self.assertIn("comercial_kit/marca/navarino-favicon.svg", rendered)
        self.assertIn("data-nv-theme-toggle", rendered)
        # Sin :root en línea ni data-theme fijo en <html>
        self.assertNotIn(":root", rendered)
        self.assertRegex(rendered, r"<html lang=\"es-CL\">")
        # Clases heredadas que usan los servicios
        self.assertIn("nav-header", rendered)
        self.assertIn("nav-container", rendered)

    def test_plantilla_base_conserva_bloques(self):
        fuente = leer(RAIZ, "src", "comercial_kit", "templates", "comercial_kit", "base.html")
        for bloque in ("title", "extra_head", "nav_links", "content", "footer", "extra_scripts"):
            self.assertIn("{% block " + bloque + " %}", fuente)
