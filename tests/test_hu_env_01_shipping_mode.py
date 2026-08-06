"""HU-ENV-01 · Modalidad de envío de la tienda con override por producto (API real)."""

from __future__ import annotations

import pytest

from tests.pag_test_utils import seed_buyer, seed_store, set_store_shipping_config

pytestmark = pytest.mark.integration


def test_tarifas_propias_por_zonas_exige_lugar(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env01a")
    resp = client.put(
        "/api/v1/seller/store/settings",
        json={"shipping_mode": "zones", "shipping_zones": []},
        headers=token_for(seller.id),
    )
    assert resp.status_code == 400


def test_override_producto_a_convenir_en_ficha(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env01b")
    set_store_shipping_config(db, store, {"shipping_mode": "zones", "shipping_flat_cost": 12000,
                                          "shipping_zones": [{"city": "Bogota", "cost": 12000, "active": True}]})
    product.shipping_mode = "to_agree"
    db.commit()
    resp = client.get(f"/api/v1/catalog/products/{product.slug}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["shipping"]["to_agree"] is True
    assert resp.json()["shipping_mode"] == "to_agree"


def test_override_producto_fuerza_a_convenir_en_quote(real_db_context):
    client, db, token_for, _mail = real_db_context
    seller, store, product, variant, warehouse = seed_store(db, "env01c")
    set_store_shipping_config(db, store, {"shipping_mode": "zones", "shipping_flat_cost": 0,
                                          "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True}]})
    product.shipping_mode = "to_agree"
    db.commit()
    buyer = seed_buyer(db, "env01c")
    client.post("/api/v1/cart/items", json={"variant_id": variant.id, "quantity": 1}, headers=token_for(buyer.id))
    resp = client.post("/api/v1/checkout/quote", json={"shipping_location": {"city": "Bogota", "region": "Cundinamarca"}}, headers=token_for(buyer.id))
    assert resp.status_code == 200
    assert resp.json()["store_quotes"][0]["shipping"]["to_agree"] is True
