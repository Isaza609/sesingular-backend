"""HU-PAG-01 · Selección del método de pago en el checkout (API real)."""

from __future__ import annotations

import pytest

from app.models.payout import PayoutAccountType
from tests.pag_test_utils import ensure_gateway, seed_payout_account, seed_store

pytestmark = pytest.mark.integration

BASE = "/api/v1/catalog/stores"


def test_pasarela_y_manual_muestran_ambas_opciones(real_db_context):
    client, db, _token_for, _mail = real_db_context
    _seller, store, _p, _v, _w = seed_store(db, "01a")
    ensure_gateway(db)
    seed_payout_account(db, store, type_=PayoutAccountType.bank)
    db.commit()

    resp = client.get(f"{BASE}/{store.id}/payment-options")
    assert resp.status_code == 200
    body = resp.json()
    assert "transfer" in body["payment_methods"]
    # La pasarela aporta al menos un método automatizado.
    assert len(body["payment_methods"]) >= 2


def test_seleccionar_manual_lista_cuentas_activas(real_db_context):
    client, db, _token_for, _mail = real_db_context
    _seller, store, _p, _v, _w = seed_store(db, "01b", payment_methods={"gateway_enabled": False, "manual_transfer_enabled": True, "manual_breb_enabled": False})
    seed_payout_account(db, store, type_=PayoutAccountType.bank)
    db.commit()

    body = client.get(f"{BASE}/{store.id}/payment-options").json()
    assert body["payment_methods"] == ["transfer"]
    assert len(body["payout_accounts"]) == 1
    assert body["payout_accounts"][0]["type"] == "bank"


def test_un_solo_metodo_habilitado(real_db_context):
    client, db, _token_for, _mail = real_db_context
    _seller, store, _p, _v, _w = seed_store(db, "01c", payment_methods={"gateway_enabled": False, "manual_transfer_enabled": False, "manual_breb_enabled": True})
    seed_payout_account(db, store, type_=PayoutAccountType.bre_b)
    db.commit()

    body = client.get(f"{BASE}/{store.id}/payment-options").json()
    assert body["payment_methods"] == ["breb"]


def test_metodo_deshabilitado_no_aparece(real_db_context):
    client, db, _token_for, _mail = real_db_context
    _seller, store, _p, _v, _w = seed_store(db, "01d", payment_methods={"gateway_enabled": False, "manual_transfer_enabled": True, "manual_breb_enabled": False})
    # Cuenta Bre-B existe pero el método Bre-B está deshabilitado: no debe aparecer.
    seed_payout_account(db, store, type_=PayoutAccountType.bre_b)
    seed_payout_account(db, store, type_=PayoutAccountType.bank)
    db.commit()

    body = client.get(f"{BASE}/{store.id}/payment-options").json()
    assert "breb" not in body["payment_methods"]
    assert "transfer" in body["payment_methods"]
