from app.models import Cart, Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def _store_with_products(db):
    seller = User(id="seller-prod-06", email="seller-prod-06@example.com", name="Seller PROD", role=UserRole.seller)
    buyer = User(id="buyer-prod-06", email="buyer-prod-06@example.com", name="Buyer PROD", role=UserRole.buyer)
    store = Store(id="store-prod-06", slug="store-prod-06", name="Tienda PROD", social_links={})
    warehouse = Warehouse(id="warehouse-prod-06", store_id=store.id, name="Bodega", active=True)
    products = [
        Product(id="prod-draft-06", store_id=store.id, slug="draft", name="Draft", status=ProductStatus.draft),
        Product(id="prod-active-06", store_id=store.id, slug="active", name="Active", status=ProductStatus.active),
        Product(id="prod-out-06", store_id=store.id, slug="agotado", name="Agotado", status=ProductStatus.out_of_stock),
        Product(id="prod-disc-06", store_id=store.id, slug="disc", name="Disc", status=ProductStatus.discontinued),
    ]
    variants = [
        ProductVariant(id="var-draft-06", product_id="prod-draft-06", sku="DRAFT", price=1000),
        ProductVariant(id="var-active-06", product_id="prod-active-06", sku="ACTIVE", price=1000),
        ProductVariant(id="var-out-06", product_id="prod-out-06", sku="OUT", price=1000),
        ProductVariant(id="var-disc-06", product_id="prod-disc-06", sku="DISC", price=1000),
    ]
    db.add_all([seller, buyer, store, warehouse, *products, *variants])
    db.flush()
    db.add_all(
        [
            StoreMember(store_id=store.id, user_id=seller.id, role="owner"),
            Cart(id="cart-prod-06", user_id=buyer.id),
            StockLevel(variant_id="var-active-06", warehouse_id=warehouse.id, quantity=2),
            StockLevel(variant_id="var-out-06", warehouse_id=warehouse.id, quantity=0),
        ]
    )
    db.commit()
    return seller, buyer, store


def test_hu_prod_06_public_visibility_by_status(api_context):
    client, db, _auth, token_for = api_context
    seller, _buyer, store = _store_with_products(db)

    public = client.get("/api/v1/catalog/products", params={"store_id": store.id})
    seller_view = client.get("/api/v1/seller/products", headers=token_for(seller.id))

    assert {row["slug"] for row in public.json()["items"]} == {"active", "agotado"}
    assert client.get("/api/v1/catalog/products/draft", params={"store_id": store.id}).status_code == 404
    assert client.get("/api/v1/catalog/products/disc", params={"store_id": store.id}).status_code == 404
    assert {row["slug"] for row in seller_view.json()["items"]} == {"draft", "active", "agotado", "disc"}


def test_hu_prod_06_out_of_stock_visible_but_not_cartable(api_context):
    client, db, _auth, token_for = api_context
    _seller, buyer, store = _store_with_products(db)

    out_product = client.get("/api/v1/catalog/products/agotado", params={"store_id": store.id})
    active_cart = client.post("/api/v1/cart/items", headers=token_for(buyer.id), json={"variant_id": "var-active-06", "quantity": 1})
    out_cart = client.post("/api/v1/cart/items", headers=token_for(buyer.id), json={"variant_id": "var-out-06", "quantity": 1})

    assert out_product.status_code == 200
    assert out_product.json()["variants"][0]["available"] is False
    assert active_cart.status_code == 200
    assert out_cart.status_code == 409
