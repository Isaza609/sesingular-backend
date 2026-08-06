from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Coupon, ExtraCharge, Order, OrderItem, Payment, PayoutAccount, PlatformSetting, Product, ProductVariant, Promotion, StockLevel, Store, StoreMember, User, Warehouse
from app.models.order import OrderStatus, SaleChannel
from app.models.payment import PaymentStatus
from app.models.payout import PayoutAccountType
from app.models.promotion import ChargeType, DiscountType, PromotionScope
from app.modules.common import mailer
from app.modules.common.permissions import get_seller_store, require_seller
from app.modules.common.storage import signed_url
from app.modules.inventory.service import consume_reserved_order_from_warehouse, consume_variant, fulfill_reserved_order, restock_order
from app.modules.orders.router import _order_out, _payout_account_out
from app.modules.orders.schemas import OrderOut, OrderStatusPatch, PosOrderIn, WarehouseAssign
from app.modules.payments import service as payment_service
from app.modules.seller.schemas import (
    CouponIn,
    CouponPatch,
    ExtraChargeIn,
    ExtraChargeOut,
    ExtraChargePatch,
    PaymentConfirmIn,
    PaymentIncompleteIn,
    PaymentOverpaidIn,
    PaymentRejectIn,
    PayoutAccountIn,
    PayoutAccountOut,
    PayoutAccountPatch,
    PromotionIn,
    PromotionOut,
    PromotionPatch,
    SalesChannelReportOut,
    SellerPaymentOut,
    SellerStoreMemberOut,
)

router = APIRouter(prefix="/seller", tags=["seller"])

COMMON_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio obligatorio de contrasena pendiente."},
    404: {"description": "Recurso no encontrado."},
    422: {"description": "Validacion Pydantic."},
}


def _assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    allowed = {
        OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
        OrderStatus.confirmed: {OrderStatus.preparing, OrderStatus.cancelled},
        OrderStatus.preparing: {OrderStatus.shipped, OrderStatus.cancelled},
        OrderStatus.shipped: {OrderStatus.delivered, OrderStatus.returned},
        OrderStatus.delivered: {OrderStatus.returned},
        OrderStatus.cancelled: set(),
        OrderStatus.returned: set(),
    }
    if target != current and target not in allowed[current]:
        raise HTTPException(status.HTTP_409_CONFLICT, f"No se puede pasar de {current.value} a {target.value}")


