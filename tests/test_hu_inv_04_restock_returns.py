from app.models import InventoryMovement, Order
from app.models.inventory import InventoryReason
from app.models.order import OrderStatus

from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def test_hu_inv_04_buyer_cancel_releases_reserved_stock(api_context):
    client, db, _auth, token_for = api_context
    _seller, _store, _product, variant, warehouses, buyers = seed_inventory_store(db, "04-cancel", warehouses=2, quantity=2)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 3)
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    order_id = checkout.json()["orders"][0]["id"]

    cancelled = client.post(f"/api/v1/orders/{order_id}/cancel", headers=token_for(buyer.id))

    db.refresh(warehouses[0].stock_levels[0])
    db.refresh(warehouses[1].stock_levels[0])
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert sum(level.reserved for level in [warehouses[0].stock_levels[0], warehouses[1].stock_levels[0]]) == 0
    assert sum(level.quantity for level in [warehouses[0].stock_levels[0], warehouses[1].stock_levels[0]]) == 4
    assert db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order_id,
        InventoryMovement.reason == InventoryReason.release,
    ).count()


def test_hu_inv_04_return_replenishes_consumed_stock_once(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, warehouses, buyers = seed_inventory_store(db, "04-return", warehouses=1, quantity=3)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 2)
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    order_id = checkout.json()["orders"][0]["id"]
    order = db.get(Order, order_id)
    order.status = OrderStatus.delivered
    db.commit()

    returned = client.patch(
        f"/api/v1/seller/orders/{order_id}/status",
        headers=token_for(seller.id),
        json={"status": "returned"},
    )
    returned_again = client.patch(
        f"/api/v1/seller/orders/{order_id}/status",
        headers=token_for(seller.id),
        json={"status": "returned"},
    )

    db.refresh(warehouses[0].stock_levels[0])
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned"
    assert returned_again.status_code == 200
    assert warehouses[0].stock_levels[0].quantity == 3
    assert db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order_id,
        InventoryMovement.reason == InventoryReason.return_in,
    ).count() == 1

