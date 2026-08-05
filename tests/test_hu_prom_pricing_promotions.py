from datetime import datetime, timedelta, timezone

from app.models import Address, Cart, CartItem, Coupon, ExtraCharge, PlatformSetting, Product, ProductVariant, Promotion, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.promotion import ChargeType, DiscountType, PromotionScope
from app.models.user import UserRole


def _seed_cart(db, suffix: str, *, price: int = 10000, quantity: int = 1, cost: int | None = 4000):
    seller = User(id=f"seller-prom-{suffix}", email=f"seller-prom-{suffix}@example.com", name="Seller PROM", role=UserRole.seller)
    buyer = User(id=f"buyer-prom-{suffix}", email=f"buyer-prom-{suffix}@example.com", name="Buyer PROM", role=UserRole.buyer)
    store = Store(id=f"store-prom-{suffix}", slug=f"store-prom-{suffix}", name="Tienda PROM", social_links={})
    product = Product(id=f"product-prom-{suffix}", store_id=store.id, slug=f"producto-prom-{suffix}", name="Producto PROM", status=ProductStatus.active)
    variant = ProductVariant(id=f"variant-prom-{suffix}", product_id=product.id, sku=f"PROM-{suffix}", price=price, cost=cost)
    warehouse = Warehouse(id=f"wh-prom-{suffix}", store_id=store.id, name="Principal", active=True, is_default=True)
    address = Address(id=f"addr-prom-{suffix}", user_id=buyer.id, recipient_name="Ana", address_line="Calle 1", city="Bogota")
    cart = Cart(id=f"cart-prom-{suffix}", user_id=buyer.id)
    db.add_all([seller, buyer, store, product, variant, warehouse, address, cart])
    db.flush()
    db.add_all(
        [
            StoreMember(store_id=store.id, user_id=seller.id, role="owner"),
            StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=20),
            CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity),
            PlatformSetting(key="payment_gateway", value={"provider": "test"}),
            PlatformSetting(key=f"store_config:{store.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0}),
        ]
    )
    db.commit()
    return seller, buyer, store, product, variant, address


def test_hu_prom_01_public_catalog_uses_active_special_price_and_validates_regular_price(api_context):
    client, db, _auth, token_for = api_context
    now = datetime.now(timezone.utc)
    seller, _buyer, store, _product, variant, _address = _seed_cart(db, "01", price=100000)
    variant.special_price = 80000
    variant.special_starts_at = now - timedelta(days=1)
    variant.special_ends_at = now + timedelta(days=1)
    db.commit()

    public_detail = client.get(f"/api/v1/catalog/products/producto-prom-01?store_id={store.id}")
    seller_patch = client.patch(
        f"/api/v1/seller/variants/{variant.id}",
        headers=token_for(seller.id),
        json={"special_price": 120000},
    )

    public_variant = public_detail.json()["variants"][0]
    assert public_detail.status_code == 200
    assert public_variant["price"] == 80000
    assert public_variant["regular_price"] == 100000
    assert public_variant["special_price_active"] is True
    assert seller_patch.status_code == 400
    assert "precio especial" in seller_patch.json()["detail"]


def test_hu_prom_02_volume_promotions_apply_automatically_and_expired_coupon_is_rejected(api_context):
    client, db, _auth, token_for = api_context
    now = datetime.now(timezone.utc)
    seller, buyer, store, _product, _variant, _address = _seed_cart(db, "02", price=10000, quantity=3)
    db.add_all(
        [
            Promotion(
                store_id=store.id,
                name="3x2 automatico",
                discount_type=DiscountType.volume,
                value=0,
                min_quantity=3,
                pay_quantity=2,
                scope=PromotionScope.store,
                product_ids=[],
                active=True,
            ),
            Coupon(
                store_id=store.id,
                code="AHORRA10",
                discount_type=DiscountType.percent,
                value=10,
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=1),
                scope=PromotionScope.store,
                product_ids=[],
                active=True,
            ),
            Coupon(
                store_id=store.id,
                code="VENCIDO",
                discount_type=DiscountType.fixed,
                value=5000,
                ends_at=now - timedelta(days=1),
                scope=PromotionScope.store,
                product_ids=[],
                active=True,
            ),
        ]
    )
    db.commit()

    listed = client.get("/api/v1/seller/promotions", headers=token_for(seller.id))
    quote = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={"coupon_code": "ahorra10"})
    expired = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={"coupon_code": "VENCIDO"})

    assert listed.status_code == 200
    assert listed.json()[0]["pay_quantity"] == 2
    assert quote.status_code == 200
    discounts = {line["source_type"]: line["amount"] for line in quote.json()["discounts"]}
    assert discounts == {"promotion": 10000, "coupon": 3000}
    assert quote.json()["subtotal"] == 17000
    assert expired.status_code == 400
    assert "Cupon invalido o expirado" in expired.json()["detail"]


