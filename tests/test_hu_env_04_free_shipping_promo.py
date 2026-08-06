"""HU-ENV-04 · Promoción de envío gratis por lugar con vigencia (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_store, set_store_shipping_config

pytestmark = pytest.mark.integration

BOGOTA = {"city": "Bogota", "region": "Cundinamarca", "country": "Colombia"}


def _quote(client, db, token_for, suffix, config, quantity=1):
    seller, store, product, variant, warehouse = seed_store(db, suffix)  # variant price 50000
    buyer = seed_buyer(db, suffix)
    set_store_shipping_config(db, store, config)
    client.post("/api/v1/cart/items", json={"variant_id": variant.id, "quantity": quantity}, headers=token_for(buyer.id))
    return client.post("/api/v1/checkout/quote", json={"shipping_location": BOGOTA}, headers=token_for(buyer.id))


def test_envio_gratis_por_zona_vigente(real_db_context):
    client, db, token_for, _mail = real_db_context
    config = {"shipping_mode": "zones", "shipping_flat_cost": 0, "shipping_free_threshold": 0,
              "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True, "free_shipping": True}]}
    resp = _quote(client, db, token_for, "env04a", config)
    shipping = resp.json()["store_quotes"][0]["shipping"]
    assert shipping["cost"] == 0
    assert shipping["promotion_applied"] is True


def test_envio_gratis_fuera_de_vigencia_cobra(real_db_context):
    client, db, token_for, _mail = real_db_context
    config = {"shipping_mode": "zones", "shipping_flat_cost": 0, "shipping_free_threshold": 0,
              "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True,
                                   "free_shipping": True, "free_shipping_from": "2000-01-01", "free_shipping_to": "2000-12-31"}]}
    resp = _quote(client, db, token_for, "env04b", config)
    shipping = resp.json()["store_quotes"][0]["shipping"]
    assert shipping["cost"] == 12000
    assert shipping["promotion_applied"] is False


def test_umbral_no_alcanzado_cobra(real_db_context):
    client, db, token_for, _mail = real_db_context
    config = {"shipping_mode": "zones", "shipping_flat_cost": 0, "shipping_free_threshold": 1000000,
              "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True}]}
    resp = _quote(client, db, token_for, "env04c", config, quantity=1)
    shipping = resp.json()["store_quotes"][0]["shipping"]
    assert shipping["cost"] == 12000
    assert shipping["promotion_applied"] is False
