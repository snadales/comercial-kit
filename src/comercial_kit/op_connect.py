"""Cliente 1Password Connect con caché en memoria para comercial-kit (K6)."""

import os
import re
import logging
import requests

logger = logging.getLogger("comercial_kit.op_connect")

_CACHE: dict[str, str] = {}
_OP_REGEX = re.compile(r"^op://([^/]+)/([^/]+)/(.+)$")


class ConnectError(Exception):
    """Error al comunicarse con 1Password Connect."""
    pass


def parse_op_reference(ref: str) -> tuple[str, str, str]:
    """Parsea una referencia tipo op://<vault>/<item>/<field>."""
    match = _OP_REGEX.match(ref.strip())
    if not match:
        raise ValueError(f"Formato op:// inválido: {ref}")
    return match.group(1), match.group(2), match.group(3)


def get_connect_config() -> tuple[str, str]:
    """Obtiene host y token de 1Password Connect."""
    token = os.environ.get("OP_CONNECT_TOKEN", "").strip()
    host = os.environ.get("OP_CONNECT_HOST", "http://192.168.60.25:8080").rstrip("/")
    return host, token


def clear_cache():
    """Limpia la caché en memoria (útil para tests)."""
    _CACHE.clear()


def set_mock_secret(ref: str, value: str):
    """Establece un secreto mock en caché para tests."""
    _CACHE[ref] = value


def resolve_op_reference(ref: str, use_cache: bool = True) -> str:
    """Resuelve una referencia op:// usando Connect API con caché en memoria.
    
    NUNCA imprime ni loguea el valor del secreto.
    """
    if not ref.startswith("op://"):
        return ref

    if use_cache and ref in _CACHE:
        return _CACHE[ref]

    vault_name, item_title, field_label = parse_op_reference(ref)
    host, token = get_connect_config()

    if not token:
        logger.warning("OP_CONNECT_TOKEN no configurado; no se puede resolver %s", ref)
        raise ConnectError("OP_CONNECT_TOKEN no disponible en entorno")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        # 1. Buscar bóveda por nombre o id
        vaults_resp = requests.get(f"{host}/v1/vaults", headers=headers, timeout=5)
        vaults_resp.raise_for_status()
        vaults = vaults_resp.json()
        vault_id = None
        for v in vaults:
            if v.get("name") == vault_name or v.get("id") == vault_name:
                vault_id = v.get("id")
                break
        if not vault_id:
            raise ConnectError(f"Bóveda '{vault_name}' no encontrada en 1Password Connect")

        # 2. Buscar item por título o id
        items_resp = requests.get(
            f"{host}/v1/vaults/{vault_id}/items",
            headers=headers,
            params={"filter": f'title eq "{item_title}"'},
            timeout=5,
        )
        items_resp.raise_for_status()
        items = items_resp.json()
        item_id = None
        for it in items:
            if it.get("title") == item_title or it.get("id") == item_title:
                item_id = it.get("id")
                break
        if not item_id:
            raise ConnectError(f"Item '{item_title}' no encontrado en bóveda '{vault_name}'")

        # 3. Obtener detalle del item y campo
        detail_resp = requests.get(f"{host}/v1/vaults/{vault_id}/items/{item_id}", headers=headers, timeout=5)
        detail_resp.raise_for_status()
        detail = detail_resp.json()

        value = None
        for f in detail.get("fields", []):
            if f.get("label") == field_label or f.get("id") == field_label:
                value = f.get("value")
                break

        if value is None:
            raise ConnectError(f"Campo '{field_label}' no encontrado en item '{item_title}'")

        _CACHE[ref] = value
        logger.debug("Secreto resuelto y almacenado en caché en memoria para ref")
        return value

    except requests.RequestException as e:
        logger.error("Fallo de red al consultar 1Password Connect: %s", str(e))
        raise ConnectError(f"Error de conexión con 1Password Connect: {e}") from e
