from app.models import CartItem, InventoryMovement, Order, Payment, StockLevel

from tests.checkout_test_utils import add_cart_item, seed_checkout_store


def test_hu_chk_03_checkout_with_stock_creates_order_and_inventory_movement(api_context):
    client, db, _auth, token_for = api_context
    _seller, buyer, _store, _product, variant, address, cart, _warehouses = seed_checkout_store(db, "03", quantity=3)
    add_cart_item(db, cart, variant, 1)

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )

    assert checkout.status_code == 201
    assert checkout.json()["orders"][0]["checkout_group_id"] == checkout.json()["purchase_id"]
    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 1
    assert db.query(InventoryMovement).count() == 1


def test_hu_chk_03_stock_failure_is_atomic_and_keeps_cart(api_context):
    client, db, _auth, token_for = api_context
    _seller_a, buyer, _store_a, _product_a, variant_a, address, cart, _wh_a = seed_checkout_store(db, "03a", quantity=5)
    _seller_b, _buyer, _store_b, _product_b, variant_b, _addr_b, cart, _wh_b = seed_checkout_store(db, "03b", buyer=buyer, cart=cart, quantity=0)
    add_cart_item(db, cart, variant_a, 1)
    add_cart_item(db, cart, variant_b, 1)

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )

    assert checkout.status_code == 409
    assert db.query(Order).count() == 0
    assert db.query(Payment).count() == 0
    assert db.query(InventoryMovement).count() == 0
    assert db.query(CartItem).count() == 2
    assert db.query(StockLevel).filter(StockLevel.variant_id == variant_a.id).one().quantity == 5
