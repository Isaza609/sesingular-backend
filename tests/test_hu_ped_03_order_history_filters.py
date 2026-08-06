"""HU-PED-03 · Historial de pedidos por usuario y por tienda con filtros (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration


def _order(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, store, buyer, order


def test_comprador_ve_su_historial(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, buyer, order = _order(db, "ped03a")
    rows = client.get("/api/v1/orders", headers=token_for(buyer.id)).json()
    assert any(o["id"] == order.id for o in rows)


def test_vendedor_ve_solo_su_tienda(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller_a, store_a, buyer_a, order_a = _order(db, "ped03b")
    seller_b, store_b, buyer_b, order_b = _order(db, "ped03b2")
    rows = client.get("/api/v1/seller/orders", headers=token_for(seller_a.id)).json()
    ids = {o["id"] for o in rows}
    assert order_a.id in ids
    assert order_b.id not in ids


def test_filtro_por_estado(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _order(db, "ped03c")
    rows = client.get("/api/v1/seller/orders", params={"status": "cancelled"}, headers=token_for(seller.id)).json()
    assert rows == []
    rows = client.get("/api/v1/seller/orders", params={"status": "pending"}, headers=token_for(seller.id)).json()
    assert any(o["id"] == order.id for o in rows)


def test_filtro_por_fecha_futura_vacia(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _order(db, "ped03d")
    rows = client.get("/api/v1/seller/orders", params={"date_from": "2099-01-01"}, headers=token_for(seller.id)).json()
    assert rows == []
