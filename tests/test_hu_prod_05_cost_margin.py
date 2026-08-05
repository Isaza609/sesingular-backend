from app.models import Product, ProductVariant, Store, StoreMember, User
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def test_hu_prod_05_cost_is_seller_only_and_margin_recalculates(api_context):
    client, db, _auth, token_for = api_context
    seller = User(id="seller-prod-05", email="seller-prod-05@example.com", name="Seller PROD", role=UserRole.seller)
    store = Store(id="store-prod-05", slug="store-prod-05", name="Tienda PROD", social_links={})
    product = Product(id="product-prod-05", store_id=store.id, slug="camisa", name="Camisa", status=ProductStatus.active)
    variant = ProductVariant(id="variant-prod-05", product_id=product.id, sku="CAM-S", price=70000, cost=30000)
    db.add_all([seller, store, product, variant])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()

    seller_view = client.get("/api/v1/seller/products", headers=token_for(seller.id))
    public_view = client.get("/api/v1/catalog/products/camisa", params={"store_id": store.id})
    patched = client.patch(f"/api/v1/seller/variants/{variant.id}", headers=token_for(seller.id), json={"cost": 40000})

    seller_variant = seller_view.json()["items"][0]["variants"][0]
    public_variant = public_view.json()["variants"][0]
    patched_variant = patched.json()

    assert seller_variant["cost"] == 30000
    assert seller_variant["margin"] == 40000
    assert "cost" not in public_variant
    assert "margin" not in public_variant
    assert patched_variant["cost"] == 40000
    assert patched_variant["margin"] == 30000
