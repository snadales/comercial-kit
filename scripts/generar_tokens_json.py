#!/usr/bin/env python3
"""Genera navarino-tokens.json a partir de navarino-tokens.css.

El CSS es la única fuente escrita a mano; este script lo lee y produce la
versión JSON para herramientas que no consumen CSS (gráficos, scripts, Figma).

Uso:
    python3 scripts/generar_tokens_json.py          # escribe el JSON
    python3 scripts/generar_tokens_json.py --check  # falla si el JSON está desactualizado
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS_DIR = RAIZ / "src" / "comercial_kit" / "static" / "comercial_kit" / "css"
CSS = CSS_DIR / "navarino-tokens.css"
JSON_OUT = CSS_DIR / "navarino-tokens.json"

RE_DECL = re.compile(r"(--nv-[\w-]+)\s*:\s*([^;]+);")
RE_COMENTARIO = re.compile(r"/\*.*?\*/", re.S)
RE_BREAKPOINT = re.compile(r"\b(sm|md|lg|xl)\s*≥\s*(\d+px)")

# Uso por token (o por prefijo, el más largo gana). Texto breve, en español.
USOS = {
    "--nv-beagle": "Marca: azul casi negro; fondo Nocturno y tinta Día",
    "--nv-basalto": "Marca: superficie elevada en Nocturno",
    "--nv-acero": "Marca: gris acero; texto secundario en Nocturno",
    "--nv-niebla": "Marca: gris niebla; superficie elevada en Día",
    "--nv-blanco": "Marca: blanco",
    "--nv-senal": "Marca: naranja señal; acento en Nocturno",
    "--nv-senal-profunda": "Marca: naranja profundo; acento en Día",
    "--nv-kraft": "Marca: kraft; material de empaque, uso decorativo",
    "--nv-glaciar-marca": "Marca D5: glaciar, color de apoyo",
    "--nv-lenga-marca": "Marca D5: lenga, color de apoyo y gráficos",
    "--nv-surface": "Fondo de tarjetas, campos y paneles",
    "--nv-surface-sunken": "Fondo de página (tinte glaciar en Día, D5) y bloques hundidos",
    "--nv-surface-raised": "Superficie elevada: encabezados de tabla, tarjetas destacadas",
    "--nv-ink": "Texto principal",
    "--nv-ink-muted": "Texto secundario, ayudas y rótulos",
    "--nv-line": "Filete de 1 px para separar",
    "--nv-line-strong": "Borde de campos y controles",
    "--nv-line-card": "Borde de tarjeta: transparente en Día (sombra), filete en Nocturno",
    "--nv-accent": "Acento legible como texto o borde (compatibilidad; en Día #B84A00)",
    "--nv-accent-hover": "Acento en hover",
    "--nv-on-accent": "Texto sobre --nv-accent",
    "--nv-accent-fill": "Acento como relleno: botón principal (D5)",
    "--nv-accent-fill-hover": "Relleno del botón principal en hover",
    "--nv-on-accent-fill": "Texto tinta sobre el relleno naranja",
    "--nv-accent-text": "Naranja como texto sobre fondo claro u oscuro (≥ 4,5)",
    "--nv-glaciar": "Apoyo glaciar: gráficos, foco de campos, bordes activos",
    "--nv-glaciar-ink": "Texto glaciar: botón secundario, insignia, pestaña activa",
    "--nv-glaciar-bg": "Fondo teñido glaciar: insignias, pestaña activa, hover",
    "--nv-glaciar-line": "Borde glaciar del botón secundario y filetes de tabla",
    "--nv-lenga": "Apoyo lenga: gráficos y punto de insignia",
    "--nv-lenga-ink": "Texto lenga en insignias",
    "--nv-lenga-bg": "Fondo teñido lenga en insignias",
    "--nv-focus": "Anillo de foco de 2 px con offset de 2 px",
    "--nv-link": "Enlaces",
    "--nv-link-hover": "Enlaces en hover",
    "--nv-success": "Estado éxito: texto y borde",
    "--nv-success-bg": "Estado éxito: fondo",
    "--nv-warning": "Estado aviso: texto y borde",
    "--nv-warning-bg": "Estado aviso: fondo",
    "--nv-danger": "Estado error o peligro: texto y borde",
    "--nv-danger-bg": "Estado error o peligro: fondo",
    "--nv-info": "Estado información: texto y borde",
    "--nv-info-bg": "Estado información: fondo",
    "--nv-data-grid": "Grilla de gráficos",
    "--nv-data-": "Serie de datos en orden; se distinguen por claridad, no solo por tono",
    "--nv-font-display": "Titulares (Outfit 500, tipo oración)",
    "--nv-font-sans": "Texto de interfaz (Inter)",
    "--nv-font-mono": "Datos, montos y SKU (JetBrains Mono)",
    "--nv-text-": "Tamaño de la escala tipográfica",
    "--nv-lh-": "Interlineado de la escala tipográfica",
    "--nv-tracking-eyebrow": "Tracking de rótulos en mayúsculas",
    "--nv-weight-": "Peso tipográfico",
    "--nv-space-": "Espaciado Fibonacci",
    "--nv-gutter": "Medianil del contenedor (escritorio)",
    "--nv-gutter-mobile": "Medianil del contenedor (móvil)",
    "--nv-container-": "Ancho máximo de contenedor",
    "--nv-radius-0": "Compatibilidad (sin uso en D5: ninguna esquina en 0)",
    "--nv-radius-3": "Compatibilidad (reemplazado por --nv-radius-control en D5)",
    "--nv-radius-sm": "Casillas, esqueletos y código",
    "--nv-radius-control": "Botones y campos (10 px, D5)",
    "--nv-radius-card": "Tarjetas, tablas, alertas, menús y paneles (12 px, D5)",
    "--nv-radius-full": "Píldora: insignias, chips, pestañas y punto de estado",
    "--nv-border-hairline": "Grosor de filete",
    "--nv-border-focus": "Grosor del anillo de foco",
    "--nv-shadow-card": "Sombra suave de tarjeta (reemplaza el borde duro, D5)",
    "--nv-shadow-card-hover": "Sombra de tarjeta o botón principal en hover",
    "--nv-shadow-overlay": "Sombra de capa: menús, diálogos y toasts",
    "--nv-z-": "Capa de apilamiento",
    "--nv-duration": "Duración de transiciones",
    "--nv-ease": "Curva de transiciones",
}


def familia(nombre: str) -> str:
    n = nombre[len("--nv-"):]
    if n.startswith("z-"):
        return "z"
    if n.startswith(("space-", "gutter", "container-")):
        return "spacing"
    if n.startswith(("radius-", "border-", "shadow-")):
        return "radius"
    if n.startswith(("font-", "text-", "lh-", "tracking-", "weight-")):
        return "type"
    if n in ("duration", "ease"):
        return "motion"
    return "color"


def uso(nombre: str) -> str:
    if nombre in USOS:
        return USOS[nombre]
    prefijos = [p for p in USOS if p.endswith("-") and nombre.startswith(p)]
    return USOS[max(prefijos, key=len)] if prefijos else ""


def bloque(css: str, selector_re: str) -> str:
    m = re.search(selector_re + r"\s*\{(.*?)\n\s*\}", css, re.S)
    if not m:
        raise SystemExit(f"No encontré el bloque {selector_re!r} en {CSS}")
    return RE_COMENTARIO.sub("", m.group(1))


def decls(texto: str) -> dict[str, str]:
    return {k: " ".join(v.split()) for k, v in RE_DECL.findall(texto)}


def generar() -> dict:
    css = CSS.read_text(encoding="utf-8")
    dia = decls(bloque(css, r"(?m)^:root"))
    nocturno = decls(bloque(css, r':root\[data-theme="nocturno"\]'))
    auto = decls(bloque(css, r':root\[data-theme="auto"\]'))
    if auto != nocturno:
        raise SystemExit("El bloque data-theme=auto no coincide con nocturno; revisa el CSS")

    tokens = [
        {
            "name": nombre,
            "family": familia(nombre),
            "value": {"dia": valor, "nocturno": nocturno.get(nombre, valor)},
            "usage": uso(nombre),
        }
        for nombre, valor in dia.items()
    ]
    for bp, px in RE_BREAKPOINT.findall(css):
        tokens.append({
            "name": f"--nv-bp-{bp}",
            "family": "breakpoints",
            "value": {"dia": px, "nocturno": px},
            "usage": f"Breakpoint {bp}: min-width {px} (solo en media queries)",
        })
    orden = ["color", "spacing", "radius", "type", "z", "breakpoints", "motion"]
    tokens.sort(key=lambda t: orden.index(t["family"]))
    return {
        "source": "src/comercial_kit/static/comercial_kit/css/navarino-tokens.css",
        "generated_by": "scripts/generar_tokens_json.py",
        "themes": {"dia": "por defecto", "nocturno": 'data-theme="nocturno" o "auto" con sistema oscuro'},
        "tokens": tokens,
    }


def main() -> int:
    salida = json.dumps(generar(), ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        actual = JSON_OUT.read_text(encoding="utf-8") if JSON_OUT.exists() else ""
        if actual != salida:
            print("navarino-tokens.json está desactualizado: corre scripts/generar_tokens_json.py")
            return 1
        print("navarino-tokens.json al día")
        return 0
    JSON_OUT.write_text(salida, encoding="utf-8")
    print(f"Escrito {JSON_OUT.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
