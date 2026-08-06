from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Page(BaseModel):
    total: int
    page: int
    page_size: int


class UserOut(BaseModel):
    id: str = Field(description="Identificador del usuario.", example="4c1a3d6e-7f2d-4e9b-9b9a-8e6f2c4a1234")
    email: str = Field(description="Correo electronico del usuario.", example="vendedor@example.com")
    name: str = Field(description="Nombre visible del usuario.", example="Carlos Rojas")
    phone: str | None = Field(default=None, description="Telefono de contacto.", example="+573001112233")
    role: str = Field(description="Rol de plataforma.", example="seller")
    active: bool = Field(description="Indica si el usuario puede acceder.", example=True)
    must_change_password: bool = Field(description="Indica si debe cambiar contrasena antes de operar.", example=True)
    temporary_password_expires_at: datetime | None = Field(default=None, description="Vencimiento de la credencial temporal.", example="2026-08-06T10:00:00Z")
    created_at: datetime = Field(description="Fecha de creacion.", example="2026-08-05T10:00:00Z")


class UserListOut(Page):
    items: list[UserOut]


class UserPatch(BaseModel):
    active: bool | None = Field(default=None, description="Activa o desactiva el usuario.", example=False)
    role: Literal["buyer", "seller", "admin"] | None = Field(default=None, description="Nuevo rol de plataforma.", example="seller")

    model_config = ConfigDict(json_schema_extra={"example": {"active": False}})


class UserCreate(BaseModel):
    id: str | None = Field(default=None, description="Identificador externo opcional; si no se envia, lo retorna Supabase.", example="4c1a3d6e-7f2d-4e9b-9b9a-8e6f2c4a1234")
    email: str = Field(description="Correo electronico del usuario.", pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", example="vendedor@example.com")
    name: str = Field(description="Nombre visible del usuario.", min_length=1, max_length=200, example="Carlos Rojas")
    phone: str | None = Field(default=None, description="Telefono de contacto.", max_length=40, example="+573001112233")
    role: Literal["buyer", "seller", "admin"] = Field(default="buyer", description="Rol que asigna administracion.", example="seller")
    temporary_password: str | None = Field(default=None, description="Contrasena temporal opcional; si no se envia, se genera.", min_length=8, example="TempSegura123")
    temporary_password_hours: int = Field(default=24, description="Horas de vigencia de la contrasena temporal.", ge=1, le=168, example=24)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "vendedor@example.com",
                "name": "Carlos Rojas",
                "phone": "+573001112233",
                "role": "seller",
                "temporary_password_hours": 24,
            }
        }
    )


class UserCreateOut(UserOut):
    temporary_password: str | None = Field(default=None, description="Credencial temporal visible una sola vez para entrega segura.", example="TempSegura123")


class TemporaryPasswordOut(BaseModel):
    user: UserOut = Field(description="Usuario actualizado con cambio obligatorio pendiente.")
    temporary_password: str = Field(description="Nueva credencial temporal visible una sola vez.", example="TempSegura123")


class StoreOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    logo_url: str | None
    contact_email: str | None
    contact_phone: str | None
    active: bool
    created_at: datetime


class StoreListOut(Page):
    items: list[StoreOut]


class StoreDetailOut(StoreOut):
    members: int
    warehouses: int
    products: int


class StorePatch(BaseModel):
    active: bool


class StoreCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    owner_user_id: str | None = None


class StoreMemberCreate(BaseModel):
    email: str = Field(description="Correo del usuario adicional de la tienda.", pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", example="equipo@example.com")
    name: str = Field(description="Nombre del usuario de equipo.", min_length=1, max_length=200, example="Laura Gomez")
    phone: str | None = Field(default=None, description="Telefono de contacto.", max_length=40, example="+573002223333")
    member_role: str = Field(default="staff", description="Rol interno dentro de la tienda.", max_length=40, example="staff")
    temporary_password: str | None = Field(default=None, description="Credencial temporal opcional.", min_length=8, example="EquipoTemp123")
    temporary_password_hours: int = Field(default=24, description="Horas de vigencia de la credencial temporal.", ge=1, le=168, example=24)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "equipo@example.com",
                "name": "Laura Gomez",
                "phone": "+573002223333",
                "member_role": "staff",
                "temporary_password_hours": 24,
            }
        }
    )


class StoreMemberPatch(BaseModel):
    active: bool | None = Field(default=None, description="Activa o desactiva el usuario de equipo.", example=False)
    member_role: str | None = Field(default=None, description="Rol interno dentro de la tienda.", max_length=40, example="manager")

    model_config = ConfigDict(json_schema_extra={"example": {"active": False, "member_role": "staff"}})


