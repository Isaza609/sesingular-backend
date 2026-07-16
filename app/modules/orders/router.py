from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Address, Cart, CartItem, Coupon, Order, OrderItem, Payment, PlatformSetting, ProductVariant, Store, Warehouse
from app.models.order import OrderStatus, SaleChannel
from app.models.payment import PaymentStatus
from app.modules.auth.deps import get_current_user
from app.models.user import User
from app.modules.common.permissions import get_seller_store, require_buyer
from app.modules.inventory.service import release_order, reserve_variant
from app.modules.orders.schemas import AddressIn, AddressPatch, CartItemIn, CartItemPatch, CheckoutIn, CartOut, OrderOut, OrderStatusPatch, WarehouseAssign

buyer_router = APIRouter(tags=["buyer"])
seller_router = APIRouter(prefix="/seller", tags=["seller-orders"])

FREE_SHIPPING = 120_000
SHIPPING_COST = 12_900


def _address_out(address: Address) -> dict:
    return {"id": address.id, "label": address.label, "recipient_name": address.recipient_name, "phone": address.phone, "address_line": address.address_line, "city": address.city, "region": address.region, "postal_code": address.postal_code, "is_default": address.is_default}


def _order_out(order: Order) -> dict:
    return {
        "id": order.id,
        "store_id": order.store_id,
        "store_name": order.store.name,
        "buyer_id": order.buyer_id,
        "warehouse_id": order.warehouse_id,
        "address_id": order.address_id,
        "channel": order.channel.value,
        "status": order.status.value,
        "subtotal": order.subtotal,
        "shipping_cost": order.shipping_cost,
        "tax": order.tax,
        "total": order.total,
        "notes": order.notes,
        "created_at": order.created_at,
        "items": [{"id": item.id, "variant_id": item.variant_id, "product_name": item.product_name, "sku": item.sku, "quantity": item.quantity, "unit_price": item.unit_price, "unit_cost": item.unit_cost} for item in order.items],
        "payments": [{"id": payment.id, "provider": payment.provider, "method": payment.method, "status": payment.status.value, "amount": payment.amount, "currency": payment.currency} for payment in order.payments],
    }


def _get_cart(user: User, db: Session) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def _resolve_variant(body: CartItemIn, db: Session) -> ProductVariant:
    if body.variant_id:
        variant = db.get(ProductVariant, body.variant_id)
    else:
        stmt = select(ProductVariant).where(ProductVariant.product_id == body.product_id, ProductVariant.active.is_(True))
        if body.color:
            stmt = stmt.where(ProductVariant.color == body.color)
        variant = db.scalars(stmt.order_by(ProductVariant.price)).first()
    if variant is None or not variant.active or variant.product.status.value != "active" or not variant.product.store.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no disponible")
    return variant


def _cart_out(cart: Cart) -> dict:
    items = []
    for item in cart.items:
        variant = item.variant
        stock = sum(max(0, level.quantity - level.reserved) for level in variant.stock_levels)
        items.append({"id": item.id, "variant_id": variant.id, "product_id": variant.product_id, "slug": variant.product.slug, "name": variant.product.name, "sku": variant.sku, "color": variant.color, "image": variant.product.images[0].url if variant.product.images else None, "quantity": item.quantity, "unit_price": variant.price, "stock": stock, "store_id": variant.product.store_id, "store_name": variant.product.store.name})
    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    shipping = 0 if subtotal == 0 or subtotal >= FREE_SHIPPING else SHIPPING_COST
    return {"id": cart.id, "items": items, "subtotal": subtotal, "shipping_cost": shipping, "tax": 0, "total": subtotal + shipping}


@buyer_router.get("/addresses")
def list_addresses(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    rows = db.scalars(select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.created_at.desc())).all()
    return [_address_out(row) for row in rows]


