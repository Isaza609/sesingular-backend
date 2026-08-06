"""HU-PED-05 · Asignación manual del responsable de un pedido (API real)."""

from __future__ import annotations

import pytest

from app.models import OrderAssignmentEvent
from tests.pag_test_utils import (
    seed_buyer,
    seed_manual_order,
    seed_payout_account,
    seed_store,
    seed_store_member,
)

pytestmark = pytest.mark.integration


def _order(db, suffix):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    member = seed_store_member(db, store, suffix)
    buyer = seed_buyer(db, suffix)
    account = seed_payout_account(db, store)
    order, payment, _addr = seed_manual_order(db, store, buyer, variant, payout_account=account)
    return seller, member, store, buyer, order


def test_pedido_nuevo_sin_responsable(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, member, store, buyer, order = _order(db, "ped05a")
    body = client.get(f"/api/v1/seller/orders", headers=token_for(seller.id)).json()
    row = next(o for o in body if o["id"] == order.id)
    assert row["assignee_id"] is None


def test_asignar_y_reasignar_con_historial(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, member, store, buyer, order = _order(db, "ped05b")
    r = client.patch(f"/api/v1/seller/orders/{order.id}/assignee", json={"assignee_id": member.id}, headers=token_for(seller.id))
    assert r.status_code == 200
    assert r.json()["assignee_id"] == member.id
    assert r.json()["assigned_at"] is not None

    r = client.patch(f"/api/v1/seller/orders/{order.id}/assignee", json={"assignee_id": seller.id}, headers=token_for(member.id))
    assert r.status_code == 200
    assert r.json()["assignee_id"] == seller.id

    events = db.query(OrderAssignmentEvent).filter(OrderAssignmentEvent.order_id == order.id).all()
    assert len(events) == 2
    assert events[-1].from_user_id == member.id
    assert events[-1].to_user_id == seller.id


def test_filtro_por_responsable_y_sin_asignar(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, member, store, buyer, order = _order(db, "ped05c")
    # sin asignar
    unassigned = client.get("/api/v1/seller/orders", params={"assignee": "unassigned"}, headers=token_for(seller.id)).json()
    assert any(o["id"] == order.id for o in unassigned)
    # asignar y filtrar por responsable
    client.patch(f"/api/v1/seller/orders/{order.id}/assignee", json={"assignee_id": member.id}, headers=token_for(seller.id))
    mine = client.get("/api/v1/seller/orders", params={"assignee": member.id}, headers=token_for(seller.id)).json()
    assert any(o["id"] == order.id for o in mine)
    still_unassigned = client.get("/api/v1/seller/orders", params={"assignee": "unassigned"}, headers=token_for(seller.id)).json()
    assert all(o["id"] != order.id for o in still_unassigned)


def test_asignar_a_usuario_ajeno_da_400(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, member, store, buyer, order = _order(db, "ped05d")
    resp = client.patch(f"/api/v1/seller/orders/{order.id}/assignee", json={"assignee_id": buyer.id}, headers=token_for(seller.id))
    assert resp.status_code == 400


def test_otro_miembro_puede_actuar_pese_a_responsable(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, member, store, buyer, order = _order(db, "ped05e")
    client.patch(f"/api/v1/seller/orders/{order.id}/assignee", json={"assignee_id": member.id}, headers=token_for(seller.id))
    # el seller (no responsable) igual puede cambiar el estado del pedido
    r = client.patch(f"/api/v1/seller/orders/{order.id}/status", json={"status": "confirmed"}, headers=token_for(seller.id))
    assert r.status_code == 200
