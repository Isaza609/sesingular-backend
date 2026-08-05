from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromotionIn(BaseModel):
    name: str = Field(description="Nombre visible interno de la promocion.", min_length=1, max_length=200, example="Compra 3 paga 2")
    discount_type: str = Field(description="Tipo de promocion: percent, fixed o volume.", pattern="^(percent|fixed|volume)$", example="volume")
    value: int = Field(description="Valor del descuento: porcentaje, monto fijo o unidades gratis si es volumen.", ge=0, example=1)
    min_quantity: int | None = Field(default=None, description="Cantidad minima para promociones de volumen.", ge=1, example=3)
    pay_quantity: int | None = Field(default=None, description="Cantidad que se paga dentro del grupo de volumen; si se envia, reemplaza unidades gratis.", ge=1, example=2)
    scope: str = Field(default="store", description="Alcance de la promocion: toda la tienda o productos especificos.", pattern="^(store|products)$", example="products")
    product_ids: list[str] = Field(default_factory=list, description="Productos propios incluidos cuando scope=products.", example=["prod-collar"])
    starts_at: datetime | None = Field(default=None, description="Inicio de vigencia.", example="2026-08-01T00:00:00Z")
    ends_at: datetime | None = Field(default=None, description="Fin de vigencia.", example="2026-08-31T23:59:59Z")
    active: bool = Field(default=True, description="Indica si la promocion aplica a pedidos nuevos.", example=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Compra 3 paga 2",
                "discount_type": "volume",
                "value": 1,
                "min_quantity": 3,
                "pay_quantity": 2,
                "scope": "products",
                "product_ids": ["prod-collar"],
                "starts_at": "2026-08-01T00:00:00Z",
                "ends_at": "2026-08-31T23:59:59Z",
                "active": True,
            }
        }
    )


class PromotionPatch(PromotionIn):
    name: str | None = Field(default=None, description="Nombre actualizado de la promocion.", min_length=1, max_length=200, example="Compra 4 paga 3")
    discount_type: str | None = Field(default=None, description="Nuevo tipo de promocion.", pattern="^(percent|fixed|volume)$", example="percent")
    value: int | None = Field(default=None, description="Nuevo valor del descuento.", ge=0, example=10)
    scope: str | None = Field(default=None, description="Nuevo alcance.", pattern="^(store|products)$", example="store")


class CouponIn(BaseModel):
    code: str = Field(description="Codigo ingresado por el comprador; se normaliza a mayusculas.", min_length=1, max_length=60, example="VERANO10")
    discount_type: str = Field(description="Tipo de descuento del cupon.", pattern="^(percent|fixed)$", example="percent")
    value: int = Field(description="Porcentaje o valor fijo del cupon.", ge=0, example=10)
    max_uses: int | None = Field(default=None, description="Limite de usos del cupon.", ge=1, example=100)
    scope: str = Field(default="store", description="Alcance del cupon: tienda completa o productos especificos.", pattern="^(store|products)$", example="store")
    product_ids: list[str] = Field(default_factory=list, description="Productos propios incluidos cuando scope=products.", example=[])
    starts_at: datetime | None = Field(default=None, description="Inicio de vigencia.", example="2026-08-01T00:00:00Z")
    ends_at: datetime | None = Field(default=None, description="Fin de vigencia.", example="2026-08-31T23:59:59Z")
    active: bool = Field(default=True, description="Indica si el cupon puede usarse en pedidos nuevos.", example=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VERANO10",
                "discount_type": "percent",
                "value": 10,
                "max_uses": 100,
                "scope": "store",
                "product_ids": [],
                "starts_at": "2026-08-01T00:00:00Z",
                "ends_at": "2026-08-31T23:59:59Z",
                "active": True,
            }
        }
    )


class CouponPatch(CouponIn):
    code: str | None = Field(default=None, description="Codigo actualizado.", min_length=1, max_length=60, example="VERANO15")
    discount_type: str | None = Field(default=None, description="Nuevo tipo de descuento.", pattern="^(percent|fixed)$", example="fixed")
    value: int | None = Field(default=None, description="Nuevo valor del cupon.", ge=0, example=15000)
    scope: str | None = Field(default=None, description="Nuevo alcance.", pattern="^(store|products)$", example="products")


class PromotionOut(BaseModel):
    id: str = Field(description="Identificador de promocion o cupon.", example="promo-123")
    store_id: str = Field(description="Tienda propietaria.", example="store-123")
    code: str | None = Field(default=None, description="Codigo cuando la fila representa un cupon.", example="VERANO10")
    name: str | None = Field(default=None, description="Nombre cuando la fila representa una promocion.", example="Compra 3 paga 2")
    discount_type: str = Field(description="Tipo de descuento.", example="percent")
    value: int = Field(description="Valor configurado.", example=10)
    min_quantity: int | None = Field(default=None, description="Cantidad minima para volumen.", example=3)
    pay_quantity: int | None = Field(default=None, description="Cantidad pagada para volumen.", example=2)
    max_uses: int | None = Field(default=None, description="Limite de usos del cupon.", example=100)
    used_count: int | None = Field(default=None, description="Usos consumidos del cupon.", example=4)
    scope: str = Field(description="Alcance configurado.", example="store")
    product_ids: list[str] = Field(default_factory=list, description="Productos incluidos si scope=products.", example=["prod-collar"])
    starts_at: datetime | None = Field(default=None, description="Inicio de vigencia.", example="2026-08-01T00:00:00Z")
    ends_at: datetime | None = Field(default=None, description="Fin de vigencia.", example="2026-08-31T23:59:59Z")
    active: bool = Field(description="Indica si aplica a pedidos nuevos.", example=True)
    created_at: datetime = Field(description="Fecha de creacion.", example="2026-08-05T10:00:00Z")


