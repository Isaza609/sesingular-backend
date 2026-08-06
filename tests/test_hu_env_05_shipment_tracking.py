"""HU-ENV-05 · Actualización manual del estado de envío y seguimiento (API real)."""

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


def test_sin_actualizaciones_estado_inicial(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, buyer, order = _order(db, "env05a")
    resp = client.get(f"/api/v1/orders/{order.id}/shipment", headers=token_for(buyer.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["events"] == []


def test_actualizacion_notifica_y_agrega_evento(real_db_context):
    client, db, token_for, mail_calls = real_db_context
    seller, store, buyer, order = _order(db, "env05b")
    mail_calls.clear()
    resp = client.patch(
        f"/api/v1/seller/orders/{order.id}/shipment",
        json={"status": "shipped", "note": "Entregado a mensajero"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "shipped"
    assert body["note"] == "Entregado a mensajero"
    assert body["events"][-1]["status"] == "shipped"
    assert any("despachado" in c["subject"].lower() or "shipped" in c["subject"].lower() for c in mail_calls)


def test_timeline_solo_lectura_para_comprador(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _order(db, "env05c")
    client.patch(f"/api/v1/seller/orders/{order.id}/shipment", json={"status": "preparing"}, headers=token_for(seller.id))
    client.patch(f"/api/v1/seller/orders/{order.id}/shipment", json={"status": "shipped", "note": "guia ABC"}, headers=token_for(seller.id))
    body = client.get(f"/api/v1/orders/{order.id}/shipment", headers=token_for(buyer.id)).json()
    statuses = [e["status"] for e in body["events"]]
    assert statuses == ["preparing", "shipped"]
    assert any(e["note"] == "guia ABC" for e in body["events"])


def test_envio_de_otra_tienda_da_404(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller_a, store_a, buyer, order = _order(db, "env05d")
    seller_b, _store_b, _p, _v, _w = seed_store(db, "env05d-otra")
    resp = client.patch(f"/api/v1/seller/orders/{order.id}/shipment", json={"status": "shipped"}, headers=token_for(seller_b.id))
    assert resp.status_code == 404
