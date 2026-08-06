"""HU-FAC-03 · Consulta de comprobantes emitidos por la tienda (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("c.pdf", b"%PDF fake", "application/pdf")}


def _confirmed(client, db, token_for, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))
    return seller, store, buyer, order


def test_listado_de_comprobantes_de_la_tienda(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _confirmed(client, db, token_for, "fac03a")
    resp = client.get("/api/v1/seller/invoices", headers=token_for(seller.id))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["order_id"] == order.id
    assert rows[0]["total"] == order.total


def test_descarga_por_el_vendedor(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _confirmed(client, db, token_for, "fac03b")
    invoice_id = client.get("/api/v1/seller/invoices", headers=token_for(seller.id)).json()[0]["id"]
    resp = client.get(f"/api/v1/seller/invoices/{invoice_id}/download", headers=token_for(seller.id))
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_filtro_por_estado(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _confirmed(client, db, token_for, "fac03c")
    resp = client.get("/api/v1/seller/invoices", params={"status": "cancelled"}, headers=token_for(seller.id))
    assert resp.status_code == 200
    assert resp.json() == []


def test_comprobante_de_otra_tienda_da_404(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller_a, store_a, buyer, order = _confirmed(client, db, token_for, "fac03d")
    invoice_id = client.get("/api/v1/seller/invoices", headers=token_for(seller_a.id)).json()[0]["id"]
    seller_b, _store_b, _p, _v, _w = seed_store(db, "fac03d-otra")
    resp = client.get(f"/api/v1/seller/invoices/{invoice_id}", headers=token_for(seller_b.id))
    assert resp.status_code == 404
