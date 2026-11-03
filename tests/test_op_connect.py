"""Pruebas exhaustivas para op_connect.py."""

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
import requests
from comercial_kit.op_connect import (
    parse_op_reference,
    resolve_op_reference,
    clear_cache,
    ConnectError,
    set_mock_secret,
)


class TestOpConnect(SimpleTestCase):
    def tearDown(self):
        clear_cache()

    def test_parse_op_reference_valida(self):
        v, i, f = parse_op_reference("op://IA/mi_item/mi_campo")
        self.assertEqual(v, "IA")
        self.assertEqual(i, "mi_item")
        self.assertEqual(f, "mi_campo")

    def test_parse_op_reference_invalida(self):
        with self.assertRaises(ValueError):
            parse_op_reference("invalido://algo")

    def test_resolve_sin_op_prefijo(self):
        self.assertEqual(resolve_op_reference("texto_plano"), "texto_plano")

    def test_resolve_sin_token_lanza_connect_error(self):
        with patch.dict("os.environ", {"OP_CONNECT_TOKEN": ""}):
            with self.assertRaises(ConnectError):
                resolve_op_reference("op://IA/item/campo", use_cache=False)

    @patch("requests.get")
    def test_resolve_exitoso_con_connect_api(self, mock_get):
        # 1. /v1/vaults
        resp_vaults = MagicMock()
        resp_vaults.json.return_value = [{"id": "vault-1", "name": "IA"}]
        resp_vaults.raise_for_status = MagicMock()

        # 2. /v1/vaults/vault-1/items
        resp_items = MagicMock()
        resp_items.json.return_value = [{"id": "item-1", "title": "zbook_token"}]
        resp_items.raise_for_status = MagicMock()

        # 3. /v1/vaults/vault-1/items/item-1
        resp_detail = MagicMock()
        resp_detail.json.return_value = {
            "fields": [{"id": "credential", "label": "credential", "value": "super-secreto-resuelto"}]
        }
        resp_detail.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_vaults, resp_items, resp_detail]

        with patch.dict("os.environ", {"OP_CONNECT_TOKEN": "token-test"}):
            val = resolve_op_reference("op://IA/zbook_token/credential", use_cache=False)
            self.assertEqual(val, "super-secreto-resuelto")

    @patch("requests.get")
    def test_resolve_boveda_no_encontrada(self, mock_get):
        resp_vaults = MagicMock()
        resp_vaults.json.return_value = []
        resp_vaults.raise_for_status = MagicMock()
        mock_get.return_value = resp_vaults

        with patch.dict("os.environ", {"OP_CONNECT_TOKEN": "token-test"}):
            with self.assertRaises(ConnectError):
                resolve_op_reference("op://BovedaInexistente/item/campo", use_cache=False)

    @patch("requests.get")
    def test_resolve_error_red_connect(self, mock_get):
        mock_get.side_effect = requests.RequestException("Conexión rechazada")
        with patch.dict("os.environ", {"OP_CONNECT_TOKEN": "token-test"}):
            with self.assertRaises(ConnectError):
                resolve_op_reference("op://IA/item/campo", use_cache=False)