def _sales_channel_report(store: Store, db: Session, date_from: date | None = None, date_to: date | None = None) -> dict:
    stmt = select(Order).where(Order.store_id == store.id, Order.status != OrderStatus.cancelled)
    if date_from:
        stmt = stmt.where(Order.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to:
        stmt = stmt.where(Order.created_at <= datetime.combine(date_to, datetime.max.time(), timezone.utc))

    orders = db.scalars(stmt).all()
    by_channel = []
    for channel in SaleChannel:
        channel_orders = [order for order in orders if order.channel == channel]
        by_channel.append(
            {
                "channel": channel.value,
                "orders": len(channel_orders),
                "gross": sum(order.total for order in channel_orders),
            }
        )

    gross = sum(row["gross"] for row in by_channel)
    costs = sum(item.quantity * (item.unit_cost or 0) for order in orders for item in order.items)
    fees = sum(payment.platform_fee for order in orders for payment in order.payments if payment.status == PaymentStatus.paid)
    return {
        "totals": {
            "orders": sum(row["orders"] for row in by_channel),
            "gross": gross,
            "costs": costs,
            "platform_fees": fees,
            "profit": gross - costs - fees,
        },
        "by_channel": by_channel,
    }


@router.get("/dashboard")
def seller_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    return _sales_channel_report(store, db, date_from, date_to)


@router.get(
    "/reports/sales",
    response_model=SalesChannelReportOut,
    status_code=status.HTTP_200_OK,
    summary="Comparar ventas por canal",
    description=(
        "Rol permitido: seller. HU-CANAL-03. Retorna ventas online y presenciales "
        "de la tienda autenticada en un rango de fechas inclusivo, excluyendo pedidos cancelados "
        "y mostrando cero cuando un canal no tuvo ventas."
    ),
    response_description="Reporte comparativo con totales generales y desglose por canal.",
    responses=COMMON_RESPONSES,
)
def seller_sales_report(
    date_from: date | None = Query(default=None, description="Fecha inicial inclusiva del reporte.", example="2026-08-01"),
    date_to: date | None = Query(default=None, description="Fecha final inclusiva del reporte.", example="2026-08-31"),
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    return _sales_channel_report(store, db, date_from, date_to)


@router.get(
    "/store/members",
    response_model=list[SellerStoreMemberOut],
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios de mi tienda",
    description=(
        "Rol permitido: seller. HU-USR-05. Permite al vendedor consultar usuarios activos "
        "e inactivos asociados a su misma tienda, sin crearlos ni desactivarlos."
    ),
    response_description="Usuarios asociados a la tienda del vendedor.",
    responses=COMMON_RESPONSES,
)
def seller_store_members(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(StoreMember).where(StoreMember.store_id == store.id).order_by(StoreMember.created_at)
    ).all()
    return [
        SellerStoreMemberOut(
            user_id=row.user.id,
            email=row.user.email,
            name=row.user.name,
            phone=row.user.phone,
            member_role=row.role,
            active=row.user.active,
            must_change_password=row.user.must_change_password,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get(
    "/orders",
    response_model=list[OrderOut],
    status_code=status.HTTP_200_OK,
    summary="Listar pedidos de mi tienda",
    description="Rol permitido: seller. HU-CHK-05. Lista solo pedidos asignados a la tienda del seller o su equipo, aunque la compra del comprador tenga varias tiendas.",
    response_description="Pedidos de la tienda autenticada.",
    responses={401: {"description": "Token requerido o invalido."}, 403: {"description": "Requiere rol seller o tienda no permitida."}, 422: {"description": "Validacion Pydantic."}},
)
def seller_orders(
    status_filter: str | None = Query(None, alias="status"),
    channel: str | None = Query(None, pattern="^(online|presencial)$"),
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(Order).where(Order.store_id == store.id).order_by(Order.created_at.desc())
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    if channel:
        stmt = stmt.where(Order.channel == channel)
    return [OrderOut.model_validate(_order_out(order)) for order in db.scalars(stmt).all()]


def _seller_order(order_id: str, store: Store, db: Session) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return order


ORDER_INVENTORY_RESPONSES = {
    400: {"description": "Datos invalidos o almacen inactivo."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o pedido fuera de la tienda."},
    404: {"description": "Pedido o almacen no encontrado."},
    409: {"description": "Transicion invalida, stock insuficiente o pedido ya descontado."},
    422: {"description": "Validacion Pydantic."},
}

POS_ORDER_RESPONSES = {
    400: {"description": "La tienda no tiene almacen activo para vender."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o tienda no permitida."},
    404: {"description": "Comprador inexistente o variante fuera de la tienda."},
    409: {"description": "Stock insuficiente; informa la disponibilidad real."},
    422: {"description": "Validacion Pydantic."},
}


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estado de pedido",
    description="Rol permitido: seller. HU-INV-04. Actualiza el estado de un pedido propio y repone o libera inventario cuando se cancela o devuelve.",
    response_description="Pedido actualizado con inventario conciliado segun el estado.",
    responses=ORDER_INVENTORY_RESPONSES,
)
def patch_order_status(order_id: str, body: OrderStatusPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    order = _seller_order(order_id, store, db)
    target = OrderStatus(body.status)
    _assert_transition(order.status, target)
    if target == OrderStatus.cancelled and order.status != OrderStatus.cancelled:
        restock_order(db, order, note="Reposicion por cancelacion seller")
    if target == OrderStatus.shipped and order.status != OrderStatus.shipped:
        fulfill_reserved_order(db, order)
    if target == OrderStatus.returned and order.status != OrderStatus.returned:
        restock_order(db, order, note="Reposicion por devolucion aprobada")
    order.status = target
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


@router.patch(
    "/orders/{order_id}/warehouse",
    response_model=OrderOut,
    status_code=status.HTTP_200_OK,
    summary="Asignar almacen de despacho",
    description="Rol permitido: seller. HU-INV-03. Asigna el almacen de despacho de un pedido propio y descuenta firmemente el stock reservado desde ese almacen.",
    response_description="Pedido con almacen asignado y movimientos de salida registrados.",
    responses=ORDER_INVENTORY_RESPONSES,
)
def assign_order_warehouse(order_id: str, body: WarehouseAssign, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    order = _seller_order(order_id, store, db)
    consume_reserved_order_from_warehouse(db, order, body.warehouse_id)
    order.warehouse_id = body.warehouse_id
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


@router.post(
    "/pos/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear venta presencial",
    description=(
        "Rol permitido: seller. HU-CANAL-01 y HU-CANAL-02. Registra una venta mini-POS "
        "en canal presencial, sin exigir comprador, validando pertenencia de variantes y "
        "stock real antes de descontar inventario inmediatamente."
    ),
    response_description="Pedido presencial creado, entregado, con pago POS pagado e inventario descontado.",
    responses=POS_ORDER_RESPONSES,
)
def create_pos_order(body: PosOrderIn, store: Store = Depends(get_seller_store), user: User = Depends(require_seller), db: Session = Depends(get_db)):
    warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True), Warehouse.is_default.is_(True)))
    if warehouse is None:
        warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True)).order_by(Warehouse.name))
    if warehouse is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes registrar un almacÃ©n antes de vender")
    if body.buyer_id and db.get(User, body.buyer_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comprador no encontrado")

    requested: dict[str, int] = defaultdict(int)
    for item in body.items:
        requested[item.variant_id] += item.quantity

    variants: dict[str, ProductVariant] = {}
    for variant_id, quantity in requested.items():
        variant = db.get(ProductVariant, variant_id)
        if variant is None or not variant.active or variant.product.store_id != store.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Una variante no pertenece a tu tienda")
        level = db.scalar(
            select(StockLevel)
            .where(StockLevel.variant_id == variant.id, StockLevel.warehouse_id == warehouse.id)
            .with_for_update()
        )
        available = max(0, (level.quantity if level else 0) - (level.reserved if level else 0))
        if available < quantity:
            sku = variant.sku or variant.id
            raise HTTPException(status.HTTP_409_CONFLICT, f"Stock insuficiente para {sku}. Disponible: {available}")
        variants[variant_id] = variant

    try:
        subtotal = sum(quantity * variants[variant_id].price for variant_id, quantity in requested.items())
        order = Order(store_id=store.id, buyer_id=body.buyer_id, warehouse_id=warehouse.id, channel=SaleChannel.presencial, status=OrderStatus.delivered, subtotal=subtotal, total=subtotal, notes=body.notes)
        db.add(order)
        db.flush()
        for variant_id, quantity in requested.items():
            variant = variants[variant_id]
            consume_variant(db, variant.id, quantity, order_id=order.id, warehouse_id=warehouse.id)
            db.add(OrderItem(order_id=order.id, variant_id=variant.id, product_name=variant.product.name, sku=variant.sku, quantity=quantity, unit_price=variant.price, unit_cost=variant.cost))
        setting = db.get(PlatformSetting, "commission")
        pct = int((setting.value if setting else {}).get("value", 0))
        fee = subtotal * pct // 100
        pos_payment = Payment(order_id=order.id, provider="pos", method=body.payment_method, status=PaymentStatus.paid, amount=subtotal, platform_fee=fee, seller_amount=subtotal - fee, currency="COP")
        db.add(pos_payment)
        db.flush()
        payment_service.record_creation(db, pos_payment, actor_role="seller", actor_user_id=user.id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


PROMOTION_RESPONSES = {
    400: {"description": "Datos invalidos, vigencia incoherente o productos fuera de scope."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio obligatorio de contrasena pendiente."},
    404: {"description": "Promocion, cupon, cargo o producto no encontrado."},
    409: {"description": "Codigo de cupon duplicado en la tienda."},
    422: {"description": "Validacion Pydantic."},
}


def _promotion_out(item: Promotion | Coupon) -> dict:
    return {
        "id": item.id,
        "store_id": item.store_id,
        "code": getattr(item, "code", None),
        "name": getattr(item, "name", None),
        "discount_type": item.discount_type.value,
        "value": item.value,
        "min_quantity": getattr(item, "min_quantity", None),
        "pay_quantity": getattr(item, "pay_quantity", None),
        "max_uses": getattr(item, "max_uses", None),
        "used_count": getattr(item, "used_count", None),
        "scope": item.scope.value,
        "product_ids": item.product_ids or [],
        "starts_at": item.starts_at,
        "ends_at": item.ends_at,
        "active": item.active,
        "created_at": item.created_at,
    }


def _extra_charge_out(item: ExtraCharge) -> dict:
    return {
        "id": item.id,
        "store_id": item.store_id,
        "name": item.name,
        "charge_type": item.charge_type.value,
        "value": item.value,
        "scope": item.scope.value,
        "product_ids": item.product_ids or [],
        "active": item.active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _validate_window(starts_at: datetime | None, ends_at: datetime | None) -> None:
    if starts_at is not None and ends_at is not None and starts_at > ends_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha de inicio no puede ser posterior a la fecha de fin")


def _validate_product_scope(store: Store, product_ids: list[str] | None, scope: str | PromotionScope, db: Session) -> list[str]:
    scope_value = scope.value if isinstance(scope, PromotionScope) else scope
    ids = product_ids or []
    if scope_value == PromotionScope.store.value:
        return []
    if not ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes enviar product_ids cuando el alcance es products")
    products = db.scalars(select(Product).where(Product.id.in_(ids), Product.store_id == store.id)).all()
    if len(products) != len(set(ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Un producto no pertenece a tu tienda")
    return ids


def _validate_discount(discount_type: str, value: int, *, min_quantity: int | None = None, pay_quantity: int | None = None) -> None:
    if discount_type == "percent" and not 1 <= value <= 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El porcentaje debe estar entre 1 y 100")
    if discount_type == "volume":
        if not min_quantity or min_quantity < 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La promocion de volumen requiere min_quantity")
        if pay_quantity is not None and pay_quantity >= min_quantity:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "pay_quantity debe ser menor que min_quantity")
        if pay_quantity is None and value < 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La promocion de volumen requiere unidades gratis")


def _commit_seller_promo(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un cupon con ese codigo en tu tienda") from exc


@router.get(
    "/promotions",
    response_model=list[PromotionOut],
    status_code=status.HTTP_200_OK,
    summary="Listar promociones",
    description="Rol permitido: seller. HU-PROM-02. Lista promociones de porcentaje, valor fijo o volumen configuradas para la tienda autenticada.",
    response_description="Promociones de la tienda con vigencia, alcance y estado.",
    responses=PROMOTION_RESPONSES,
)
def list_promotions(active: bool | None = None, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    stmt = select(Promotion).where(Promotion.store_id == store.id).order_by(Promotion.created_at.desc())
    if active is not None:
        stmt = stmt.where(Promotion.active.is_(active))
    return [PromotionOut.model_validate(_promotion_out(item)) for item in db.scalars(stmt).all()]


@router.post(
    "/promotions",
    response_model=PromotionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear promocion",
    description="Rol permitido: seller. HU-PROM-02. Crea una promocion con vigencia y alcance de tienda o productos propios; las promociones de volumen se aplican automaticamente en checkout.",
    response_description="Promocion creada.",
    responses=PROMOTION_RESPONSES,
)
def create_promotion(body: PromotionIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    _validate_window(body.starts_at, body.ends_at)
    _validate_discount(body.discount_type, body.value, min_quantity=body.min_quantity, pay_quantity=body.pay_quantity)
    product_ids = _validate_product_scope(store, body.product_ids, body.scope, db)
    item = Promotion(
        store_id=store.id,
        discount_type=DiscountType(body.discount_type),
        scope=PromotionScope(body.scope),
        product_ids=product_ids,
        **body.model_dump(exclude={"discount_type", "scope", "product_ids"}),
    )
    db.add(item)
    _commit_seller_promo(db)
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.patch(
    "/promotions/{promotion_id}",
    response_model=PromotionOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar promocion",
    description="Rol permitido: seller. HU-PROM-02. Actualiza una promocion propia, su vigencia, valor, alcance o estado activo para pedidos nuevos.",
    response_description="Promocion actualizada.",
    responses=PROMOTION_RESPONSES,
)
def patch_promotion(promotion_id: str, body: PromotionPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Promotion, promotion_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PromociÃ³n no encontrada")
    values = body.model_dump(exclude_unset=True)
    _validate_window(values.get("starts_at", item.starts_at), values.get("ends_at", item.ends_at))
    discount_type = values.get("discount_type", item.discount_type.value)
    _validate_discount(
        discount_type,
        values.get("value", item.value),
        min_quantity=values.get("min_quantity", item.min_quantity),
        pay_quantity=values.get("pay_quantity", item.pay_quantity),
    )
    if "scope" in values or "product_ids" in values:
        scope = values.get("scope", item.scope.value)
        values["product_ids"] = _validate_product_scope(store, values.get("product_ids", item.product_ids), scope, db)
        values["scope"] = PromotionScope(scope)
    if "discount_type" in values:
        values["discount_type"] = DiscountType(values["discount_type"])
    for key, value in values.items():
        setattr(item, key, value)
    _commit_seller_promo(db)
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.delete(
    "/promotions/{promotion_id}",
    response_model=PromotionOut,
    status_code=status.HTTP_200_OK,
    summary="Desactivar promocion",
    description="Rol permitido: seller. HU-PROM-02. Desactiva una promocion propia para que deje de aplicar a pedidos nuevos.",
    response_description="Promocion desactivada.",
    responses=PROMOTION_RESPONSES,
)
def delete_promotion(promotion_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Promotion, promotion_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promocion no encontrada")
    item.active = False
    db.commit()
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.get(
    "/coupons",
    response_model=list[PromotionOut],
    status_code=status.HTTP_200_OK,
    summary="Listar cupones",
    description="Rol permitido: seller. HU-PROM-02. Lista cupones de la tienda autenticada con vigencia, usos y alcance.",
    response_description="Cupones configurados por la tienda.",
    responses=PROMOTION_RESPONSES,
)
def list_coupons(active: bool | None = None, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    stmt = select(Coupon).where(Coupon.store_id == store.id).order_by(Coupon.created_at.desc())
    if active is not None:
        stmt = stmt.where(Coupon.active.is_(active))
    return [PromotionOut.model_validate(_promotion_out(item)) for item in db.scalars(stmt).all()]


@router.post(
    "/coupons",
    response_model=PromotionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cupon",
    description="Rol permitido: seller. HU-PROM-02. Crea un cupon con codigo normalizado, vigencia, usos y alcance de tienda o productos propios.",
    response_description="Cupon creado.",
    responses=PROMOTION_RESPONSES,
)
def create_coupon(body: CouponIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    _validate_window(body.starts_at, body.ends_at)
    _validate_discount(body.discount_type, body.value)
    product_ids = _validate_product_scope(store, body.product_ids, body.scope, db)
    item = Coupon(
        store_id=store.id,
        code=body.code.upper(),
        discount_type=DiscountType(body.discount_type),
        scope=PromotionScope(body.scope),
        product_ids=product_ids,
        **body.model_dump(exclude={"code", "discount_type", "scope", "product_ids"}),
    )
    db.add(item)
    _commit_seller_promo(db)
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.patch(
    "/coupons/{coupon_id}",
    response_model=PromotionOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar cupon",
    description="Rol permitido: seller. HU-PROM-02. Actualiza un cupon propio, incluido codigo, vigencia, usos, alcance o estado activo.",
    response_description="Cupon actualizado.",
    responses=PROMOTION_RESPONSES,
)
def patch_coupon(coupon_id: str, body: CouponPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Coupon, coupon_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CupÃ³n no encontrado")
    values = body.model_dump(exclude_unset=True)
    _validate_window(values.get("starts_at", item.starts_at), values.get("ends_at", item.ends_at))
    discount_type = values.get("discount_type", item.discount_type.value)
    _validate_discount(discount_type, values.get("value", item.value))
    if "code" in values:
        values["code"] = values["code"].upper()
    if "scope" in values or "product_ids" in values:
        scope = values.get("scope", item.scope.value)
        values["product_ids"] = _validate_product_scope(store, values.get("product_ids", item.product_ids), scope, db)
        values["scope"] = PromotionScope(scope)
    if "discount_type" in values:
        values["discount_type"] = DiscountType(values["discount_type"])
    for key, value in values.items():
        setattr(item, key, value)
    _commit_seller_promo(db)
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.delete(
    "/coupons/{coupon_id}",
    response_model=PromotionOut,
    status_code=status.HTTP_200_OK,
    summary="Desactivar cupon",
    description="Rol permitido: seller. HU-PROM-02. Desactiva un cupon propio para que deje de aplicar a pedidos nuevos.",
    response_description="Cupon desactivado.",
    responses=PROMOTION_RESPONSES,
)
def delete_coupon(coupon_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Coupon, coupon_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cupon no encontrado")
    item.active = False
    db.commit()
    db.refresh(item)
    return PromotionOut.model_validate(_promotion_out(item))


@router.get(
    "/extra-charges",
    response_model=list[ExtraChargeOut],
    status_code=status.HTTP_200_OK,
    summary="Listar cargos extra",
    description="Rol permitido: seller. HU-PROM-04. Lista cargos extra manuales definidos por la tienda para desglose en checkout.",
    response_description="Cargos extra de la tienda.",
    responses=PROMOTION_RESPONSES,
)
def list_extra_charges(active: bool | None = None, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    stmt = select(ExtraCharge).where(ExtraCharge.store_id == store.id).order_by(ExtraCharge.created_at.desc())
    if active is not None:
        stmt = stmt.where(ExtraCharge.active.is_(active))
    return [ExtraChargeOut.model_validate(_extra_charge_out(item)) for item in db.scalars(stmt).all()]


@router.post(
    "/extra-charges",
    response_model=ExtraChargeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cargo extra",
    description="Rol permitido: seller. HU-PROM-04. Crea un cargo extra manual fijo o porcentual con alcance de tienda o productos propios.",
    response_description="Cargo extra creado.",
    responses=PROMOTION_RESPONSES,
)
def create_extra_charge(body: ExtraChargeIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    if body.charge_type == "percent" and not 1 <= body.value <= 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El porcentaje debe estar entre 1 y 100")
    product_ids = _validate_product_scope(store, body.product_ids, body.scope, db)
    item = ExtraCharge(
        store_id=store.id,
        charge_type=ChargeType(body.charge_type),
        scope=PromotionScope(body.scope),
        product_ids=product_ids,
        **body.model_dump(exclude={"charge_type", "scope", "product_ids"}),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ExtraChargeOut.model_validate(_extra_charge_out(item))


@router.patch(
    "/extra-charges/{charge_id}",
    response_model=ExtraChargeOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar cargo extra",
    description="Rol permitido: seller. HU-PROM-04. Actualiza nombre, tipo, valor, alcance o estado de un cargo extra propio para pedidos nuevos.",
    response_description="Cargo extra actualizado.",
    responses=PROMOTION_RESPONSES,
)
def patch_extra_charge(charge_id: str, body: ExtraChargePatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(ExtraCharge, charge_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cargo extra no encontrado")
    values = body.model_dump(exclude_unset=True)
    charge_type = values.get("charge_type", item.charge_type.value)
    value = values.get("value", item.value)
    if charge_type == "percent" and not 1 <= value <= 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El porcentaje debe estar entre 1 y 100")
    if "scope" in values or "product_ids" in values:
        scope = values.get("scope", item.scope.value)
        values["product_ids"] = _validate_product_scope(store, values.get("product_ids", item.product_ids), scope, db)
        values["scope"] = PromotionScope(scope)
    if "charge_type" in values:
        values["charge_type"] = ChargeType(values["charge_type"])
    for key, value in values.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return ExtraChargeOut.model_validate(_extra_charge_out(item))


@router.delete(
    "/extra-charges/{charge_id}",
    response_model=ExtraChargeOut,
    status_code=status.HTTP_200_OK,
    summary="Desactivar cargo extra",
    description="Rol permitido: seller. HU-PROM-04. Desactiva un cargo extra para que deje de aplicarse a pedidos nuevos sin alterar pedidos historicos.",
    response_description="Cargo extra desactivado.",
    responses=PROMOTION_RESPONSES,
)
def delete_extra_charge(charge_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(ExtraCharge, charge_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cargo extra no encontrado")
    item.active = False
    db.commit()
    db.refresh(item)
    return ExtraChargeOut.model_validate(_extra_charge_out(item))


@router.get("/customers")
def seller_customers(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.execute(select(User.id, User.name, User.email, User.tier, func.count(Order.id).label("orders"), func.coalesce(func.sum(Order.total), 0).label("spent")).join(Order, Order.buyer_id == User.id).where(Order.store_id == store.id, Order.status != OrderStatus.cancelled).group_by(User.id, User.name, User.email, User.tier).order_by(func.sum(Order.total).desc())).all()
    return [{"id": row.id, "name": row.name, "email": row.email, "tier": row.tier, "orders": row.orders, "spent": row.spent} for row in rows]


# --- Cuentas de cobro manual (HU-PAG-03 / HU-PAG-04) ------------------------

PAYOUT_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller."},
    404: {"description": "Cuenta de cobro no encontrada en la tienda del vendedor."},
    422: {"description": "Validacion Pydantic (datos incompletos por tipo de cuenta)."},
}


@router.get(
    "/payout-accounts",
    response_model=list[PayoutAccountOut],
    status_code=status.HTTP_200_OK,
    summary="Listar cuentas de cobro",
    description="Rol permitido: seller. HU-PAG-03 y HU-PAG-04. Lista las cuentas de cobro manual (banco/Bre-B) de la tienda, activas e inactivas.",
    response_description="Cuentas de cobro de la tienda.",
    responses=PAYOUT_RESPONSES,
)
def list_payout_accounts(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(PayoutAccount)
        .where(PayoutAccount.store_id == store.id)
        .order_by(PayoutAccount.active.desc(), PayoutAccount.created_at.desc())
    ).all()
    return [_seller_payout_account_out(row) for row in rows]


@router.post(
    "/payout-accounts",
    response_model=PayoutAccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cuenta de cobro",
    description="Rol permitido: seller. HU-PAG-03. Registra una cuenta bancaria o llave Bre-B como medio de cobro manual de la tienda.",
    response_description="Cuenta de cobro creada.",
    responses=PAYOUT_RESPONSES,
)
def create_payout_account(body: PayoutAccountIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    values = body.model_dump()
    values["type"] = PayoutAccountType(values["type"])
    account = PayoutAccount(store_id=store.id, **values)
    db.add(account)
    db.commit()
    db.refresh(account)
    return _seller_payout_account_out(account)


def _seller_payout_account_out(account: PayoutAccount) -> dict:
    return {
        "id": account.id,
        "store_id": account.store_id,
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


def _seller_payout_account(account_id: str, store: Store, db: Session) -> PayoutAccount:
    account = db.get(PayoutAccount, account_id)
    if account is None or account.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cuenta de cobro no encontrada")
    return account


@router.patch(
    "/payout-accounts/{account_id}",
    response_model=PayoutAccountOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar o reactivar cuenta de cobro",
    description="Rol permitido: seller. HU-PAG-04. Actualiza los datos de una cuenta o la reactiva con `active=true`.",
    response_description="Cuenta de cobro actualizada.",
    responses=PAYOUT_RESPONSES,
)
def patch_payout_account(account_id: str, body: PayoutAccountPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    account = _seller_payout_account(account_id, store, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return _seller_payout_account_out(account)


@router.delete(
    "/payout-accounts/{account_id}",
    response_model=PayoutAccountOut,
    status_code=status.HTTP_200_OK,
    summary="Desactivar cuenta de cobro",
    description="Rol permitido: seller. HU-PAG-04. Baja logica: deja de ofrecerse en el checkout pero conserva la referencia en pedidos ya pagados con esa cuenta.",
    response_description="Cuenta de cobro desactivada.",
    responses=PAYOUT_RESPONSES,
)
def deactivate_payout_account(account_id: str, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    account = _seller_payout_account(account_id, store, db)
    account.active = False
    db.commit()
    db.refresh(account)
    return _seller_payout_account_out(account)


# --- Revision de comprobantes (HU-PAG-06 / HU-PAG-07) -----------------------

PAYMENT_REVIEW_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller."},
    404: {"description": "Pago no encontrado en la tienda del vendedor."},
    409: {"description": "El pago ya fue revisado o no admite esta accion."},
    422: {"description": "Validacion Pydantic."},
}


def _seller_payment_out(payment: Payment) -> dict:
    order = payment.order
    difference = payment.amount - payment.received_amount if payment.received_amount is not None else None
    return {
        "id": payment.id,
        "order_id": order.id,
        "status": payment.status.value,
        "method": payment.method,
        "amount": payment.amount,
        "currency": payment.currency,
        "buyer_name": order.buyer.name if order.buyer else None,
        "buyer_email": order.buyer.email if order.buyer else None,
        "buyer_phone": getattr(order.buyer, "phone", None) if order.buyer else None,
        "order_status": order.status.value,
        "created_at": order.created_at,
        "receipt_uploaded_at": payment.receipt_uploaded_at,
        "receipt_url": signed_url(payment.receipt_path),
        "received_amount": payment.received_amount,
        "difference": difference,
        "review_note": payment.review_note,
        "agreement_note": payment.agreement_note,
        "reviewed_at": payment.reviewed_at,
        "payout_account": _seller_payout_account_out(payment.payout_account) if payment.payout_account else None,
    }


@router.get(
    "/payments",
    response_model=list[SellerPaymentOut],
    status_code=status.HTTP_200_OK,
    summary="Listar pagos por revisar",
    description=(
        "Rol permitido: seller. HU-PAG-06. Bandeja de pagos manuales de la tienda. Por defecto "
        "muestra los que esperan revision (`in_review`); acepta `status` para filtrar por cualquier "
        "estado, incluido `incomplete` (pago_incompleto)."
    ),
    response_description="Pagos manuales de la tienda segun el filtro.",
    responses={401: PAYMENT_REVIEW_RESPONSES[401], 403: PAYMENT_REVIEW_RESPONSES[403], 422: PAYMENT_REVIEW_RESPONSES[422]},
)
def seller_payments(
    payment_status: str | None = Query(default=None, alias="status", pattern="^(pending|in_review|incomplete|paid|rejected|refunded)$", description="Estado a filtrar; por defecto in_review."),
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(Payment).join(Order, Payment.order_id == Order.id).where(Order.store_id == store.id)
    if payment_status:
        stmt = stmt.where(Payment.status == PaymentStatus(payment_status))
    else:
        stmt = stmt.where(Payment.status == PaymentStatus.in_review)
    rows = db.scalars(stmt.order_by(Payment.receipt_uploaded_at.desc().nullslast(), Payment.created_at.desc())).unique().all()
    return [_seller_payment_out(row) for row in rows]


def _seller_payment(payment_id: str, store: Store, db: Session) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None or payment.order.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")
    return payment


@router.post(
    "/payments/{payment_id}/confirm",
    response_model=SellerPaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Confirmar comprobante",
    description=(
        "Rol permitido: seller. HU-PAG-06 y HU-PAG-07. Confirma que el dinero llego registrando el "
        "monto recibido; el pago pasa a `paid` (pago_confirmado) y el pedido avanza a confirmado."
    ),
    response_description="Pago confirmado.",
    responses=PAYMENT_REVIEW_RESPONSES,
)
def confirm_manual_payment(
    payment_id: str,
    body: PaymentConfirmIn,
    background: BackgroundTasks,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    payment = _seller_payment(payment_id, store, db)
    if payment.status not in (PaymentStatus.in_review, PaymentStatus.pending, PaymentStatus.incomplete):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pago ya fue revisado")
    order = payment.order
    payment.received_amount = body.received_amount
    payment.review_note = body.note
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = user.id
    payment_service.transition(
        db, payment, PaymentStatus.paid, actor_role="seller", actor_user_id=user.id, note=body.note, received_amount=body.received_amount
    )
    db.commit()
    db.refresh(payment)

    amount_text = f"${body.received_amount:,.0f} COP".replace(",", ".")
    background.add_task(
        mailer.payment_confirmed_to_buyer,
        order.buyer.email if order.buyer else None,
        order.id,
        amount_text,
    )
    return _seller_payment_out(payment)


@router.post(
    "/payments/{payment_id}/reject",
    response_model=SellerPaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Rechazar comprobante",
    description=(
        "Rol permitido: seller. HU-PAG-06. Rechaza el pago: pasa a `rejected` (pago_rechazado), "
        "libera el stock reservado, cancela el pedido y notifica al comprador con el motivo."
    ),
    response_description="Pago rechazado.",
    responses=PAYMENT_REVIEW_RESPONSES,
)
def reject_manual_payment(
    payment_id: str,
    body: PaymentRejectIn,
    background: BackgroundTasks,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    payment = _seller_payment(payment_id, store, db)
    if payment.status not in (PaymentStatus.in_review, PaymentStatus.pending, PaymentStatus.incomplete):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pago ya fue revisado")
    order = payment.order
    payment.review_note = body.note
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = user.id
    payment_service.transition(
        db, payment, PaymentStatus.rejected, actor_role="seller", actor_user_id=user.id, note=body.note
    )
    db.commit()
    db.refresh(payment)

    background.add_task(
        mailer.payment_rejected_to_buyer,
        order.buyer.email if order.buyer else None,
        order.id,
        body.note,
    )
    return _seller_payment_out(payment)


@router.post(
    "/payments/{payment_id}/reopen",
    response_model=SellerPaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Registrar novedad y reabrir por monto de menos",
    description=(
        "Rol permitido: seller. HU-PAG-07. Cuando el comprador transfirio de menos, el vendedor "
        "registra el monto recibido y la novedad, y reabre la carga de comprobante: el pago pasa a "
        "`incomplete` (pago_incompleto), el stock sigue reservado y el comprador recibe en su perfil "
        "y por correo el monto esperado, el recibido, la diferencia y los datos de la cuenta."
    ),
    response_description="Pago en pago_incompleto con la carga reabierta.",
    responses={**PAYMENT_REVIEW_RESPONSES, 400: {"description": "El monto recibido no es menor al total."}},
)
def reopen_manual_payment(
    payment_id: str,
    body: PaymentIncompleteIn,
    background: BackgroundTasks,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    payment = _seller_payment(payment_id, store, db)
    if payment.status not in (PaymentStatus.in_review, PaymentStatus.pending):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pago ya fue revisado")
    if body.received_amount >= payment.amount:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El monto recibido debe ser menor al total para reabrir por saldo faltante")
    order = payment.order
    difference = payment.amount - body.received_amount
    payment.received_amount = body.received_amount
    payment.review_note = body.note
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = user.id
    # El stock sigue reservado: incomplete no aplica efectos de inventario.
    payment_service.transition(
        db, payment, PaymentStatus.incomplete, actor_role="seller", actor_user_id=user.id, note=body.note, received_amount=body.received_amount
    )
    db.commit()
    db.refresh(payment)

    account = _seller_payout_account_out(payment.payout_account) if payment.payout_account else None
    background.add_task(
        mailer.payment_incomplete_to_buyer,
        order.buyer.email if order.buyer else None,
        order.id,
        payment.amount,
        body.received_amount,
        difference,
        account,
    )
    return _seller_payment_out(payment)


@router.post(
    "/payments/{payment_id}/overpaid",
    response_model=SellerPaymentOut,
    status_code=status.HTTP_200_OK,
    summary="Registrar acuerdo por monto de mas",
    description=(
        "Rol permitido: seller. HU-PAG-07. Cuando el comprador pago de mas, el vendedor confirma el "
        "pago y registra la constancia del acuerdo de devolucion. La devolucion se coordina por fuera "
        "de la plataforma (no se genera ningun movimiento de dinero); la respuesta incluye los datos "
        "de contacto del comprador."
    ),
    response_description="Pago confirmado con la constancia del acuerdo por monto de mas.",
    responses=PAYMENT_REVIEW_RESPONSES,
)
def overpaid_manual_payment(
    payment_id: str,
    body: PaymentOverpaidIn,
    background: BackgroundTasks,
    store: Store = Depends(get_seller_store),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    payment = _seller_payment(payment_id, store, db)
    if payment.status not in (PaymentStatus.in_review, PaymentStatus.pending):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este pago ya fue revisado")
    order = payment.order
    payment.received_amount = body.received_amount
    payment.review_note = body.note
    payment.agreement_note = body.note
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = user.id
    # El acuerdo confirma el pago; la devolucion del excedente se hace por fuera.
    payment_service.transition(
        db, payment, PaymentStatus.paid, actor_role="seller", actor_user_id=user.id, note=f"Monto de mas. {body.note}", received_amount=body.received_amount
    )
    db.commit()
    db.refresh(payment)

    amount_text = f"${body.received_amount:,.0f} COP".replace(",", ".")
    background.add_task(
        mailer.payment_confirmed_to_buyer,
        order.buyer.email if order.buyer else None,
        order.id,
        amount_text,
    )
    return _seller_payment_out(payment)
