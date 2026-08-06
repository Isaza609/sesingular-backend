from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WarehouseIn(BaseModel):
    name: str = Field(description="Nombre del punto o almacen.", min_length=1, max_length=200, example="Bodega principal")
    address_line: str | None = Field(default=None, description="Direccion fisica del almacen.", max_length=300, example="Calle 10 # 20-30")
    city: str | None = Field(default=None, description="Ciudad o municipio del almacen.", max_length=120, example="Bogota")
    region: str | None = Field(default=None, description="Departamento o region.", max_length=120, example="Cundinamarca")
    is_default: bool = Field(default=False, description="Indica si sera el almacen operativo por defecto.", example=True)
    active: bool = Field(default=True, description="Indica si el almacen esta disponible para nuevas operaciones.", example=True)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Bodega principal",
                "address_line": "Calle 10 # 20-30",
                "city": "Bogota",
                "region": "Cundinamarca",
                "is_default": True,
                "active": True,
            }
        }
    }


class WarehousePatch(WarehouseIn):
    name: str | None = Field(default=None, description="Nombre actualizado del almacen.", min_length=1, max_length=200, example="Bodega norte")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Bodega norte",
                "address_line": "Carrera 15 # 80-20",
                "city": "Medellin",
                "region": "Antioquia",
                "is_default": False,
                "active": True,
            }
        }
    }


class WarehouseOut(BaseModel):
    id: str = Field(description="Identificador del almacen.", example="wh-123")
    name: str = Field(description="Nombre del punto o almacen.", example="Bodega principal")
    address_line: str | None = Field(default=None, description="Direccion fisica del almacen.", example="Calle 10 # 20-30")
    city: str | None = Field(default=None, description="Ciudad o municipio.", example="Bogota")
    region: str | None = Field(default=None, description="Departamento o region.", example="Cundinamarca")
    is_default: bool = Field(description="Indica si es el almacen por defecto.", example=True)
    active: bool = Field(description="Indica si esta disponible para nuevas operaciones.", example=True)
    requires_manual_dispatch_selection: bool = Field(description="Indica si la tienda requiere seleccionar almacen manualmente por tener varios activos.", example=False)


class StockPatch(BaseModel):
    warehouse_id: str = Field(description="Almacen de la tienda donde se ajusta el stock.", example="wh-123")
    quantity: int = Field(description="Cantidad fisica total que queda registrada en el almacen.", ge=0, example=12)
    threshold: int = Field(default=5, description="Umbral para alerta de stock bajo en este almacen.", ge=0, example=3)
    note: str | None = Field(default=None, description="Nota visible en el historial de movimientos.", example="Reposicion semanal")

    model_config = {
        "json_schema_extra": {
            "example": {
                "warehouse_id": "wh-123",
                "quantity": 12,
                "threshold": 3,
                "note": "Reposicion semanal",
            }
        }
    }


class StockOut(BaseModel):
    id: str = Field(description="Identificador del registro de stock.", example="stock-123")
    variant_id: str = Field(description="Variante asociada al stock.", example="variant-123")
    sku: str = Field(description="SKU de la variante.", example="CAM-S")
    product_id: str = Field(description="Producto asociado.", example="product-123")
    product_name: str = Field(description="Nombre del producto.", example="Camisa lino")
    warehouse_id: str = Field(description="Almacen asociado.", example="wh-123")
    warehouse_name: str = Field(description="Nombre del almacen.", example="Bodega principal")
    quantity: int = Field(description="Cantidad fisica en el almacen.", example=12)
    reserved: int = Field(description="Unidades reservadas para pedidos aun no despachados.", example=2)
    available: int = Field(description="Cantidad disponible para venta en este almacen.", example=10)
    threshold: int = Field(description="Umbral de alerta de stock bajo.", example=3)
    updated_at: datetime = Field(description="Fecha de ultima actualizacion.", example="2026-08-05T10:00:00Z")