def test_hu_prom_03_margin_reports_missing_cost_instead_of_wrong_value(api_context):
    client, db, _auth, token_for = api_context
    seller, _buyer, _store, _product, _variant, _address = _seed_cart(db, "03", price=65000, cost=None)

    response = client.get("/api/v1/seller/products", headers=token_for(seller.id))

    variant = response.json()["items"][0]["variants"][0]
    assert response.status_code == 200
    assert variant["cost"] is None
    assert variant["margin"] is None
    assert variant["margin_missing_cost"] is True


def test_hu_prom_04_extra_charges_are_visible_in_checkout_and_historical_orders_do_not_change(api_context):
    client, db, _auth, token_for = api_context
    seller, buyer, store, _product, _variant, address = _seed_cart(db, "04", price=100000, quantity=1)
    created = client.post(
        "/api/v1/seller/extra-charges",
        headers=token_for(seller.id),
        json={"name": "Empaque regalo", "charge_type": "fixed", "value": 7000, "scope": "store"},
    )
    assert created.status_code == 201
    charge_id = created.json()["id"]

    quote = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={})
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )
    assert checkout.status_code == 201
    order = checkout.json()["orders"][0]
    client.patch(f"/api/v1/seller/extra-charges/{charge_id}", headers=token_for(seller.id), json={"value": 9900, "active": False})
    historical = client.get(f"/api/v1/orders/{order['id']}", headers=token_for(buyer.id))

    assert quote.status_code == 200
    assert quote.json()["extra_charges"][0]["name"] == "Empaque regalo"
    assert quote.json()["extra_charge_total"] == 7000
    assert order["adjustments"][0]["kind"] == "extra_charge"
    assert order["adjustments"][0]["amount"] == 7000
    assert historical.json()["adjustments"][0]["amount"] == 7000


def test_pricing_keeps_store_scope_and_checkout_matches_quote_totals(api_context):
    client, db, _auth, token_for = api_context
    buyer = User(id="buyer-prom-scope", email="buyer-prom-scope@example.com", name="Buyer PROM", role=UserRole.buyer)
    address = Address(id="addr-prom-scope", user_id=buyer.id, recipient_name="Ana", address_line="Calle 1", city="Bogota")
    cart = Cart(id="cart-prom-scope", user_id=buyer.id)
    store_a = Store(id="store-prom-scope-a", slug="store-prom-scope-a", name="Tienda A", social_links={})
    store_b = Store(id="store-prom-scope-b", slug="store-prom-scope-b", name="Tienda B", social_links={})
    product_a = Product(id="product-prom-scope-a", store_id=store_a.id, slug="producto-scope-a", name="Producto A", status=ProductStatus.active)
    product_b = Product(id="product-prom-scope-b", store_id=store_b.id, slug="producto-scope-b", name="Producto B", status=ProductStatus.active)
    variant_a = ProductVariant(id="variant-prom-scope-a", product_id=product_a.id, sku="SCOPE-A", price=10000, cost=5000)
    variant_b = ProductVariant(id="variant-prom-scope-b", product_id=product_b.id, sku="SCOPE-B", price=20000, cost=8000)
    warehouse_a = Warehouse(id="wh-prom-scope-a", store_id=store_a.id, name="Principal A", active=True, is_default=True)
    warehouse_b = Warehouse(id="wh-prom-scope-b", store_id=store_b.id, name="Principal B", active=True, is_default=True)
    db.add_all([buyer, address, cart, store_a, store_b, product_a, product_b, variant_a, variant_b, warehouse_a, warehouse_b])
    db.flush()
    db.add_all(
        [
            StockLevel(variant_id=variant_a.id, warehouse_id=warehouse_a.id, quantity=5),
            StockLevel(variant_id=variant_b.id, warehouse_id=warehouse_b.id, quantity=5),
            CartItem(cart_id=cart.id, variant_id=variant_a.id, quantity=1),
            CartItem(cart_id=cart.id, variant_id=variant_b.id, quantity=1),
            PlatformSetting(key="payment_gateway", value={"provider": "test"}),
            PlatformSetting(key=f"store_config:{store_a.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0}),
            PlatformSetting(key=f"store_config:{store_b.id}", value={"shipping_flat_cost": 0, "shipping_free_threshold": 0}),
            Promotion(store_id=store_a.id, name="Promo tienda A", discount_type=DiscountType.percent, value=50, scope=PromotionScope.store, product_ids=[], active=True),
            ExtraCharge(store_id=store_b.id, name="Cargo tienda B", charge_type=ChargeType.fixed, value=3000, scope=PromotionScope.store, product_ids=[], active=True),
        ]
    )
    db.commit()

    quote = client.post("/api/v1/checkout/quote", headers=token_for(buyer.id), json={})
    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "card"},
    )

    assert quote.status_code == 200
    assert quote.json()["discount"] == 5000
    assert quote.json()["extra_charge_total"] == 3000
    assert quote.json()["total"] == 28000
    assert checkout.status_code == 201
    orders = checkout.json()["orders"]
    assert sum(order["subtotal"] for order in orders) == quote.json()["subtotal"]
    assert sum(order["total"] for order in orders) == quote.json()["total"]
    adjustments = [line for order in orders for line in order["adjustments"]]
    assert {(line["kind"], line["amount"]) for line in adjustments} == {("discount", 5000), ("extra_charge", 3000)}
