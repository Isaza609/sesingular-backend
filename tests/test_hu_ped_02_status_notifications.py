"""HU-PED-02 · Notificaciones automáticas de cambio de estado (API real, correo mockeado)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration


def _order(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    # correo de contacto de tienda para notificar al vendedor al despachar
    store.contact_email = f"tienda-{suffix}@example.com"
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    db.commit()
    return seller, store, buyer, order, warehouse


def _subjects(mail_calls):
    return " || ".join(c["subject"] for c in mail_calls)


def test_cambio_de_estado_notifica_al_comprador(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, store, buyer, order, _wh = _order(db, "ped02a")
    mail_calls.clear()
    client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "confirmed"}, headers=token_for(seller.id))
    assert "confirmado" in _subjects(mail_calls)


def test_despacho_notifica_a_comprador_y_vendedor(integration_context):
    client, db, token_for, mail_calls = integration_context
    seller, store, buyer, order, warehouse = _order(db, "ped02b")
    # avanzar hasta preparing y asignar almacen antes de despachar
    client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "confirmed"}, headers=token_for(seller.id))
    client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "preparing"}, headers=token_for(seller.id))
    client.patch(f"/api/v1/seller/orders/{order.id}/warehouse", json={"warehouse_id": warehouse.id}, headers=token_for(seller.id))
    mail_calls.clear()
    r = client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "shipped"}, headers=token_for(seller.id))
    assert r.status_code == 200
    subjects = _subjects(mail_calls)
    # comprador (por 'enviado') y vendedor (correo a la tienda)
    assert "enviado" in subjects
    assert len(mail_calls) >= 2
