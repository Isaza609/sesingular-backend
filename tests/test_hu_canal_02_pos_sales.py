from app.models import InventoryMovement, Order, PlatformSetting, ProductVariant, StockLevel
from app.models.inventory import InventoryReason

from tests.inventory_test_utils import seed_inventory_store


def test_hu_canal_02_pos_sale_without_buyer_discounts_inventory_and_creates_paid_payment(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "canal-02-ok", warehouses=1, quantity=5)

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": 2}], "payment_method": "cash"},
    )

    db.refresh(warehouses[0].stock_levels[0])
    data = response.json()
    assert response.status_code == 201
    assert data["buyer_id"] is None
    assert data["channel"] == "presencial"
    assert warehouses[0].stock_levels[0].quantity == 3
    assert data["payments"][0]["provider"] == "pos"
    assert data["payments"][0]["status"] == "paid"
    assert data["payments"][0]["method"] == "cash"
    assert db.query(InventoryMovement).filter(
        InventoryMovement.order_id == data["id"],
        InventoryMovement.reason == InventoryReason.sale,
        InventoryMovement.delta == -2,
    ).count() == 1


def test_hu_canal_02_pos_rejects_insufficient_stock_with_real_availability(api_context):
    client, db, _auth, token_for = api_context
    seller, store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "canal-02-stock", warehouses=1, quantity=1)

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": 2}], "payment_method": "cash"},
    )

    db.refresh(warehouses[0].stock_levels[0])
    assert response.status_code == 409
    assert "Disponible: 1" in response.json()["detail"]
    assert warehouses[0].stock_levels[0].quantity == 1
    assert db.query(Order).filter(Order.store_id == store.id).count() == 0


def test_hu_canal_02_pos_rejects_unknown_optional_buyer(api_context):
    client, db, _auth, token_for = api_context
    seller, store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "canal-02-buyer", warehouses=1, quantity=3)

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": 1}], "buyer_id": "buyer-missing", "payment_method": "cash"},
    )

    db.refresh(warehouses[0].stock_levels[0])
    assert response.status_code == 404
    assert warehouses[0].stock_levels[0].quantity == 3
    assert db.query(Order).filter(Order.store_id == store.id).count() == 0


def test_hu_canal_02_pos_rejects_foreign_variant_without_creating_order(api_context):
    client, db, _auth, token_for = api_context
    seller, store, _product, _variant, _warehouses, _buyers = seed_inventory_store(db, "canal-02-own", warehouses=1, quantity=3)
    db.delete(db.get(PlatformSetting, "payment_gateway"))
    db.commit()
    _other_seller, _other_store, _other_product, other_variant, other_warehouses, _other_buyers = seed_inventory_store(db, "canal-02-other", warehouses=1, quantity=4)

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": other_variant.id, "quantity": 1}], "payment_method": "cash"},
    )

    db.refresh(other_warehouses[0].stock_levels[0])
    assert response.status_code == 404
    assert db.query(Order).filter(Order.store_id == store.id).count() == 0
    assert other_warehouses[0].stock_levels[0].quantity == 4


def test_hu_canal_02_pos_requires_active_warehouse(api_context):
    client, db, _auth, token_for = api_context
    seller, store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "canal-02-nowh", warehouses=1, quantity=3)
    warehouses[0].active = False
    db.commit()

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={"items": [{"variant_id": variant.id, "quantity": 1}], "payment_method": "cash"},
    )

    assert response.status_code == 400
    assert "almac" in response.json()["detail"].lower()
    assert db.query(Order).filter(Order.store_id == store.id).count() == 0


def test_hu_canal_02_pos_prevalidates_all_items_and_avoids_partial_discount(api_context):
    client, db, _auth, token_for = api_context
    seller, store, product, variant_ok, warehouses, _buyers = seed_inventory_store(db, "canal-02-rollback", warehouses=1, quantity=5)
    variant_low = ProductVariant(id="variant-inv-canal-02-low", product_id=product.id, sku="LOW", price=10000, cost=4000)
    db.add(variant_low)
    db.flush()
    low_level = StockLevel(variant_id=variant_low.id, warehouse_id=warehouses[0].id, quantity=1, threshold=0)
    db.add(low_level)
    db.commit()

    response = client.post(
        "/api/v1/seller/pos/orders",
        headers=token_for(seller.id),
        json={
            "items": [
                {"variant_id": variant_ok.id, "quantity": 2},
                {"variant_id": variant_low.id, "quantity": 3},
            ],
            "payment_method": "cash",
        },
    )

    db.refresh(warehouses[0].stock_levels[0])
    db.refresh(low_level)
    assert response.status_code == 409
    assert "Disponible: 1" in response.json()["detail"]
    assert warehouses[0].stock_levels[0].quantity == 5
    assert low_level.quantity == 1
    assert db.query(Order).filter(Order.store_id == store.id).count() == 0
