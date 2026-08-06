"""HU-PAG-03 y HU-PAG-04 · Cuentas de cobro manual del vendedor (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_store

pytestmark = pytest.mark.integration

BANK = {"type": "bank", "bank_name": "Bancolombia", "account_type": "ahorros", "account_number": "12345678901", "holder_name": "Nova Ropa SAS"}
BREB = {"type": "bre_b", "breb_key": "nova@breb", "holder_name": "Nova Ropa SAS"}


def _seller_headers(db, token_for, suffix):
    seller, store, _p, _v, _w = seed_store(db, suffix)
    return token_for(seller.id), store


# --- HU-PAG-03 -------------------------------------------------------------

def test_registrar_cuenta_bancaria(integration_context):
    client, db, token_for, _mail = integration_context
    headers, _store = _seller_headers(db, token_for, "03a")
    resp = client.post("/api/v1/seller/payout-accounts", json=BANK, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["type"] == "bank"
    assert resp.json()["active"] is True


def test_registrar_llave_breb(integration_context):
    client, db, token_for, _mail = integration_context
    headers, _store = _seller_headers(db, token_for, "03b")
    resp = client.post("/api/v1/seller/payout-accounts", json=BREB, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["breb_key"] == "nova@breb"


def test_cuenta_bancaria_incompleta_es_rechazada(integration_context):
    client, db, token_for, _mail = integration_context
    headers, _store = _seller_headers(db, token_for, "03c")
    resp = client.post("/api/v1/seller/payout-accounts", json={"type": "bank", "holder_name": "Nova"}, headers=headers)
    assert resp.status_code == 422


# --- HU-PAG-04 -------------------------------------------------------------

def test_desactivar_y_reactivar_cuenta(integration_context):
    client, db, token_for, _mail = integration_context
    headers, _store = _seller_headers(db, token_for, "04a")
    account_id = client.post("/api/v1/seller/payout-accounts", json=BANK, headers=headers).json()["id"]

    off = client.delete(f"/api/v1/seller/payout-accounts/{account_id}", headers=headers)
    assert off.status_code == 200 and off.json()["active"] is False

    on = client.patch(f"/api/v1/seller/payout-accounts/{account_id}", json={"active": True}, headers=headers)
    assert on.status_code == 200 and on.json()["active"] is True


def test_cuenta_de_otra_tienda_da_404(integration_context):
    client, db, token_for, _mail = integration_context
    headers_a, _store_a = _seller_headers(db, token_for, "04b")
    account_id = client.post("/api/v1/seller/payout-accounts", json=BANK, headers=headers_a).json()["id"]

    headers_b, _store_b = _seller_headers(db, token_for, "04c")
    resp = client.patch(f"/api/v1/seller/payout-accounts/{account_id}", json={"label": "hackeo"}, headers=headers_b)
    assert resp.status_code == 404
