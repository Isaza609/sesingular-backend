from __future__ import annotations

from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InventoryMovement, Product, ProductVariant, StockLevel, Warehouse
from app.models.inventory import InventoryReason
from app.modules.common.permissions import get_seller_store
from app.modules.inventory.schemas import (
    InventoryAlertOut,
    InventoryItemOut,
    MovementOut,
    PublicStockOut,
    StockOut,
    StockPatch,
    WarehouseIn,
    WarehouseOut,
    WarehousePatch,
)
from app.modules.inventory.service import (
    available_for_variant,
    refresh_product_stock_state,
    stock_alerts_for_variant,
    stock_breakdown_for_variant,
    stock_totals_for_variant,
)

seller_router = APIRouter(prefix="/seller", tags=["seller-inventory"])
public_router = APIRouter(prefix="/catalog", tags=["catalog-inventory"])

WAREHOUSE_RESPONSES = {
    400: {"description": "Almacen inactivo o regla de negocio no permitida."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "Almacen o recurso no encontrado en la tienda."},
    422: {"description": "Validacion Pydantic."},
}
INVENTORY_RESPONSES = {
    400: {"description": "Datos invalidos o almacen inactivo."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o recurso fuera de la tienda."},
    404: {"description": "Variante, producto o almacen no encontrado."},
    409: {"description": "Stock insuficiente o estado incompatible."},
    422: {"description": "Validacion Pydantic."},
}


def _warehouse(store_id: str, warehouse_id: str, db: Session) -> Warehouse:
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None or warehouse.store_id != store_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Almacen no encontrado")
    return warehouse


def _active_warehouse(store_id: str, warehouse_id: str, db: Session) -> Warehouse:
    warehouse = _warehouse(store_id, warehouse_id, db)
    if not warehouse.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El almacen esta inactivo y no admite nuevas operaciones")
    return warehouse


def _requires_manual_dispatch_selection(store_id: str, db: Session) -> bool:
    active_count = db.scalar(select(func.count()).select_from(Warehouse).where(Warehouse.store_id == store_id, Warehouse.active.is_(True))) or 0
    return active_count > 1


def _warehouse_out(row: Warehouse, requires_manual_dispatch_selection: bool) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "address_line": row.address_line,
        "city": row.city,
        "region": row.region,
        "is_default": row.is_default,
        "active": row.active,
        "requires_manual_dispatch_selection": requires_manual_dispatch_selection,
    }


def _stock_out(row: StockLevel) -> dict:
    return {
        "id": row.id,
        "variant_id": row.variant_id,
        "sku": row.variant.sku,
        "product_id": row.variant.product_id,
        "product_name": row.variant.product.name,
        "warehouse_id": row.warehouse_id,
        "warehouse_name": row.warehouse.name,
        "quantity": row.quantity,
        "reserved": row.reserved,
        "available": max(0, row.quantity - row.reserved),
        "threshold": row.threshold,
        "updated_at": row.updated_at,
    }


def _inventory_item_out(variant: ProductVariant, *, warehouse_id: str | None = None) -> dict:
    warehouses = stock_breakdown_for_variant(variant)
    if warehouse_id:
        warehouses = [row for row in warehouses if row["warehouse_id"] == warehouse_id]
    quantity = sum(row["quantity"] for row in warehouses)
    reserved = sum(row["reserved"] for row in warehouses)
    available = sum(row["available"] for row in warehouses)
    threshold = min((row["threshold"] for row in warehouses), default=0)
    return {
        "variant_id": variant.id,
        "sku": variant.sku,
        "product_id": variant.product_id,
        "product_name": variant.product.name,
        "product_status": variant.product.status.value,
        "quantity": quantity,
        "reserved": reserved,
        "available": available,
        "threshold": threshold,
        "low_stock": bool(threshold and 0 < available <= threshold),
        "out_of_stock": available == 0,
        "warehouses": warehouses,
    }


def _movement_out(row: InventoryMovement) -> dict:
    return {
        "id": row.id,
        "variant_id": row.variant_id,
        "sku": row.variant.sku,
        "product_id": row.variant.product_id,
        "product_name": row.variant.product.name,
        "warehouse_id": row.warehouse_id,
        "warehouse_name": row.warehouse.name if row.warehouse_id and row.warehouse else None,
        "delta": row.delta,
        "reason": row.reason.value,
        "order_id": row.order_id,
        "note": row.note,
        "created_at": row.created_at,
    }


