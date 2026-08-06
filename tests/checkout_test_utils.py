from app.models import Address, Cart, CartItem, PlatformSetting, Product, ProductVariant, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.user import UserRole


def ensure_gateway(db):
    if db.get(PlatformSetting, "payment_gateway") is None:
        db.add(PlatformSetting(key="payment_gateway", value={"provider": "test"}))


def seed_checkout_store(
    db,
    suffix: str,
    *,
    buyer: User | None = None,
    cart: Cart | None = None,
    price: int = 50000,
    quantity: int = 5,
    warehouses: int = 1,
    shipping_config: dict | None = None,
):
    ensure_gateway(db)
    seller = User(id=f"seller-chk-{suffix}", email=f"seller-chk-{suffix}@example.com", name=f"Seller {suffix}", role=UserRole.seller)
    if buyer is None:
        buyer = User(id=f"buyer-chk-{suffix}", email=f"buyer-chk-{suffix}@example.com", name="Buyer CHK", role=UserRole.buyer)
        db.add(buyer)
        db.flush()
    address = db.get(Address, f"addr-chk-{suffix}") or Address(
        id=f"addr-chk-{suffix}",
        user_id=buyer.id,
        recipient_name="Ana Perez",
        phone="+573001112233",
        address_line="Calle 10 # 20-30",
        city="Bogota",
        region="Cundinamarca",
    )
    if cart is None:
        cart = db.scalar(db.query(Cart).filter(Cart.user_id == buyer.id).statement)
        if cart is None:
            cart = Cart(id=f"cart-chk-{suffix}", user_id=buyer.id)
    store = Store(
        id=f"store-chk-{suffix}",
        slug=f"store-chk-{suffix}",
        name=f"Tienda {suffix}",
        contact_email=f"tienda-{suffix}@example.com",
        contact_phone="+571111111",
        whatsapp_phone="+572222222",
        social_links={},
    )
    product = Product(id=f"product-chk-{suffix}", store_id=store.id, slug=f"producto-chk-{suffix}", name=f"Producto {suffix}", status=ProductStatus.active)
    variant = ProductVariant(id=f"variant-chk-{suffix}", product_id=product.id, sku=f"CHK-{suffix}", price=price, cost=price // 2)
    db.add_all([seller, address, cart, store, product, variant])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    warehouse_rows = []
    for index in range(warehouses):
        warehouse = Warehouse(
            id=f"wh-chk-{suffix}-{index + 1}",
            store_id=store.id,
            name=f"Bodega {index + 1}",
            active=True,
            is_default=index == 0,
        )
        warehouse_rows.append(warehouse)
        db.add(warehouse)
    db.flush()
    for warehouse in warehouse_rows:
        db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=quantity))
    db.add(
        PlatformSetting(
            key=f"store_config:{store.id}",
            value=shipping_config or {"shipping_mode": "flat", "shipping_flat_cost": 0, "shipping_free_threshold": 0},
        )
    )
    db.commit()
    return seller, buyer, store, product, variant, address, cart, warehouse_rows


def add_cart_item(db, cart: Cart, variant: ProductVariant, quantity: int = 1):
    item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity)
    db.add(item)
    db.commit()
    return item
