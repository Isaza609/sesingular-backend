"""Consultas y operaciones del panel de administración."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.orm import Session

from app.models import (
    Dispute,
    Order,
    Payment,
    PlatformSetting,
    Product,
    ProductVariant,
    Review,
    ReviewReport,
    StockLevel,
    Store,
    StoreMember,
    User,
    Warehouse,
)
from app.models.order import OrderStatus, SaleChannel
from app.models.payment import PaymentStatus

SECRET_GATEWAY_FIELDS = ("access_token", "webhook_secret")


# ---------- usuarios / tiendas ----------

def list_users(
    db: Session,
    q: str | None,
    role: str | None,
    active: bool | None,
    page: int,
    page_size: int,
):
    stmt = select(User)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(User.email).like(pattern) | func.lower(User.name).like(pattern))
    if role:
        stmt = stmt.where(User.role == role)
    if active is not None:
        stmt = stmt.where(User.active == active)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return rows, total


def list_stores(db: Session, q: str | None, active: bool | None, page: int, page_size: int):
    stmt = select(Store)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Store.name).like(pattern) | func.lower(Store.slug).like(pattern))
    if active is not None:
        stmt = stmt.where(Store.active == active)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Store.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return rows, total


def store_counts(db: Session, store_id: str) -> dict:
    members = db.scalar(
        select(func.count()).select_from(StoreMember).where(StoreMember.store_id == store_id)
    )
    warehouses = db.scalar(
        select(func.count()).select_from(Warehouse).where(Warehouse.store_id == store_id)
    )
    products = db.scalar(
        select(func.count()).select_from(Product).where(Product.store_id == store_id)
    )
    return {"members": members or 0, "warehouses": warehouses or 0, "products": products or 0}


# ---------- configuración de plataforma ----------

def get_settings_masked(db: Session) -> list[PlatformSetting]:
    rows = db.scalars(select(PlatformSetting)).all()
    for row in rows:
        if row.key == "payment_gateway":
            masked = dict(row.value)
            for field in SECRET_GATEWAY_FIELDS:
                secret = masked.get(field) or ""
                masked[field] = f"****{secret[-4:]}" if secret else ""
            row.value = masked
    return rows


def upsert_setting(db: Session, key: str, value: dict, admin_id: str) -> PlatformSetting:
    row = db.get(PlatformSetting, key)
    if row is None:
        row = PlatformSetting(key=key, value=value, updated_by=admin_id)
        db.add(row)
    else:
        row.value = value
        row.updated_by = admin_id
    db.commit()
    db.refresh(row)
    return row


def update_gateway(db: Session, incoming: dict, admin_id: str) -> PlatformSetting:
    row = db.get(PlatformSetting, "payment_gateway")
    current = dict(row.value) if row else {}
    for field in SECRET_GATEWAY_FIELDS:
        # Campo vacío en el request = conservar el secreto guardado
        if not incoming.get(field):
            incoming[field] = current.get(field, "")
    return upsert_setting(db, "payment_gateway", incoming, admin_id)


# ---------- reportes globales ----------

def sales_report(
    db: Session,
    date_from: date | None,
    date_to: date | None,
    store_id: str | None,
    channel: str | None,
) -> dict:
    def base_filter(stmt):
        if date_from:
            stmt = stmt.where(Order.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
        if date_to:
            stmt = stmt.where(Order.created_at < datetime.combine(date_to, datetime.max.time(), timezone.utc))
        if store_id:
            stmt = stmt.where(Order.store_id == store_id)
        if channel:
            stmt = stmt.where(Order.channel == SaleChannel(channel))
        return stmt.where(Order.status != OrderStatus.cancelled)

    totals_row = db.execute(
        base_filter(
            select(
                func.count(Order.id).label("orders"),
                func.coalesce(func.sum(Order.total), 0).label("gross"),
            )
        )
    ).one()

    fees = db.scalar(
        base_filter(
            select(func.coalesce(func.sum(Payment.platform_fee), 0))
            .select_from(Payment)
            .join(Order, Payment.order_id == Order.id)
            .where(Payment.status == PaymentStatus.paid)
        )
    ) or 0

    by_channel = [
        {"channel": r.channel.value, "orders": r.orders, "gross": r.gross}
        for r in db.execute(
            base_filter(
                select(
                    Order.channel,
                    func.count(Order.id).label("orders"),
                    func.coalesce(func.sum(Order.total), 0).label("gross"),
                )
            ).group_by(Order.channel)
        ).all()
    ]

    by_store = [
        {"store_id": r.store_id, "store_name": r.name, "orders": r.orders, "gross": r.gross}
        for r in db.execute(
            base_filter(
                select(
                    Order.store_id,
                    Store.name,
                    func.count(Order.id).label("orders"),
                    func.coalesce(func.sum(Order.total), 0).label("gross"),
                ).join(Store, Order.store_id == Store.id)
            )
            .group_by(Order.store_id, Store.name)
            .order_by(func.coalesce(func.sum(Order.total), 0).desc())
            .limit(20)
        ).all()
    ]

    day = cast(Order.created_at, Date)
    by_day = [
        {"day": r.day.isoformat(), "orders": r.orders, "gross": r.gross}
        for r in db.execute(
            base_filter(
                select(
                    day.label("day"),
                    func.count(Order.id).label("orders"),
                    func.coalesce(func.sum(Order.total), 0).label("gross"),
                )
            )
            .group_by(day)
            .order_by(day)
        ).all()
    ]

    return {
        "totals": {"orders": totals_row.orders, "gross": totals_row.gross, "platform_fees": fees},
        "by_channel": by_channel,
        "by_store": by_store,
        "by_day": by_day,
    }


def inventory_report(db: Session, store_id: str | None) -> dict:
    low_stock = (StockLevel.quantity - StockLevel.reserved) <= StockLevel.threshold

    store_stmt = (
        select(
            Store.id.label("store_id"),
            Store.name.label("store_name"),
            func.count(StockLevel.id).label("skus"),
            func.coalesce(func.sum(StockLevel.quantity), 0).label("quantity"),
            func.coalesce(func.sum(StockLevel.reserved), 0).label("reserved"),
            func.coalesce(func.sum(case((low_stock, 1), else_=0)), 0).label("low_stock"),
        )
        .select_from(StockLevel)
        .join(Warehouse, StockLevel.warehouse_id == Warehouse.id)
        .join(Store, Warehouse.store_id == Store.id)
        .group_by(Store.id, Store.name)
        .order_by(Store.name)
    )
    if store_id:
        store_stmt = store_stmt.where(Store.id == store_id)

    stores = [dict(r._mapping) for r in db.execute(store_stmt).all()]

    wh_stmt = (
        select(
            Warehouse.id.label("warehouse_id"),
            Warehouse.name.label("warehouse_name"),
            Warehouse.store_id.label("store_id"),
            func.count(StockLevel.id).label("skus"),
            func.coalesce(func.sum(StockLevel.quantity), 0).label("quantity"),
            func.coalesce(func.sum(StockLevel.reserved), 0).label("reserved"),
        )
        .select_from(Warehouse)
        .outerjoin(StockLevel, StockLevel.warehouse_id == Warehouse.id)
        .group_by(Warehouse.id, Warehouse.name, Warehouse.store_id)
        .order_by(Warehouse.name)
    )
    if store_id:
        wh_stmt = wh_stmt.where(Warehouse.store_id == store_id)

    warehouses = [dict(r._mapping) for r in db.execute(wh_stmt).all()]
    return {"stores": stores, "warehouses": warehouses}


# ---------- moderación ----------

def reported_reviews(db: Session, status: str | None):
    stmt = (
        select(ReviewReport, Review, Product.name.label("product_name"), Store.name.label("store_name"), User.name.label("reviewer_name"))
        .join(Review, ReviewReport.review_id == Review.id)
        .join(Product, Review.product_id == Product.id)
        .join(Store, Review.store_id == Store.id)
        .outerjoin(User, Review.user_id == User.id)
        .order_by(ReviewReport.created_at.desc())
    )
    if status:
        stmt = stmt.where(ReviewReport.status == status)
    return db.execute(stmt).all()


def list_disputes(db: Session, status: str | None):
    stmt = (
        select(Dispute, Store.name.label("store_name"), User.name.label("opener_name"))
        .join(Order, Dispute.order_id == Order.id)
        .join(Store, Order.store_id == Store.id)
        .outerjoin(User, Dispute.opened_by == User.id)
        .order_by(Dispute.created_at.desc())
    )
    if status:
        stmt = stmt.where(Dispute.status == status)
    return db.execute(stmt).all()