class WarehouseStockOut(BaseModel):
    warehouse_id: str = Field(description="Identificador del almacen.", example="wh-123")
    warehouse_name: str = Field(description="Nombre del almacen.", example="Bodega principal")
    quantity: int = Field(description="Cantidad fisica en el almacen.", example=12)
    reserved: int = Field(description="Cantidad reservada en el almacen.", example=2)
    available: int = Field(description="Cantidad disponible en el almacen.", example=10)
    threshold: int = Field(description="Umbral de alerta configurado.", example=3)
    low_stock: bool = Field(description="Indica si esta por debajo o igual al umbral.", example=False)
    out_of_stock: bool = Field(description="Indica si no tiene disponible.", example=False)


class InventoryItemOut(BaseModel):
    variant_id: str = Field(description="Identificador de la variante.", example="variant-123")
    sku: str = Field(description="SKU de la variante.", example="CAM-S")
    product_id: str = Field(description="Identificador del producto.", example="product-123")
    product_name: str = Field(description="Nombre del producto.", example="Camisa lino")
    product_status: str = Field(description="Estado operativo del producto.", example="active")
    quantity: int = Field(description="Stock fisico agregado en almacenes activos.", example=20)
    reserved: int = Field(description="Reservado agregado en almacenes activos.", example=3)
    available: int = Field(description="Disponible agregado para compradores.", example=17)
    threshold: int = Field(description="Umbral minimo agregado usado para alerta.", example=3)
    low_stock: bool = Field(description="Indica si el disponible agregado esta bajo.", example=False)
    out_of_stock: bool = Field(description="Indica si la variante esta agotada.", example=False)
    warehouses: list[WarehouseStockOut] = Field(description="Desglose por almacen activo.")


class InventoryAlertOut(BaseModel):
    variant_id: str = Field(description="Variante que genera la alerta.", example="variant-123")
    sku: str = Field(description="SKU alertado.", example="CAM-S")
    product_id: str = Field(description="Producto asociado.", example="product-123")
    product_name: str = Field(description="Nombre del producto.", example="Camisa lino")
    alert_type: str = Field(description="Tipo de alerta: low_stock u out_of_stock.", example="low_stock")
    available: int = Field(description="Disponible actual agregado.", example=2)
    threshold: int = Field(description="Umbral configurado.", example=3)
    message: str = Field(description="Mensaje funcional de la alerta.", example="Stock bajo")


class MovementOut(BaseModel):
    id: str = Field(description="Identificador del movimiento.", example="mov-123")
    variant_id: str = Field(description="Variante afectada.", example="variant-123")
    sku: str = Field(description="SKU afectado.", example="CAM-S")
    product_id: str = Field(description="Producto afectado.", example="product-123")
    product_name: str = Field(description="Nombre del producto.", example="Camisa lino")
    warehouse_id: str | None = Field(default=None, description="Almacen afectado cuando aplica.", example="wh-123")
    warehouse_name: str | None = Field(default=None, description="Nombre del almacen cuando aplica.", example="Bodega principal")
    delta: int = Field(description="Cambio fisico de stock; reservas/liberaciones usan 0.", example=-2)
    reason: str = Field(description="Motivo del movimiento.", example="sale")
    order_id: str | None = Field(default=None, description="Pedido relacionado cuando aplica.", example="order-123")
    note: str | None = Field(default=None, description="Nota del movimiento.", example="Salida por venta")
    created_at: datetime = Field(description="Fecha del movimiento.", example="2026-08-05T10:00:00Z")


class PublicStockOut(BaseModel):
    variant_id: str = Field(description="Identificador de la variante.", example="variant-123")
    stock: int = Field(description="Disponible agregado para compradores.", example=8)
    available: bool = Field(description="Indica si se puede comprar.", example=True)
    low_stock: bool = Field(description="Indica si queda poco stock.", example=False)
    out_of_stock: bool = Field(description="Indica si esta agotada.", example=False)
