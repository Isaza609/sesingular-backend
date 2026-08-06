"""HU-PAG-05 · Flujo de pago manual: subir comprobante (API real)."""

from __future__ import annotations

import pytest

from app.models.payment import PaymentStatus
from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("comprobante.pdf", b"%PDF-1.4 fake", "application/pdf")}


def _scenario(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return buyer, store, order, payment, account


def test_estado_pendiente_sin_comprobante(integration_context):
    client, db, token_for, _mail = integration_context
    buyer, _store, order, _payment, _acc = _scenario(db, "05a")
    resp = client.get(f"/api/v1/orders/{order.id}/payment", headers=token_for(buyer.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["amount"] == order.total
    assert body["payout_account"] is not None


def test_subir_comprobante_deja_en_revision(integration_context):
    client, db, token_for, _mail = integration_context
    buyer, _store, order, payment, _acc = _scenario(db, "05b")
    resp = client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"
    assert resp.json()["has_receipt"] is True
    db.expire_all()
    from app.models import Payment
    assert db.get(Payment, payment.id).status == PaymentStatus.in_review


def test_reemplazo_tras_rechazo(integration_context):
    client, db, token_for, _mail = integration_context
    buyer, _store, order, payment, _acc = _scenario(db, "05c")
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    # el vendedor rechaza -> pago_rechazado; el comprador ya no puede resubir (pedido cancelado)
    # aquí probamos el reemplazo cuando sigue en revisión: subir de nuevo mantiene in_review
    resp = client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"


def test_pedido_ajeno_da_404(integration_context):
    client, db, token_for, _mail = integration_context
    buyer, _store, order, _payment, _acc = _scenario(db, "05d")
    otro = seed_buyer(db, "05d-otro")
    resp = client.get(f"/api/v1/orders/{order.id}/payment", headers=token_for(otro.id))
    assert resp.status_code == 404
