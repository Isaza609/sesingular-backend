from app.models import Order, OrderItem, Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.order import OrderStatus, SaleChannel
from app.models.user import UserRole


def _seed_sort_catalog(db, suffix: str):
    seller = User(id=f"seller-bus-02-{suffix}", email=f"seller-bus-02-{suffix}@example.com", name="Seller BUS", role=UserRole.seller)
    store = Store(id=f"store-bus-02-{suffix}", slug=f"store-bus-02-{suffix}", name="Tienda BUS", social_links={})
    warehouse = Warehouse(id=f"wh-bus-02-{suffix}", store_id=store.id, name="Bodega", active=True, is_default=True)
    db.add_all([seller, store, warehouse])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))

    variants = {}
    for slug, name, price in [
        ("barato", "Producto Barato", 30000),
        ("medio", "Producto Medio", 50000),
        ("caro", "Producto Caro", 90000),
    ]:
        product = Product(id=f"prod-bus-02-{suffix}-{slug}", store_id=store.id, slug=slug, name=name, status=ProductStatus.active)
        variant = ProductVariant(id=f"variant-bus-02-{suffix}-{slug}", product_id=product.id, sku=f"BUS02-{suffix}-{slug}", price=price)
        db.add_all([product, variant])
        db.flush()
        db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=10))
        variants[slug] = variant
    db.commit()
    return store, variants


def _sold(db, store: Store, variant: ProductVariant, quantity: int, *, status: OrderStatus = OrderStatus.delivered):
    order = Order(store_id=store.id, channel=SaleChannel.online, status=status, subtotal=quantity * variant.price, total=quantity * variant.price)
    db.add(order)
    db.flush()
    db.add(
        OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            product_name=variant.product.name,
            sku=variant.sku,
            quantity=quantity,
            unit_price=variant.price,
            unit_cost=variant.cost,
        )
    )
    db.commit()


def test_hu_bus_02_sorts_by_effective_price_ascending_and_descending(api_context):
    client, db, _auth, _token_for = api_context
    _store, _variants = _seed_sort_catalog(db, "price")

    asc = client.get("/api/v1/catalog/products", params={"sort": "precio-asc"})
    desc = client.get("/api/v1/catalog/products", params={"sort": "precio-desc"})

    assert asc.status_code == 200
    assert [row["price"] for row in asc.json()["items"][:3]] == [30000, 50000, 90000]
    assert desc.status_code == 200
    assert [row["price"] for row in desc.json()["items"][:3]] == [90000, 50000, 30000]


def test_hu_bus_02_sorts_by_real_sold_units_excluding_cancelled_orders(api_context):
    client, db, _auth, _token_for = api_context
    store, variants = _seed_sort_catalog(db, "sold")
    _sold(db, store, variants["barato"], 2)
    _sold(db, store, variants["medio"], 5)
    _sold(db, store, variants["caro"], 20, status=OrderStatus.cancelled)
    _sold(db, store, variants["caro"], 1)

    response = client.get("/api/v1/catalog/products", params={"store_id": store.id, "sort": "vendidos"})

    assert response.status_code == 200
    assert [row["slug"] for row in response.json()["items"]] == ["medio", "barato", "caro"]