class StoreMemberOut(BaseModel):
    user_id: str = Field(description="Identificador del usuario.", example="4c1a3d6e-7f2d-4e9b-9b9a-8e6f2c4a1234")
    store_id: str = Field(description="Identificador de la tienda.", example="store-123")
    email: str = Field(description="Correo del miembro.", example="equipo@example.com")
    name: str = Field(description="Nombre del miembro.", example="Laura Gomez")
    phone: str | None = Field(default=None, description="Telefono del miembro.", example="+573002223333")
    platform_role: str = Field(description="Rol de plataforma.", example="seller")
    member_role: str = Field(description="Rol interno de tienda.", example="staff")
    active: bool = Field(description="Indica si conserva acceso.", example=True)
    must_change_password: bool = Field(description="Indica si debe cambiar contrasena antes de operar.", example=True)
    created_at: datetime = Field(description="Fecha de asociacion a la tienda.", example="2026-08-05T10:00:00Z")


class StoreMemberCreateOut(StoreMemberOut):
    temporary_password: str = Field(description="Credencial temporal visible una sola vez.", example="EquipoTemp123")


class CommissionIn(BaseModel):
    type: Literal["percent", "fixed"] = "percent"
    value: int = Field(ge=0)


class GatewayIn(BaseModel):
    provider: str = "mercadopago"
    sandbox: bool = True
    public_key: str = ""
    webhook_url: str = ""
    # Si llegan vacíos se conserva el valor guardado (no se borra el secreto)
    access_token: str = ""
    webhook_secret: str = ""


class SettingOut(BaseModel):
    key: str
    value: dict
    updated_at: datetime


class SalesReportOut(BaseModel):
    totals: dict
    by_channel: list[dict]
    by_store: list[dict]
    by_day: list[dict]


class InventoryReportOut(BaseModel):
    stores: list[dict]
    warehouses: list[dict]


class ReportedReviewOut(BaseModel):
    report_id: str
    report_reason: str
    report_status: str
    report_created_at: datetime
    review_id: str
    review_status: str
    rating: int
    comment: str | None
    product_name: str
    store_name: str
    reviewer_name: str | None


class ReviewPatch(BaseModel):
    status: Literal["published", "hidden"]


class ReportPatch(BaseModel):
    status: Literal["resolved", "dismissed"]
    resolution_note: str = ""


class DisputeOut(BaseModel):
    id: str
    order_id: str
    reason: str
    description: str | None
    status: str
    resolution_note: str | None
    store_name: str | None
    opener_name: str | None
    created_at: datetime


class DisputePatch(BaseModel):
    status: Literal["open", "in_review", "resolved", "rejected"]
    resolution_note: str = ""


class TransactionEventOut(BaseModel):
    id: str = Field(description="Identificador del asiento del historial.", example="evt-123")
    from_status: str | None = Field(default=None, description="Estado anterior (nulo en el primer evento).", example="in_review")
    to_status: str = Field(description="Estado al que paso la transaccion.", example="paid")
    actor_role: str | None = Field(default=None, description="Quien origino el cambio: buyer, seller, admin, system o gateway.", example="seller")
    actor_user_id: str | None = Field(default=None, description="Usuario que origino el cambio, si aplica.", example="seller-123")
    received_amount: int | None = Field(default=None, description="Monto recibido registrado en el evento, si aplica.", example=110000)
    note: str | None = Field(default=None, description="Nota o novedad del evento.", example="Coincide con el total")
    created_at: datetime = Field(description="Fecha del evento.", example="2026-08-05T11:00:00Z")


class TransactionOut(BaseModel):
    id: str = Field(description="Identificador de la transaccion (pago).", example="pay-123")
    order_id: str = Field(description="Pedido asociado.", example="order-123")
    store_id: str = Field(description="Tienda asociada.", example="store-123")
    store_name: str | None = Field(default=None, description="Nombre de la tienda.", example="Nova Ropa")
    buyer_id: str | None = Field(default=None, description="Comprador asociado.", example="buyer-123")
    buyer_name: str | None = Field(default=None, description="Nombre del comprador.", example="Ana Perez")
    provider: str = Field(description="Proveedor: manual, pos, pending o pasarela.", example="manual")
    method: str | None = Field(default=None, description="Metodo de pago.", example="transfer")
    status: str = Field(description="Estado vigente de la transaccion.", example="paid")
    amount: int = Field(description="Monto esperado.", example=110000)
    received_amount: int | None = Field(default=None, description="Monto recibido registrado.", example=110000)
    currency: str = Field(description="Moneda.", example="COP")
    created_at: datetime = Field(description="Fecha de creacion de la transaccion.", example="2026-08-05T10:00:00Z")
    events: list[TransactionEventOut] = Field(default_factory=list, description="Historial de estados (solo en el detalle).")


class TransactionListOut(BaseModel):
    items: list[TransactionOut] = Field(description="Transacciones que cumplen los filtros.")
    total: int = Field(description="Cantidad de transacciones devueltas.", example=1)
