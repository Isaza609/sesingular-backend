from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Coupon, Order, OrderItem, Payment, PlatformSetting, ProductVariant, Promotion, Store, User, Warehouse
from app.models.order import OrderStatus, SaleChannel
from app.models.payment import PaymentStatus
from app.models.promotion import DiscountType
from app.modules.common.permissions import get_seller_store
from app.modules.inventory.service import consume_variant, fulfill_reserved_order, release_order
from app.modules.orders.router import _order_out
from app.modules.orders.schemas import OrderOut, OrderStatusPatch, PosOrderIn, WarehouseAssign
from app.modules.seller.schemas import CouponIn, CouponPatch, PromotionIn, PromotionPatch

router = APIRouter(prefix="/seller", tags=["seller"])


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


@router.get("/dashboard")
def seller_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(Order).where(Order.store_id == store.id, Order.status != OrderStatus.cancelled)
    if date_from:
        stmt = stmt.where(Order.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to:
        stmt = stmt.where(Order.created_at < datetime.combine(date_to, datetime.max.time(), timezone.utc))
    orders = db.scalars(stmt).all()
    gross = sum(order.total for order in orders)
    costs = sum(item.quantity * (item.unit_cost or 0) for order in orders for item in order.items)
    fees = sum(payment.platform_fee for order in orders for payment in order.payments if payment.status == PaymentStatus.paid)
    by_channel = []
    for channel in SaleChannel:
        channel_orders = [order for order in orders if order.channel == channel]
        by_channel.append({"channel": channel.value, "orders": len(channel_orders), "gross": sum(order.total for order in channel_orders)})
    return {"totals": {"orders": len(orders), "gross": gross, "costs": costs, "platform_fees": fees, "profit": gross - costs - fees}, "by_channel": by_channel}


@router.get("/reports/sales")
def seller_sales_report(
    date_from: date | None = None,
    date_to: date | None = None,
    store: Store = Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    return seller_dashboard(date_from, date_to, store, db)


@router.get("/orders", response_model=list[OrderOut])
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


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def patch_order_status(order_id: str, body: OrderStatusPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    order = _seller_order(order_id, store, db)
    target = OrderStatus(body.status)
    _assert_transition(order.status, target)
    if target == OrderStatus.cancelled and order.status != OrderStatus.cancelled:
        release_order(db, order)
    if target == OrderStatus.shipped and order.status != OrderStatus.shipped:
        fulfill_reserved_order(db, order)
    order.status = target
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


@router.patch("/orders/{order_id}/warehouse", response_model=OrderOut)
def assign_order_warehouse(order_id: str, body: WarehouseAssign, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    order = _seller_order(order_id, store, db)
    warehouse = db.get(Warehouse, body.warehouse_id)
    if warehouse is None or warehouse.store_id != store.id or not warehouse.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El almacén no pertenece a tu tienda o está inactivo")
    order.warehouse_id = warehouse.id
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


@router.post("/pos/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_pos_order(body: PosOrderIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True), Warehouse.is_default.is_(True)))
    if warehouse is None:
        warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True)).order_by(Warehouse.name))
    if warehouse is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes registrar un almacén antes de vender")
    try:
        variants = []
        for item in body.items:
            variant = db.get(ProductVariant, item.variant_id)
            if variant is None or not variant.active or variant.product.store_id != store.id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Una variante no pertenece a tu tienda")
            consume_variant(db, variant.id, item.quantity, warehouse_id=warehouse.id)
            variants.append((item, variant))
        subtotal = sum(item.quantity * variant.price for item, variant in variants)
        order = Order(store_id=store.id, buyer_id=body.buyer_id, warehouse_id=warehouse.id, channel=SaleChannel.presencial, status=OrderStatus.delivered, subtotal=subtotal, total=subtotal, notes=body.notes)
        db.add(order)
        db.flush()
        for item, variant in variants:
            db.add(OrderItem(order_id=order.id, variant_id=variant.id, product_name=variant.product.name, sku=variant.sku, quantity=item.quantity, unit_price=variant.price, unit_cost=variant.cost))
        setting = db.get(PlatformSetting, "commission")
        pct = int((setting.value if setting else {}).get("value", 0))
        fee = subtotal * pct // 100
        db.add(Payment(order_id=order.id, provider="pos", method=body.payment_method, status=PaymentStatus.paid, amount=subtotal, platform_fee=fee, seller_amount=subtotal - fee, currency="COP"))
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return OrderOut.model_validate(_order_out(order))


def _promotion_out(item: Promotion | Coupon) -> dict:
    return {"id": item.id, "store_id": item.store_id, "code": getattr(item, "code", None), "name": getattr(item, "name", None), "discount_type": item.discount_type.value, "value": item.value, "min_quantity": getattr(item, "min_quantity", None), "max_uses": getattr(item, "max_uses", None), "used_count": getattr(item, "used_count", None), "starts_at": item.starts_at, "ends_at": item.ends_at, "active": item.active, "created_at": item.created_at}


@router.get("/promotions")
def list_promotions(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    return [_promotion_out(item) for item in db.scalars(select(Promotion).where(Promotion.store_id == store.id).order_by(Promotion.created_at.desc())).all()]


@router.post("/promotions", status_code=status.HTTP_201_CREATED)
def create_promotion(body: PromotionIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = Promotion(store_id=store.id, discount_type=DiscountType(body.discount_type), **body.model_dump(exclude={"discount_type"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    return _promotion_out(item)


@router.patch("/promotions/{promotion_id}")
def patch_promotion(promotion_id: str, body: PromotionPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Promotion, promotion_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promoción no encontrada")
    values = body.model_dump(exclude_unset=True)
    if "discount_type" in values:
        values["discount_type"] = DiscountType(values["discount_type"])
    for key, value in values.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return _promotion_out(item)


@router.get("/coupons")
def list_coupons(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    return [_promotion_out(item) for item in db.scalars(select(Coupon).where(Coupon.store_id == store.id).order_by(Coupon.created_at.desc())).all()]


@router.post("/coupons", status_code=status.HTTP_201_CREATED)
def create_coupon(body: CouponIn, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = Coupon(store_id=store.id, code=body.code.upper(), discount_type=DiscountType(body.discount_type), **body.model_dump(exclude={"code", "discount_type"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    return _promotion_out(item)


@router.patch("/coupons/{coupon_id}")
def patch_coupon(coupon_id: str, body: CouponPatch, store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    item = db.get(Coupon, coupon_id)
    if item is None or item.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cupón no encontrado")
    values = body.model_dump(exclude_unset=True)
    if "code" in values:
        values["code"] = values["code"].upper()
    if "discount_type" in values:
        values["discount_type"] = DiscountType(values["discount_type"])
    for key, value in values.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return _promotion_out(item)


@router.get("/customers")
def seller_customers(store: Store = Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.execute(select(User.id, User.name, User.email, func.count(Order.id).label("orders"), func.coalesce(func.sum(Order.total), 0).label("spent")).join(Order, Order.buyer_id == User.id).where(Order.store_id == store.id, Order.status != OrderStatus.cancelled).group_by(User.id, User.name, User.email).order_by(func.sum(Order.total).desc())).all()
    return [{"id": row.id, "name": row.name, "email": row.email, "orders": row.orders, "spent": row.spent} for row in rows]
