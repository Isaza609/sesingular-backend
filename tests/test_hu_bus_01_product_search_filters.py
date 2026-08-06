from datetime import datetime, timezone

from app.models import Category, PlatformSetting, Product, ProductCategory, ProductImage, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def _seed_search_catalog(db, suffix: str):
    seller = User(id=f"seller-bus-01-{suffix}", email=f"seller-bus-01-{suffix}@example.com", name="Seller BUS", role=UserRole.seller)
    store = Store(id=f"store-bus-01-{suffix}", slug=f"store-bus-01-{suffix}", name="Tienda BUS", social_links={})
    warehouse = Warehouse(id=f"wh-bus-01-{suffix}", store_id=store.id, name="Bodega", active=True, is_default=True)
    camisas = Category(id=f"cat-bus-01-camisas-{suffix}", store_id=store.id, slug="camisas", name="Camisas", active=True)
    accesorios = Category(id=f"cat-bus-01-accesorios-{suffix}", store_id=store.id, slug="accesorios", name="Accesorios", active=True)
    db.add_all([seller, store, warehouse, camisas, accesorios])
    db.flush()
    db.add_all(
        [
            StoreMember(store_id=store.id, user_id=seller.id, role="owner"),
            PlatformSetting(key=f"store_config:{store.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0, "shipping_zones": []}),
        ]
    )

    def product(slug: str, name: str, description: str, category: Category, price: int, stock: int, *, special_price: int | None = None, status: ProductStatus = ProductStatus.active):
        row = Product(id=f"prod-bus-01-{suffix}-{slug}", store_id=store.id, slug=slug, name=name, description=description, status=status)
        variant = ProductVariant(
            id=f"variant-bus-01-{suffix}-{slug}",
            product_id=row.id,
            sku=f"BUS01-{suffix}-{slug}",
            price=price,
            special_price=special_price,
            special_starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc) if special_price is not None else None,
            special_ends_at=datetime(2027, 1, 1, tzinfo=timezone.utc) if special_price is not None else None,
        )
        db.add_all([row, variant])
        db.flush()
        db.add_all(
            [
                ProductCategory(product_id=row.id, category_id=category.id),
                ProductImage(product_id=row.id, url=f"https://cdn.example.com/{slug}.jpg", alt=name),
                StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=stock),
            ]
        )
        return row

    camisa = product("camisa-blanca", "Camisa Blanca", "Prenda fresca para clima calido", camisas, 90000, 5, special_price=70000)
    bolso = product("bolso-viaje", "Bolso Viaje", "Accesorio amplio para guardar camisa y zapatos", accesorios, 60000, 5)
    no_stock = product("camisa-vintage", "Camisa Vintage", "Prenda retro", camisas, 50000, 0)
    premium = product("camisa-premium", "Camisa Premium", "Algodon premium", camisas, 120000, 5)
    hidden = product("camisa-borrador", "Camisa Borrador", "No visible", camisas, 1000, 5, status=ProductStatus.draft)
    db.commit()
    return store, camisas, accesorios, {"camisa": camisa, "bolso": bolso, "no_stock": no_stock, "premium": premium, "hidden": hidden}


def test_hu_bus_01_search_matches_name_and_description_case_insensitive(api_context):
    client, db, _auth, _token_for = api_context
    _store, _camisas, _accesorios, products = _seed_search_catalog(db, "text")

    by_name = client.get("/api/v1/catalog/products", params={"q": "CAMISA"})
    by_description = client.get("/api/v1/catalog/products", params={"q": "zapatos"})

    by_name_ids = {row["id"] for row in by_name.json()["items"]}
    by_description_ids = {row["id"] for row in by_description.json()["items"]}
    assert by_name.status_code == 200
    assert products["camisa"].id in by_name_ids
    assert products["hidden"].id not in by_name_ids
    assert by_description.status_code == 200
    assert by_description_ids == {products["bolso"].id}


def test_hu_bus_01_combined_filters_use_effective_price_and_real_stock(api_context):
    client, db, _auth, _token_for = api_context
    store, camisas, _accesorios, products = _seed_search_catalog(db, "combined")

    response = client.get(
        "/api/v1/catalog/products",
        params={
            "store_id": store.id,
            "q": "camisa",
            "category": camisas.slug,
            "min_price": 65000,
            "max_price": 80000,
            "in_stock": True,
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["total"] == 1
    assert data["items"][0]["id"] == products["camisa"].id
    assert data["items"][0]["price"] == 70000


def test_hu_bus_01_empty_state_and_invalid_price_range(api_context):
    client, db, _auth, _token_for = api_context
    _store, _camisas, _accesorios, _products = _seed_search_catalog(db, "empty")

    empty = client.get("/api/v1/catalog/products", params={"q": "inexistente"})
    invalid = client.get("/api/v1/catalog/products", params={"min_price": 90000, "max_price": 10000})

    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["items"] == []
    assert invalid.status_code == 400
