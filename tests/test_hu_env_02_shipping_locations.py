"""HU-ENV-02 · Definición de lugares y precios de envío (API real, vía checkout/quote)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_store, set_store_shipping_config

pytestmark = pytest.mark.integration

BOGOTA = {"city": "Bogota", "region": "Cundinamarca", "country": "Colombia"}


def _quote(client, db, token_for, suffix, config, location):
    seller, store, product, variant, warehouse = seed_store(db, suffix)
    buyer = seed_buyer(db, suffix)
    set_store_shipping_config(db, store, config)
    client.post("/api/v1/cart/items", json={"variant_id": variant.id, "quantity": 1}, headers=token_for(buyer.id))
    resp = client.post("/api/v1/checkout/quote", json={"shipping_location": location}, headers=token_for(buyer.id))
    return resp


def test_precio_por_lugar_visible(real_db_context):
    client, db, token_for, _mail = real_db_context
    config = {"shipping_mode": "zones", "shipping_flat_cost": 0, "shipping_free_threshold": 0,
              "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True}]}
    resp = _quote(client, db, token_for, "env02a", config, BOGOTA)
    assert resp.status_code == 200, resp.text
    shipping = resp.json()["store_quotes"][0]["shipping"]
    assert shipping["cost"] == 12000
    assert shipping["to_agree"] is False


def test_lugar_no_configurado_pide_contacto(real_db_context):
    client, db, token_for, _mail = real_db_context
    config = {"shipping_mode": "zones", "shipping_flat_cost": 0, "shipping_free_threshold": 0,
              "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True}]}
    resp = _quote(client, db, token_for, "env02b", config, {"city": "Leticia", "region": "Amazonas", "country": "Colombia"})
    assert resp.status_code == 200
    shipping = resp.json()["store_quotes"][0]["shipping"]
    assert shipping["to_agree"] is True
