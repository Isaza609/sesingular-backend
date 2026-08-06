from app.models import InventoryMovement
from app.models.inventory import InventoryReason

from tests.inventory_test_utils import add_cart_item, seed_inventory_store


def test_hu_inv_03_assigns_dispatch_warehouse_and_consumes_selected_stock(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, warehouses, buyers = seed_inventory_store(db, "03", warehouses=2, quantity=3)
    buyer, address, cart = buyers[0]
    add_cart_item(db, cart, variant, 2)
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    order_id = checkout.json()["orders"][0]["id"]

    assigned = client.patch(
        f"/api/v1/seller/orders/{order_id}/warehouse",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[1].id},
    )
    duplicated = client.patch(
        f"/api/v1/seller/orders/{order_id}/warehouse",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[0].id},
    )

    db.refresh(warehouses[0].stock_levels[0])
    db.refresh(warehouses[1].stock_levels[0])
    sale = db.query(InventoryMovement).filter(
        InventoryMovement.order_id == order_id,
        InventoryMovement.reason == InventoryReason.sale,
        InventoryMovement.warehouse_id == warehouses[1].id,
    ).one()
    assert checkout.status_code == 201
    assert assigned.status_code == 200
    assert assigned.json()["warehouse_id"] == warehouses[1].id
    assert warehouses[1].stock_levels[0].quantity == 1
    assert warehouses[0].stock_levels[0].reserved + warehouses[1].stock_levels[0].reserved == 0
    assert sale.delta == -2
    assert duplicated.status_code == 409

