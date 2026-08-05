from app.models import Address, Cart, CartItem, PlatformSetting, Product, ProductVariant, PayoutAccount, StockLevel, Store, StoreMember, User, Warehouse
from app.models.catalog import ProductStatus
from app.models.payout import PayoutAccountType
from app.models.user import UserRole


def _seller_store(db):
    seller = User(id="seller-tda-03", email="seller-tda-03@example.com", name="Seller TDA", role=UserRole.seller)
    store = Store(id="store-tda-03", slug="pagos", name="Pagos Store", social_links={})
    db.add_all([seller, store, PlatformSetting(key="payment_gateway", value={"provider": "test"})])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.commit()
    return seller, store


def _add_manual_accounts(db, store_id):
    bank = PayoutAccount(
        id="bank-tda-03",
        store_id=store_id,
        type=PayoutAccountType.bank,
        label="Banco principal",
        bank_name="Bancolombia",
        account_type="ahorros",
        account_number="123",
        holder_name="Pagos Store",
        active=True,
    )
    breb = PayoutAccount(
        id="breb-tda-03",
        store_id=store_id,
        type=PayoutAccountType.bre_b,
        label="Bre-B principal",
        breb_key="pagos@breb",
        holder_name="Pagos Store",
        active=True,
    )
    db.add_all([bank, breb])
    db.commit()
    return bank, breb


def test_hu_tda_03_payment_options_follow_enabled_methods_and_active_accounts(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db)
    _bank, _breb = _add_manual_accounts(db, store.id)

    settings = client.put(
        "/api/v1/seller/store/settings",
        headers=token_for(seller.id),
        json={
            "payment_methods": {
                "gateway_enabled": True,
                "manual_transfer_enabled": True,
                "manual_breb_enabled": False,
            },
            "shipping_flat_cost": 12900,
            "shipping_free_threshold": 120000,
            "shipping_zones": [],
        },
    )
    assert settings.status_code == 200

    options = client.get(f"/api/v1/catalog/stores/{store.id}/payment-options")
    assert options.status_code == 200
    body = options.json()
    assert {"card", "pse", "nequi", "transfer"} <= set(body["payment_methods"])
    assert "breb" not in body["payment_methods"]
    assert [account["type"] for account in body["payout_accounts"]] == ["bank"]


def test_hu_tda_03_disabled_method_is_hidden_and_rejected_in_checkout(api_context):
    client, db, _auth, token_for = api_context
    seller, store = _seller_store(db)
    bank, _breb = _add_manual_accounts(db, store.id)
    buyer = User(id="buyer-tda-03", email="buyer-tda-03@example.com", name="Buyer TDA", role=UserRole.buyer)
    address = Address(id="addr-tda-03", user_id=buyer.id, recipient_name="Ana", address_line="Calle 1", city="Bogota")
    product = Product(id="product-tda-03", store_id=store.id, slug="collar", name="Collar", status=ProductStatus.active)
    variant = ProductVariant(id="variant-tda-03", product_id=product.id, sku="SKU-TDA-03", price=50000)
    warehouse = Warehouse(id="wh-tda-03", store_id=store.id, name="Principal", active=True, is_default=True)
    cart = Cart(id="cart-tda-03", user_id=buyer.id)
    db.add_all([buyer, address, product, variant, warehouse, cart])
    db.flush()
    db.add_all(
        [
            StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=5),
            CartItem(cart_id=cart.id, variant_id=variant.id, quantity=1),
        ]
    )
    db.commit()

    client.put(
        "/api/v1/seller/store/settings",
        headers=token_for(seller.id),
        json={
            "payment_methods": {
                "gateway_enabled": False,
                "manual_transfer_enabled": False,
                "manual_breb_enabled": True,
            }
        },
    )

    options = client.get(f"/api/v1/catalog/stores/{store.id}/payment-options")
    assert options.status_code == 200
    assert "transfer" not in options.json()["payment_methods"]
    assert "breb" in options.json()["payment_methods"]

    checkout = client.post(
        "/api/v1/checkout",
        headers=token_for(buyer.id),
        json={"address_id": address.id, "payment_method": "transfer", "payout_account_id": bank.id},
    )
    assert checkout.status_code == 400
    assert "Metodo de pago no disponible" in checkout.json()["detail"]
