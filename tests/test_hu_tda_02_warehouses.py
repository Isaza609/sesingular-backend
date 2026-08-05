from app.models import InventoryMovement, Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.inventory import InventoryReason
from app.models.user import UserRole


def _seller_with_product(db):
    seller = User(id="seller-tda-02", email="seller-tda-02@example.com", name="Seller TDA", role=UserRole.seller)
    store = Store(id="store-tda-02", slug="almacenes", name="Almacenes Store", social_links={})
    product = Product(id="product-tda-02", store_id=store.id, slug="anillo", name="Anillo", status=ProductStatus.active)
    variant = ProductVariant(id="variant-tda-02", product_id=product.id, sku="SKU-TDA-02", price=50000)
    db.add_all([seller, store, product, variant])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store, variant


def test_hu_tda_02_create_first_warehouse_available_for_stock(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, variant = _seller_with_product(db)

    created = client.post(
        "/api/v1/seller/warehouses",
        headers=token_for(seller.id),
        json={"name": "Bodega principal", "address_line": "Calle 1", "city": "Bogota"},
    )

    assert created.status_code == 201
    warehouse = created.json()
    assert warehouse["is_default"] is True
    assert warehouse["requires_manual_dispatch_selection"] is False

    stock = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouse["id"], "quantity": 8, "threshold": 2},
    )
    assert stock.status_code == 200
    assert stock.json()[0]["quantity"] == 8


def test_hu_tda_02_default_is_unique_and_multiple_active_require_selection(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _variant = _seller_with_product(db)

    first = client.post("/api/v1/seller/warehouses", headers=token_for(seller.id), json={"name": "Norte"}).json()
    second = client.post(
        "/api/v1/seller/warehouses",
        headers=token_for(seller.id),
        json={"name": "Sur", "is_default": True},
    ).json()

    listed = client.get("/api/v1/seller/warehouses", headers=token_for(seller.id))
    assert listed.status_code == 200
    rows = {row["id"]: row for row in listed.json()}
    assert rows[first["id"]]["is_default"] is False
    assert rows[second["id"]]["is_default"] is True
    assert all(row["requires_manual_dispatch_selection"] is True for row in rows.values())


def test_hu_tda_02_inactive_warehouse_rejects_new_stock_and_keeps_history(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, variant = _seller_with_product(db)
    warehouse = Warehouse(id="wh-tda-02", store_id="store-tda-02", name="Historica", active=False)
    db.add_all(
        [
            warehouse,
            StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=3),
            InventoryMovement(variant_id=variant.id, warehouse_id=warehouse.id, delta=3, reason=InventoryReason.restock),
        ]
    )
    db.commit()

    response = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouse.id, "quantity": 5},
    )

    assert response.status_code == 400
    movements = client.get("/api/v1/seller/inventory/movements", headers=token_for(seller.id))
    assert movements.status_code == 200
    assert any(row["warehouse_id"] == warehouse.id for row in movements.json())
