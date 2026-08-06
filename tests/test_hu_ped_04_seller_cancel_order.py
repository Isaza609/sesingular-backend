"""HU-PED-04 · Anulación de un pedido por el vendedor (API real)."""

from __future__ import annotations

import pytest

from app.models import InventoryMovement, Order
from app.models.inventory import InventoryReason
from app.models.order import OrderStatus
from tests.pag_test_utils import (
    reserved_units,
    seed_buyer,
    seed_manual_order,
    seed_payout_account,
    seed_store,
)

pytestmark = pytest.mark.integration


def _order(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, store, buyer, order, variant


def test_anular_libera_stock_y_registra_motivo(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, store, buyer, order, variant = _order(db, "ped04a")
    assert reserved_units(db, variant.id) == 2

    resp = client.post(f"/api/v1/seller/orders/{order.id}/cancel", json={"reason": "Sin pago"}, headers=token_for(seller.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    assert resp.json()["cancel_reason"] == "Sin pago"
    db.expire_all()
    assert reserved_units(db, variant.id) == 0
    assert any("cancelado" in c["subject"].lower() for c in mail_calls)


def test_movimiento_de_liberacion_registrado(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, variant = _order(db, "ped04b")
    client.post(f"/api/v1/seller/orders/{order.id}/cancel", json={"reason": "Sin pago"}, headers=token_for(seller.id))
    releases = db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order.id, InventoryMovement.reason == InventoryReason.release
    ).all()
    assert releases


def test_pedido_despachado_no_se_anula(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, variant = _order(db, "ped04c")
    # forzar estado despachado para probar la guarda
    db.get(Order, order.id).status = OrderStatus.shipped
    db.commit()
    resp = client.post(f"/api/v1/seller/orders/{order.id}/cancel", json={"reason": "tarde"}, headers=token_for(seller.id))
    assert resp.status_code == 409


def test_reason_obligatorio(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, variant = _order(db, "ped04d")
    resp = client.post(f"/api/v1/seller/orders/{order.id}/cancel", json={}, headers=token_for(seller.id))
    assert resp.status_code == 422
