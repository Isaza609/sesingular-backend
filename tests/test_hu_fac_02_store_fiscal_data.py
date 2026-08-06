"""HU-FAC-02 · Datos de facturación del vendedor en el comprobante (API real)."""

from __future__ import annotations

import pytest

from app.models import User
from app.models.user import UserRole
from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("c.pdf", b"%PDF fake", "application/pdf")}


def _admin(db, suffix):
    admin = User(id=f"admin-fac-{suffix}", email=f"admin-fac-{suffix}@example.com", name="Admin", role=UserRole.admin)
    db.add(admin)
    db.commit()
    return admin


def _confirm(client, token_for, seller, buyer, order, payment):
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))


def test_admin_registra_fiscal_y_aparece_en_comprobante(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "fac02a")
    buyer = seed_buyer(db, "fac02a")
    admin = _admin(db, "fac02a")

    r = client.patch(f"/api/v1/admin/stores/{store.id}", json={"legal_name": "Nova Ropa SAS", "tax_id": "900123456-7"}, headers=token_for(admin.id))
    assert r.status_code == 200

    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    _confirm(client, token_for, seller, buyer, order, payment)

    body = client.get(f"/api/v1/orders/{order.id}/invoice", headers=token_for(buyer.id)).json()
    assert body["store_fiscal"]["legal_name"] == "Nova Ropa SAS"
    assert body["store_fiscal"]["tax_id"] == "900123456-7"


def test_vendedor_consulta_sus_datos_fiscales(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "fac02b")
    admin = _admin(db, "fac02b")
    client.patch(f"/api/v1/admin/stores/{store.id}", json={"legal_name": "Nova SAS", "tax_id": "111"}, headers=token_for(admin.id))

    resp = client.get("/api/v1/seller/store", headers=token_for(seller.id))
    assert resp.status_code == 200
    assert resp.json()["legal_name"] == "Nova SAS"
    assert resp.json()["tax_id"] == "111"


def test_correccion_aplica_solo_a_comprobantes_nuevos(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "fac02c")
    buyer = seed_buyer(db, "fac02c")
    admin = _admin(db, "fac02c")
    client.patch(f"/api/v1/admin/stores/{store.id}", json={"legal_name": "Nombre Viejo"}, headers=token_for(admin.id))

    account = seed_payout_account(db, store)
    order1, payment1, _a1 = seed_manual_order(db, store, buyer, variant, quantity=1, payout_account=account)
    _confirm(client, token_for, seller, buyer, order1, payment1)

    # corrección posterior
    client.patch(f"/api/v1/admin/stores/{store.id}", json={"legal_name": "Nombre Nuevo"}, headers=token_for(admin.id))
    order2, payment2, _a2 = seed_manual_order(db, store, buyer, variant, quantity=1, payout_account=account)
    _confirm(client, token_for, seller, buyer, order2, payment2)

    inv1 = client.get(f"/api/v1/orders/{order1.id}/invoice", headers=token_for(buyer.id)).json()
    inv2 = client.get(f"/api/v1/orders/{order2.id}/invoice", headers=token_for(buyer.id)).json()
    assert inv1["store_fiscal"]["legal_name"] == "Nombre Viejo"
    assert inv2["store_fiscal"]["legal_name"] == "Nombre Nuevo"
