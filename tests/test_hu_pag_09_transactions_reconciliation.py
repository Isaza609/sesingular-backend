"""HU-PAG-09 · Registro y conciliación de transacciones (admin, API real)."""

from __future__ import annotations

import pytest

from app.models import User
from app.models.user import UserRole
from tests.pag_test_utils import seed_buyer, seed_manual_order, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

FILE = {"file": ("comprobante.pdf", b"%PDF-1.4 fake", "application/pdf")}


def _seed_admin(db, suffix):
    admin = User(id=f"admin-pag-{suffix}", email=f"admin-pag-{suffix}@example.com", name="Admin", role=UserRole.admin)
    db.add(admin)
    db.commit()
    return admin


def _paid_scenario(client, db, token_for, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    client.post(f"/api/v1/orders/{order.id}/payment/receipt", files=FILE, headers=token_for(buyer.id))
    client.post(f"/api/v1/seller/payments/{payment.id}/confirm", json={"received_amount": order.total}, headers=token_for(seller.id))
    return seller, store, buyer, order, payment


def test_listado_de_transacciones_con_trazabilidad(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, payment = _paid_scenario(client, db, token_for, "09a")
    admin = _seed_admin(db, "09a")

    resp = client.get("/api/v1/admin/transactions", headers=token_for(admin.id))
    assert resp.status_code == 200
    body = resp.json()
    row = next(r for r in body["items"] if r["id"] == payment.id)
    assert row["order_id"] == order.id
    assert row["store_id"] == store.id
    assert row["method"] == "transfer"
    assert row["status"] == "paid"


def test_detalle_conserva_historial_de_estados(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, payment = _paid_scenario(client, db, token_for, "09b")
    admin = _seed_admin(db, "09b")

    resp = client.get(f"/api/v1/admin/transactions/{payment.id}", headers=token_for(admin.id))
    assert resp.status_code == 200
    states = [e["to_status"] for e in resp.json()["events"]]
    # nacimiento (pending) -> comprobante (in_review) -> pagado (paid)
    assert states[0] == "pending"
    assert "in_review" in states
    assert states[-1] == "paid"


def test_filtro_por_estado(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, payment = _paid_scenario(client, db, token_for, "09c")
    admin = _seed_admin(db, "09c")

    resp = client.get("/api/v1/admin/transactions", params={"status": "paid"}, headers=token_for(admin.id))
    assert resp.status_code == 200
    assert all(r["status"] == "paid" for r in resp.json()["items"])


def test_no_admin_no_puede_conciliar(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, buyer, order, payment = _paid_scenario(client, db, token_for, "09d")
    resp = client.get("/api/v1/admin/transactions", headers=token_for(buyer.id))
    assert resp.status_code == 403