@public_router.get(
    "/variants/{variant_id}/stock",
    response_model=PublicStockOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar stock publico de variante",
    description="Endpoint publico. HU-INV-07. Retorna disponibilidad real agregada de una variante descontando reservas vigentes.",
    response_description="Stock disponible y banderas de disponibilidad para comprador.",
    responses={404: {"description": "Variante no encontrada o inactiva."}, 422: {"description": "Validacion Pydantic."}},
)
def public_variant_stock(variant_id: str, db: Session = Depends(get_db)):
    variant = db.get(ProductVariant, variant_id)
    if variant is None or not variant.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no encontrada")
    totals = stock_totals_for_variant(variant)
    return PublicStockOut(
        variant_id=variant.id,
        stock=totals["available"],
        available=totals["available"] > 0 and variant.product.status.value == "active",
        low_stock=bool(totals["threshold"] and 0 < totals["available"] <= totals["threshold"]),
        out_of_stock=totals["available"] == 0,
    )


@seller_router.get(
    "/warehouses",
    response_model=list[WarehouseOut],
    status_code=status.HTTP_200_OK,
    summary="Listar almacenes",
    description="Rol permitido: seller. HU-TDA-02 y HU-INV-03. Lista puntos o almacenes activos e inactivos de la tienda autenticada e indica si requiere asignacion manual de despacho.",
    response_description="Almacenes de la tienda con indicador de seleccion manual de despacho.",
    responses=WAREHOUSE_RESPONSES,
)
def list_warehouses(store=Depends(get_seller_store), db: Session = Depends(get_db)):
    rows = db.scalars(select(Warehouse).where(Warehouse.store_id == store.id).order_by(Warehouse.is_default.desc(), Warehouse.name)).all()
    requires_manual = _requires_manual_dispatch_selection(store.id, db)
    return [_warehouse_out(row, requires_manual) for row in rows]


@seller_router.post(
    "/warehouses",
    response_model=WarehouseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear almacen",
    description="Rol permitido: seller. HU-TDA-02 y HU-INV-01. Registra un punto o almacen de la tienda para asociarle stock por SKU.",
    response_description="Almacen creado y disponible segun su estado activo.",
    responses=WAREHOUSE_RESPONSES,
)
def create_warehouse(body: WarehouseIn, store=Depends(get_seller_store), db: Session = Depends(get_db)):
    active_count = db.scalar(select(func.count()).select_from(Warehouse).where(Warehouse.store_id == store.id, Warehouse.active.is_(True))) or 0
    values = body.model_dump()
    if values["active"] and active_count == 0:
        values["is_default"] = True
    if values["is_default"]:
        db.query(Warehouse).filter(Warehouse.store_id == store.id).update({Warehouse.is_default: False})
    warehouse = Warehouse(store_id=store.id, **values)
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return _warehouse_out(warehouse, _requires_manual_dispatch_selection(store.id, db))


@seller_router.patch(
    "/warehouses/{warehouse_id}",
    response_model=WarehouseOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar almacen",
    description="Rol permitido: seller. HU-TDA-02 y HU-INV-03. Actualiza o desactiva un almacen sin afectar pedidos ni movimientos historicos.",
    response_description="Almacen actualizado.",
    responses=WAREHOUSE_RESPONSES,
)
def patch_warehouse(warehouse_id: str, body: WarehousePatch, store=Depends(get_seller_store), db: Session = Depends(get_db)):
    warehouse = _warehouse(store.id, warehouse_id, db)
    values = body.model_dump(exclude_unset=True)
    if values.get("is_default"):
        db.query(Warehouse).filter(Warehouse.store_id == store.id).update({Warehouse.is_default: False})
    for key, value in values.items():
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return _warehouse_out(warehouse, _requires_manual_dispatch_selection(store.id, db))


