"""HU-PAG-02 · Pago mediante pasarela automatizada y webhook (API real)."""

from __future__ import annotations

import pytest

from app.models import Payment
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from tests.pag_test_utils import ensure_gateway, seed_buyer, seed_manual_order, seed_store

pytestmark = pytest.mark.integration


def _setup(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, method="card")
    payment.provider = "pending"
    db.commit()
    return buyer, store, order, payment


def test_intent_crea_transaccion(real_db_context):
    client, db, token_for, _mail = real_db_context
    ensure_gateway(db)
    buyer, _store, order, _payment = _setup(db, "02a")

    resp = client.post(f"/api/v1/payments/orders/{order.id}/intent", headers=token_for(buyer.id))
    assert resp.status_code == 201
    assert resp.json()["provider"] == "test"


def test_webhook_aprobado_confirma_pedido(real_db_context):
    client, db, token_for, _mail = real_db_context
    ensure_gateway(db)
    buyer, _store, order, payment = _setup(db, "02b")
    payment.provider = "test"
    db.commit()

    resp = client.post("/api/v1/payments/webhooks/test", json={"order_id": order.id, "status": "approved"})
    assert resp.status_code == 200
    db.expire_all()
    assert db.get(Payment, payment.id).status == PaymentStatus.paid
    from app.models import Order
    assert db.get(Order, order.id).status == OrderStatus.confirmed


def test_webhook_rechazado_cancela_y_repone(real_db_context):
    client, db, token_for, _mail = real_db_context
    ensure_gateway(db)
    buyer, _store, order, payment = _setup(db, "02c")
    payment.provider = "test"
    db.commit()

    resp = client.post("/api/v1/payments/webhooks/test", json={"order_id": order.id, "status": "rejected"})
    assert resp.status_code == 200
    db.expire_all()
    assert db.get(Payment, payment.id).status == PaymentStatus.rejected
    from app.models import Order
    assert db.get(Order, order.id).status == OrderStatus.cancelled


def test_webhook_firma_invalida_no_cambia_estado(real_db_context):
    client, db, token_for, _mail = real_db_context
    ensure_gateway(db, webhook_secret="s3cr3t")
    buyer, _store, order, payment = _setup(db, "02d")
    payment.provider = "test"
    db.commit()

    resp = client.post("/api/v1/payments/webhooks/test", json={"order_id": order.id, "status": "approved"}, headers={"x-webhook-secret": "mala"})
    assert resp.status_code == 401
    db.expire_all()
    assert db.get(Payment, payment.id).status == PaymentStatus.pending


def test_webhook_estado_no_soportado(real_db_context):
    client, db, token_for, _mail = real_db_context
    ensure_gateway(db)
    buyer, _store, order, payment = _setup(db, "02e")
    payment.provider = "test"
    db.commit()

    resp = client.post("/api/v1/payments/webhooks/test", json={"order_id": order.id, "status": "explota"})
    assert resp.status_code == 400
