from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import InventoryMovement, Order, Product, ProductVariant, StockLevel, Warehouse
from app.models.catalog import ProductStatus
from app.models.inventory import InventoryReason


def active_warehouses_for_store(db: Session, store_id: str) -> list[Warehouse]:
    return db.scalars(
        select(Warehouse)
        .where(Warehouse.store_id == store_id, Warehouse.active.is_(True))
        .order_by(Warehouse.is_default.desc(), Warehouse.name)
    ).all()


def active_warehouse_count(db: Session, store_id: str) -> int:
    return db.scalar(
        select(func.count()).select_from(Warehouse).where(Warehouse.store_id == store_id, Warehouse.active.is_(True))
    ) or 0


def single_active_warehouse(db: Session, store_id: str) -> Warehouse | None:
    rows = active_warehouses_for_store(db, store_id)
    return rows[0] if len(rows) == 1 else None


def _levels_for_variant(db: Session, variant_id: str, warehouse_id: str | None = None, *, lock: bool = True) -> list[StockLevel]:
    stmt = (
        select(StockLevel)
        .join(Warehouse)
        .where(StockLevel.variant_id == variant_id, Warehouse.active.is_(True))
        .order_by(Warehouse.is_default.desc(), StockLevel.id)
    )
    if warehouse_id:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)
    if lock:
        stmt = stmt.with_for_update()
    return db.scalars(stmt).all()


def available_for_variant(variant: ProductVariant) -> int:
    return sum(max(0, level.quantity - level.reserved) for level in variant.stock_levels if level.warehouse and level.warehouse.active)


def stock_totals_for_variant(variant: ProductVariant) -> dict:
    levels = [level for level in variant.stock_levels if level.warehouse and level.warehouse.active]
    quantity = sum(level.quantity for level in levels)
    reserved = sum(level.reserved for level in levels)
    available = sum(max(0, level.quantity - level.reserved) for level in levels)
    threshold = min((level.threshold for level in levels), default=0)
    return {"quantity": quantity, "reserved": reserved, "available": available, "threshold": threshold}


def stock_breakdown_for_variant(variant: ProductVariant) -> list[dict]:
    return [
        {
            "warehouse_id": level.warehouse_id,
            "warehouse_name": level.warehouse.name,
            "quantity": level.quantity,
            "reserved": level.reserved,
            "available": max(0, level.quantity - level.reserved),
            "threshold": level.threshold,
            "low_stock": 0 < max(0, level.quantity - level.reserved) <= level.threshold,
            "out_of_stock": max(0, level.quantity - level.reserved) == 0,
        }
        for level in sorted(variant.stock_levels, key=lambda item: (not item.warehouse.is_default, item.warehouse.name))
        if level.warehouse and level.warehouse.active
    ]


def stock_alerts_for_variant(variant: ProductVariant) -> list[dict]:
    totals = stock_totals_for_variant(variant)
    alerts: list[dict] = []
    if totals["available"] == 0:
        alerts.append(
            {
                "variant_id": variant.id,
                "sku": variant.sku,
                "product_id": variant.product_id,
                "product_name": variant.product.name,
                "alert_type": "out_of_stock",
                "available": 0,
                "threshold": totals["threshold"],
                "message": "Stock agotado",
            }
        )
    elif totals["threshold"] and totals["available"] <= totals["threshold"]:
        alerts.append(
            {
                "variant_id": variant.id,
                "sku": variant.sku,
                "product_id": variant.product_id,
                "product_name": variant.product.name,
                "alert_type": "low_stock",
                "available": totals["available"],
                "threshold": totals["threshold"],
                "message": "Stock bajo",
            }
        )
    return alerts


def refresh_product_stock_state(product: Product) -> None:
    active_variants = [variant for variant in product.variants if variant.active]
    if not active_variants or product.status in (ProductStatus.draft, ProductStatus.discontinued):
        return
    any_available = any(available_for_variant(variant) > 0 for variant in active_variants)
    if not any_available and product.status == ProductStatus.active:
        product.status = ProductStatus.out_of_stock
    elif any_available and product.status == ProductStatus.out_of_stock:
        product.status = ProductStatus.active


def _ensure_positive(quantity: int) -> None:
    if quantity <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cantidad debe ser positiva")


def reserve_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None) -> None:
    _ensure_positive(quantity)
    levels = _levels_for_variant(db, variant_id)
    if sum(max(0, level.quantity - level.reserved) for level in levels) < quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente para completar la reserva")

    remaining = quantity
    touched_products: set[Product] = set()
    for level in levels:
        available = max(0, level.quantity - level.reserved)
        reserved = min(available, remaining)
        if reserved:
            level.reserved += reserved
            touched_products.add(level.variant.product)
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
        remaining -= reserved
        if remaining == 0:
            break
    for product in touched_products:
        refresh_product_stock_state(product)


def release_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None) -> None:
    _ensure_positive(quantity)
    remaining = quantity
    touched_products: set[Product] = set()
    for level in _levels_for_variant(db, variant_id):
        released = min(level.reserved, remaining)
        if released:
            level.reserved -= released
            touched_products.add(level.variant.product)
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    warehouse_id=level.warehouse_id,
                    delta=0,
                    reason=InventoryReason.release,
                    order_id=order_id,
                    note=f"Liberacion de {released} unidad(es)",
                )
            )
        remaining -= released
        if remaining == 0:
            break
    for product in touched_products:
        refresh_product_stock_state(product)


