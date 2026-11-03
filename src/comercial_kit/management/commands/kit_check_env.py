"""Comando kit_check_env para verificar la lista cerrada de 4 variables de entorno (K6)."""

import os
import re
import sys
from django.core.management.base import BaseCommand
from comercial_kit.models import Aviso

# Lista exacta y cerrada de 4 variables del estándar K6
VARIABLES_PERMITIDAS = {
    "DATABASE_URL",
    "DJANGO_SECRET_KEY",
    "OP_CONNECT_TOKEN",
    "PUBLIC_HOST",
}

# Variables del sistema operativo y herramientas comunes que se ignoran
VARIABLES_SISTEMA_IGNORADAS = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "LANG", "PWD", "OLDPWD",
    "SHLVL", "_", "VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", "PYTHONUNBUFFERED",
    "TMPDIR", "XPC_FLAGS", "XPC_SERVICE_NAME", "SSH_AUTH_SOCK", "GIT_COMMIT",
    "CI", "HOSTNAME", "DEV_ROOT", "AGY_ACCOUNT", "OP_CONNECT_HOST", "TZ",
}


class Command(BaseCommand):
    help = "Verifica que solo existan las 4 variables de entorno permitidas por el estándar K6."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Falla con código 1 si detecta variables no estándar.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔍 Verificando variables de entorno según estándar K6..."))

        faltantes = []
        for var in VARIABLES_PERMITIDAS:
            if not os.environ.get(var):
                faltantes.append(var)

        if faltantes:
            self.stdout.write(self.style.WARNING(f"⚠️  Faltan variables base obligatorias: {', '.join(faltantes)}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Las 4 variables base de entorno están presentes."))

        # Detectar variables no estándar (ignorar prefijos del sistema)
        desconocidas = []
        for key in os.environ:
            if key in VARIABLES_PERMITIDAS or key in VARIABLES_SISTEMA_IGNORADAS:
                continue
            if key.startswith(("LC_", "APPLE_", "COLOR", "SECURITY", "TERM_", "COMMAND_")):
                continue
            desconocidas.append(key)

        if desconocidas:
            msg = (
                f"Variables no estándar detectadas en entorno: {', '.join(sorted(desconocidas))}. "
                "Regla K6: Todo parámetro de negocio, URLs, timeouts y referencias op:// "
                "debe ir en el modelo Parametro, nunca en variables de entorno."
            )
            self.stdout.write(self.style.WARNING(f"⚠️  {msg}"))
            try:
                Aviso.objects.create(
                    origen="kit_check_env",
                    codigo="K6_ENV",
                    objeto="os.environ",
                    mensaje=msg,
                    nivel=Aviso.NIVEL_AVISO,
                )
            except Exception:
                pass

            if options.get("strict"):
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("✅ No se detectaron variables desconocidas. Entorno K6 limpio."))
