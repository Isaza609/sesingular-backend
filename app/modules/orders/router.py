from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Address, Cart, CartItem, CheckoutGroup, Coupon, Favorite, Order, OrderAdjustment, OrderItem, Payment, PayoutAccount, PlatformSetting, Product, ProductVariant, Store, StoreMember, Warehouse
from app.models.catalog import ProductStatus
from app.models.order import OrderAdjustmentKind, OrderStatus, SaleChannel
from app.models.payment import PaymentStatus
from app.modules.auth.deps import get_current_user
from app.models.user import User
from app.models.payout import PayoutAccountType
from app.modules.catalog.router import _product_out, get_store_settings_value, payment_options_for_store
from app.modules.common import mailer
from app.modules.common.permissions import get_seller_store, require_buyer
from app.modules.common.storage import signed_url, upload_receipt
from app.modules.inventory.service import active_warehouse_count, available_for_variant, consume_variant, reserve_variant, restock_order, single_active_warehouse
from app.modules.orders.schemas import AddressIn, AddressOut, AddressPatch, CartItemIn, CartItemPatch, CheckoutConfirmationOut, CheckoutIn, CheckoutQuoteIn, CheckoutQuoteOut, CartOut, OrderOut, PaymentOut, PurchaseOut, OrderStatusPatch, ShipmentOut, WarehouseAssign
from app.modules.payments import service as payment_service
from app.modules.pricing.service import calculate_store_pricing, effective_unit_price, priced_items_from_cart_items

buyer_router = APIRouter(tags=["buyer"])
seller_router = APIRouter(prefix="/seller", tags=["seller-orders"])

FREE_SHIPPING = 120_000
SHIPPING_COST = 12_900


def _address_out(address: Address) -> dict:
    return {"id": address.id, "label": address.label, "recipient_name": address.recipient_name, "phone": address.phone, "address_line": address.address_line, "city": address.city, "region": address.region, "postal_code": address.postal_code, "is_default": address.is_default}


def _order_out(order: Order) -> dict:
    return {
        "id": order.id,
        "checkout_group_id": order.checkout_group_id,
        "store_id": order.store_id,
        "store_name": order.store.name,
        "buyer_id": order.buyer_id,
        "buyer_name": order.buyer.name if order.buyer else None,
        "warehouse_id": order.warehouse_id,
        "address_id": order.address_id,
        "channel": order.channel.value,
        "status": order.status.value,
        "assignee_id": order.assignee_id,
        "assigned_at": order.assigned_at,
        "cancel_reason": order.cancel_reason,
        "subtotal": order.subtotal,
        "shipping_cost": order.shipping_cost,
        "tax": order.tax,
        "total": order.total,
        "notes": order.notes,
        "created_at": order.created_at,
        "address": _address_out(order.address) if order.address else None,
        "shipping": None,
        "shipping_to_agree": order.shipping_cost == 0 and any(
            (item.variant and item.variant.product and item.variant.product.shipping_mode == "to_agree") for item in order.items
        ),
        "store_contact": {
            "email": order.store.contact_email,
            "phone": order.store.contact_phone,
            "whatsapp_phone": order.store.whatsapp_phone,
        },
        "items": [{"id": item.id, "variant_id": item.variant_id, "product_name": item.product_name, "sku": item.sku, "quantity": item.quantity, "unit_price": item.unit_price, "unit_cost": item.unit_cost} for item in order.items],
        "adjustments": [
            {
                "kind": adjustment.kind.value,
                "source_type": adjustment.source_type,
                "source_id": adjustment.source_id,
                "name": adjustment.name,
                "amount": adjustment.amount,
                "code": (adjustment.metadata_json or {}).get("code"),
            }
            for adjustment in order.adjustments
        ],
        "payments": [{"id": payment.id, "provider": payment.provider, "method": payment.method, "status": payment.status.value, "amount": payment.amount, "currency": payment.currency} for payment in order.payments],
    }


def _payout_account_out(account: PayoutAccount | None) -> dict | None:
    """Datos de la cuenta destino que ve el comprador para transferir."""
    if account is None:
        return None
    return {
        "id": account.id,
        "type": account.type.value,
        "label": account.label,
        "bank_name": account.bank_name,
        "account_type": account.account_type,
        "account_number": account.account_number,
        "breb_key": account.breb_key,
        "holder_name": account.holder_name,
        "holder_document": account.holder_document,
        "active": account.active,
    }


MANUAL_METHODS = {"transfer", "breb"}
ADDRESS_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol buyer o recurso fuera del scope del comprador."},
    404: {"description": "Direccion no encontrada."},
    422: {"description": "Validacion Pydantic."},
}


