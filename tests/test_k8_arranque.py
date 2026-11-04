"""K8: arranque sin .env con Connect simulado."""

import logging
from unittest.mock import patch

import pytest

from comercial_kit import arranque
from comercial_kit.arranque import ArranqueError, cargar_secretos, leer_token
from comercial_kit.op_connect import ConnectError, clear_cache

REFS = {
    "DATABASE_URL": "op://IA/zbook_comercialdb_mercados/url",
    "DJANGO_SECRET_KEY": "op://IA/zbook_mercados_django/clave",
    "CLAVE_MAESTRA_CIFRADO": "op://IA/zbook_mercados_cifrado/clave_maestra",
}
VALORES = {
    REFS["DATABASE_URL"]: "postgres://u:p@h/db",
    REFS["DJANGO_SECRET_KEY"]: "django-xyz",
    REFS["CLAVE_MAESTRA_CIFRADO"]: "maestra-abc",
}


@pytest.fixture(autouse=True)
def _limpio():
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def secret(tmp_path):
    f = tmp_path / "op_connect_token"
    f.write_text("tok-secreto\n")
    return str(f)


def test_leer_token_ausente(tmp_path):
    assert leer_token(str(tmp_path / "no_existe")) is None


def test_leer_token_vacio(tmp_path):
    f = tmp_path / "t"
    f.write_text("  \n")
    assert leer_token(str(f)) is None


def test_leer_token_recorta(secret):
    assert leer_token(secret) == "tok-secreto"


def test_con_secret_resuelve_via_connect(secret):
    llamadas = []

    def falso(ref, token=None, host=None, **_):
        llamadas.append((token, host))
        return VALORES[ref]

    with patch.object(arranque, "resolve_op_reference", falso):
        out = cargar_secretos(REFS, ruta_secret=secret, host="http://connect:8080")
    assert out == {k: VALORES[v] for k, v in REFS.items()}
    assert llamadas == [("tok-secreto", "http://connect:8080")] * 3


def test_sin_secret_usa_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///x")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.delenv("CLAVE_MAESTRA_CIFRADO", raising=False)
    with patch.object(arranque, "resolve_op_reference") as r:
        out = cargar_secretos(REFS, ruta_secret=str(tmp_path / "nada"))
    r.assert_not_called()
    assert out == {"DATABASE_URL": "sqlite:///x"}


def test_reintenta_con_backoff_y_luego_resuelve(secret):
    estado = {"n": 0}
    esperas = []

    def falso(ref, **_):
        estado["n"] += 1
        if estado["n"] <= 2:
            raise ConnectError("caído")
        return "ok"

    with patch.object(arranque, "resolve_op_reference", falso):
        out = cargar_secretos({"DATABASE_URL": REFS["DATABASE_URL"]}, ruta_secret=secret,
                              dormir=esperas.append)
    assert out == {"DATABASE_URL": "ok"}
    assert esperas == [1.0, 2.0]


def test_agota_intentos_lanza_arranque_error_sin_filtrar_secretos(secret, caplog):
    with (
        patch.object(arranque, "resolve_op_reference", side_effect=ConnectError("caído")),
        caplog.at_level(logging.DEBUG, logger="comercial_kit.arranque"),
        pytest.raises(ArranqueError),
    ):
        cargar_secretos(REFS, ruta_secret=secret, intentos=3, dormir=lambda s: None)
    assert "tok-secreto" not in caplog.text
    assert "Arranque abortado" in caplog.text


def test_integracion_con_requests_simulado(secret):
    from unittest.mock import MagicMock

    def resp(data):
        m = MagicMock()
        m.json.return_value = data
        return m

    secuencia = [
        resp([{"id": "v1", "name": "IA"}]),
        resp([{"id": "i1", "title": "zbook_mercados_django"}]),
        resp({"fields": [{"id": "clave", "label": "clave", "value": "django-xyz"}]}),
    ]
    with patch("requests.get", side_effect=secuencia) as g:
        out = cargar_secretos({"DJANGO_SECRET_KEY": REFS["DJANGO_SECRET_KEY"]},
                              ruta_secret=secret, host="http://connect:8080/")
    assert out == {"DJANGO_SECRET_KEY": "django-xyz"}
    assert g.call_args_list[0].args[0] == "http://connect:8080/v1/vaults"
    assert g.call_args_list[0].kwargs["headers"]["Authorization"] == "Bearer tok-secreto"
