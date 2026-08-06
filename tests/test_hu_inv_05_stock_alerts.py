from app.models.catalog import ProductStatus

from tests.inventory_test_utils import seed_inventory_store


def test_hu_inv_05_low_stock_alerts_are_exposed_by_seller_scope(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "05-low", warehouses=1, quantity=5, threshold=2)

    adjusted = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[0].id, "quantity": 2, "threshold": 3},
    )
    alerts = client.get("/api/v1/seller/inventory/alerts", headers=token_for(seller.id))

    assert adjusted.status_code == 200
    assert alerts.status_code == 200
    assert alerts.json()[0]["alert_type"] == "low_stock"
    assert alerts.json()[0]["available"] == 2
    assert alerts.json()[0]["threshold"] == 3


def test_hu_inv_05_out_of_stock_updates_product_state(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, product, variant, warehouses, _buyers = seed_inventory_store(db, "05-out", warehouses=1, quantity=1, threshold=1)

    adjusted = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[0].id, "quantity": 0, "threshold": 1},
    )
    alerts = client.get("/api/v1/seller/inventory/alerts", headers=token_for(seller.id))

    db.refresh(product)
    assert adjusted.status_code == 200
    assert product.status == ProductStatus.out_of_stock
    assert alerts.json()[0]["alert_type"] == "out_of_stock"