def _payment_out(payment: Payment | None, with_receipt: bool = False) -> dict | None:
    """Estado del pago manual, con la cuenta destino y el comprobante firmado."""
    if payment is None:
        return None
    difference = payment.amount - payment.received_amount if payment.received_amount is not None else None
    data = {
        "id": payment.id,
        "order_id": payment.order_id,
        "method": payment.method,
        "provider": payment.provider,
        "status": payment.status.value,
        "amount": payment.amount,
        "currency": payment.currency,
        "is_manual": payment.method in MANUAL_METHODS,
        "payout_account": _payout_account_out(payment.payout_account),
        "has_receipt": bool(payment.receipt_path),
        "receipt_url": None,
        "receipt_uploaded_at": payment.receipt_uploaded_at,
        "received_amount": payment.received_amount,
        "difference": difference,
        "review_note": payment.review_note,
        "reviewed_at": payment.reviewed_at,
    }
    if with_receipt:
        data["receipt_url"] = signed_url(payment.receipt_path)
    return data


def _latest_payment(order: Order) -> Payment | None:
    if not order.payments:
        return None
    return sorted(order.payments, key=lambda p: p.created_at)[-1]


def _get_cart(user: User, db: Session) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def _store_contact(store: Store) -> dict:
    return {
        "email": store.contact_email,
        "phone": store.contact_phone,
        "whatsapp_phone": store.whatsapp_phone,
    }


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _location_from_address(address: Address | AddressIn | None) -> dict:
    if address is None:
        return {}
    return {
        "city": getattr(address, "city", None),
        "region": getattr(address, "region", None),
        "country": getattr(address, "country", None),
    }


def _availability_for_item(item: CartItem) -> tuple[bool, str, str | None, int]:
    variant = item.variant
    product = variant.product if variant else None
    store = product.store if product else None
    stock = available_for_variant(variant) if variant else 0
    if variant is None or product is None or not variant.active or product.status in (ProductStatus.draft, ProductStatus.discontinued):
        return False, "product_unavailable", "El producto ya no esta disponible", stock
    if store is None or not store.active:
        return False, "store_inactive", "La tienda ya no esta activa", stock
    if product.status == ProductStatus.out_of_stock or stock <= 0:
        return False, "out_of_stock", "Producto agotado", stock
    if stock < item.quantity:
        return False, "insufficient_stock", f"Solo quedan {stock} unidad(es) disponibles", stock
    return True, "available", None, stock


def _cart_item_out(item: CartItem) -> dict:
    variant = item.variant
    pricing = effective_unit_price(variant)
    available, availability_status, availability_message, stock = _availability_for_item(item)
    return {
        "id": item.id,
        "variant_id": variant.id,
        "product_id": variant.product_id,
        "slug": variant.product.slug,
        "name": variant.product.name,
        "sku": variant.sku,
        "color": variant.color,
        "image": variant.product.images[0].url if variant.product.images else None,
        "quantity": item.quantity,
        "unit_price": pricing["price"],
        "regular_unit_price": pricing["regular_price"],
        "special_price_applied": pricing["special_price_active"],
        "stock": stock,
        "available": available,
        "availability_status": availability_status,
        "availability_message": availability_message,
        "store_id": variant.product.store_id,
        "store_name": variant.product.store.name,
    }


def _resolve_variant(body: CartItemIn, db: Session) -> ProductVariant:
    if body.variant_id:
        variant = db.get(ProductVariant, body.variant_id)
    else:
        stmt = select(ProductVariant).where(ProductVariant.product_id == body.product_id, ProductVariant.active.is_(True))
        if body.color:
            stmt = stmt.where(ProductVariant.color == body.color)
        variant = db.scalars(stmt.order_by(ProductVariant.price)).first()
    if variant is None or not variant.active or variant.product.status in (ProductStatus.draft, ProductStatus.discontinued) or not variant.product.store.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no disponible")
    if variant.product.status == ProductStatus.out_of_stock:
        raise HTTPException(status.HTTP_409_CONFLICT, "Producto agotado")
    stock = available_for_variant(variant)
    if stock < body.quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente")
    return variant


def _cart_out(cart: Cart) -> dict:
    items = [_cart_item_out(item) for item in cart.items]
    grouped: dict[str, dict] = {}
    for item in items:
        group = grouped.setdefault(
            item["store_id"],
            {
                "store_id": item["store_id"],
                "store_name": item["store_name"],
                "items": [],
                "regular_subtotal": 0,
                "subtotal": 0,
            },
        )
        group["items"].append(item)
        group["regular_subtotal"] += item["quantity"] * item["regular_unit_price"]
        group["subtotal"] += item["quantity"] * item["unit_price"]
    regular_subtotal = sum(item["quantity"] * item["regular_unit_price"] for item in items)
    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    shipping = 0 if subtotal == 0 or subtotal >= FREE_SHIPPING else SHIPPING_COST
    blocking_reasons = [
        item["availability_message"] or "Item no disponible"
        for item in items
        if not item["available"]
    ]
    return {
        "id": cart.id,
        "items": items,
        "store_groups": list(grouped.values()),
        "regular_subtotal": regular_subtotal,
        "subtotal": subtotal,
        "discount": 0,
        "extra_charge_total": 0,
        "shipping_cost": shipping,
        "tax": 0,
        "total": subtotal + shipping,
        "checkout_blocked": bool(blocking_reasons),
        "blocking_reasons": blocking_reasons,
    }


