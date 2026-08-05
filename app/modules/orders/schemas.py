from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AddressIn(BaseModel):
    label: str | None = Field(default=None, description="Etiqueta visible para el comprador.", max_length=80, example="Casa")
    recipient_name: str = Field(description="Nombre de quien recibe el envio.", min_length=1, max_length=200, example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto para la entrega.", max_length=40, example="+573001112233")
    address_line: str = Field(description="Direccion completa de entrega.", min_length=1, max_length=300, example="Calle 10 # 20-30")
    city: str = Field(description="Ciudad o municipio de entrega.", min_length=1, max_length=120, example="Bogota")
    region: str | None = Field(default=None, description="Departamento, provincia o region.", max_length=120, example="Cundinamarca")
    postal_code: str | None = Field(default=None, description="Codigo postal opcional.", max_length=20, example="110111")
    is_default: bool = Field(default=False, description="Indica si sera la direccion por defecto.", example=True)

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Casa",
                "recipient_name": "Ana Perez",
                "phone": "+573001112233",
                "address_line": "Calle 10 # 20-30",
                "city": "Bogota",
                "region": "Cundinamarca",
                "postal_code": "110111",
                "is_default": True,
            }
        }
    }


class AddressPatch(AddressIn):
    recipient_name: str | None = Field(default=None, description="Nombre actualizado de quien recibe.", min_length=1, max_length=200, example="Ana Maria Perez")
    address_line: str | None = Field(default=None, description="Direccion completa actualizada.", min_length=1, max_length=300, example="Carrera 15 # 80-20")
    city: str | None = Field(default=None, description="Ciudad o municipio actualizado.", min_length=1, max_length=120, example="Medellin")

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Apartamento",
                "recipient_name": "Ana Maria Perez",
                "phone": "+573004445566",
                "address_line": "Carrera 15 # 80-20",
                "city": "Medellin",
                "region": "Antioquia",
                "postal_code": "050021",
                "is_default": True,
            }
        }
    }


class AddressOut(BaseModel):
    id: str = Field(description="Identificador de la direccion.", example="addr-123")
    label: str | None = Field(default=None, description="Etiqueta visible para el comprador.", example="Casa")
    recipient_name: str = Field(description="Nombre de quien recibe el envio.", example="Ana Perez")
    phone: str | None = Field(default=None, description="Telefono de contacto para la entrega.", example="+573001112233")
    address_line: str = Field(description="Direccion completa de entrega.", example="Calle 10 # 20-30")
    city: str = Field(description="Ciudad o municipio de entrega.", example="Bogota")
    region: str | None = Field(default=None, description="Departamento, provincia o region.", example="Cundinamarca")
    postal_code: str | None = Field(default=None, description="Codigo postal opcional.", example="110111")
    is_default: bool = Field(description="Indica si es la direccion por defecto.", example=True)


class CartItemIn(BaseModel):
    variant_id: str | None = None
    product_id: str | None = None
    color: str | None = None
    quantity: int = Field(ge=1, le=100)

    @model_validator(mode="after")
    def variant_or_product(self):
        if not self.variant_id and not self.product_id:
            raise ValueError("Debes indicar variant_id o product_id")
        return self


class CartItemPatch(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CheckoutIn(BaseModel):
    address_id: str | None = None
    address: AddressIn | None = None
    coupon_code: str | None = None
    payment_method: str = Field(default="card", min_length=1, max_length=60)
    # Cuenta de cobro elegida cuando el método es manual (transfer | breb)
    payout_account_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def address_required(self):
        if not self.address_id and not self.address:
            raise ValueError("Debes seleccionar o registrar una dirección")
        return self


class OrderStatusPatch(BaseModel):
    status: str = Field(pattern="^(pending|confirmed|preparing|shipped|delivered|cancelled|returned)$")


class WarehouseAssign(BaseModel):
    warehouse_id: str


class OrderItemOut(BaseModel):
    id: str
    variant_id: str | None
    product_name: str
    sku: str | None
    quantity: int
    unit_price: int
    unit_cost: int | None


class CheckoutAdjustmentOut(BaseModel):
    kind: str = Field(description="Tipo de linea: discount o extra_charge.", example="extra_charge")
    source_type: str | None = Field(default=None, description="Origen funcional de la linea.", example="extra_charge")
    source_id: str | None = Field(default=None, description="Identificador del origen cuando aplica.", example="charge-123")
    name: str = Field(description="Nombre visible de la linea.", example="Empaque para regalo")
    amount: int = Field(description="Monto positivo de la linea en COP.", example=5000)
    code: str | None = Field(default=None, description="Codigo de cupon cuando aplica.", example="VERANO10")


class OrderOut(BaseModel):
    id: str
    store_id: str
    store_name: str
    buyer_id: str | None
    buyer_name: str | None = None
    warehouse_id: str | None
    address_id: str | None
    channel: str
    status: str
    subtotal: int
    shipping_cost: int
    tax: int
    total: int
    notes: str | None
    created_at: datetime
    items: list[OrderItemOut]
    adjustments: list[CheckoutAdjustmentOut] = Field(default_factory=list)
    payments: list[dict]


class CartOut(BaseModel):
    id: str
    items: list[dict]
    regular_subtotal: int = 0
    subtotal: int
    shipping_cost: int
    tax: int
    total: int


class CheckoutQuoteOut(BaseModel):
    subtotal: int = Field(description="Subtotal despues de descuentos.", example=95000)
    regular_subtotal: int = Field(description="Subtotal regular antes de precios especiales.", example=110000)
    discount: int = Field(description="Total descontado.", example=15000)
    discounts: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Descuentos aplicados por promocion o cupon.")
    extra_charge_total: int = Field(description="Total de cargos extra definidos por vendedor.", example=5000)
    extra_charges: list[CheckoutAdjustmentOut] = Field(default_factory=list, description="Cargos extra aplicados por separado.")
    shipping_cost: int = Field(description="Costo de envio.", example=12900)
    tax: int = Field(description="Impuestos automaticos de plataforma; permanece en cero porque los cargos son manuales.", example=0)
    total: int = Field(description="Total final.", example=112900)
    currency: str = Field(description="Moneda.", example="COP")


class PosItemIn(BaseModel):
    variant_id: str
    quantity: int = Field(ge=1, le=1000)


class PosOrderIn(BaseModel):
    items: list[PosItemIn] = Field(min_length=1)
    buyer_id: str | None = None
    payment_method: str = Field(default="cash", min_length=1, max_length=60)
    notes: str | None = None

