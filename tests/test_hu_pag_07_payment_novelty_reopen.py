"""HU-PAG-07 · Novedad y reapertura del pago por monto incorrecto (API real)."""

from __future__ import annotations

import pytest

from app.models import Order, Payment, PaymentEvent
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from tests.pag_test_utils import (
    reserved_units,
    seed_buyer,
    seed_manual_order,
    seed_payout_account,
    seed_store,
)

pytestmark = pytest.mark.integration

FILE = {"file": ("comprobante.pdf", b"%PDF-1.4 fake", "application/pdf")}


def _in_review(client, db, token_for, suffix, quantity=2):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, quantity=quantity, payout_account=account)
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    return seller, store, buyer, order, payment, variant


def test_reabrir_por_monto_de_menos_deja_incompleto(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment, variant = _in_review(client, db, token_for, "07a")
    reserved_before = reserved_units(db, variant.id)

    resp = client.post(
        f"/api/v1/seller/payments/{payment.id}/reopen",
        json={"received_amount": order.total - 20000, "note": "Faltan $20.000"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "incomplete"
    assert resp.json()["difference"] == 20000
    db.expire_all()
    assert db.get(Payment, payment.id).status == PaymentStatus.incomplete
    # HU-PAG-07: el stock sigue reservado; el pedido no se cancela.
    assert reserved_units(db, variant.id) == reserved_before
    assert db.get(Order, order.id).status == OrderStatus.pending


def test_reopen_con_monto_igual_o_mayor_da_400(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment, _variant = _in_review(client, db, token_for, "07b")
    resp = client.post(
        f"/api/v1/seller/payments/{payment.id}/reopen",
        json={"received_amount": order.total, "note": "igual"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 400


def test_comprador_sube_saldo_vuelve_a_revision(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment, _variant = _in_review(client, db, token_for, "07c")
    client.post(
        f"/api/v1/seller/payments/{payment.id}/reopen",
        json={"received_amount": order.total - 20000, "note": "Faltan $20.000"},
        headers=token_for(seller.id),
    )
    resp = client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"


def test_monto_de_mas_registra_acuerdo_y_contacto(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment, _variant = _in_review(client, db, token_for, "07d")
    resp = client.post(
        f"/api/v1/seller/payments/{payment.id}/overpaid",
        json={"received_amount": order.total + 30000, "note": "Acordamos devolver $30.000 por transferencia"},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "paid"
    assert body["agreement_note"]
    # Datos de contacto del comprador para acordar por fuera.
    assert body["buyer_email"] == buyer.email


def test_novedad_queda_en_historial(integration_context):
    client, db, token_for, _mail = integration_context
    seller, store, buyer, order, payment, _variant = _in_review(client, db, token_for, "07e")
    client.post(
        f"/api/v1/seller/payments/{payment.id}/reopen",
        json={"received_amount": order.total - 5000, "note": "Faltan $5.000"},
        headers=token_for(seller.id),
    )
    events = db.query(PaymentEvent).filter(PaymentEvent.payment_id == payment.id).all()
    to_states = [e.to_status for e in events]
    assert "incomplete" in to_states
    assert any(e.note and "5.000" in e.note for e in events)