def _assert_cart_ready(cart: Cart) -> None:
    failures = [_cart_item_out(item) for item in cart.items if not _availability_for_item(item)[0]]
    if failures:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {
                "message": "Hay productos del carrito que no pueden continuar al checkout",
                "items": [
                    {
                        "cart_item_id": item["id"],
                        "variant_id": item["variant_id"],
                        "product_name": item["name"],
                        "availability_status": item["availability_status"],
                        "availability_message": item["availability_message"],
                    }
                    for item in failures
                ],
            },
        )


@buyer_router.get(
    "/addresses",
    response_model=list[AddressOut],
    status_code=status.HTTP_200_OK,
    summary="Listar direcciones",
    description="Rol permitido: buyer. HU-USR-03. Lista solo las direcciones de envio del comprador autenticado.",
    response_description="Direcciones guardadas del comprador.",
    responses=ADDRESS_RESPONSES,
)
def list_addresses(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    rows = db.scalars(select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.created_at.desc())).all()
    return [_address_out(row) for row in rows]


@buyer_router.post(
    "/addresses",
    response_model=AddressOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear direccion",
    description="Rol permitido: buyer. HU-USR-03. Crea una direccion de envio asociada al comprador autenticado.",
    response_description="Direccion creada y disponible para checkout.",
    responses=ADDRESS_RESPONSES,
)
def create_address(body: AddressIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    if body.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    address = Address(user_id=user.id, **body.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return _address_out(address)


@buyer_router.patch(
    "/addresses/{address_id}",
    response_model=AddressOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar direccion",
    description="Rol permitido: buyer. HU-USR-03. Actualiza solo una direccion propia del comprador autenticado.",
    response_description="Direccion actualizada.",
    responses=ADDRESS_RESPONSES,
)
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


@buyer_router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar direccion",
    description="Rol permitido: buyer. HU-USR-03. Elimina solo una direccion propia del comprador autenticado.",
    response_description="Direccion eliminada sin contenido.",
    responses=ADDRESS_RESPONSES,
)
def delete_address(address_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dirección no encontrada")
    db.delete(address)
    db.commit()


@buyer_router.get("/favorites")
def list_favorites(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    favs = db.scalars(
        select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    ).all()
    return [_product_out(f.product) for f in favs if f.product is not None]


@buyer_router.post("/favorites/{product_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(product_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None or product.status == ProductStatus.discontinued:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id)
    )
    if existing is None:
        db.add(Favorite(user_id=user.id, product_id=product_id))
        db.commit()
    return {"product_id": product_id, "favorited": True}


@buyer_router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(product_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    favorite = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id)
    )
    if favorite is not None:
        db.delete(favorite)
        db.commit()


@buyer_router.get(
    "/cart",
    response_model=CartOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar carrito",
    description="Rol permitido: buyer. HU-CHK-01 y HU-INV-07. Retorna el carrito persistente del comprador con stock vigente, precios efectivos y bloqueos antes del checkout.",
    response_description="Carrito persistente actualizado con disponibilidad real.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 422: {"description": "Validacion Pydantic."}},
)
def get_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return CartOut.model_validate(_cart_out(_get_cart(user, db)))


@buyer_router.post(
    "/cart/items",
    response_model=CartOut,
    status_code=status.HTTP_200_OK,
    summary="Agregar item al carrito",
    description="Rol permitido: buyer. HU-CHK-01 y HU-INV-07. Agrega una variante al carrito persistente solo si mantiene disponibilidad real agregada suficiente.",
    response_description="Carrito actualizado con el item agregado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Variante no disponible."}, 409: {"description": "Producto agotado o stock insuficiente."}, 422: {"description": "Validacion Pydantic."}},
)
def add_cart_item(body: CartItemIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    variant = _resolve_variant(body, db)
    cart = _get_cart(user, db)
    item = db.scalar(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant.id))
    if item:
        new_quantity = min(100, item.quantity + body.quantity)
        if available_for_variant(variant) < new_quantity:
            raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente")
        item.quantity = new_quantity
    else:
        item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=body.quantity)
        db.add(item)
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.patch(
    "/cart/items/{item_id}",
    response_model=CartOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar item del carrito",
    description="Rol permitido: buyer. HU-CHK-01. Actualiza la cantidad de un item propio del carrito y recalcula disponibilidad antes de checkout.",
    response_description="Carrito actualizado con la nueva cantidad.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Articulo no encontrado."}, 422: {"description": "Validacion Pydantic."}},
)
def patch_cart_item(item_id: str, body: CartItemPatch, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artículo no encontrado")
    item.quantity = body.quantity
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.delete(
    "/cart/items/{item_id}",
    response_model=CartOut,
    status_code=status.HTTP_200_OK,
    summary="Eliminar item del carrito",
    description="Rol permitido: buyer. HU-CHK-01. Elimina un item propio del carrito persistente y recalcula totales.",
    response_description="Carrito actualizado sin el item eliminado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Articulo no encontrado."}, 422: {"description": "Validacion Pydantic."}},
)
def delete_cart_item(item_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artículo no encontrado")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return CartOut.model_validate(_cart_out(cart))


@buyer_router.delete(
    "/cart",
    response_model=CartOut,
    status_code=status.HTTP_200_OK,
    summary="Vaciar carrito",
    description="Rol permitido: buyer. HU-CHK-01. Elimina todos los items del carrito persistente del comprador autenticado.",
    response_description="Carrito vacio del comprador.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 422: {"description": "Validacion Pydantic."}},
)
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


def _zone_matches(zone: dict, location: dict) -> bool:
    if zone.get("active") is False:
        return False
    for field in ("city", "region", "country"):
        expected = _normalize_text(zone.get(field))
        actual = _normalize_text(location.get(field))
        if expected and expected != actual:
            return False
    return bool(_normalize_text(zone.get("city")) or _normalize_text(zone.get("region")) or _normalize_text(zone.get("country")))


def _free_shipping_window_active(config: dict) -> bool:
    """HU-ENV-04: la promoción de envío gratis solo aplica dentro de su vigencia (si tiene fechas)."""
    today = date.today()
    start = config.get("free_shipping_from")
    end = config.get("free_shipping_to")
    try:
        if start and today < date.fromisoformat(str(start)):
            return False
        if end and today > date.fromisoformat(str(end)):
            return False
    except ValueError:
        return True
    return True


def _shipping_for_store(store: Store, subtotal: int, location: dict, db: Session, *, force_to_agree: bool = False) -> dict:
    settings = get_store_settings_value(store.id, db)
    mode = settings.shipping_mode
    zones = settings.shipping_zones or []
    contact_message = "Contacta al vendedor para acordar el costo de envio."

    if mode == "to_agree" or force_to_agree:
        return {
            "mode": "to_agree",
            "cost": 0,
            "original_cost": 0,
            "to_agree": True,
            "requires_contact": True,
            "promotion_applied": False,
            "label": "Envio a convenir",
            "message": contact_message,
        }

    selected_zone = None
    if mode == "zones" or zones:
        selected_zone = next((zone for zone in zones if _zone_matches(zone, location)), None)
        if selected_zone is None:
            return {
                "mode": "to_agree",
                "cost": 0,
                "original_cost": 0,
                "to_agree": True,
                "requires_contact": True,
                "promotion_applied": False,
                "label": "Zona sin tarifa configurada",
                "message": contact_message,
            }
        original_cost = int(selected_zone.get("cost", 0))
        label = selected_zone.get("label") or selected_zone.get("city") or selected_zone.get("region") or "Zona configurada"
        free_minimum = int(selected_zone.get("free_shipping_min_subtotal") or selected_zone.get("free_threshold") or 0)
        zone_free = (
            bool(selected_zone.get("free_shipping"))
            and _free_shipping_window_active(selected_zone)
            and (free_minimum == 0 or subtotal >= free_minimum)
        )
    else:
        original_cost = int(settings.shipping_flat_cost)
        label = "Envio plano"
        zone_free = False

    threshold = int(settings.shipping_free_threshold or 0)
    store_config = {"free_shipping_from": getattr(settings, "free_shipping_from", None), "free_shipping_to": getattr(settings, "free_shipping_to", None)}
    threshold_free = threshold > 0 and subtotal >= threshold and _free_shipping_window_active(store_config)
    promotion_applied = zone_free or threshold_free
    missing_for_free = None
    if not promotion_applied and threshold > 0 and _free_shipping_window_active(store_config) and subtotal < threshold:
        missing_for_free = threshold - subtotal
    return {
        "mode": mode,
        "cost": 0 if promotion_applied else original_cost,
        "original_cost": original_cost,
        "to_agree": False,
        "requires_contact": False,
        "promotion_applied": promotion_applied,
        "label": label,
        "message": "Envio gratis aplicado." if promotion_applied else (f"Te faltan {missing_for_free} para envio gratis." if missing_for_free else None),
    }


def _pricing_for_cart(cart: Cart, coupon_code: str | None, db: Session, *, shipping_location: dict | None = None, payment_method: str | None = None) -> list[dict]:
    groups: dict[str, list[CartItem]] = defaultdict(list)
    for item in cart.items:
        groups[item.variant.product.store_id].append(item)

    results: list[dict] = []
    for store_id, items in groups.items():
        store = db.get(Store, store_id)
        priced_items = priced_items_from_cart_items(items)
        first_pass = calculate_store_pricing(
            store_id=store_id,
            priced_items=priced_items,
            db=db,
            coupon_code=coupon_code,
            shipping_cost=0,
        )
        force_to_agree = any((item.variant.product.shipping_mode == "to_agree") for item in items if item.variant and item.variant.product)
        shipping = _shipping_for_store(store, first_pass["subtotal_after_discounts"], shipping_location or {}, db, force_to_agree=force_to_agree)
        result = calculate_store_pricing(
            store_id=store_id,
            priced_items=priced_items,
            db=db,
            coupon_code=coupon_code,
            shipping_cost=shipping["cost"],
        )
        payment_options = payment_options_for_store(store_id, db)
        if payment_method and payment_method not in payment_options["payment_methods"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Metodo de pago no disponible para esta tienda")
        result["shipping"] = shipping
        result["store"] = store
        result["payment_options"] = payment_options
        result["contact"] = _store_contact(store)
        results.append(result)
    return results


def _store_quote_out(result: dict) -> dict:
    return {
        "store_id": result["store_id"],
        "store_name": result["store"].name,
        "items": [_cart_item_out(line["cart_item"]) for line in result["items"] if line["cart_item"] is not None],
        "regular_subtotal": result["regular_subtotal"],
        "subtotal": result["subtotal_after_discounts"],
        "discount": result["discount"],
        "discounts": result["discounts"],
        "extra_charge_total": result["extra_charge_total"],
        "extra_charges": result["extra_charges"],
        "shipping": result["shipping"],
        "tax": 0,
        "total": result["total"],
        "payment_methods": result["payment_options"]["payment_methods"],
        "payout_accounts": result["payment_options"]["payout_accounts"],
        "contact": result["contact"],
    }


def _quote_out(results: list[dict]) -> dict:
    discounts = [line for result in results for line in result["discounts"]]
    extra_charges = [line for result in results for line in result["extra_charges"]]
    subtotal = sum(result["subtotal_after_discounts"] for result in results)
    shipping = sum(result["shipping_cost"] for result in results)
    extra_charge_total = sum(result["extra_charge_total"] for result in results)
    return {
        "subtotal": subtotal,
        "regular_subtotal": sum(result["regular_subtotal"] for result in results),
        "discount": sum(result["discount"] for result in results),
        "discounts": discounts,
        "extra_charge_total": extra_charge_total,
        "extra_charges": extra_charges,
        "shipping_cost": shipping,
        "store_quotes": [_store_quote_out(result) for result in results],
        "tax": 0,
        "total": subtotal + extra_charge_total + shipping,
        "currency": "COP",
    }


def _quote_location(body: CheckoutQuoteIn, user: User, db: Session) -> dict:
    if body.address_id:
        address = db.get(Address, body.address_id)
        if address is None or address.user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "La direccion no pertenece al usuario")
        return _location_from_address(address)
    if body.address:
        return _location_from_address(body.address)
    if body.shipping_location:
        return body.shipping_location.model_dump()
    return {}


@buyer_router.post(
    "/checkout/quote",
    response_model=CheckoutQuoteOut,
    status_code=status.HTTP_200_OK,
    summary="Cotizar checkout",
    description="Rol permitido: buyer. HU-CHK-02, HU-PROM-01, HU-PROM-02 y HU-PROM-04. Calcula precios efectivos, descuentos, cargos extra, envio por tienda/zona o a convenir y total antes de confirmar.",
    response_description="Cotizacion del checkout con desglose por tienda, cargos separados y modalidad de envio.",
    responses={400: {"description": "Cupon invalido, metodo de pago no disponible o datos invalidos."}, 401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer o direccion fuera del comprador."}, 409: {"description": "El carrito contiene items no disponibles."}, 422: {"description": "Validacion Pydantic."}},
)
def checkout_quote(body: CheckoutQuoteIn, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    _assert_cart_ready(cart)
    results = _pricing_for_cart(
        cart,
        body.coupon_code,
        db,
        shipping_location=_quote_location(body, user, db),
        payment_method=body.payment_method,
    )
    return _quote_out(results)


@buyer_router.post(
    "/checkout",
    response_model=CheckoutConfirmationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear checkout",
    description="Rol permitido: buyer. HU-CHK-03, HU-CHK-04, HU-CHK-05, HU-CANAL-01, HU-PROM-01, HU-PROM-02, HU-PROM-04 y HU-INV-02. Valida stock final, crea una compra agrupada y un pedido por tienda, reserva/descuenta inventario y retorna el resumen de confirmacion.",
    response_description="Confirmacion con compra agrupada, pedidos creados, resumen completo y notas de envio.",
    responses={400: {"description": "Carrito vacio, cupon invalido o metodo de pago no disponible."}, 401: {"description": "Token requerido o invalido."}, 403: {"description": "Direccion fuera del comprador."}, 409: {"description": "Stock insuficiente o item no disponible."}, 422: {"description": "Validacion Pydantic."}},
)
def checkout(body: CheckoutIn, background: BackgroundTasks, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = _get_cart(user, db)
    if not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El carrito está vacío")
    _assert_cart_ready(cart)
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
    pricing_results = _pricing_for_cart(
        cart,
        body.coupon_code,
        db,
        shipping_location=_location_from_address(address),
        payment_method=body.payment_method,
    )
    quote = _quote_out(pricing_results)
    created: list[Order] = []
    checkout_group: CheckoutGroup | None = None
    try:
        commission_setting = db.get(PlatformSetting, "commission")
        commission_pct = int((commission_setting.value if commission_setting else {}).get("value", 0))
        checkout_group = CheckoutGroup(
            buyer_id=user.id,
            address_id=address.id,
            subtotal=quote["subtotal"],
            discount_total=quote["discount"],
            extra_charge_total=quote["extra_charge_total"],
            shipping_cost=quote["shipping_cost"],
            tax=quote["tax"],
            total=quote["total"],
            currency=quote["currency"],
            payment_method=body.payment_method,
            notes=body.notes,
        )
        db.add(checkout_group)
        db.flush()
        for result in pricing_results:
            store_id = result["store_id"]
            subtotal = result["subtotal_after_discounts"]
            shipping = result["shipping_cost"]
            payment_options = payment_options_for_store(store_id, db)
            if body.payment_method not in payment_options["payment_methods"]:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Metodo de pago no disponible para esta tienda")
            single_warehouse = single_active_warehouse(db, store_id)
            has_multiple_warehouses = active_warehouse_count(db, store_id) > 1
            shipping_note = result["shipping"]["message"] if result["shipping"].get("to_agree") else None
            notes = body.notes
            if shipping_note:
                notes = f"{notes}\n{shipping_note}" if notes else shipping_note
            order = Order(checkout_group_id=checkout_group.id, store_id=store_id, buyer_id=user.id, address_id=address.id, warehouse_id=single_warehouse.id if single_warehouse else None, channel=SaleChannel.online, status=OrderStatus.pending, subtotal=subtotal, shipping_cost=shipping, tax=0, total=result["total"], notes=notes)
            db.add(order)
            db.flush()
            for priced in result["items"]:
                cart_item = priced["cart_item"]
                if single_warehouse and not has_multiple_warehouses:
                    consume_variant(db, cart_item.variant_id, cart_item.quantity, order.id, warehouse_id=single_warehouse.id)
                else:
                    reserve_variant(db, cart_item.variant_id, cart_item.quantity, order.id)
                db.add(OrderItem(order_id=order.id, variant_id=cart_item.variant_id, product_name=cart_item.variant.product.name, sku=cart_item.variant.sku, quantity=cart_item.quantity, unit_price=priced["unit_price"], unit_cost=cart_item.variant.cost))
            for line in [*result["discounts"], *result["extra_charges"]]:
                db.add(
                    OrderAdjustment(
                        order_id=order.id,
                        kind=OrderAdjustmentKind(line["kind"]),
                        source_type=line.get("source_type"),
                        source_id=line.get("source_id"),
                        name=line["name"],
                        amount=line["amount"],
                        metadata_json={"code": line.get("code")} if line.get("code") else {},
                    )
                )
            if result["coupon"] is not None:
                result["coupon"].used_count += 1
            is_manual = body.payment_method in MANUAL_METHODS
            # La cuenta elegida solo aplica si pertenece a esta tienda y está activa.
            payout_account_id = None
            if is_manual and body.payout_account_id:
                account = db.get(PayoutAccount, body.payout_account_id)
                if account is not None and account.store_id == store_id and account.active:
                    payout_account_id = account.id
            if is_manual:
                expected_type = PayoutAccountType.bank if body.payment_method == "transfer" else PayoutAccountType.bre_b
                account = db.get(PayoutAccount, body.payout_account_id) if body.payout_account_id else None
                if account is None or account.store_id != store_id or not account.active or account.type != expected_type:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cuenta de cobro no valida para esta tienda")
                payout_account_id = account.id
            payment = Payment(order_id=order.id, provider="manual" if is_manual else "pending", method=body.payment_method, status=PaymentStatus.pending, amount=order.total, platform_fee=order.total * commission_pct // 100, seller_amount=order.total - (order.total * commission_pct // 100), currency="COP", payout_account_id=payout_account_id)
            db.add(payment)
            db.flush()
            payment_service.record_creation(db, payment, actor_role="buyer", actor_user_id=user.id)
            created.append(order)
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    for order in created:
        db.refresh(order)
    db.refresh(checkout_group)
    shipping_notes = [
        f"{store_quote['store_name']}: {store_quote['shipping']['message']}"
        for store_quote in quote["store_quotes"]
        if store_quote["shipping"].get("message")
    ]
    summary = {
        "purchase_id": checkout_group.id,
        "subtotal": quote["subtotal"],
        "discount": quote["discount"],
        "extra_charge_total": quote["extra_charge_total"],
        "shipping_cost": quote["shipping_cost"],
        "tax": quote["tax"],
        "total": quote["total"],
        "currency": quote["currency"],
        "payment_method": body.payment_method,
        "address": _address_out(address),
        "store_quotes": quote["store_quotes"],
    }
    confirmation = {
        "purchase_id": checkout_group.id,
        "orders": [OrderOut.model_validate(_order_out(order)) for order in created],
        "summary": summary,
        "payment_required": True,
        "shipping_notes": shipping_notes,
    }
    background.add_task(mailer.checkout_summary_to_buyer, user.email, confirmation)
    return confirmation


def _purchase_out(group: CheckoutGroup) -> dict:
    orders = sorted(group.orders, key=lambda order: order.created_at)
    return {
        "id": group.id,
        "buyer_id": group.buyer_id,
        "address_id": group.address_id,
        "subtotal": group.subtotal,
        "discount_total": group.discount_total,
        "extra_charge_total": group.extra_charge_total,
        "shipping_cost": group.shipping_cost,
        "tax": group.tax,
        "total": group.total,
        "currency": group.currency,
        "payment_method": group.payment_method,
        "notes": group.notes,
        "created_at": group.created_at,
        "orders": [OrderOut.model_validate(_order_out(order)) for order in orders],
        "store_statuses": [
            {
                "store_id": order.store_id,
                "store_name": order.store.name,
                "order_id": order.id,
                "status": order.status.value,
                "total": order.total,
            }
            for order in orders
        ],
    }


@buyer_router.get(
    "/purchases",
    response_model=list[PurchaseOut],
    status_code=status.HTTP_200_OK,
    summary="Listar compras agrupadas",
    description="Rol permitido: buyer. HU-CHK-05. Lista compras agrupadas del comprador con el estado de cada tienda por separado.",
    response_description="Compras agrupadas propias del comprador autenticado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 422: {"description": "Validacion Pydantic."}},
)
def buyer_purchases(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    groups = db.scalars(
        select(CheckoutGroup).where(CheckoutGroup.buyer_id == user.id).order_by(CheckoutGroup.created_at.desc())
    ).all()
    return [PurchaseOut.model_validate(_purchase_out(group)) for group in groups]


@buyer_router.get(
    "/purchases/{purchase_id}",
    response_model=PurchaseOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar compra agrupada",
    description="Rol permitido: buyer. HU-CHK-05. Consulta una compra agrupada propia y muestra los pedidos/estados por tienda.",
    response_description="Compra agrupada propia con pedidos por tienda.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Compra no encontrada."}, 422: {"description": "Validacion Pydantic."}},
)
def buyer_purchase(purchase_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    group = db.get(CheckoutGroup, purchase_id)
    if group is None or group.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compra no encontrada")
    return PurchaseOut.model_validate(_purchase_out(group))


@buyer_router.get(
    "/orders",
    response_model=list[OrderOut],
    status_code=status.HTTP_200_OK,
    summary="Listar pedidos del comprador",
    description="Rol permitido: buyer. HU-PED-01 e HU-PED-03. Lista pedidos propios con su estado; filtra por estado y rango de fechas. Para compras multi-tienda usar tambien /purchases.",
    response_description="Pedidos propios del comprador autenticado segun los filtros.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 422: {"description": "Validacion Pydantic."}},
)
def buyer_orders(
    status_filter: str | None = Query(None, alias="status", description="Estado de pedido para filtrar.", example="pending"),
    date_from: date | None = Query(None, description="Fecha inicial inclusiva (por creacion)."),
    date_to: date | None = Query(None, description="Fecha final inclusiva (por creacion)."),
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    stmt = select(Order).where(Order.buyer_id == user.id).order_by(Order.created_at.desc())
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    if date_from:
        stmt = stmt.where(Order.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to:
        stmt = stmt.where(Order.created_at <= datetime.combine(date_to, datetime.max.time(), timezone.utc))
    return [OrderOut.model_validate(_order_out(order)) for order in db.scalars(stmt).all()]


@buyer_router.get(
    "/orders/{order_id}",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar pedido del comprador",
    description="Rol permitido: buyer. HU-CHK-05. Consulta solo un pedido propio asignado a una tienda.",
    response_description="Detalle del pedido propio.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Pedido no encontrado."}, 422: {"description": "Validacion Pydantic."}},
)
def buyer_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return OrderOut.model_validate(_order_out(order))


@buyer_router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Cancelar pedido",
    description="Rol permitido: buyer. HU-INV-04. Cancela un pedido propio permitido y libera o repone inventario segun su etapa.",
    response_description="Pedido cancelado con inventario conciliado.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Pedido no encontrado."}, 409: {"description": "Pedido ya no cancelable."}, 422: {"description": "Validacion Pydantic."}},
)
def cancel_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya no se puede cancelar")
    restock_order(db, order, note="Reposicion por cancelacion del comprador")
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


# --- Seguimiento de envio del comprador (HU-ENV-05) --------------------------


def _latest_shipment(order: Order):
    if not order.shipments:
        return None
    return sorted(order.shipments, key=lambda s: s.created_at)[-1]


def shipment_out_for_order(order: Order) -> dict:
    """Estado de envio + linea de tiempo; sin envio devuelve el estado inicial sin inventar tracking."""
    shipment = _latest_shipment(order)
    if shipment is None:
        return {"order_id": order.id, "status": "pending", "note": None, "carrier": None, "tracking_number": None, "shipped_at": None, "delivered_at": None, "events": []}
    return {
        "order_id": order.id,
        "status": shipment.tracking_status or "pending",
        "note": shipment.note,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
        "shipped_at": shipment.shipped_at,
        "delivered_at": shipment.delivered_at,
        "events": [{"status": e.status, "note": e.note, "created_at": e.created_at} for e in sorted(shipment.events, key=lambda e: e.created_at)],
    }


@buyer_router.get(
    "/orders/{order_id}/shipment",
    response_model=ShipmentOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar seguimiento del envio",
    description=(
        "Rol permitido: buyer. HU-ENV-05. Devuelve el estado de envio de un pedido propio y su "
        "linea de tiempo de solo lectura (estados con fecha y hora). Sin actualizaciones muestra el "
        "estado inicial sin informacion falsa de tracking."
    ),
    response_description="Estado de envio y linea de tiempo del pedido.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol buyer."}, 404: {"description": "Pedido no encontrado dentro del scope del comprador."}, 422: {"description": "Validacion Pydantic."}},
)
def buyer_order_shipment(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = _buyer_order(order_id, user, db)
    return shipment_out_for_order(order)


# --- Pago manual del comprador (RF-PAGO-03 / RF-PAGO-05) ---------------------


def _buyer_order(order_id: str, user: User, db: Session) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return order


PAYMENT_RESPONSES = {
    400: {"description": "Debe elegirse una cuenta destino valida o el archivo es invalido."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol buyer."},
    404: {"description": "Pedido o pago no encontrado dentro del scope del comprador."},
    409: {"description": "El pedido o el pago ya no admite comprobantes."},
    422: {"description": "Validacion Pydantic."},
}


@buyer_router.get(
    "/orders/{order_id}/payment",
    response_model=PaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado del pago",
    description=(
        "Rol permitido: buyer. HU-PAG-05. Devuelve el estado del pago del pedido, la cuenta "
        "destino elegida, el monto exacto a pagar y el comprobante ya subido (URL firmada). "
        "Sin comprobante el estado es `pending` (pendiente_pago)."
    ),
    response_description="Estado del pago con cuenta destino y comprobante.",
    responses={
        401: PAYMENT_RESPONSES[401],
        403: PAYMENT_RESPONSES[403],
        404: {"description": "Pedido no encontrado dentro del scope del comprador."},
        422: PAYMENT_RESPONSES[422],
    },
)
def buyer_order_payment(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = _buyer_order(order_id, user, db)
    payment = _latest_payment(order)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El pedido no tiene un pago asociado")
    return _payment_out(payment, with_receipt=True)


@buyer_router.post(
    "/orders/{order_id}/payment/receipt",
    response_model=PaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Subir comprobante de pago",
    description=(
        "Rol permitido: buyer. HU-PAG-05 y HU-PAG-07. Sube (o reemplaza) el comprobante de una "
        "transferencia o pago Bre-B en imagen o PDF y deja el pago en revision del vendedor "
        "(`in_review` / comprobante_subido). Reabre la revision si el pago venia rechazado o "
        "incompleto (pago_incompleto). El stock permanece reservado."
    ),
    response_description="Pago actualizado con el comprobante en revision.",
    responses=PAYMENT_RESPONSES,
)
def upload_payment_receipt(
    order_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(..., description="Comprobante en JPG, PNG o PDF (max 5 MB)."),
    payout_account_id: str | None = Form(default=None, description="Cuenta destino elegida; obligatoria si aun no se fijo."),
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    order = _buyer_order(order_id, user, db)
    if order.status in (OrderStatus.cancelled, OrderStatus.returned):
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya no admite comprobantes")

    payment = _latest_payment(order)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El pedido no tiene un pago asociado")
    if payment.status == PaymentStatus.paid:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pago ya fue confirmado")

    if payout_account_id:
        account = db.get(PayoutAccount, payout_account_id)
        if account is None or account.store_id != order.store_id or not account.active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cuenta de cobro no válida para esta tienda")
        payment.payout_account_id = account.id
    if payment.payout_account_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes elegir la cuenta a la que transferiste")

    content = file.file.read()
    payment.receipt_path = upload_receipt(content, file.content_type, order.store_id, order.id)
    payment.receipt_uploaded_at = datetime.now(timezone.utc)
    payment.provider = "manual"
    # Un comprobante nuevo reabre la revisión: se limpia el veredicto anterior.
    payment.review_note = None
    payment.reviewed_at = None
    payment.reviewed_by = None
    # El comprador vuelve a dejar el pago en revisión (desde pending o pago_incompleto).
    payment_service.transition(
        db, payment, PaymentStatus.in_review, actor_role="buyer", actor_user_id=user.id, note="Comprobante subido"
    )
    db.commit()
    db.refresh(payment)

    amount_text = f"${payment.amount:,.0f} COP".replace(",", ".")
    seller_email = db.scalar(
        select(User.email)
        .join(StoreMember, StoreMember.user_id == User.id)
        .where(StoreMember.store_id == order.store_id)
        .order_by(StoreMember.created_at)
    )
    background.add_task(mailer.receipt_uploaded_to_seller, seller_email, order.id, user.name, amount_text)
    background.add_task(mailer.receipt_uploaded_to_buyer, user.email, order.id)
    return _payment_out(payment, with_receipt=True)
