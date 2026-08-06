"""HU-ENV-06 · Gestión de devoluciones con reingreso a inventario (API real)."""

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


def _delivered_order(db, suffix):
    """Pedido con stock consumido en firme y estado entregado, listo para devolver."""
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, quantity=2, payout_account=account)
    # consumir en firme desde el almacen (como un despacho) y marcar entregado
    from app.modules.inventory.service import consume_reserved_order_from_warehouse
    consume_reserved_order_from_warehouse(db, order, warehouse.id)
    order.warehouse_id = warehouse.id
    order.status = OrderStatus.delivered
    db.commit()
    return seller, store, buyer, order, variant, warehouse


def test_devolucion_con_reingreso(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, variant, warehouse = _delivered_order(db, "env06a")
    resp = client.post(
        f"/api/v1/seller/orders/{order.id}/return",
        json={"restock": True, "reason": "Buen estado"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "returned"
    db.expire_all()
    returns = db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order.id, InventoryMovement.reason == InventoryReason.return_in
    ).all()
    assert returns


def test_devolucion_sin_reingreso(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, variant, warehouse = _delivered_order(db, "env06b")
    resp = client.post(
        f"/api/v1/seller/orders/{order.id}/return",
        json={"restock": False, "reason": "Producto dañado"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "returned"
    assert resp.json()["cancel_reason"] == "Producto dañado"
    db.expire_all()
    returns = db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order.id, InventoryMovement.reason == InventoryReason.return_in
    ).all()
    assert not returns  # dañado: no reintegra


def test_comprador_ve_estado_devuelto(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, variant, warehouse = _delivered_order(db, "env06c")
    client.post(f"/api/v1/seller/orders/{order.id}/return", json={"restock": True, "reason": "ok"}, headers=token_for(seller.id))
    body = client.get(f"/api/v1/orders/{order.id}", headers=token_for(buyer.id)).json()
    assert body["status"] == "returned"


def test_pedido_no_despachado_no_se_devuelve(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env06d")
    buyer = seed_buyer(db, "env06d")
    account = seed_payout_account(db, store)
    order, _payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)  # pending
    resp = client.post(f"/api/v1/seller/orders/{order.id}/return", json={"restock": True, "reason": "x"}, headers=token_for(seller.id))
    assert resp.status_code == 409
