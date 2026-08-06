"""Utilidades de siembra para los tests de integración de la Épica 10 (Pagos).

Construyen datos reales en la BD de test (comprador, tienda con equipo, producto con
stock, pedido con reserva y pago pendiente) para ejercitar las APIs de pago tal como
las consume el frontend.
"""

from __future__ import annotations

from app.models import (
    Address,
    Order,
    OrderItem,
    Payment,
    PayoutAccount,
    PlatformSetting,
    Product,
    ProductVariant,
    StockLevel,
    Store,
    StoreMember,
    User,
    Warehouse,
)
from app.models.catalog import ProductStatus
from app.models.order import OrderStatus, SaleChannel
from app.models.payment import PaymentStatus
from app.models.payout import PayoutAccountType
from app.models.user import UserRole
from app.modules.inventory.service import reserve_variant
from app.modules.payments import service as payment_service


def ensure_gateway(db, *, webhook_secret: str | None = None) -> None:
    row = db.get(PlatformSetting, "payment_gateway")
    value = {"provider": "test"}
    if webhook_secret:
        value["webhook_secret"] = webhook_secret
    if row is None:
        db.add(PlatformSetting(key="payment_gateway", value=value))
    else:
        row.value = value


def seed_store(db, suffix: str, *, payment_methods: dict | None = None):
    """Crea vendedor + tienda + almacén + producto/variante con stock."""
    seller = User(id=f"seller-pag-{suffix}", email=f"seller-pag-{suffix}@example.com", name=f"Seller {suffix}", role=UserRole.seller)
    store = Store(
        id=f"store-pag-{suffix}",
        slug=f"store-pag-{suffix}",
        name=f"Tienda {suffix}",
        contact_email=f"tienda-{suffix}@example.com",
        contact_phone="+571111111",
        whatsapp_phone="+572222222",
        social_links={},
    )
    product = Product(id=f"product-pag-{suffix}", store_id=store.id, slug=f"producto-pag-{suffix}", name=f"Producto {suffix}", status=ProductStatus.active)
    variant = ProductVariant(id=f"variant-pag-{suffix}", product_id=product.id, sku=f"PAG-{suffix}", price=50000, cost=20000)
    warehouse = Warehouse(id=f"wh-pag-{suffix}", store_id=store.id, name="Bodega", active=True, is_default=True)
    db.add_all([seller, store, product, variant, warehouse])
    db.flush()
    db.add(StoreMember(store_id=store.id, user_id=seller.id, role="owner"))
    db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=10))
    db.add(
        PlatformSetting(
            key=f"store_config:{store.id}",
            value={"shipping_mode": "flat", "shipping_flat_cost": 0, "shipping_free_threshold": 0, "payment_methods": payment_methods or {"gateway_enabled": True, "manual_transfer_enabled": True, "manual_breb_enabled": True}},
        )
    )
    db.commit()
    return seller, store, product, variant, warehouse


def seed_buyer(db, suffix: str) -> User:
    buyer = User(id=f"buyer-pag-{suffix}", email=f"buyer-pag-{suffix}@example.com", name="Ana Perez", role=UserRole.buyer)
    db.add(buyer)
    db.commit()
    return buyer


def seed_payout_account(db, store: Store, *, type_: PayoutAccountType = PayoutAccountType.bank, active: bool = True) -> PayoutAccount:
    account = PayoutAccount(
        store_id=store.id,
        type=type_,
        label="Ahorros principal",
        bank_name="Bancolombia" if type_ == PayoutAccountType.bank else None,
        account_type="ahorros" if type_ == PayoutAccountType.bank else None,
        account_number="12345678901" if type_ == PayoutAccountType.bank else None,
        breb_key="nova@breb" if type_ == PayoutAccountType.bre_b else None,
        holder_name="Nova Ropa SAS",
        holder_document="900123456",
        active=active,
    )
    db.add(account)
    db.commit()
    return account


def seed_manual_order(
    db,
    store: Store,
    buyer: User,
    variant: ProductVariant,
    *,
    quantity: int = 2,
    method: str = "transfer",
    payout_account: PayoutAccount | None = None,
    reserve: bool = True,
):
    """Crea un pedido pendiente con stock reservado y un pago manual pendiente."""
    total = variant.price * quantity
    address = Address(user_id=buyer.id, recipient_name="Ana Perez", phone="+573001112233", address_line="Calle 10 # 20-30", city="Bogota", region="Cundinamarca")
    db.add(address)
    db.flush()
    order = Order(store_id=store.id, buyer_id=buyer.id, address_id=address.id, channel=SaleChannel.online, status=OrderStatus.pending, subtotal=total, total=total)
    db.add(order)
    db.flush()
    db.add(OrderItem(order_id=order.id, variant_id=variant.id, product_name=variant.product.name, sku=variant.sku, quantity=quantity, unit_price=variant.price, unit_cost=variant.cost))
    if reserve:
        reserve_variant(db, variant.id, quantity, order_id=order.id)
    payment = Payment(
        order_id=order.id,
        provider="manual",
        method=method,
        status=PaymentStatus.pending,
        amount=total,
        seller_amount=total,
        currency="COP",
        payout_account_id=payout_account.id if payout_account else None,
    )
    db.add(payment)
    db.flush()
    payment_service.record_creation(db, payment, actor_role="buyer", actor_user_id=buyer.id)
    db.commit()
    return order, payment, address


def reserved_units(db, variant_id: str) -> int:
    levels = db.query(StockLevel).filter(StockLevel.variant_id == variant_id).all()
    return sum(level.reserved for level in levels)
