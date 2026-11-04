"""K8: arranque sin .env. El único secreto es el Docker secret op_connect_token."""

import logging
import os
import time

from comercial_kit.op_connect import ConnectError, resolve_op_reference

logger = logging.getLogger("comercial_kit.arranque")

RUTA_SECRET_POR_DEFECTO = "/run/secrets/op_connect_token"
CLAVES_ARRANQUE = ("DATABASE_URL", "DJANGO_SECRET_KEY", "CLAVE_MAESTRA_CIFRADO")


class ArranqueError(Exception):
    """Connect no respondió o una referencia no pudo resolverse."""


def leer_token(ruta: str | None = None) -> str | None:
    """Devuelve el token del Docker secret, o None si no existe o está vacío."""
    ruta = ruta or os.environ.get("OP_CONNECT_TOKEN_FILE", RUTA_SECRET_POR_DEFECTO)
    try:
        with open(ruta, encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def cargar_secretos(
    referencias: dict[str, str],
    *,
    ruta_secret: str | None = None,
    host: str | None = None,
    intentos: int = 5,
    espera_inicial: float = 1.0,
    dormir=time.sleep,
) -> dict[str, str]:
    """Resuelve en memoria cada referencia op://.

    Sin Docker secret devuelve las variables de entorno de mismo nombre (modo
    retrocompatible). Con secret, reintenta con backoff exponencial y falla con
    ArranqueError. Nunca escribe a disco ni loguea valores.
    """
    token = leer_token(ruta_secret)
    if token is None:
        logger.info("Sin Docker secret op_connect_token: se usan variables de entorno")
        return {k: os.environ[k] for k in referencias if k in os.environ}

    host = host or os.environ.get("OP_CONNECT_HOST")
    resueltos: dict[str, str] = {}
    for clave, ref in referencias.items():
        espera = espera_inicial
        for intento in range(1, intentos + 1):
            try:
                resueltos[clave] = resolve_op_reference(ref, token=token, host=host)
                break
            except ConnectError as exc:
                if intento == intentos:
                    logger.error("Arranque abortado: 1Password Connect no resolvió %s (%s)", clave, exc)
                    raise ArranqueError(f"No se pudo resolver {clave} desde 1Password Connect") from exc
                logger.warning("Connect no disponible para %s (intento %d/%d); reintento en %.0fs",
                               clave, intento, intentos, espera)
                dormir(espera)
                espera = min(espera * 2, 30.0)
    return resueltos


def leer_secretos(ruta_token: str, referencias: list[str], **kwargs) -> dict:
    """Contrato de `mercados` (config/connect.py, probado en producción): {referencia: valor | {campo: valor}}.

    Lee el token del Docker secret en `ruta_token` (falla si falta o está vacío), resuelve cada
    `op://<bóveda>/<ítem>/<campo>` (o `/*` para todos los campos del ítem) con reintento y backoff,
    y devuelve el resultado indexado por la referencia misma. Host por defecto
    `http://host.docker.internal:8080` (el nombre `op-connect` no resuelve desde red-comercial).
    """
    token = leer_token(ruta_token)
    if token is None:
        raise ArranqueError("Docker secret op_connect_token vacío o ausente")
    resueltos: dict = {}
    for ref in referencias:
        resueltos.update(_resolver(ref, token, **kwargs))
    return resueltos


def _resolver(ref: str, token: str, host: str | None = None, intentos: int = 5, espera_inicial: float = 1.0,
              dormir=time.sleep) -> dict:
    espera = espera_inicial
    for intento in range(1, intentos + 1):
        try:
            return {ref: resolve_op_reference(ref, token=token, host=host)}
        except ConnectError as exc:
            if intento == intentos:
                raise ArranqueError(f"No se pudo resolver {ref} desde 1Password Connect") from exc
            dormir(espera)
            espera = min(espera * 2, 30.0)
