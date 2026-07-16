from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryMovement, Order, OrderItem, ProductVariant, StockLevel, Warehouse
from app.models.inventory import InventoryReason


def _levels_for_variant(db: Session, variant_id: str, warehouse_id: str | None = None):
    stmt = (
        select(StockLevel)
        .join(Warehouse)
        .where(StockLevel.variant_id == variant_id, Warehouse.active.is_(True))
        .order_by(Warehouse.is_default.desc(), StockLevel.id)
        .with_for_update()
    )
    if warehouse_id:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)
    return db.scalars(stmt).all()


def reserve_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None) -> None:
    if quantity <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cantidad debe ser positiva")
    levels = _levels_for_variant(db, variant_id)
    remaining = quantity
    for level in levels:
        available = max(0, level.quantity - level.reserved)
        reserved = min(available, remaining)
        level.reserved += reserved
        remaining -= reserved
        if reserved:
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    warehouse_id=level.warehouse_id,
                    delta=0,
                    reason=InventoryReason.reserve,
                    order_id=order_id,
                    note=f"Reserva de {reserved} unidad(es)",
                )
            )
        if remaining == 0:
            break
    if remaining:
        raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente para completar la reserva")


def release_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None) -> None:
    remaining = quantity
    for level in _levels_for_variant(db, variant_id):
        released = min(level.reserved, remaining)
        level.reserved -= released
        remaining -= released
        if released:
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    warehouse_id=level.warehouse_id,
                    delta=0,
                    reason=InventoryReason.release,
                    order_id=order_id,
                    note=f"Liberación de {released} unidad(es)",
                )
            )
        if remaining == 0:
            break


def consume_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None, warehouse_id: str | None = None) -> None:
    if quantity <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cantidad debe ser positiva")
    levels = _levels_for_variant(db, variant_id, warehouse_id)
    remaining = quantity
    for level in levels:
        available = max(0, level.quantity - level.reserved)
        consumed = min(available, remaining)
        level.quantity -= consumed
        remaining -= consumed
        if consumed:
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    warehouse_id=level.warehouse_id,
                    delta=-consumed,
                    reason=InventoryReason.sale,
                    order_id=order_id,
                    note="Salida por venta",
                )
            )
        if remaining == 0:
            break
    if remaining:
        raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente para completar la venta")


def fulfill_reserved_order(db: Session, order: Order) -> None:
    """Convierte las reservas de un pedido en salidas reales al despacharlo."""

    for item in order.items:
        remaining = item.quantity
        levels = _levels_for_variant(db, item.variant_id)
        if order.warehouse_id:
            levels.sort(key=lambda level: 0 if level.warehouse_id == order.warehouse_id else 1)
        for level in levels:
            moved = min(level.reserved, remaining)
            level.reserved -= moved
            level.quantity -= moved
            remaining -= moved
            if moved:
                db.add(
                    InventoryMovement(
                        variant_id=item.variant_id,
                        warehouse_id=level.warehouse_id,
                        delta=-moved,
                        reason=InventoryReason.sale,
                        order_id=order.id,
                        note="Salida de pedido reservado",
                    )
                )
            if remaining == 0:
                break
        if remaining:
            raise HTTPException(status.HTTP_409_CONFLICT, "La reserva del pedido ya no está disponible")


def release_order(db: Session, order: Order) -> None:
    for item in order.items:
        if item.variant_id:
            release_variant(db, item.variant_id, item.quantity, order.id)