class ExtraChargeIn(BaseModel):
    name: str = Field(description="Nombre visible para el comprador en checkout.", min_length=1, max_length=200, example="Empaque para regalo")
    charge_type: str = Field(description="Tipo de cargo: valor fijo o porcentaje.", pattern="^(fixed|percent)$", example="fixed")
    value: int = Field(description="Valor del cargo en COP o porcentaje.", ge=0, example=5000)
    scope: str = Field(default="store", description="Alcance del cargo: tienda completa o productos especificos.", pattern="^(store|products)$", example="store")
    product_ids: list[str] = Field(default_factory=list, description="Productos propios incluidos cuando scope=products.", example=[])
    active: bool = Field(default=True, description="Indica si aplica a pedidos nuevos.", example=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Empaque para regalo",
                "charge_type": "fixed",
                "value": 5000,
                "scope": "store",
                "product_ids": [],
                "active": True,
            }
        }
    )


class ExtraChargePatch(ExtraChargeIn):
    name: str | None = Field(default=None, description="Nombre visible actualizado.", min_length=1, max_length=200, example="Empaque premium")
    charge_type: str | None = Field(default=None, description="Nuevo tipo de cargo.", pattern="^(fixed|percent)$", example="percent")
    value: int | None = Field(default=None, description="Nuevo valor del cargo.", ge=0, example=19)
    scope: str | None = Field(default=None, description="Nuevo alcance.", pattern="^(store|products)$", example="products")


class ExtraChargeOut(BaseModel):
    id: str = Field(description="Identificador del cargo extra.", example="charge-123")
    store_id: str = Field(description="Tienda propietaria.", example="store-123")
    name: str = Field(description="Nombre visible en checkout.", example="Empaque para regalo")
    charge_type: str = Field(description="Tipo de cargo.", example="fixed")
    value: int = Field(description="Valor configurado.", example=5000)
    scope: str = Field(description="Alcance configurado.", example="store")
    product_ids: list[str] = Field(default_factory=list, description="Productos incluidos si scope=products.", example=[])
    active: bool = Field(description="Indica si aplica a pedidos nuevos.", example=True)
    created_at: datetime = Field(description="Fecha de creacion.", example="2026-08-05T10:00:00Z")
    updated_at: datetime = Field(description="Fecha de actualizacion.", example="2026-08-05T10:00:00Z")


class PayoutAccountIn(BaseModel):
    """Cuenta de cobro manual del vendedor: transferencia bancaria o Bre-B."""

    type: str = Field(default="bank", pattern="^(bank|bre_b)$")
    label: str | None = Field(default=None, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    account_type: str | None = Field(default=None, pattern="^(ahorros|corriente)$")
    account_number: str | None = Field(default=None, max_length=60)
    breb_key: str | None = Field(default=None, max_length=120)
    holder_name: str = Field(min_length=1, max_length=200)
    holder_document: str | None = Field(default=None, max_length=40)
    active: bool = True

    @model_validator(mode="after")
    def check_required_by_type(self):
        if self.type == "bank" and not (self.bank_name and self.account_number):
            raise ValueError("Una cuenta bancaria requiere banco y número de cuenta")
        if self.type == "bre_b" and not self.breb_key:
            raise ValueError("Una cuenta Bre-B requiere la llave")
        return self


class PayoutAccountPatch(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    account_type: str | None = Field(default=None, pattern="^(ahorros|corriente)$")
    account_number: str | None = Field(default=None, max_length=60)
    breb_key: str | None = Field(default=None, max_length=120)
    holder_name: str | None = Field(default=None, min_length=1, max_length=200)
    holder_document: str | None = Field(default=None, max_length=40)
    active: bool | None = None


class PaymentConfirmIn(BaseModel):
    """El vendedor registra el monto realmente recibido al confirmar."""

    received_amount: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


class PaymentRejectIn(BaseModel):
    note: str = Field(min_length=1, max_length=500)


class SellerStoreMemberOut(BaseModel):
    user_id: str = Field(description="Identificador del usuario de la tienda.", example="4c1a3d6e-7f2d-4e9b-9b9a-8e6f2c4a1234")
    email: str = Field(description="Correo del usuario.", example="equipo@example.com")
    name: str = Field(description="Nombre del usuario.", example="Laura Gomez")
    phone: str | None = Field(default=None, description="Telefono de contacto.", example="+573002223333")
    member_role: str = Field(description="Rol interno dentro de la tienda.", example="staff")
    active: bool = Field(description="Indica si el usuario mantiene acceso.", example=True)
    must_change_password: bool = Field(description="Indica si debe cambiar contrasena antes de operar.", example=False)
    created_at: datetime = Field(description="Fecha en que fue asociado a la tienda.", example="2026-08-05T10:00:00Z")

