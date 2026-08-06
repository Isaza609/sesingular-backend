"""HU-FAC-01 · Emisión del comprobante de venta al comprador (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import (
    add_order_charge,
    seed_buyer,
    seed_manual_order,
    seed_payout_account,
    seed_store,
)

pytestmark = pytest.mark.integration

FILE = {"file": ("c.pdf", b"%PDF fake", "application/pdf")}


def _confirmed_order(client, db, token_for, suffix, *, with_charge=False):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    if with_charge:
        add_order_charge(db, order, "Empaque para regalo", 5000)
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))
    return seller, store, buyer, order


def test_comprobante_se_emite_al_confirmar_pago(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, buyer, order = _confirmed_order(client, db, token_for, "fac01a")
    resp = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(buyer.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_id"] == order.id
    assert body["status"] == "issued"
    assert body["total"] == order.total
    assert body["number"] >= 1


def test_cargos_extra_desglosados(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, buyer, order = _confirmed_order(client, db, token_for, "fac01b", with_charge=True)
    body = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(buyer.id)).json()
    names = [c["name"] for c in body["charges"]]
    assert "Empaque para regalo" in names
    assert body["extra_charge_total"] == 5000


def test_descarga_html(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, buyer, order = _confirmed_order(client, db, token_for, "fac01c")
    resp = client.get(f"/api/v1/orders/{order.id}/invoice/download", headers=token_for(buyer.id))
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Comprobante" in resp.text


def test_sin_pago_confirmado_no_hay_comprobante(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "fac01d")
    buyer = seed_buyer(db, "fac01d")
    account = seed_payout_account(db, store)
    order, _payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    resp = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(buyer.id))
    assert resp.status_code == 404


def test_comprobante_refleja_cancelacion(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order = _confirmed_order(client, db, token_for, "fac01e")
    # el pedido ya está confirmado (paid); el vendedor lo pasa a cancelado vía status
    client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "cancelled"}, headers=token_for(seller.id))
    body = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(buyer.id)).json()
    assert body["status"] == "cancelled"


def test_comprobante_de_otro_comprador_da_404(real_db_context):
    client, db, token_for, _mail = real_db_context
    _seller, _store, _buyer, order = _confirmed_order(client, db, token_for, "fac01f")
    otro = seed_buyer(db, "fac01f-otro")
    resp = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(otro.id))
    assert resp.status_code == 404
