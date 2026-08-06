from app.models import ExtraCharge
from app.models.promotion import ChargeType, PromotionScope

from tests.checkout_test_utils import add_cart_item, seed_checkout_store


def test_hu_chk_02_quote_uses_shipping_zone_and_separate_extra_charges(api_context):
    client, db, _auth, token_for = api_context
    shipping = {
        "shipping_mode": "zones",
        "shipping_flat_cost": 20000,
        "shipping_free_threshold": 0,
        "shipping_zones": [{"city": "Bogota", "region": "Cundinamarca", "cost": 12000, "active": True}],
    }
    _seller, buyer, store, _product, variant, address, cart, _warehouses = seed_checkout_store(db, "02", price=100000, shipping_config=shipping)
    add_cart_item(db, cart, variant, 1)
    db.add_all(
        [
            ExtraCharge(store_id=store.id, name="Empaque regalo", charge_type=ChargeType.fixed, value=5000, scope=PromotionScope.store, product_ids=[], active=True),
            ExtraCharge(store_id=store.id, name="Seguro", charge_type=ChargeType.fixed, value=3000, scope=PromotionScope.store, product_ids=[], active=True),
        ]
    )
    db.commit()

    quote = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={"address_id": address.id})

    assert quote.status_code == 200
    body = quote.json()
    assert body["shipping_cost"] == 12000
    assert body["extra_charge_total"] == 8000
    assert [line["name"] for line in body["extra_charges"]] == ["Empaque regalo", "Seguro"]
    assert body["total"] == 120000
    assert body["store_quotes"][0]["shipping"]["label"] == "Bogota"


def test_hu_chk_02_quote_handles_to_agree_unconfigured_zone_and_free_shipping(api_context):
    client, db, _auth, token_for = api_context
    to_agree = {"shipping_mode": "to_agree", "shipping_flat_cost": 0, "shipping_free_threshold": 0, "shipping_zones": []}
    _seller_a, buyer, _store_a, _product_a, variant_a, address_a, cart, _warehouses_a = seed_checkout_store(db, "02a", price=40000, shipping_config=to_agree)
    add_cart_item(db, cart, variant_a, 1)

    free_zone = {
        "shipping_mode": "zones",
        "shipping_flat_cost": 15000,
        "shipping_free_threshold": 0,
        "shipping_zones": [{"city": "Bogota", "cost": 10000, "free_shipping": True, "active": True}],
    }
    _seller_b, _buyer, _store_b, _product_b, variant_b, _address_b, cart, _warehouses_b = seed_checkout_store(
        db, "02b", buyer=buyer, cart=cart, price=20000, shipping_config=free_zone
    )
    add_cart_item(db, cart, variant_b, 1)

    quote = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={"address_id": address_a.id})

    assert quote.status_code == 200
    quotes = {row["store_id"]: row for row in quote.json()["store_quotes"]}
    assert len(quotes) == 2
    assert any(row["shipping"]["to_agree"] for row in quotes.values())
    assert any(row["shipping"]["promotion_applied"] for row in quotes.values())
    assert quote.json()["shipping_cost"] == 0
