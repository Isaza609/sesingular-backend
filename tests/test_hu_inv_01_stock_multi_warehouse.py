from app.models import Product, ProductVariant, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole

from tests.inventory_test_utils import seed_inventory_store


def test_hu_inv_01_stock_multi_warehouse_is_aggregated_and_broken_down(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, warehouses, _buyers = seed_inventory_store(db, "01", warehouses=2, quantity=0)

    first = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[0].id, "quantity": 10, "threshold": 3},
    )
    second = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(seller.id),
        json={"warehouse_id": warehouses[1].id, "quantity": 10, "threshold": 3},
    )
    listed = client.get("/api/v1/seller/inventory", headers=token_for(seller.id))

    assert first.status_code == 200
    assert second.status_code == 200
    row = listed.json()[0]
    assert row["quantity"] == 20
    assert row["available"] == 20
    assert {item["warehouse_id"]: item["quantity"] for item in row["warehouses"]} == {
        warehouses[0].id: 10,
        warehouses[1].id: 10,
    }


def test_hu_inv_01_seller_cannot_adjust_other_store_inventory(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, _product, variant, _warehouses, _buyers = seed_inventory_store(db, "01-scope", warehouses=1, quantity=4)
    other_store = Store(id="store-inv-01-other", slug="store-inv-01-other", name="Otra tienda", social_links={})
    other_seller = User(id="seller-inv-01-other", email="seller-inv-01-other@example.com", name="Otro Seller", role=UserRole.seller)
    other_product = Product(id="product-inv-01-other", store_id=other_store.id, slug="otro", name="Otro", status=ProductStatus.active)
    other_variant = ProductVariant(id="variant-inv-01-other", product_id=other_product.id, sku="OTHER", price=10000)
    other_wh = Warehouse(id="wh-inv-01-other", store_id=other_store.id, name="Otra bodega", active=True, is_default=True)
    db.add_all([other_store, other_seller, other_product, other_variant, other_wh])
    db.flush()
    db.add(StoreMember(store_id=other_store.id, user_id=other_seller.id, role="owner"))
    db.commit()

    response = client.patch(
        f"/api/v1/seller/inventory/{variant.id}",
        headers=token_for(other_seller.id),
        json={"warehouse_id": other_wh.id, "quantity": 2},
    )

    assert response.status_code == 404
