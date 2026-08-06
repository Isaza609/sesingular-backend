"""HU-ENV-03 · Envío a convenir con contacto directo al vendedor (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration


def test_detalle_pedido_muestra_contacto_a_convenir(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env03a")
    product.shipping_mode = "to_agree"
    buyer = seed_buyer(db, "env03a")
    account = seed_payout_account(db, store)
    order, _payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)  # shipping_cost 0
    db.commit()

    body = client.get(f"/api/v1/orders/{order.id}", headers=token_for(buyer.id)).json()
    assert body["shipping_to_agree"] is True
    assert body["store_contact"]["email"] == store.contact_email
    assert body["store_contact"]["whatsapp_phone"] == store.whatsapp_phone


def test_pedido_normal_no_es_a_convenir(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env03b")
    buyer = seed_buyer(db, "env03b")
    account = seed_payout_account(db, store)
    order, _payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    # sin override y sin marca a convenir por producto
    body = client.get(f"/api/v1/orders/{order.id}", headers=token_for(buyer.id)).json()
    assert body["shipping_to_agree"] is False
