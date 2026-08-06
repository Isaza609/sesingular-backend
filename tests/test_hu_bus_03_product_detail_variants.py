from app.models import PlatformSetting, Product, ProductImage, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def _seed_detail_catalog(db, suffix: str):
    seller = User(id=f"seller-bus-03-{suffix}", email=f"seller-bus-03-{suffix}@example.com", name="Seller BUS", role=UserRole.seller)
    store = Store(
        id=f"store-bus-03-{suffix}",
        slug=f"store-bus-03-{suffix}",
        name="Tienda BUS",
        contact_email="hola@bus.example",
        contact_phone="+573001112233",
        whatsapp_phone="+573009998888",
        social_links={},
    )
    warehouse = Warehouse(id=f"wh-bus-03-{suffix}", store_id=store.id, name="Bodega", active=True, is_default=True)
    product = Product(id=f"prod-bus-03-{suffix}", store_id=store.id, slug="camisa-detalle", name="Camisa detalle", status=ProductStatus.active)
    out_product = Product(id=f"prod-bus-03-out-{suffix}", store_id=store.id, slug="sin-stock", name="Sin stock", status=ProductStatus.out_of_stock)
    draft_product = Product(id=f"prod-bus-03-draft-{suffix}", store_id=store.id, slug="borrador", name="Borrador", status=ProductStatus.draft)
    discontinued_product = Product(id=f"prod-bus-03-disc-{suffix}", store_id=store.id, slug="descontinuado", name="Descontinuado", status=ProductStatus.discontinued)
    active_variant = ProductVariant(id=f"variant-bus-03-active-{suffix}", product_id=product.id, sku="BUS03-A", color="Azul", size="M", price=80000)
    empty_variant = ProductVariant(id=f"variant-bus-03-empty-{suffix}", product_id=product.id, sku="BUS03-E", color="Negro", size="L", price=90000)
    out_variant = ProductVariant(id=f"variant-bus-03-out-{suffix}", product_id=out_product.id, sku="BUS03-O", price=70000)
    db.add_all([seller, store, warehouse, product, out_product, draft_product, discontinued_product, active_variant, empty_variant, out_variant])
    db.flush()
    db.add_all(
        [
            StoreMember(store_id=store.id, user_id=seller.id, role="owner"),
            PlatformSetting(key=f"store_config:{store.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0, "shipping_zones": []}),
            ProductImage(product_id=product.id, url="https://cdn.example.com/general.jpg", alt="General", sort_order=0),
            ProductImage(product_id=product.id, variant_id=active_variant.id, url="https://cdn.example.com/azul.jpg", alt="Azul", sort_order=1),
            ProductImage(product_id=product.id, variant_id=empty_variant.id, url="https://cdn.example.com/negro.jpg", alt="Negro", sort_order=1),
            StockLevel(variant_id=active_variant.id, warehouse_id=warehouse.id, quantity=3),
            StockLevel(variant_id=empty_variant.id, warehouse_id=warehouse.id, quantity=0),
            StockLevel(variant_id=out_variant.id, warehouse_id=warehouse.id, quantity=4),
        ]
    )
    db.commit()
    return store, product, out_product, draft_product, discontinued_product, active_variant, empty_variant


def test_hu_bus_03_detail_exposes_variant_price_stock_images_shipping_and_contact(api_context):
    client, db, _auth, _token_for = api_context
    store, product, _out_product, _draft_product, _discontinued_product, active_variant, empty_variant = _seed_detail_catalog(db, "detail")

    response = client.get(f"/api/v1/catalog/products/{product.slug}", params={"store_id": store.id})

    data = response.json()
    variants = {row["id"]: row for row in data["variants"]}
    assert response.status_code == 200
    assert data["store_contact"]["email"] == "hola@bus.example"
    assert data["store_contact"]["whatsapp_phone"] == "+573009998888"
    assert data["shipping"]["to_agree"] is True
    assert variants[active_variant.id]["price"] == 80000
    assert variants[active_variant.id]["stock"] == 3
    assert variants[active_variant.id]["available"] is True
    assert variants[active_variant.id]["images"][0]["url"] == "https://cdn.example.com/azul.jpg"
    assert variants[empty_variant.id]["stock"] == 0
    assert variants[empty_variant.id]["available"] is False
    assert variants[empty_variant.id]["images"][0]["url"] == "https://cdn.example.com/negro.jpg"


def test_hu_bus_03_out_of_stock_is_visible_but_not_available_and_hidden_statuses_404(api_context):
    client, db, _auth, _token_for = api_context
    store, _product, out_product, draft_product, discontinued_product, _active_variant, _empty_variant = _seed_detail_catalog(db, "status")

    out_response = client.get(f"/api/v1/catalog/products/{out_product.slug}", params={"store_id": store.id})
    draft_response = client.get(f"/api/v1/catalog/products/{draft_product.slug}", params={"store_id": store.id})
    discontinued_response = client.get(f"/api/v1/catalog/products/{discontinued_product.slug}", params={"store_id": store.id})

    assert out_response.status_code == 200
    assert out_response.json()["status"] == "out_of_stock"
    assert all(row["available"] is False for row in out_response.json()["variants"])
    assert draft_response.status_code == 404
    assert discontinued_response.status_code == 404