def consume_variant(db: Session, variant_id: str, quantity: int, order_id: str | None = None, warehouse_id: str | None = None) -> None:
    _ensure_positive(quantity)
    levels = _levels_for_variant(db, variant_id, warehouse_id)
    if sum(max(0, level.quantity - level.reserved) for level in levels) < quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, "Stock insuficiente para completar la venta")

    remaining = quantity
    touched_products: set[Product] = set()
    for level in levels:
        available = max(0, level.quantity - level.reserved)
        consumed = min(available, remaining)
        if consumed:
            level.quantity -= consumed
            touched_products.add(level.variant.product)
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
        remaining -= consumed
        if remaining == 0:
            break
    for product in touched_products:
        refresh_product_stock_state(product)


def _has_sale_movements(db: Session, order: Order) -> bool:
    return bool(
        db.scalar(
            select(InventoryMovement.id).where(
                InventoryMovement.order_id == order.id,
                InventoryMovement.reason == InventoryReason.sale,
            )
        )
    )


def _has_return_movements(db: Session, order: Order) -> bool:
    return bool(
        db.scalar(
            select(InventoryMovement.id).where(
                InventoryMovement.order_id == order.id,
                InventoryMovement.reason == InventoryReason.return_in,
            )
        )
    )


def _release_reserved_for_assignment(db: Session, variant_id: str, quantity: int, order_id: str) -> None:
    remaining = quantity
    for level in _levels_for_variant(db, variant_id):
        released = min(level.reserved, remaining)
        if released:
            level.reserved -= released
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    warehouse_id=level.warehouse_id,
                    delta=0,
                    reason=InventoryReason.release,
                    order_id=order_id,
                    note=f"Liberacion por asignacion de despacho ({released})",
                )
            )
        remaining -= released
        if remaining == 0:
            return
    if remaining:
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva del pedido ya no esta disponible")


def consume_reserved_order_from_warehouse(db: Session, order: Order, warehouse_id: str) -> None:
    if _has_sale_movements(db, order):
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya tiene stock descontado")
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None or warehouse.store_id != order.store_id or not warehouse.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El almacen no pertenece a tu tienda o esta inactivo")

    for item in order.items:
        if item.variant_id is None:
            continue
        levels = _levels_for_variant(db, item.variant_id, warehouse_id)
        level = levels[0] if levels else None
        if level is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "El almacen seleccionado no tiene stock para el pedido")
        usable = level.quantity - max(0, level.reserved - item.quantity)
        if usable < item.quantity:
            raise HTTPException(status.HTTP_409_CONFLICT, "El almacen seleccionado no tiene stock suficiente")

    for item in order.items:
        if item.variant_id is None:
            continue
        _release_reserved_for_assignment(db, item.variant_id, item.quantity, order.id)
        level = _levels_for_variant(db, item.variant_id, warehouse_id)[0]
        level.quantity -= item.quantity
        db.add(
            InventoryMovement(
                variant_id=item.variant_id,
                warehouse_id=warehouse_id,
                delta=-item.quantity,
                reason=InventoryReason.sale,
                order_id=order.id,
                note="Salida por asignacion de despacho",
            )
        )
        refresh_product_stock_state(level.variant.product)
    order.warehouse_id = warehouse_id


def fulfill_reserved_order(db: Session, order: Order) -> None:
    """Convierte reservas de un pedido en salidas reales al despacharlo."""

    if _has_sale_movements(db, order):
        return
    if order.warehouse_id:
        consume_reserved_order_from_warehouse(db, order, order.warehouse_id)
        return
    raise HTTPException(status.HTTP_409_CONFLICT, "Debes asignar un almacen de despacho antes de enviar")


def release_order(db: Session, order: Order) -> None:
    for item in order.items:
        if item.variant_id:
            release_variant(db, item.variant_id, item.quantity, order.id)


def restock_order(db: Session, order: Order, *, note: str = "Reposicion por cancelacion o devolucion") -> None:
    if _has_return_movements(db, order):
        return
    if not _has_sale_movements(db, order):
        release_order(db, order)
        return
    if not order.warehouse_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido no tiene almacen de origen para reponer")
    for item in order.items:
        if item.variant_id is None:
            continue
        level = db.scalar(
            select(StockLevel)
            .where(StockLevel.variant_id == item.variant_id, StockLevel.warehouse_id == order.warehouse_id)
            .with_for_update()
        )
        if level is None:
            level = StockLevel(variant_id=item.variant_id, warehouse_id=order.warehouse_id, quantity=0)
            db.add(level)
            db.flush()
        level.quantity += item.quantity
        db.add(
            InventoryMovement(
                variant_id=item.variant_id,
                warehouse_id=order.warehouse_id,
                delta=item.quantity,
                reason=InventoryReason.return_in,
                order_id=order.id,
                note=note,
            )
        )
        refresh_product_stock_state(level.variant.product)