@buyer_router.post("/addresses", status_code=status.HTTP_201_CREATED)
def create_address(body: AddressIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    if body.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    address = Address(user_id=user.id, **body.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return _address_out(address)


@buyer_router.patch("/addresses/{address_id}")
def patch_address(address_id: str, body: AddressPatch, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dirección no encontrada")
    values = body.model_dump(exclude_unset=True)
    if values.get("is_default"):
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    for key, value in values.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return _address_out(address)


@buyer_router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dirección no encontrada")
    db.delete(address)
    db.commit()


@buyer_router.get("/cart", response_model=CartOut)
def get_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return CartOut.model_validate(_cart_out(_get_cart(user, db)))


@buyer_router.post("/cart/items", response_model=CartOut)
def add_cart_item(body: CartItemIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    variant = _resolve_variant(body, db)
    cart = _get_cart(user, db)
    item = db.scalar(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant.id))
    if item:
        item.quantity = min(100, item.quantity + body.quantity)
    else:
        item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=body.quantity)
        db.add(item)
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.patch("/cart/items/{item_id}", response_model=CartOut)
def patch_cart_item(item_id: str, body: CartItemPatch, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artículo no encontrado")
    item.quantity = body.quantity
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.delete("/cart/items/{item_id}", response_model=CartOut)
def delete_cart_item(item_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artículo no encontrado")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.delete("/cart", response_model=CartOut)
def clear_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


def _coupon_discount(code: str | None, subtotal: int, store_id: str, db: Session) -> int:
    if not code:
        return 0
    coupon = db.scalar(select(Coupon).where(Coupon.store_id == store_id, func.upper(Coupon.code) == code.upper(), Coupon.active.is_(True)))
    now = datetime.now(timezone.utc)
    if coupon is None or (coupon.starts_at and coupon.starts_at > now) or (coupon.ends_at and coupon.ends_at < now) or (coupon.max_uses is not None and coupon.used_count >= coupon.max_uses):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cupón inválido o expirado")
    if coupon.discount_type.value == "percent":
        return min(subtotal, subtotal * coupon.value // 100)
    return min(subtotal, coupon.value)


def _shipping_config(store_id: str, db: Session) -> tuple[int, int]:
    row = db.get(PlatformSetting, f"store_config:{store_id}")
    config = row.value if row else {}
    return int(config.get("shipping_flat_cost", SHIPPING_COST)), int(config.get("shipping_free_threshold", FREE_SHIPPING))


@buyer_router.post("/checkout/quote")
def checkout_quote(body: dict, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    data = _cart_out(cart)
    groups = defaultdict(int)
    for item in data["items"]:
        groups[item["store_id"]] += item["quantity"] * item["unit_price"]
    discount = sum(_coupon_discount(body.get("coupon_code"), subtotal, store_id, db) for store_id, subtotal in groups.items())
    subtotal = data["subtotal"] - discount
    shipping = sum(0 if subtotal >= _shipping_config(store_id, db)[1] else _shipping_config(store_id, db)[0] for store_id, subtotal in groups.items())
    return {"subtotal": subtotal, "discount": discount, "shipping_cost": shipping, "tax": 0, "total": subtotal + shipping, "currency": "COP"}


@buyer_router.post("/checkout", response_model=dict, status_code=status.HTTP_201_CREATED)
def checkout(body: CheckoutIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    if not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El carrito está vacío")
    address = db.get(Address, body.address_id) if body.address_id else None
    if address is not None and address.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La dirección no pertenece al usuario")
    if address is None and body.address:
        if body.address.is_default:
            db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
        address = Address(user_id=user.id, **body.address.model_dump())
        db.add(address)
        db.flush()
    if address is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dirección inválida")
    groups: dict[str, list[CartItem]] = defaultdict(list)
    for item in cart.items:
        groups[item.variant.product.store_id].append(item)
    created: list[Order] = []
    try:
        commission_setting = db.get(PlatformSetting, "commission")
        commission_pct = int((commission_setting.value if commission_setting else {}).get("value", 0))
        for store_id, items in groups.items():
            subtotal_before = sum(item.quantity * item.variant.price for item in items)
            discount = _coupon_discount(body.coupon_code, subtotal_before, store_id, db)
            subtotal = subtotal_before - discount
            flat_shipping, free_threshold = _shipping_config(store_id, db)
            shipping = 0 if subtotal >= free_threshold else flat_shipping
            order = Order(store_id=store_id, buyer_id=user.id, address_id=address.id, channel=SaleChannel.online, status=OrderStatus.pending, subtotal=subtotal, shipping_cost=shipping, tax=0, total=subtotal + shipping, notes=body.notes)
            db.add(order)
            db.flush()
            for cart_item in items:
                reserve_variant(db, cart_item.variant_id, cart_item.quantity, order.id)
                db.add(OrderItem(order_id=order.id, variant_id=cart_item.variant_id, product_name=cart_item.variant.product.name, sku=cart_item.variant.sku, quantity=cart_item.quantity, unit_price=cart_item.variant.price, unit_cost=cart_item.variant.cost))
            db.add(Payment(order_id=order.id, provider="pending", method=body.payment_method, status=PaymentStatus.pending, amount=order.total, platform_fee=order.total * commission_pct // 100, seller_amount=order.total - (order.total * commission_pct // 100), currency="COP"))
            created.append(order)
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    for order in created:
        db.refresh(order)
    return {"orders": [OrderOut.model_validate(_order_out(order)) for order in created], "payment_required": True}


@buyer_router.get("/orders", response_model=list[OrderOut])
def buyer_orders(status_filter: str | None = Query(None, alias="status"), user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    stmt = select(Order).where(Order.buyer_id == user.id).order_by(Order.created_at.desc())
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    return [OrderOut.model_validate(_order_out(order)) for order in db.scalars(stmt).all()]


@buyer_router.get("/orders/{order_id}", response_model=OrderOut)
def buyer_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return OrderOut.model_validate(_order_out(order))


@buyer_router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya no se puede cancelar")
    release_order(db, order)
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))
