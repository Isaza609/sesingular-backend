from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def test_hu_inv_02_checkout_reserves_aggregate_stock_and_blocks_second_buyer(api_context):
    client, db, _auth, token_for = api_context
    _seller, _store, _product, variant, warehouses, buyers = seed_inventory_store(db, "02", warehouses=2, quantity=1, buyer_count=2)
    buyer_one, address_one, cart_one = buyers[0]
    buyer_two, address_two, cart_two = buyers[1]
    add_cart_item(db, cart_one, variant, 2)
    add_cart_item(db, cart_two, variant, 1)

    first = client.post("/api/v1/checkout", headers=token_for(buyer_one.id), json={"address_id": address_one.id, "payment_method": "card"})
    second = client.post("/api/v1/checkout", headers=token_for(buyer_two.id), json={"address_id": address_two.id, "payment_method": "card"})

    db.refresh(warehouses[0].stock_levels[0])
    db.refresh(warehouses[1].stock_levels[0])
    assert first.status_code == 201
    assert first.json()["orders"][0]["warehouse_id"] is None
    assert sum(level.reserved for level in [warehouses[0].stock_levels[0], warehouses[1].stock_levels[0]]) == 2
    assert second.status_code == 409


def test_hu_inv_02_single_warehouse_checkout_discounts_immediately(api_context):
    client, db, _auth, token_for = api_context
    _seller, _store, _product, variant, warehouses, buyers = seed_inventory_store(db, "02-single", warehouses=1, quantity=3)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 2)

    checkout = client.post("/api/v1/checkout", headers=token_for(buyer.id), json={"address_id": address.id, "payment_method": "card"})

    db.refresh(warehouses[0].stock_levels[0])
    assert checkout.status_code == 201
    assert checkout.json()["orders"][0]["warehouse_id"] == warehouses[0].id
    assert warehouses[0].stock_levels[0].quantity == 1
    assert warehouses[0].stock_levels[0].reserved == 0
