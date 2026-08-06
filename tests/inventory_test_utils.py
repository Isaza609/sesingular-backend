from app.models import Address, Cart, CartItem, PlatformSetting, Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def seed_inventory_store(db, suffix: str, *, warehouses: int = 1, quantity: int = 5, threshold: int = 2, buyer_count: int = 1):
    seller = User(id=f"seller-inv-{suffix}", email=f"seller-inv-{suffix}@example.com", name="Seller INV", role=UserRole.seller)
    store = Store(id=f"store-inv-{suffix}", slug=f"store-inv-{suffix}", name="Tienda INV", social_links={})
    product = Product(id=f"product-inv-{suffix}", store_id=store.id, slug=f"producto-inv-{suffix}", name="Producto INV", status=ProductStatus.active)
    variant = ProductVariant(id=f"variant-inv-{suffix}", product_id=product.id, sku=f"INV-{suffix}", price=10000, cost=4000)
    db.add_all([seller, store, product, variant])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    warehouse_rows = []
    for index in range(warehouses):
        warehouse = Warehouse(
            id=f"wh-inv-{suffix}-{index + 1}",
            store_id=store.id,
            name=f"Bodega {index + 1}",
            active=True,
            is_default=index == 0,
        )
        warehouse_rows.append(warehouse)
        db.add(warehouse)
    db.flush()
    for warehouse in warehouse_rows:
        db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=quantity, threshold=threshold))
    buyers = []
    for index in range(buyer_count):
        buyer = User(id=f"buyer-inv-{suffix}-{index + 1}", email=f"buyer-inv-{suffix}-{index + 1}@example.com", name="Buyer INV", role=UserRole.buyer)
        address = Address(id=f"addr-inv-{suffix}-{index + 1}", user_id=buyer.id, recipient_name="Ana", address_line="Calle 1", city="Bogota")
        cart = Cart(id=f"cart-inv-{suffix}-{index + 1}", user_id=buyer.id)
        db.add_all([buyer, address, cart])
        db.flush()
        buyers.append((buyer, address, cart))
    db.add_all(
        [
            PlatformSetting(key="payment_gateway", value={"provider": "test"}),
            PlatformSetting(key=f"store_config:{store.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0}),
        ]
    )
    db.commit()
    return seller, store, product, variant, warehouse_rows, buyers


def add_cart_item(db, cart, variant, quantity: int = 1):
    item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity)
    db.add(item)
    db.commit()
    return item