@seller_router.get(
    "/inventory",
    response_model=list[InventoryItemOut],
    status_code=status.HTTP_200_OK,
    summary="Listar inventario",
    description="Rol permitido: seller. HU-INV-01 y HU-INV-05. Lista inventario agregado por variante con desglose por almacen, disponible, reservado y alertas de bajo stock o agotado.",
    response_description="Inventario agregado de la tienda autenticada.",
    responses=INVENTORY_RESPONSES,
)
def list_inventory(
    warehouse_id: str | None = None,
    product_id: str | None = None,
    variant_id: str | None = None,
    low_stock: bool = False,
    store=Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    if warehouse_id:
        _warehouse(store.id, warehouse_id, db)
    stmt = select(ProductVariant).join(Product).where(Product.store_id == store.id)
    if product_id:
        stmt = stmt.where(Product.id == product_id)
    if variant_id:
        stmt = stmt.where(ProductVariant.id == variant_id)
    rows = db.scalars(stmt.order_by(Product.name, ProductVariant.sku)).unique().all()
    result = [_inventory_item_out(variant, warehouse_id=warehouse_id) for variant in rows]
    if low_stock:
        result = [row for row in result if row["low_stock"] or row["out_of_stock"]]
    return [InventoryItemOut.model_validate(row) for row in result]


@seller_router.patch(
    "/inventory/{variant_id}",
    response_model=list[StockOut],
    status_code=status.HTTP_200_OK,
    summary="Ajustar stock de variante",
    description="Rol permitido: seller. HU-INV-01, HU-INV-05 y HU-INV-06. Registra o actualiza el stock de una variante en un almacen propio y deja movimiento de auditoria.",
    response_description="Desglose actualizado de stock por almacen para la variante.",
    responses=INVENTORY_RESPONSES,
)
def adjust_inventory(variant_id: str, body: StockPatch, store=Depends(get_seller_store), db: Session = Depends(get_db)):
    variant = db.get(ProductVariant, variant_id)
    if variant is None or variant.product.store_id != store.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no encontrada")
    warehouse = _active_warehouse(store.id, body.warehouse_id, db)
    row = db.scalar(select(StockLevel).where(StockLevel.variant_id == variant_id, StockLevel.warehouse_id == warehouse.id).with_for_update())
    previous = row.quantity if row else 0
    if row is None:
        row = StockLevel(variant_id=variant_id, warehouse_id=warehouse.id, quantity=body.quantity, threshold=body.threshold)
        db.add(row)
    else:
        row.quantity = body.quantity
        row.threshold = body.threshold
    reason = InventoryReason.restock if body.quantity >= previous else InventoryReason.adjust
    db.add(InventoryMovement(variant_id=variant_id, warehouse_id=warehouse.id, delta=body.quantity - previous, reason=reason, note=body.note))
    refresh_product_stock_state(variant.product)
    db.commit()
    rows = db.scalars(select(StockLevel).join(Warehouse).where(StockLevel.variant_id == variant_id, Warehouse.store_id == store.id).order_by(Warehouse.name)).all()
    return [StockOut.model_validate(_stock_out(item)) for item in rows]


@seller_router.get(
    "/inventory/alerts",
    response_model=list[InventoryAlertOut],
    status_code=status.HTTP_200_OK,
    summary="Listar alertas de inventario",
    description="Rol permitido: seller. HU-INV-05. Lista alertas dinamicas de stock bajo o agotado calculadas desde el disponible agregado actual.",
    response_description="Alertas vigentes de bajo stock y agotado.",
    responses=INVENTORY_RESPONSES,
)
def inventory_alerts(store=Depends(get_seller_store), db: Session = Depends(get_db)):
    variants = db.scalars(select(ProductVariant).join(Product).where(Product.store_id == store.id).order_by(Product.name, ProductVariant.sku)).unique().all()
    alerts = [alert for variant in variants for alert in stock_alerts_for_variant(variant)]
    return [InventoryAlertOut.model_validate(alert) for alert in alerts]


@seller_router.get(
    "/inventory/movements",
    response_model=list[MovementOut],
    status_code=status.HTTP_200_OK,
    summary="Listar movimientos de inventario",
    description="Rol permitido: seller. HU-INV-04 y HU-INV-06. Lista historial de ajustes, reservas, liberaciones, ventas y devoluciones con filtros de auditoria.",
    response_description="Movimientos de inventario dentro del scope de la tienda.",
    responses=INVENTORY_RESPONSES,
)
def inventory_movements(
    product_id: str | None = None,
    variant_id: str | None = None,
    warehouse_id: str | None = None,
    reason: str | None = Query(None, pattern="^(reserve|release|sale|adjust|restock|return_in)$"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    store=Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    if warehouse_id:
        _warehouse(store.id, warehouse_id, db)
    stmt = (
        select(InventoryMovement)
        .join(ProductVariant, ProductVariant.id == InventoryMovement.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Warehouse, Warehouse.id == InventoryMovement.warehouse_id, isouter=True)
        .where(Product.store_id == store.id)
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )
    if product_id:
        stmt = stmt.where(Product.id == product_id)
    if variant_id:
        stmt = stmt.where(ProductVariant.id == variant_id)
    if warehouse_id:
        stmt = stmt.where(InventoryMovement.warehouse_id == warehouse_id)
    if reason:
        stmt = stmt.where(InventoryMovement.reason == InventoryReason(reason))
    if date_from:
        stmt = stmt.where(InventoryMovement.created_at >= date_from)
    if date_to:
        end = datetime.combine(date_to.date(), time.max, timezone.utc) if date_to.time() == time.min else date_to
        stmt = stmt.where(InventoryMovement.created_at <= end)
    rows = db.scalars(stmt).all()
    return [MovementOut.model_validate(_movement_out(row)) for row in rows]
