from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InventoryMovement, ProductVariant, StockLevel, Warehouse
from app.models.inventory import InventoryReason
from app.models.user import User
from app.modules.auth.deps import get_current_user
from app.modules.catalog.router import _stock
from app.modules.common.permissions import get_seller_store, require_seller
from app.modules.inventory.schemas import MovementOut, StockOut, StockPatch, WarehouseIn, WarehouseOut, WarehousePatch

seller_router = APIRouter(prefix="/seller", tags=["seller-inventory"])
public_router = APIRouter(prefix="/catalog", tags=["catalog-inventory"])
WAREHOUSE_RESPONSES = {
    400: {"description": "Almacen inactivo o regla de negocio no permitida."},
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol seller o cambio de contrasena pendiente."},
    404: {"description": "Almacen o recurso no encontrado en la tienda."},
    422: {"description": "Validacion Pydantic."},
}


def _warehouse(store_id: str, warehouse_id: str, db: Session) -> Warehouse:
    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None or warehouse.store_id != store_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Almacén no encontrado")
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


@public_router.get("/variants/{variant_id}/stock")
def public_variant_stock(variant_id: str, db: Session = Depends(get_db)):
    variant = db.get(ProductVariant, variant_id)
    if variant is None or not variant.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Variante no encontrada")
    return {"variant_id": variant.id, "stock": _stock(variant), "available": _stock(variant) > 0}


@seller_router.get(
    "/warehouses",
    response_model=list[WarehouseOut],
    status_code=status.HTTP_200_OK,
    summary="Listar almacenes",
    description="Rol permitido: seller. HU-TDA-02. Lista puntos o almacenes activos e inactivos de la tienda autenticada.",
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
    description="Rol permitido: seller. HU-TDA-02. Registra un punto o almacen de la tienda para asociarle stock.",
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
    description="Rol permitido: seller. HU-TDA-02. Actualiza o desactiva un almacen sin afectar pedidos ni movimientos historicos.",
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


@seller_router.get("/inventory", response_model=list[StockOut])
def list_inventory(
    warehouse_id: str | None = None,
    low_stock: bool = False,
    store=Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = select(StockLevel).join(Warehouse).where(Warehouse.store_id == store.id)
    if warehouse_id:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)
    if low_stock:
        stmt = stmt.where((StockLevel.quantity - StockLevel.reserved) <= StockLevel.threshold)
    return [StockOut.model_validate(_stock_out(row)) for row in db.scalars(stmt.order_by(StockLevel.updated_at.desc())).all()]


@seller_router.patch("/inventory/{variant_id}", response_model=list[StockOut])
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
    db.add(InventoryMovement(variant_id=variant_id, warehouse_id=warehouse.id, delta=body.quantity - previous, reason=InventoryReason.restock if body.quantity >= previous else InventoryReason.adjust, note=body.note))
    db.commit()
    rows = db.scalars(select(StockLevel).join(Warehouse).where(StockLevel.variant_id == variant_id, Warehouse.store_id == store.id)).all()
    return [StockOut.model_validate(_stock_out(item)) for item in rows]


@seller_router.get("/inventory/movements", response_model=list[MovementOut])
def inventory_movements(
    variant_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    store=Depends(get_seller_store),
    db: Session = Depends(get_db),
):
    stmt = (
        select(InventoryMovement)
        .join(ProductVariant, ProductVariant.id == InventoryMovement.variant_id)
        .join(Warehouse, Warehouse.id == InventoryMovement.warehouse_id, isouter=True)
        .where(ProductVariant.product.has(store_id=store.id))
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )
    if variant_id:
        stmt = stmt.where(InventoryMovement.variant_id == variant_id)
    rows = db.scalars(stmt).all()
    return [MovementOut.model_validate({"id": row.id, "variant_id": row.variant_id, "sku": row.variant.sku, "product_name": row.variant.product.name, "warehouse_id": row.warehouse_id, "warehouse_name": row.warehouse.name if row.warehouse_id and row.warehouse else None, "delta": row.delta, "reason": row.reason.value, "order_id": row.order_id, "note": row.note, "created_at": row.created_at}) for row in rows]
