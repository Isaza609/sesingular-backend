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
    warehouse_id: str
    quantity: int = Field(ge=0)
    threshold: int = Field(default=5, ge=0)
    note: str | None = None


class StockOut(BaseModel):
    id: str
    variant_id: str
    sku: str
    product_id: str
    product_name: str
    warehouse_id: str
    warehouse_name: str
    quantity: int
    reserved: int
    available: int
    threshold: int
    updated_at: datetime


class MovementOut(BaseModel):
    id: str
    variant_id: str
    sku: str
    product_name: str
    warehouse_id: str | None
    warehouse_name: str | None
    delta: int
    reason: str
    order_id: str | None
    note: str | None
    created_at: datetime

