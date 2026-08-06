"""HU-PAG-06 · Revisión y confirmación/rechazo del comprobante por el vendedor (API real)."""

from __future__ import annotations

import pytest

from app.models import Order, Payment
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("comprobante.pdf", b"%PDF-1.4 fake", "application/pdf")}


def _in_review(client, db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, store, buyer, order, payment


def test_bandeja_muestra_pendientes(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment = _in_review(client, db, "06a")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))

    resp = client.get("/api/v1/seller/payments", headers=token_for(seller.id))
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]
    assert payment.id in ids


def test_confirmar_marca_pagado(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment = _in_review(client, db, "06b")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))

    resp = client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"
    db.expire_all()
    assert db.get(Payment, payment.id).status == PaymentStatus.paid
    assert db.get(Order, order.id).status == OrderStatus.confirmed


def test_rechazar_libera_stock_y_cancela(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment = _in_review(client, db, "06c")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))

    resp = client.post(f"/api/v1/seller/payments/{payment.id}/reject", json={"note": "No corresponde"}, headers=token_for(seller.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    db.expire_all()
    assert db.get(Order, order.id).status == OrderStatus.cancelled


def test_revisar_dos_veces_da_409(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment = _in_review(client, db, "06d")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))

    again = client.post(f"/api/v1/seller/payments/{payment.id}/reject", json={"note": "tarde"}, headers=token_for(seller.id))
    assert again.status_code == 409


def test_pago_de_otra_tienda_da_404(integration_context):
    client, db, token_for, _mail = integration_context
    seller_a, store_a, buyer, order, payment = _in_review(client, db, "06e")
    seller_b, _store_b, _p2, _v2, _w2 = seed_store(db, "06e-otra")
    resp = client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": 1}, headers=token_for(seller_b.id))
    assert resp.status_code == 404
