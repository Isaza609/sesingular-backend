"""HU-PED-01 · Seguimiento de estados del pedido (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration


def _order(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, store, buyer, order, payment


def test_estado_pedido_y_pago_separados(integration_context):
    client, db, token_for, _mail = integration_context
    _seller, _store, buyer, order, _payment = _order(db, "ped01a")
    body = client.get(f"/api/v1/orders/{order.id}", headers=token_for(buyer.id)).json()
    assert body["status"] == "pending"  # estado del pedido
    assert body["payments"][0]["status"] == "pending"  # estado del pago, separado


def test_actualizacion_refleja_para_comprador(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, _payment = _order(db, "ped01b")
    r = client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "confirmed"}, headers=token_for(seller.id))
    assert r.status_code == 200
    body = client.get(f"/api/v1/orders/{order.id}", headers=token_for(buyer.id)).json()
    assert body["status"] == "confirmed"


def test_transicion_invalida_da_409(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, _payment = _order(db, "ped01c")
    # pending -> delivered no es una transición permitida
    r = client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "delivered"}, headers=token_for(seller.id))
    assert r.status_code == 409
