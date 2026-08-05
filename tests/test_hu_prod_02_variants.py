from app.models import Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def _seller_product(db):
    seller = User(id="seller-prod-02", email="seller-prod-02@example.com", name="Seller PROD", role=UserRole.seller)
    store = Store(id="store-prod-02", slug="store-prod-02", name="Tienda PROD", social_links={})
    product = Product(id="product-prod-02", store_id=store.id, slug="camisa", name="Camisa", status=ProductStatus.active)
    base = ProductVariant(id="variant-prod-02-base", product_id=product.id, sku="CAM-S", color="Negro", size="S", price=70000, cost=30000)
    warehouse = Warehouse(id="warehouse-prod-02", store_id=store.id, name="Bodega", active=True)
    db.add_all([seller, store, product, base, warehouse])
    db.flush()
    db.add_all([StoreMember(store_id=store.id, user_id=seller.id, role="owner"), StockLevel(variant_id=base.id, warehouse_id=warehouse.id, quantity=5)])
    db.commit()
    return seller, store, product, base, warehouse


def test_hu_prod_02_create_variants_with_price_and_availability(api_context):
    client, db, _auth, token_for = api_context
    seller, store, product, _base, warehouse = _seller_product(db)

    created = client.post(
        f"/api/v1/seller/products/{product.id}/variants",
        headers=token_for(seller.id),
        json={"sku": "CAM-M", "color": "Negro", "size": "M", "price": 80000, "cost": 32000},
    )
    assert created.status_code == 201
    variant_id = created.json()["id"]
    db.add(StockLevel(variant_id=variant_id, warehouse_id=warehouse.id, quantity=0))
    db.commit()

    public = client.get("/api/v1/catalog/products/camisa", params={"store_id": store.id})
    variants = {row["sku"]: row for row in public.json()["variants"]}

    assert variants["CAM-S"]["price"] == 70000
    assert variants["CAM-S"]["available"] is True
    assert variants["CAM-M"]["price"] == 80000
    assert variants["CAM-M"]["available"] is False
    assert "cost" not in variants["CAM-S"]


def test_hu_prod_02_rejects_duplicate_sku_and_foreign_variant(api_context):
    client, db, _auth, token_for = api_context
    seller, _store, product, base, _warehouse = _seller_product(db)
    other_seller = User(id="seller-prod-02-other", email="seller-prod-02-other@example.com", name="Other", role=UserRole.seller)
    other_store = Store(id="store-prod-02-other", slug="store-prod-02-other", name="Otra", social_links={})
    db.add_all([other_seller, other_store, StoreMember(store_id=other_store.id, user_id=other_seller.id, role="owner")])
    db.commit()

    duplicate = client.post(
        f"/api/v1/seller/products/{product.id}/variants",
        headers=token_for(seller.id),
        json={"sku": base.sku, "price": 70000},
    )
    foreign = client.patch(f"/api/v1/seller/variants/{base.id}", headers=token_for(other_seller.id), json={"price": 1})

    assert duplicate.status_code == 409
    assert foreign.status_code == 404
