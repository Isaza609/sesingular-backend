"""HU-PAG-08 · Notificaciones del estado de pago manual (API real, correo mockeado)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("comprobante.pdf", b"%PDF-1.4 fake", "application/pdf")}


def _scenario(client, db, token_for, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, buyer, order, payment


def _subjects(mail_calls):
    return " || ".join(call["subject"] for call in mail_calls)


def test_subida_notifica_a_comprador_y_vendedor(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, buyer, order, payment = _scenario(client, db, token_for, "08a")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    subjects = _subjects(mail_calls)
    assert "Recibimos tu comprobante" in subjects  # al comprador
    assert "Nuevo comprobante por revisar" in subjects  # al vendedor


def test_confirmacion_notifica_al_comprador(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, buyer, order, payment = _scenario(client, db, token_for, "08b")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    mail_calls.clear()
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))
    assert "Pago confirmado" in _subjects(mail_calls)


def test_incompleto_notifica_al_comprador(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, buyer, order, payment = _scenario(client, db, token_for, "08c")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    mail_calls.clear()
    client.post(f"/api/v1/seller/payments/{payment.id}/reopen", json={"received_amount": order.total - 10000, "note": "Faltan $10.000"}, headers=token_for(seller.id))
    assert "Falta completar tu pago" in _subjects(mail_calls)


def test_rechazo_notifica_al_comprador(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, buyer, order, payment = _scenario(client, db, token_for, "08d")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    mail_calls.clear()
    client.post(f"/api/v1/seller/payments/{payment.id}/reject", json={"note": "No corresponde"}, headers=token_for(seller.id))
    assert "No pudimos verificar tu pago" in _subjects(mail_calls)
