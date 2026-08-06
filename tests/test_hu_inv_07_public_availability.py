from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def test_hu_inv_07_public_catalog_and_cart_use_available_stock(api_context):
    client, db, _auth, token_for = api_context
    _seller, _store, product, variant, _warehouses, buyers = seed_inventory_store(db, "07", warehouses=2, quantity=2)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 3)
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )

    products = client.get("/api/v1/catalog/products")
    detail = client.get(f"/api/v1/catalog/products/{product.slug}")
    stock = client.get(f"/api/v1/catalog/variants/{variant.id}/stock")
    excessive_cart = client.post(
        "/api/v1/cart/items",
        headers=token_for(buyer.id),
        json={"variant_id": variant.id, "quantity": 2},
    )

    assert checkout.status_code == 201
    listed = next(item for item in products.json()["items"] if item["id"] == product.id)
    assert listed["stock"] == 1
    assert detail.json()["stock"] == 1
    assert stock.json()["variant_id"] == variant.id
    assert stock.json()["stock"] == 1
    assert stock.json()["available"] is True
    assert excessive_cart.status_code == 409
